import yaml, os
import importlib
import inspect
from typing import Dict, List, Any
from app.core.config import settings
"""
Registry Yaml Format:
{
    "{id}":{
        "name": "APILLMServing_1",
        "cls_name": "APILLMServing_request",
        "params": {
            ...
        }
    }
}
"""
SERVING_MODULE = importlib.import_module("dataflow.serving")

SERVING_MODULE_ALL = ["APILLMServing_request"]

SERVING_CLS_REGISTRY = dict(zip(SERVING_MODULE_ALL,
                               [getattr(SERVING_MODULE, cls_name) for cls_name in SERVING_MODULE_ALL]))
    

class ServingRegistry:
    """Serving管理类，负责管理算子所需的LLM Serving实例的参数。主要用于**API Serving**"""
    def __init__(self, path: str | None = None):
        self.path = path or settings.SERVING_REGISTRY
        self._ensure()

    def _ensure(self):
        if not os.path.exists(self.path):
            with open(self.path, 'w') as f:
                yaml.dump({}, f)
                
    def _get_all(self):
        with open(self.path, 'r') as f:
            data = yaml.safe_load(f)
        return data
    
    def _get(self, id: str) -> Dict[str, Any] | None:
        data = self._get_all()
        item = data.get(id)
        item['id'] = id
        return item
                
    def _set(self, name: str, cls_name: str, params: List[Dict[str, Any]]) -> str:
        data = self._get_all() or {}
        id = os.urandom(8).hex()
        data[id] = {
            "name": name,
            "cls_name": cls_name,
            "params": params
        }
        with open(self.path, 'w') as f:
            yaml.dump(data, f)
        return id

    def _update(self, id: str, name: str | None = None, cls_name: str | None = None, params: List[Dict[str, Any]] | None = None) -> bool:
        data = self._get_all()
        if id not in data:
            return False
        
        if name:
            data[id]["name"] = name
        if cls_name:
            raise ValueError("cls_name is not allowed to be updated")
        if params is not None:
            # Update parameter values only, keeping other metadata
            current_params_map = {p['name']: p for p in data[id].get("params", [])}
            
            for new_p in params:
                name = new_p.get('name')
                if name in current_params_map:
                    # Only update the value if present in the new param
                    if 'value' in new_p:
                         current_params_map[name]['value'] = new_p['value']
                else:
                     # If it's a new parameter (like api_key), add it
                     current_params_map[name] = new_p
                     
            data[id]["params"] = list(current_params_map.values())
            
        with open(self.path, 'w') as f:
            yaml.dump(data, f)
        return True

    def _delete(self, id: str) -> bool:
        data = self._get_all()
        if id not in data:
            return False
        del data[id]
        with open(self.path, 'w') as f:
            yaml.dump(data, f)
        return True

    def get_serving_classes(self) -> List[Dict[str, Any]]:
        """获取所有注册的Serving类及其初始化参数信息"""
        result = []
        for cls_name, cls in SERVING_CLS_REGISTRY.items():
            params = []
            init_method = getattr(cls, "__init__", None)
            if init_method:
                try:
                    sig = inspect.signature(init_method)
                    for name, param in sig.parameters.items():
                        if name == "self":
                            continue
                        
                        # Get type string
                        if param.annotation != inspect.Parameter.empty:
                            if hasattr(param.annotation, "__name__"):
                                p_type = param.annotation.__name__
                            else:
                                p_type = str(param.annotation)
                        else:
                            p_type = "Any"
                            
                        # Get default value
                        default_val = None
                        required = True
                        if param.default != inspect.Parameter.empty:
                            default_val = param.default
                            required = False
                            # Handle un-serializable defaults
                            if isinstance(default_val, (type,  property)):
                                default_val = str(default_val)
                            # simple check
                            try:
                                import json
                                json.dumps(default_val)
                            except:
                                default_val = str(default_val)
                        
                        params.append({
                            "name": name,
                            "type": p_type,
                            "default_value": default_val,
                            "required": required
                        })
                except ValueError:
                    pass
            
            result.append({
                "cls_name": cls_name,
                "params": params
            })
        return result
        
_SERVING_REGISTRY = ServingRegistry()