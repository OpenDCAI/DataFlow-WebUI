"""
算子工具服务层
提供算子库管理、源码获取等功能
从 DataFlow-Agent 的 op_tools.py 迁移而来
"""
import importlib
import inspect
import json
import os
import random
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

from dataflow.utils.registry import OPERATOR_REGISTRY
from app.core.config import settings


class OperatorToolsService:
    """算子工具服务类"""
    
    def __init__(self):
        self.resource_dir = Path(settings.DATA_DIR) / "operator_resources"
        self.resource_dir.mkdir(parents=True, exist_ok=True)
        self.ops_json_path = self.resource_dir / "ops.json"
        
        # 初始化 OPERATOR_REGISTRY
        if hasattr(OPERATOR_REGISTRY, "_init_loaders"):
            OPERATOR_REGISTRY._init_loaders()
        if hasattr(OPERATOR_REGISTRY, "_get_all"):
            OPERATOR_REGISTRY._get_all()
    
    # ============ 算子库管理部分 ============
    
    @staticmethod
    def _safe_json_val(val: Any) -> Any:
        """
        把任意 Python 对象转换成 JSON 可序列化的值
        """
        if val is inspect.Parameter.empty:
            return None
        
        if isinstance(val, (str, int, float, bool)) or val is None:
            return val
        
        if isinstance(val, type):
            return f"{val.__module__}.{val.__qualname__}"
        
        if getattr(val, "__origin__", None) is None and val.__class__.__name__ == "UnionType":
            return str(val)
        
        try:
            json.dumps(val)
            return val
        except TypeError:
            return str(val)
    
    @staticmethod
    def _call_get_desc_static(cls, lang: str = "zh") -> str | None:
        """
        调用类的 get_desc 静态方法
        """
        func_obj = cls.__dict__.get("get_desc")
        if not isinstance(func_obj, staticmethod):
            return None
        
        fn = func_obj.__func__
        params = list(inspect.signature(fn).parameters)
        try:
            if params == ["lang"]:
                return fn(lang)
            if params == ["self", "lang"]:
                return fn(None, lang)
        except Exception:
            pass
        return None
    
    @staticmethod
    def _param_to_dict(p: inspect.Parameter) -> Dict[str, Any]:
        """把 inspect.Parameter 转成字典"""
        return {
            "name": p.name,
            "default": OperatorToolsService._safe_json_val(p.default),
            "kind": p.kind.name,
        }
    
    @staticmethod
    def _get_method_params(method: Any, skip_first_self: bool = False) -> List[Dict[str, Any]]:
        """提取方法形参"""
        try:
            sig = inspect.signature(method)
            params = list(sig.parameters.values())
            if skip_first_self and params and params[0].name == "self":
                params = params[1:]
            return [OperatorToolsService._param_to_dict(p) for p in params]
        except Exception:
            return []
    
    @staticmethod
    def _get_operator_relative_path(cls: type) -> str:
        """获取算子类所在文件的相对路径"""
        try:
            file_path = Path(inspect.getfile(cls)).resolve()
        except (TypeError, OSError):
            return ""
        
        module_name = getattr(cls, "__module__", "") or ""
        root_module_name = module_name.split(".")[0] if module_name else ""
        candidate_roots: List[Path] = []
        
        if root_module_name:
            try:
                root_module = importlib.import_module(root_module_name)
                module_file = getattr(root_module, "__file__", None)
                if module_file:
                    module_dir = Path(module_file).resolve().parent
                    candidate_roots.extend([
                        module_dir.parent,
                        module_dir,
                    ])
            except Exception:
                pass
        
        candidate_roots.append(Path.cwd())
        
        for base in candidate_roots:
            if not base:
                continue
            try:
                rel_path = file_path.relative_to(base)
                return rel_path.as_posix()
            except ValueError:
                continue
        
        return file_path.as_posix()
    
    @staticmethod
    def _infer_operator_type(relative_path: str) -> str:
        """根据路径推断算子类型（eval/refine/filter/generate）"""
        valid_types = {"eval", "refine", "filter", "generate"}
        if not relative_path:
            return ""
        try:
            parent_dir = Path(relative_path).parent.name
        except Exception:
            return ""
        return parent_dir if parent_dir in valid_types else ""
    
    def _gather_single_operator(self, op_name: str, cls: type, node_index: int) -> Tuple[str, Dict[str, Any]]:
        """收集单个算子的全部信息"""
        # 分类
        category = "unknown"
        if hasattr(cls, "__module__"):
            parts = cls.__module__.split(".")
            if len(parts) >= 3 and parts[0] == "dataflow" and parts[1] == "operators":
                category = parts[2]
        
        # 描述
        description = self._call_get_desc_static(cls, lang="zh") or ""
        
        # 参数
        init_params = self._get_method_params(cls.__init__, skip_first_self=True)
        run_params = self._get_method_params(getattr(cls, "run", None), skip_first_self=True)
        
        # 路径
        relative_path = self._get_operator_relative_path(cls)
        operation_type = self._infer_operator_type(relative_path)
        
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
            "path": relative_path,
            "operation_type": operation_type,
        }
        return category, info
    
    def dump_all_ops_to_file(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        遍历 OPERATOR_REGISTRY，构建完整字典并写入 ops.json
        """
        all_ops: Dict[str, List[Dict[str, Any]]] = {}
        default_bucket: List[Dict[str, Any]] = []
        
        idx = 1
        for op_name, cls in OPERATOR_REGISTRY:
            category, info = self._gather_single_operator(op_name, cls, idx)
            if 'description' in info and isinstance(info['description'], Tuple):
                info['description'] = '\n'.join(info['description'])
            all_ops.setdefault(category, []).append(info)
            default_bucket.append(info)
            idx += 1
        
        all_ops["Default"] = default_bucket
        
        try:
            with open(self.ops_json_path, "w", encoding="utf-8") as f:
                json.dump(all_ops, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        
        return all_ops
    
    def ensure_ops_cache(self) -> Dict[str, List[Dict[str, Any]]]:
        """若 ops.json 不存在或为空，则重新生成"""
        if self.ops_json_path.exists():
            try:
                with open(self.ops_json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if data:
                    return data
            except Exception:
                pass
        return self.dump_all_ops_to_file()
    
    def get_operator_content(self, data_type: str) -> str:
        """
        根据 data_type 返回该类别下所有算子的 JSON 字符串
        """
        all_ops = self.dump_all_ops_to_file()
        
        import copy
        if data_type in all_ops:
            content = copy.deepcopy(all_ops[data_type])
        else:
            content = []
        
        return json.dumps(content, ensure_ascii=False, indent=2)
    
    def get_operator_content_list(self, category: Optional[str] = None, op_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        返回算子列表（Python对象，不是JSON字符串）
        """
        all_ops = self.dump_all_ops_to_file()
        if op_type:
            filtered_ops = []
            for cat, ops in all_ops.items():
                if category and cat != category:
                    continue
                for op in ops:
                    if op.get("operation_type") == op_type:
                        filtered_ops.append(op)
            return filtered_ops
        if category and category in all_ops:
            return all_ops[category]
        elif category is None:
            return all_ops.get("Default", [])
        else:
            return []
    
    def get_operator_source_by_name(self, operator_name: str) -> str:
        """根据算子名称获取算子的源码"""
        try:
            for name, cls in OPERATOR_REGISTRY:
                if name == operator_name:
                    try:
                        source_code = inspect.getsource(cls)
                        return source_code
                    except Exception as e:
                        return f"# 无法获取源码: {e}"
            
            return f"# 未找到算子 '{operator_name}'，请检查名称是否正确。"
        except Exception as e:
            return f"# 获取算子源码时发生错误: {e}"
    
    def get_prompt_sources_of_operator(self, op_name: str) -> Dict[str, str]:
        """获取 operator 的 prompt_templates 的源码，并随机获取2个示例"""
        cls = OPERATOR_REGISTRY.get(op_name)
        if cls is None:
            raise KeyError(f"Operator {op_name} not found in registry")
        
        if getattr(cls, "ALLOWED_PROMPTS", None):
            prompt_classes = cls.ALLOWED_PROMPTS
        else:
            raise ValueError(f"Operator {op_name} has no ALLOWED_PROMPTS")
        
        if len(prompt_classes) == 0:
            raise ValueError(f"Operator {op_name} has no prompt_templates")
        if len(prompt_classes) == 1:
            sample_classes = prompt_classes
        else:
            sample_classes = random.sample(prompt_classes, min(2, len(prompt_classes)))
        
        out = {}
        for c in sample_classes:
            try:
                out[c.__name__] = inspect.getsource(c)
            except OSError:
                out[c.__name__] = "# 源码不可用（可能是C扩展/找不到源码/zip导入）"
        return out


# 全局实例
_operator_tools_service = OperatorToolsService()
