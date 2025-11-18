# app/services/operator_registry.py

import json
import inspect
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional, Callable
from loguru import logger as log
from dataflow.utils.registry import OPERATOR_REGISTRY, PROMPT_REGISTRY

# --- 1. 路径定义 ---
# __file__ 是: .../backend/app/services/operator_registry.py
# .parent.parent.parent 是: .../backend
BACKEND_DIR = Path(__file__).parent.parent.parent 
# 定义资源目录位于: .../backend/resources
RESOURCE_DIR = BACKEND_DIR / "resources"
# 定义缓存文件路径: .../backend/resources/ops.json
OPS_JSON_PATH = RESOURCE_DIR / "ops.json"


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
        "default": _safe_json_val(p.default),
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
        log.warning(f"获取方法 {method} 参数出错: {e}")
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
        log.warning(f"调用 {cls.__name__}.get_desc 失败: {e}")
    
    return "N/A (调用失败)"

def _gather_single_operator(
    op_name: str, cls: type, node_index: int
) -> Tuple[str, Dict[str, Any]]:
    """
    收集单个算子的全部详细信息，用于生成缓存。
    """
    # 1) 分类
    category = "unknown"
    if hasattr(cls, "__module__"):
        parts = cls.__module__.split(".")
        if len(parts) >= 3 and parts[0] == "dataflow" and parts[1] == "operators":
            category = parts[2]

    # 2) 描述 (使用 staticmethod 逻辑)
    description = _call_get_desc_static(cls, lang="zh") or ""

    # 3) command 形参
    init_params = _get_method_params(getattr(cls, "__init__", None), skip_first_self=True)
    run_params = _get_method_params(getattr(cls, "run", None), skip_first_self=True)

    info = {
        "node": node_index,
        "name": op_name,
        "description": description,
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
        
        log.info("初始化 OperatorRegistry，开始加载所有算子...")
        if hasattr(self._op_registry, "_init_loaders"):
            self._op_registry._init_loaders()
        if hasattr(self._op_registry, "_get_all"):
            self._op_registry._get_all()
        
        self.op_obj_map = self._op_registry.get_obj_map()
        self.op_to_type = self._op_registry.get_type_of_objects()
        log.info(f"加载完成，共 {len(self.op_obj_map)} 个算子。")


    def get_op_list(self, lang: str = "zh") -> list[dict]:
        """
        获取简化的算子列表 (实时计算)。
        此方法用于快速预览，不包含详细参数。
        """
        op_list = []
        for op_name, op_cls in self.op_obj_map.items():
            op_type_category = self.op_to_type.get(op_name, "Unknown/Unknown")
            
            _ = op_type_category[0] 
            type1 = op_type_category[1] if len(op_type_category) > 1 else "Unknown"
            type2 = op_type_category[2] if len(op_type_category) > 2 else "Unknown"

            # 描述 (使用原始的通用逻辑)
            if hasattr(op_cls, "get_desc") and callable(op_cls.get_desc):
                try:
                    desc = op_cls.get_desc(lang=lang)
                except TypeError:
                    # 兼容 staticmethod(self, lang) 这种调用
                    desc = _call_get_desc_static(op_cls, lang=lang)
            else:
                desc = "N/A"
            desc = str(desc)

            # prompt template
            allowed_prompt_templates = getattr(op_cls, "ALLOWED_PROMPTS", [])
            allowed_prompt_templates = [prompt_name.__name__ for prompt_name in allowed_prompt_templates]

            op_info = {
                "name": op_name,
                "type": {
                    "level_1": type1,
                    "level_2": type2
                },
                "description": desc,
                "allowed_prompts": allowed_prompt_templates
            }
            op_list.append(op_info)
        return op_list
    

    def dump_ops_to_json(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        执行一次完整的算子扫描，包含详细参数，并写入 ops.json 缓存文件。
        这是一个耗时操作。
        """
        log.info(f"开始扫描算子 (dump_ops_to_json)，生成 {OPS_JSON_PATH} ...")
        
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
            log.info(f"算子信息已成功写入 {OPS_JSON_PATH} (共 {len(default_bucket)} 个)")
        except Exception as e:
            log.error(f"写入 {OPS_JSON_PATH} 失败: {e}")
            raise # 抛出异常，让 API 层捕获

        return all_ops

# --- 4. 公共服务实例 ---
# API 层将导入这个单例
_op_registry = OperatorRegistry()