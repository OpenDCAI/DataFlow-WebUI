import json
import inspect
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional, Callable
from loguru import logger as log
from dataflow.utils.registry import OPERATOR_REGISTRY, PROMPT_REGISTRY
from app.core.config import settings

# --- 1. 路径定义 ---
# __file__ 是: .../backend/app/services/operator_registry.py
# .parent.parent.parent 是: .../backend
BACKEND_DIR = Path(__file__).parent.parent.parent
OPS_JSON_PATH = BACKEND_DIR / settings.OPS_JSON_PATH
RESOURCE_DIR = OPS_JSON_PATH.parent


# --- 2. 私有辅助函数 (模块内部实现) ---

def _safe_json_val(val: Any) -> Any:
    """
    将 inspect.Parameter.empty 和其他非序列化值转为 JSON 安全的值
    """
    if val is inspect.Parameter.empty:
        return None  # 在 JSON 中，"无默认值" 用 null 表示
    
    if isinstance(val, type) or callable(val):
        return str(val)
        
    try:
        json.dumps(val)
        return val
    except TypeError:
        return str(val)

def _param_to_dict(p: inspect.Parameter) -> Dict[str, Any]:
    """把 inspect.Parameter 转成 JSON 可序列化的字典"""
    return {
        "name": p.name,
        "default_value": _safe_json_val(p.default),
        "kind": p.kind.name,  # POSITIONAL_OR_KEYWORD / VAR_POSITIONAL / ...
    }

def _get_method_params(
    method: Any, skip_first_self: bool = False
) -> List[Dict[str, Any]]:
    """
    提取方法形参，转换为列表。
    skip_first_self=True 时会丢掉第一个 'self' 参数。
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
    仅当类的 get_desc 被显式声明为 @staticmethod 时才调用。
    如果 get_desc 返回一个列表，则自动用换行符拼接成字符串。
    """
    func_obj = cls.__dict__.get("get_desc")
    if not isinstance(func_obj, staticmethod):
        return "N/A (非 staticmethod)" 

    fn = func_obj.__func__
    params = list(inspect.signature(fn).parameters)
    try:
        # --- 变更开始 ---
        result: Any = None
        if params == ["lang"]:
            result = fn(lang)
        elif params == ["self", "lang"]:
            result = fn(None, lang)
        else:
            # 签名不匹配
            return "N/A (签名不匹配)"

        # 核心修复：检查返回类型
        if isinstance(result, list):
            return "\n".join(str(item) for item in result)  # 将列表拼接为字符串
        elif result:
            return str(result)  # 确保返回的是字符串
        # --- 变更结束 ---

    except Exception as e:
        log.warning(f"Failed to call {cls.__name__}.get_desc: {e}")
    
    return "N/A (Call failed)"

def _gather_single_operator(
    op_name: str, cls: type, node_index: int
) -> Tuple[str, Dict[str, Any]]:
    """
    收集单个算子的全部详细信息，用于生成缓存。
    """
    # 1) 分类（大类 category，用于 ops.json 的顶层 key）
    category = "unknown"
    if hasattr(cls, "__module__"):
        parts = cls.__module__.split(".")
        if len(parts) >= 3 and parts[0] == "dataflow" and parts[1] == "operators":
            category = parts[2]

    # 2) 描述 (使用 staticmethod 逻辑)
    description = _call_get_desc_static(cls, lang="zh") or ""

    # 3) 简化信息里也有的 type（三级分类）和 allowed_prompts
    op_type_category = OPERATOR_REGISTRY.get_type_of_objects().get(op_name, "Unknown/Unknown")
    # 新格式: ['dataflow', 'operators', 'core_text', 'generate', 'text2qa_generator']
    # [0]=dataflow前缀, [1]=operators, [2]=level_1大类, [3]=level_2类型, [4]=具体名称
    type1 = op_type_category[2] if len(op_type_category) > 2 else "Unknown"  # level_1: 算子大类（如 core_text）
    type2 = op_type_category[3] if len(op_type_category) > 3 else "Unknown"  # level_2: 算子类型（如 generate/filter/eval）

    allowed_prompt_templates = getattr(cls, "ALLOWED_PROMPTS", [])
    allowed_prompt_templates = [prompt_name.__name__ for prompt_name in allowed_prompt_templates]

    # 4) command 形参
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


# --- 3. 公共服务类 ---

class OperatorRegistry:
    """
    封装所有算子(Operator)相关的业务逻辑，
    包括加载、实时查询和生成缓存。
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
        """获取简化的算子列表 (实时计算)，用于前端列表展示。"""

        op_list: list[dict] = []
        for op_name, op_cls in self.op_obj_map.items():
            # 类型信息，三级分类
            op_type_category = self.op_to_type.get(op_name, "Unknown/Unknown")

            # 新格式: ['dataflow', 'operators', 'core_text', 'generate', 'text2qa_generator']
            # [0]=dataflow前缀, [1]=operators, [2]=level_1大类, [3]=level_2类型, [4]=具体名称
            type1 = op_type_category[2] if len(op_type_category) > 2 else "Unknown"   # level_1: 算子大类（如 core_text）
            type2 = op_type_category[3] if len(op_type_category) > 3 else "Unknown"   # level_2: 算子类型（如 generate/filter/eval）

            # 描述
            if hasattr(op_cls, "get_desc") and callable(op_cls.get_desc):
                desc = op_cls.get_desc(lang=lang)
            else:
                desc = "N/A"
            desc = str(desc)

            # prompt template
            allowed_prompt_templates = getattr(op_cls, "ALLOWED_PROMPTS", [])
            allowed_prompt_templates = [prompt_name.__name__ for prompt_name in allowed_prompt_templates]

            # get parameter info in .run()（这里只保留简要信息，不展开参数细节）
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
    

    def dump_ops_to_json(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Execute a full operator scan, including detailed parameters, and write to ops.json cache file.
        This is a time-consuming operation.
        """
        log.info(f"Scanning operators (dump_ops_to_json) to generate {OPS_JSON_PATH} ...")
        
        all_ops: Dict[str, List[Dict[str, Any]]] = {}
        default_bucket: List[Dict[str, Any]] = []

        idx = 1
        # 使用 __init__ 中加载好的 op_obj_map
        for op_name, cls in self.op_obj_map.items():
            # 调用私有辅助函数 _gather_single_operator
            category, info = _gather_single_operator(op_name, cls, idx)
            
            all_ops.setdefault(category, []).append(info)   
            default_bucket.append(info)                     
            idx += 1

        all_ops["Default"] = default_bucket

        # 确保目录存在
        RESOURCE_DIR.mkdir(parents=True, exist_ok=True)
        try:
            with open(OPS_JSON_PATH, "w", encoding="utf-8") as f:
                json.dump(all_ops, f, ensure_ascii=False, indent=2)
            log.info(f"Operator info successfully written to {OPS_JSON_PATH} ({len(default_bucket)} records)")
        except Exception as e:
            log.error(f"Failed to write {OPS_JSON_PATH}: {e}")
            raise # Throw exception to be caught by API layer

        return all_ops

    def get_op_details(self, op_name: str) -> Optional[Dict[str, Any]]:
        """获取单个算子的详细信息 (包含参数默认值)"""
        cls = self.op_obj_map.get(op_name)
        if not cls:
            return None
        
        # 使用模块内的 _gather_single_operator 函数
        # 注意：_gather_single_operator 需要 node_index，这里可以传 0 或 -1
        category, info = _gather_single_operator(op_name, cls, -1)
        return info
