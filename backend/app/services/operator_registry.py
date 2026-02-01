import json
import inspect
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional, Callable
from loguru import logger as log
from dataflow.utils.registry import OPERATOR_REGISTRY, PROMPT_REGISTRY
from app.core.config import settings

# --- 1. Path definitions ---
# __file__ is: .../backend/app/services/operator_registry.py
# .parent.parent.parent is: .../backend
BACKEND_DIR = Path(__file__).parent.parent.parent
OPS_JSON_PATH = BACKEND_DIR / settings.OPS_JSON_PATH
RESOURCE_DIR = OPS_JSON_PATH.parent


# --- 2. Private helper functions (module-internal) ---

def _safe_json_val(val: Any) -> Any:
    """
    Convert inspect.Parameter.empty and other non-serializable values to JSON-safe values.
    """
    if val is inspect.Parameter.empty:
        return None  # In JSON, "no default" is represented as null
    
    if isinstance(val, type) or callable(val):
        return str(val)
        
    try:
        json.dumps(val)
        return val
    except TypeError:
        return str(val)

def _param_to_dict(p: inspect.Parameter) -> Dict[str, Any]:
    """Convert inspect.Parameter to a JSON-serializable dict."""
    return {
        "name": p.name,
        "default_value": _safe_json_val(p.default),
        "kind": p.kind.name,
    }

def _get_method_params(
    method: Any, skip_first_self: bool = False
) -> List[Dict[str, Any]]:
    """
    Extract method parameters and convert to a list.
    When skip_first_self=True, the first 'self' parameter is dropped.
    """
    try:
        sig = inspect.signature(method)
        params = list(sig.parameters.values())
        if skip_first_self and params and params[0].name == "self":
            params = params[1:]
        return [_param_to_dict(p) for p in params]
    except Exception as e:
        log.warning(f"Error getting method {method} parameters: {e}")
        return []


def _call_get_desc_static(cls: type, lang: str = "zh") -> str | None:
    """
    Only call when the class's get_desc is explicitly declared as @staticmethod.
    If get_desc returns a list, join it with newlines into a string.
    """
    func_obj = cls.__dict__.get("get_desc")
    if not isinstance(func_obj, staticmethod):
        return "N/A (not staticmethod)"

    fn = func_obj.__func__
    params = list(inspect.signature(fn).parameters)
    try:
        result: Any = None
        if params == ["lang"]:
            result = fn(lang)
        elif params == ["self", "lang"]:
            result = fn(None, lang)
        else:
            return "N/A (signature mismatch)"

        if isinstance(result, list):
            return "\n".join(str(item) for item in result)
        elif result:
            return str(result)

    except Exception as e:
        log.warning(f"Failed to call {cls.__name__}.get_desc: {e}")

    return "N/A (Call failed)"


def _gather_single_operator(
    op_name: str, cls: type, node_index: int, lang: str = "zh"
) -> Tuple[str, Dict[str, Any]]:
    """
    Gather full details for a single operator, used for cache generation.
    """
    # 1) Category (top-level key for ops.json)
    category = "unknown"
    if hasattr(cls, "__module__"):
        parts = cls.__module__.split(".")
        if len(parts) >= 3 and parts[0] == "dataflow" and parts[1] == "operators":
            category = parts[2]

    # 2) Description (using staticmethod logic)
    description = _call_get_desc_static(cls, lang=lang) or ""

    # 3) Type (three-level classification) and allowed_prompts
    op_type_category = OPERATOR_REGISTRY.get_type_of_objects().get(op_name, "Unknown/Unknown")
    # Format: ['dataflow', 'operators', 'core_text', 'generate', 'text2qa_generator']
    # [0]=dataflow prefix, [1]=operators, [2]=level_1 category, [3]=level_2 type, [4]=concrete name
    type1 = op_type_category[2] if len(op_type_category) > 2 else "Unknown"
    type2 = op_type_category[3] if len(op_type_category) > 3 else "Unknown"

    allowed_prompt_templates = getattr(cls, "ALLOWED_PROMPTS", [])
    allowed_prompt_templates = [prompt_name.__name__ for prompt_name in allowed_prompt_templates]

    # 4) Command parameters
    init_params = _get_method_params(getattr(cls, "__init__", None), skip_first_self=True)
    run_params = _get_method_params(getattr(cls, "run", None), skip_first_self=True)

    info = {
        "node": node_index,
        "name": op_name,
        "description": description,
        "type": {
            "level_1": type1,
            "level_2": type2,
        },
        "allowed_prompts": allowed_prompt_templates,
        "parameter": {
            "init": init_params,
            "run": run_params,
        },
        "required": "",
        "depends_on": [],
        "mode": "",
    }
    return category, info


# --- 3. Public service class ---

class OperatorRegistry:
    """
    Encapsulates all operator-related business logic,
    including loading, live queries, and cache generation.
    """
    def __init__(self):
        self._op_registry = OPERATOR_REGISTRY
        self._prompt_registry = PROMPT_REGISTRY
        
        log.info("Initializing OperatorRegistry, loading all operators...")
        if hasattr(self._op_registry, "_init_loaders"):
            self._op_registry._init_loaders()
        if hasattr(self._op_registry, "_get_all"):
            self._op_registry._get_all()
        
        self.op_obj_map = self._op_registry.get_obj_map()
        self.op_to_type = self._op_registry.get_type_of_objects()
        log.info(f"Loaded {len(self.op_obj_map)} operators.")


    def get_op_list(self, lang: str = "zh") -> list[dict]:
        """Get simplified operator list (computed on demand) for frontend listing."""

        op_list: list[dict] = []
        for op_name, op_cls in self.op_obj_map.items():
            # Type info, three-level classification
            op_type_category = self.op_to_type.get(op_name, "Unknown/Unknown")

            # Format: ['dataflow', 'operators', 'core_text', 'generate', 'text2qa_generator']
            type1 = op_type_category[2] if len(op_type_category) > 2 else "Unknown"
            type2 = op_type_category[3] if len(op_type_category) > 3 else "Unknown"

            # Description
            if hasattr(op_cls, "get_desc") and callable(op_cls.get_desc):
                desc = op_cls.get_desc(lang=lang)
            else:
                desc = "N/A"
            desc = str(desc)

            # prompt template
            allowed_prompt_templates = getattr(op_cls, "ALLOWED_PROMPTS", [])
            allowed_prompt_templates = [prompt_name.__name__ for prompt_name in allowed_prompt_templates]

            # Parameter info from .run() (brief only, no full param details)
            op_info = {
                "name": op_name,
                "type": {
                    "level_1": type1,
                    "level_2": type2,
                },
                "description": desc,
                "allowed_prompts": allowed_prompt_templates,
            }
            op_list.append(op_info)

        return op_list
    

    def dump_ops_to_json(self, lang: str = "zh") -> Dict[str, List[Dict[str, Any]]]:
        """
        Run a full operator scan with detailed params and write to ops_{lang}.json cache.
        This is a heavy operation.
        """
        log.info(f"Scanning operators (dump_ops_to_json), generating {OPS_JSON_PATH.with_suffix(f'.{lang}.json')} ...")

        all_ops: Dict[str, List[Dict[str, Any]]] = {}
        default_bucket: List[Dict[str, Any]] = []

        idx = 1
        # Use op_obj_map loaded in __init__
        for op_name, cls in self.op_obj_map.items():
            # Call private helper _gather_single_operator
            category, info = _gather_single_operator(op_name, cls, idx, lang=lang)
            
            all_ops.setdefault(category, []).append(info)   
            default_bucket.append(info)                     
            idx += 1

        all_ops["Default"] = default_bucket

        # Ensure directory exists
        RESOURCE_DIR.mkdir(parents=True, exist_ok=True)
        try:
            with open(OPS_JSON_PATH.with_suffix(f'.{lang}.json'), "w", encoding="utf-8") as f:
                json.dump(all_ops, f, ensure_ascii=False, indent=2)
            log.info(f"Operator info written to {OPS_JSON_PATH.with_suffix(f'.{lang}.json')} ({len(default_bucket)} operators)")
        except Exception as e:
            log.error(f"Failed to write {OPS_JSON_PATH.with_suffix(f'.{lang}.json')}: {e}")
            raise

        return all_ops

    def get_op_details(self, op_name: str, lang: str = "zh") -> Optional[Dict[str, Any]]:
        """Get detailed info for a single operator (including param defaults)."""
        cls = self.op_obj_map.get(op_name)
        if not cls:
            return None

        # Use module-level _gather_single_operator; node_index can be 0 or -1 here
        category, info = _gather_single_operator(op_name, cls, -1, lang=lang)
        return info
