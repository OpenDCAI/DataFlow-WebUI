import json
import uuid
import datetime
import os
import ast
import re
import hashlib
from typing import List, Optional, Dict, Any, Tuple, Union
from app.core.logger_setup import get_logger
from app.core.config import settings
# from app.services.operator_registry import _op_registry
from app.core.container import container
from app.schemas.pipelines import PipelineOperator
from app.services.dataflow_engine import dataflow_engine
logger = get_logger(__name__)

from dataclasses import dataclass

@dataclass(frozen=True)
class PipelineFileAnalyzer:
    file_path: str
    source: str
    tree: ast.AST

    @classmethod
    def from_file(cls, file_path: str) -> "PipelineFileAnalyzer":
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
        return cls(file_path=file_path, source=source, tree=ast.parse(source))

    def operators(self) -> List[Dict[str, Any]]:
        """返回 [{'name': class_name, 'params': {}}...]"""
        names = self.execution_order()
        return [{"name": n, "params": {}} for n in names]

    def execution_order(self) -> List[str]:
        """按 forward() 中 self.xxx.run() 的出现顺序提取 operator 类名"""
        var_to_class = self._build_var_to_class_map()
        out: List[str] = []

        for class_node in self._iter_class_defs():
            forward = self._find_method(class_node, "forward")
            if not forward:
                continue
            for stmt in forward.body:
                self._collect_run_calls(stmt, var_to_class, out)

        return out

    def init_params_by_class(self) -> Dict[str, Dict[str, Any]]:
        """提取 __init__ 中 self.xxx = OpClass(...keyword args...)"""
        result: Dict[str, Dict[str, Any]] = {}
        for class_node in self._iter_class_defs():
            init = self._find_method(class_node, "__init__")
            if not init:
                continue

            for stmt in init.body:
                class_name, kwargs = self._parse_self_assign_call(stmt)
                if class_name:
                    result[class_name] = kwargs
        return result

    def run_params_by_class(self) -> Dict[str, Dict[str, Any]]:
        """提取 forward 中 self.xxx.run(...keyword args...)"""
        var_to_class = self._build_var_to_class_map()
        result: Dict[str, Dict[str, Any]] = {}

        def visit(node: ast.AST):
            if isinstance(node, ast.Call) and self._is_self_var_run_call(node):
                var_name = node.func.value.attr  # type: ignore[attr-defined]
                class_name = var_to_class.get(var_name)
                if class_name:
                    kwargs = {
                        kw.arg: self._node_to_value(kw.value)
                        for kw in node.keywords
                        if kw.arg is not None
                    }
                    result[class_name] = kwargs

            for child in ast.iter_child_nodes(node):
                visit(child)

        for class_node in self._iter_class_defs():
            forward = self._find_method(class_node, "forward")
            if not forward:
                continue
            for stmt in forward.body:
                visit(stmt)

        return result

    # ---------- Internal helpers ----------

    def _iter_class_defs(self) -> List[ast.ClassDef]:
        return [n for n in ast.walk(self.tree) if isinstance(n, ast.ClassDef)]

    def _find_method(self, class_node: ast.ClassDef, name: str) -> Optional[ast.FunctionDef]:
        for item in class_node.body:
            if isinstance(item, ast.FunctionDef) and item.name == name:
                return item
        return None

    def _build_var_to_class_map(self) -> Dict[str, str]:
        """
        从 __init__ 中解析 self.var = Class()，建立 var -> Class 映射
        """
        mapping: Dict[str, str] = {}

        for class_node in self._iter_class_defs():
            init = self._find_method(class_node, "__init__")
            if not init:
                continue

            for stmt in init.body:
                if not isinstance(stmt, ast.Assign):
                    continue
                for target in stmt.targets:
                    if not self._is_self_attr(target):
                        continue
                    var_name = target.attr  # self.<var_name>
                    if isinstance(stmt.value, ast.Call):
                        class_name = self._call_target_name(stmt.value)
                        if class_name:
                            mapping[var_name] = class_name

        return mapping

    def _collect_run_calls(self, node: ast.AST, var_to_class: Dict[str, str], out: List[str]) -> None:
        """
        递归收集 self.xxx.run() 出现顺序
        """
        if isinstance(node, ast.Call) and self._is_self_var_run_call(node):
            var_name = node.func.value.attr  # type: ignore[attr-defined]
            class_name = var_to_class.get(var_name)
            if class_name:
                out.append(class_name)

        for child in ast.iter_child_nodes(node):
            self._collect_run_calls(child, var_to_class, out)

    def _is_self_var_run_call(self, node: ast.Call) -> bool:
        """
        是否形如：self.xxx.run(...)
        """
        if not (isinstance(node.func, ast.Attribute) and node.func.attr == "run"):
            return False
        # node.func.value == self.xxx
        if not isinstance(node.func.value, ast.Attribute):
            return False
        if not (isinstance(node.func.value.value, ast.Name) and node.func.value.value.id == "self"):
            return False
        return True

    def _parse_self_assign_call(self, stmt: ast.stmt) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        解析：self.xxx = SomeClass(...kwargs...)
        返回 (SomeClass, kwargs)
        """
        if not isinstance(stmt, ast.Assign):
            return None, {}
        # 仅处理 self.xxx = Call(...)
        if not any(self._is_self_attr(t) for t in stmt.targets):
            return None, {}
        if not isinstance(stmt.value, ast.Call):
            return None, {}

        class_name = self._call_target_name(stmt.value)
        if not class_name:
            return None, {}

        kwargs: Dict[str, Any] = {}
        for kw in stmt.value.keywords:
            if kw.arg is not None:
                kwargs[kw.arg] = self._node_to_value(kw.value)
        return class_name, kwargs

    def _is_self_attr(self, node: ast.AST) -> bool:
        return (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == "self"
        )

    def _call_target_name(self, call: ast.Call) -> Optional[str]:
        """
        获取 Call 的目标名：Class() / module.Class()
        """
        if isinstance(call.func, ast.Name):
            return call.func.id
        if isinstance(call.func, ast.Attribute):
            return call.func.attr
        return None

    @staticmethod
    def _node_to_value(node: ast.AST) -> Any:
        """
        把 AST 节点尽量转成 Python 值；不能静态求值的返回 None
        """
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.List):
            return [PipelineFileAnalyzer._node_to_value(e) for e in node.elts]
        if isinstance(node, ast.Tuple):
            return tuple(PipelineFileAnalyzer._node_to_value(e) for e in node.elts)
        if isinstance(node, ast.Dict):
            return {
                PipelineFileAnalyzer._node_to_value(k): PipelineFileAnalyzer._node_to_value(v)
                for k, v in zip(node.keys, node.values)
            }
        if isinstance(node, ast.Name):
            return None  # 变量名，静态无法解析
        if isinstance(node, ast.Attribute):
            # self.xxx -> None；其他 attr 返回可读字符串
            if isinstance(node.value, ast.Name) and node.value.id == "self":
                return None
            left = PipelineFileAnalyzer._node_to_value(node.value)
            left = "" if left is None else str(left)
            full = f"{left}.{node.attr}" if left else node.attr
            full = full.replace("<var:", "").replace(">", "")
            return f"<class '{full}'>"
        if isinstance(node, ast.Call):
            # Prompt 类实例化：返回可读类名（沿用你原来的逻辑）
            func_name = None
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                func_name = node.func.attr
            if func_name and "Prompt" in func_name:
                return f"<class 'dataflow.prompts.{func_name}'>"
            return None

        return None


class PipelineRegistry:
    def __init__(self, path: str | None = None):
        """
        初始化Pipeline注册表i
        加载api_pipelines目录中的所有py文件并提取operator执行顺序
        """
        # using absolute path
        self.path = os.path.join(settings.BASE_DIR, "data", "pipeline_registry.json")
        self.execution_path = os.path.join(settings.BASE_DIR, "data", "pipeline_execution.json")

        self._init_registry_file()
        # 初始化后，更新所有api pipeline的operators列表
        self._update_all_api_pipelines_operators()
        
    def _read(self) -> Dict:
        """读取注册表文件"""
        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f) or {"pipelines": {}}
    
    def _read_execution(self) -> Dict:
        """读取执行记录文件"""
        with open(self.execution_path, "r", encoding="utf-8") as f:
            return json.load(f) or {"executions": {}}

    def _write(self, data: Dict):
        """写入注册表文件"""
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)    

    def _write_execution(self, data: Dict):
        """写入执行记录文件"""
        with open(self.execution_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)  

    def _init_registry_file(self):
        """
        确保注册表文件存在，并加载api_pipelines目录中的所有py文件
        """
        logger.info("初始化Pipeline Registry的注册表和执行结果表...")
        if not os.path.exists(self.path) or not os.path.exists(self.execution_path):
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            os.makedirs(os.path.dirname(self.execution_path), exist_ok=True)

            # 创建初始数据结构
            initial_data = {"pipelines": {}}
            initial_data_execution = {"executions": {}}
            
            # 尝试加载api_pipelines目录中的py文件
            try:
                # 直接使用settings中的路径作为相对路径的开头
                api_pipelines_dir = os.path.join(settings.DATAFLOW_CORE_DIR, "api_pipelines")
                
                logger.info(f"Checking for API pipelines in: {api_pipelines_dir}")
                
                # 如果目录存在，扫描所有py文件
                if os.path.exists(api_pipelines_dir):
                    logger.info(f"API pipelines directory found, scanning for Python files")
                    
                    # 获取当前时间
                    current_time = self.get_current_time()
                    
                    # 遍历目录中的所有py文件
                    for filename in os.listdir(api_pipelines_dir):
                        if filename.endswith(".py") and not filename.startswith("__"):
                            # 生成pipeline_id
                            pipeline_id = str(uuid.uuid4())
                            file_path = os.path.join(api_pipelines_dir, filename)
                            
                            # 提取operator执行顺序
                            analyzer = PipelineFileAnalyzer.from_file(file_path)
                            operators = analyzer.operators()
                            
                            # 查找关联的数据集
                            input_dataset = self._find_dataset_id(file_path)

                            # 创建pipeline配置
                            pipeline_data = {
                                "id": pipeline_id,
                                "name": filename[:-3].replace("_", " ").title(),
                                "config": {
                                    "file_path": file_path,
                                    "input_dataset": input_dataset,
                                    "operators": operators,
                                },
                                # 从代码目录(api_pipelines)提取的预置 Pipeline
                                "tags": ["api", "template"],
                                "created_at": current_time,
                                "updated_at": current_time,
                                "status": "queued"
                            }
                            
                            # 添加到初始数据中
                            initial_data["pipelines"][pipeline_id] = pipeline_data
                            logger.info(f"Added API pipeline: {pipeline_data['name']} ({pipeline_id}) with {len(operators)} operators")
                    
                    logger.info(f"Successfully loaded {len(initial_data['pipelines'])} API pipelines")
                    
                    # Enrich 所有新建的 pipelines 的参数信息
                    logger.info("Enriching pipeline operators with parameter definitions...")
                    for pipeline_id, pipeline_data in initial_data["pipelines"].items():
                        enriched_pipeline = self._enrich_pipeline_operators_internal(pipeline_data)
                        initial_data["pipelines"][pipeline_id] = enriched_pipeline
                    logger.info("Pipeline operators enrichment completed")
                else:
                    logger.warning(f"API pipelines directory not found: {api_pipelines_dir}")
            except Exception as e:
                logger.error(f"Error loading API pipelines: {e}", exc_info=True)
                # 即使出错，仍然创建基本的注册表文件
            
            # 写入初始数据到文件
            self._write(initial_data)
            self._write_execution(initial_data_execution)
    
    def _find_dataset_id(self, pipeline_file_path: str) -> Union[str, Dict[str, Any]]:
        """
        从pipeline文件中查找first_entry_file_name，并找到对应的数据集ID
        返回 {"id": "...", "location": [0, 0]} 或 ""
        """
        try:
            if not os.path.exists(pipeline_file_path):
                return ""
                
            with open(pipeline_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 查找 first_entry_file_name="..."
            match = re.search(r'first_entry_file_name\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                relative_path = match.group(1)
                # 解析绝对路径
                pipeline_dir = os.path.dirname(pipeline_file_path)
                abs_path = os.path.normpath(os.path.join(pipeline_dir, relative_path))
                
                # 转换为相对于CWD (backend/) 的路径
                cwd = os.getcwd()
                rel_path_from_cwd = os.path.relpath(abs_path, cwd)
                
                # 尝试从DatasetRegistry中查找
                
                # 1. 尝试通过路径匹配
                all_datasets = container.dataset_registry.list()
                for ds in all_datasets:
                    if ds.get("root") == rel_path_from_cwd:
                        return {"id": ds.get("id"), "location": [0, 0]}
                
                # 2. 如果没找到，尝试计算ID查找 (作为备选)
                ds_id = hashlib.md5(rel_path_from_cwd.encode("utf-8")).hexdigest()[:10]
                if container.dataset_registry.get(ds_id):
                    return {"id": ds_id, "location": [0, 0]}
                    
        except Exception as e:
            logger.warning(f"Failed to find dataset for pipeline {pipeline_file_path}: {e}")
        
        return ""

    def _update_all_api_pipelines_operators(self):
        """
        更新所有api pipeline的operators列表和input_dataset
        """
        try:
            data = self._read()
            api_pipelines_dir = os.path.join(settings.DATAFLOW_CORE_DIR, "api_pipelines")
            print(api_pipelines_dir)
            if not os.path.exists(api_pipelines_dir):
                logger.warning(f"API pipelines directory not found: {api_pipelines_dir}")
                return
            
            updated = False
            # 遍历所有pipeline
            for pipeline_id, pipeline_data in data.get("pipelines", {}).items():
                # 检查是否是api pipeline
                if "api" in pipeline_data.get("tags", []):
                    # 历史数据兼容：确保从代码提取的预置 Pipeline 都带 template tag
                    tags = pipeline_data.get("tags", [])
                    if "template" not in tags:
                        tags.append("template")
                        pipeline_data["tags"] = tags
                        data["pipelines"][pipeline_id] = pipeline_data
                        data["pipelines"][pipeline_id]["updated_at"] = self.get_current_time()
                        updated = True

                    file_path = pipeline_data.get("config", {}).get("file_path")
                    if file_path and os.path.exists(file_path):
                        # 提取operator执行顺序
                        analyzer = PipelineFileAnalyzer.from_file(file_path)
                        operators = analyzer.operators()
                        
                        # 查找关联的数据集
                        input_dataset = self._find_dataset_id(file_path)
                        
                        # 检查是否有变化
                        config_changed = False
                        
                        if pipeline_data["config"].get("operators", []) != operators:
                            pipeline_data["config"]["operators"] = operators
                            config_changed = True
                            
                        if input_dataset and pipeline_data["config"].get("input_dataset") != input_dataset:
                            pipeline_data["config"]["input_dataset"] = input_dataset
                            config_changed = True
                            
                        if config_changed:
                            # Enrich 更新后的 pipeline
                            enriched_pipeline = self._enrich_pipeline_operators_internal(pipeline_data)
                            data["pipelines"][pipeline_id] = enriched_pipeline
                            data["pipelines"][pipeline_id]["updated_at"] = self.get_current_time()
                            updated = True
                            logger.info(f"Updated and enriched pipeline {pipeline_id}")
            
            # 如果有更新，保存到文件
            if updated:
                self._write(data)
        except Exception as e:
            logger.error(f"Error updating API pipeline operators: {e}", exc_info=True)  

    def list_templates(self) -> List[Dict[str, Any]]:
        """列出所有预置(template) Pipelines"""
        data = self._read()
        pipelines = list(data.get("pipelines", {}).values())
        templates = [p for p in pipelines if "template" in (p.get("tags") or [])]
        templates.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        return templates
    
    def _parse_frontend_params(self, params):
        if not params:
            return {}
        if isinstance(params, dict):
            if "init" in params or "run" in params:
                merged = {}
                for item in (params.get("init", []) or []):
                    name = item.get("name")
                    if name is not None:
                        merged[name] = item.get("value")
                for item in (params.get("run", []) or []):
                    name = item.get("name")
                    if name is not None:
                        merged[name] = item.get("value")
                return merged
            return params
        parsed = {}
        for item in params:
            if isinstance(item, dict):
                key = item.get("name")
                value = item.get("value")
                if key is not None:
                    parsed[key] = value
        return parsed

    def get_current_time(self):
        """获取当前时间的ISO格式字符串"""
        return datetime.datetime.now().isoformat()
    
    def list_pipelines(self) -> List[Dict[str, Any]]:
        """
        列出所有注册的Pipeline
        在返回之前，确保api pipeline的operators列表是最新的
        """
        # 先更新所有api pipeline的operators列表（会自动 enrich）
        
        data = self._read()
        pipelines = list(data.get("pipelines", {}).values())
        
        # 按更新时间倒序排序
        pipelines.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        
        # 直接返回，因为 pipelines 已经在初始化/更新时 enriched
        return pipelines
    
    def create_pipeline(self, pipeline_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建一个新的Pipeline"""
        data = self._read()
        
        # 生成唯一ID
        pipeline_id = str(uuid.uuid4())
        current_time = self.get_current_time()
        
        # 直接创建字典表示的pipeline
        config = pipeline_data.get("config", {})
        operators = config.get("operators", [])
        for op in operators:
            params = op.get("params", {})
            op["params"] = self._parse_frontend_params(params)
        pipeline = {
            "id": pipeline_id,
            "name": pipeline_data.get("name", ""),
            "config": config,
            "tags": pipeline_data.get("tags", []),
            "created_at": current_time,
            "updated_at": current_time,
            "status": "queued"
        }
        
        # Enrich pipeline operators
        enriched_pipeline = self._enrich_pipeline_operators_internal(pipeline)
        
        # 保存 enriched pipeline 到文件
        data["pipelines"][pipeline_id] = enriched_pipeline
        self._write(data)
        
        logger.info(f"Successfully created pipeline: {pipeline_id} with name: {pipeline_data.get('name', '')}")
        return enriched_pipeline
    
    def get_pipeline(self, pipeline_id: str) -> Optional[Dict[str, Any]]:
        """
        根据ID获取Pipeline
        如果是api pipeline，确保返回最新的operators列表
        """
        data = self._read()
        pipeline_data = data.get("pipelines", {}).get(pipeline_id)
        
        if pipeline_data:
            # 如果是api pipeline，检查并更新operators列表
            if "api" in pipeline_data.get("tags", []):
                file_path = pipeline_data.get("config", {}).get("file_path")
                if file_path and os.path.exists(file_path):
                    analyzer = PipelineFileAnalyzer.from_file(file_path)
                    operators = analyzer.operators()
                    existing_op_names = [op.get("name") for op in pipeline_data["config"].get("operators", [])]
                    new_op_names = [op.get("name") for op in operators]
                    
                    # 只有当 operator 列表真正改变时才更新和 enrich
                    if existing_op_names != new_op_names:
                        pipeline_data["config"]["operators"] = operators
                        enriched_pipeline = self._enrich_pipeline_operators_internal(pipeline_data)
                        enriched_pipeline["updated_at"] = self.get_current_time()
                        # 保存更新
                        data["pipelines"][pipeline_id] = enriched_pipeline
                        self._write(data)
                        logger.info(f"Updated and enriched pipeline {pipeline_id} on get")
                        return enriched_pipeline
            
            # 直接返回已 enriched 的数据
            return pipeline_data
        return None
    
    def _update_pipeline_op_info(self, new_op_info: Dict[str, Any], old_op_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        new_op_info: 新的算子信息（字典格式）
        new_op_info 中包含 name, params, location 三个字段
            - single_param_format: {'name': xxx, 'value': yyy}
        old_op_info: 旧的算子信息（字典格式），我们假设其中的所有参数是全的。
        return: 更新后的算子信息（字典格式）
        """
        # if name will be updated, raise an error.
        new_name = new_op_info.get("name")
        old_name = old_op_info.get("name")
        if new_name != old_name:
            raise ValueError(f"Operator name cannot be updated. Original name: {old_name}, New name: {new_name}")
        
        # Update the locations
        if "location" in new_op_info:
            old_op_info["location"] = new_op_info.get("location")
        
        # Parse new params
        new_params = new_op_info.get("params", {})
        new_init_params = self._parse_frontend_params(new_params.get("init", []))
        new_run_params = self._parse_frontend_params(new_params.get("run", []))
        
        # Update Init Params
        old_params = old_op_info.get("params", {})
        for param in old_params.get("init", []):
            param_name = param.get("name")
            if param_name is not None:
                param_value = new_init_params.get(param_name, None)
                if param_value is not None:
                    param["value"] = param_value
                elif param.get('value') is None:
                    param["value"] = param.get("default_value", None)
        
        # Update Run Params
        for param in old_params.get("run", []):
            param_name = param.get("name")
            if param_name is not None:
                param_value = new_run_params.get(param_name, None)
                if param_value is not None:
                    param["value"] = param_value
                elif param.get('value') is None:
                    param["value"] = param.get("default_value", None)
            
        return old_op_info
        
    
    def update_pipeline(self, pipeline_id: str, pipeline_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新指定的Pipeline"""
        data = self._read()
        
        if pipeline_id not in data.get("pipelines", {}):
            raise ValueError(f"Pipeline with id {pipeline_id} not found")
        
        # 获取当前Pipeline数据并直接更新
        updated_pipeline = data["pipelines"][pipeline_id].copy()
        
        # update Operators
        new_pipeline_config = pipeline_data.get("config", None)
        if new_pipeline_config is not None:
            updated_pipeline["config"]["input_dataset"] = new_pipeline_config.get("input_dataset", "")
            if "operators" in new_pipeline_config:
                op_map = {}
                for idx, op in enumerate(updated_pipeline["config"]["operators"]):
                    op_map[f"{op.get('name')}_{idx}"] = op
                
                updated_operators = []
                for idx, op in enumerate(new_pipeline_config["operators"]):
                    old_op_info = op_map.get(f"{op.get('name')}_{idx}", None)
                    if old_op_info is None:  # new operator
                        # 创建新 operator 的字典格式
                        op_details = container.operator_registry.get_op_details(op.get("name"))
                        old_op_info = {
                            "name": op.get("name"),
                            "params": op_details.get("parameter", {"init": [], "run": []}) if op_details else {"init": [], "run": []},
                            "location": op.get("location", (0, 0))
                        }
                    
                    # 更新 operator 信息
                    updated_op = self._update_pipeline_op_info(op, old_op_info)
                    updated_operators.append(updated_op)
                
                # 更新 operators 列表
                updated_pipeline["config"]["operators"] = updated_operators
            
        
        # 更新字段，保留创建时间和状态
        updated_pipeline.update({
            "name": pipeline_data.get("name", updated_pipeline.get("name", "")),
            # "config": pipeline_data.get("config", updated_pipeline.get("config", {})),
            "tags": pipeline_data.get("tags", updated_pipeline.get("tags", [])),
            "updated_at": self.get_current_time()
            # 保持created_at和status不变
        })
        
        # Enrich pipeline operators
        # enriched_pipeline = self._enrich_pipeline_operators_internal(updated_pipeline)
        
        # 保存 enriched pipeline 到文件
        data["pipelines"][pipeline_id] = updated_pipeline
        self._write(data)
        
        logger.info(f"Updated pipeline: {pipeline_id}")
        return updated_pipeline
    
    def delete_pipeline(self, pipeline_id: str) -> bool:
        """删除指定的Pipeline"""
        data = self._read()
        
        if pipeline_id not in data.get("pipelines", {}):
            return False
        
        # 直接从文件删除
        del data["pipelines"][pipeline_id]
        self._write(data)
        
        logger.info(f"Deleted pipeline: {pipeline_id}")
        return True
        
    def start_execution(self, pipeline_id: Optional[str] = None, config: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
        """开始执行Pipeline"""
        # 获取Pipeline配置
        if pipeline_id:
            pipeline = self.get_pipeline(pipeline_id)
            if not pipeline:
                raise ValueError(f"Pipeline with id {pipeline_id} not found")
            pipeline_config = pipeline.get("config", {})
            logger.info(f"Executing predefined pipeline: {pipeline_id}")
        else:
            if not config:
                raise ValueError("Either pipeline_id or config must be provided")
            pipeline_config = config
            logger.info("Executing pipeline with provided config")
        
        # 生成执行ID
        execution_id = str(uuid.uuid4())
        
        # 创建初始结果
        initial_result = {
            "execution_id": execution_id,
            "status": "queued",
            "output": {},
            "logs": [f"[{self.get_current_time()}] Pipeline execution queued"]
        }
                
        # 直接保存到文件
        data = self._read_execution()
        data["executions"][execution_id] = initial_result
        self._write_execution(data)
        
        return execution_id, pipeline_config, initial_result
    
    def get_execution_result(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """获取Pipeline执行结果"""
        data = self._read_execution()
        execution_data = data.get("executions", {}).get(execution_id)
        if execution_data:
            return execution_data.copy()  # 返回副本避免修改原数据
        return None
    
    def list_executions(self) -> List[Dict[str, Any]]:
        """列出所有Pipeline执行记录"""
        data = self._read_execution()
        # 直接返回字典列表，不需要转换为对象
        return list(data.get("executions", {}).values())
    
    def get_execution_status(
        self, 
        execution_id: str,
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取执行状态（包含算子粒度）
        
        Args:
            execution_id: 执行 ID
            task_id: 任务 ID（可选）
        
        Returns:
            执行状态字典
        """
        # 读取执行记录
        data = self._read_execution()
        execution_data = data.get("executions", {}).get(execution_id)
        
        if not execution_data:
            return None
        
        # 如果提供了 task_id，读取任务信息
        task_info = None
        if task_id:
            task_info = container.task_registry.get(task_id)
        
        return {
            "execution_id": execution_id,
            "task_id": task_id,
            "status": execution_data.get("status"),
            "operator_progress": execution_data.get("operator_progress", {}),
            "logs": execution_data.get("logs", []),
            "output": execution_data.get("output", {}),
            "started_at": execution_data.get("started_at"),
            "completed_at": execution_data.get("completed_at"),
            "task_status": task_info.get("status") if task_info else None,
            "task_started_at": task_info.get("started_at") if task_info else None,
            "task_finished_at": task_info.get("finished_at") if task_info else None
        }
    
    def get_execution_result(
        self, 
        execution_id: str,
        step: Optional[int] = None,
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        获取执行结果
        
        Args:
            execution_id: 执行 ID
            step: 步骤索引（可选，None 表示返回最后一个步骤的输出）
            limit: 返回的数据条数（默认5条）
        
        Returns:
            执行结果字典
        """
        data = self._read_execution()
        execution_data = data.get("executions", {}).get(execution_id)
        
        if not execution_data:
            return None
        
        # 获取输出
        output = execution_data.get("output", {})
        logs = execution_data.get("logs", [])
        
        # 获取执行结果和算子进度
        execution_results = output.get("execution_results", [])
        operator_progress = execution_data.get("operator_progress", {})
        
        # 确定要查询的步骤索引
        if step is None:
            # 默认返回最后一个已完成的步骤
            if execution_results:
                step = execution_results[-1].get("index", 0)
            else:
                # 如果没有完成的步骤，尝试从 operator_progress 获取当前正在运行的步骤
                current_step = operator_progress.get("current_step")
                if current_step is not None:
                    # 使用当前正在运行的 step
                    step = current_step
                else:
                    step = 0
        
        # 读取缓存文件（使用绝对路径）
        cache_path = settings.CACHE_DIR
        cache_file_prefix = "dataflow_cache_step"
        cache_file = os.path.join(cache_path, f"{cache_file_prefix}_step{step}.jsonl")
        
        sample_data = []
        total_count = 0
        file_exists = False
        
        # 如果当前 step 的文件不存在，尝试读取上一步的文件（运行中时，当前 step 的文件还没写入）
        if not os.path.exists(cache_file) and step > 0:
            cache_file = os.path.join(cache_path, f"{cache_file_prefix}_step{step-1}.jsonl")
        
        if os.path.exists(cache_file):
            file_exists = True
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    for line in f:
                        total_count += 1
                        if len(sample_data) < limit:
                            try:
                                sample_data.append(json.loads(line.strip()))
                            except json.JSONDecodeError:
                                pass
            except Exception as e:
                logger.error(f"Failed to read cache file {cache_file}: {e}")
        
        # 获取算子信息
        operator_name = None
        operator_status = None
        
        # 首先尝试从 execution_results 获取（已完成的算子）
        if step < len(execution_results):
            operator_name = execution_results[step].get("operator")
            operator_status = execution_results[step].get("status")
        else:
            # 如果 execution_results 中没有，尝试从 operator_progress 获取（正在运行的算子）
            run_progress = operator_progress.get("run", {})
            if run_progress:
                # 找到第一个正在运行的 operator（Started 但还没有 Completed）
                current_operator_key = None
                for op_key, op_logs in run_progress.items():
                    if op_logs:
                        last_log = op_logs[-1]
                        if "Started" in last_log and "Completed" not in last_log:
                            current_operator_key = op_key
                            operator_status = "running"
                            break
                        elif "Completed" in last_log:
                            # 这个已经完成了，继续找下一个
                            continue
                
                # 从 key 中提取 operator 名称（去掉 _idx 后缀）
                if current_operator_key:
                    operator_name = current_operator_key.rsplit('_', 1)[0]
        
        return {
            "execution_id": execution_id,
            "status": execution_data.get("status"),
            "step": step,
            "operator_name": operator_name,
            "operator_status": operator_status,
            "sample_data": sample_data,
            "sample_count": len(sample_data),
            "total_count": total_count,
            "file_exists": file_exists,
            "cache_file": cache_file,
            "logs": logs,
            "started_at": execution_data.get("started_at"),
            "completed_at": execution_data.get("completed_at")
        }
    
    async def start_execution_async(
        self, 
        pipeline_id: Optional[str] = None, 
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        异步开始执行Pipeline（使用 Ray）
        
        Args:
            pipeline_id: 预定义 Pipeline ID
            config: 自定义 Pipeline 配置
        
        Returns:
            包含 task_id 和 execution_id 的字典
        """
        from app.services.dataflow_engine import ray_executor
        
        # 获取Pipeline配置
        if pipeline_id:
            pipeline = self.get_pipeline(pipeline_id)
            if not pipeline:
                raise ValueError(f"Pipeline with id {pipeline_id} not found")
            pipeline_config = pipeline.get("config", {})
            pipeline_name = pipeline.get("name", "Unknown Pipeline")
            logger.info(f"Executing predefined pipeline asynchronously: {pipeline_id}")
        else:
            if not config:
                raise ValueError("Either pipeline_id or config must be provided")
            pipeline_config = config
            pipeline_name = "Custom Pipeline"
            logger.info("Executing pipeline with provided config asynchronously")
        
        # 生成执行ID
        execution_id = str(uuid.uuid4())
        
        # 创建 Task
        task_data = {
            "dataset_id": pipeline_config.get("input_dataset", {}).get("id", ""),
            "executor_name": pipeline_name,
            "executor_type": "pipeline",
            "meta": {
                "pipeline_id": pipeline_id if pipeline_id else "custom",
                "execution_id": execution_id
            }
        }
        task = container.task_registry.create(task_data)
        task_id = task["id"]
        
        logger.info(f"Task created: {task_id}")
        
        # 创建初始结果
        initial_result = {
            "execution_id": execution_id,
            "task_id": task_id,
            "status": "queued",
            "output": {},
            "logs": [f"[{self.get_current_time()}] Pipeline execution queued"],
            "operator_progress": {}
        }
        
        # 保存初始状态
        data = self._read_execution()
        data["executions"][execution_id] = initial_result
        self._write_execution(data)
        
        # 提交到 Ray 异步执行
        await ray_executor.submit_execution(
            pipeline_config=pipeline_config,
            execution_id=execution_id,
            pipeline_registry_path=self.path,
            pipeline_execution_path=self.execution_path
        )
        
        logger.info(f"Pipeline execution submitted to Ray: {execution_id}")
        
        return {
            "execution_id": execution_id,
            "task_id": task_id
        }

    def _enrich_pipeline_operators_internal(self, pipeline_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich pipeline operators with detailed parameter info from registry.
        This method only enriches the data and returns it without saving.
        Also extracts actual parameter values from the pipeline Python file.
        """
        # Deep copy to avoid modifying original data
        pipeline = json.loads(json.dumps(pipeline_data))
        config = pipeline.get("config", {})
        operators = config.get("operators", [])
        
        # 从 pipeline 文件中提取实际参数值（init 和 run）
        file_path = config.get("file_path")
        pipeline_init_params = {}
        pipeline_run_params = {}
        if file_path and os.path.exists(file_path):
            analyzer = PipelineFileAnalyzer.from_file(file_path)
            pipeline_init_params = analyzer.init_params_by_class()
            pipeline_run_params = analyzer.run_params_by_class()
            logger.info(f"Extracted init params for {len(pipeline_init_params)} operators, run params for {len(pipeline_run_params)} operators")
        
        enriched_operators = []
        for op in operators:
            op_copy = op.copy()
            op_name = op.get("name")
            stored_params = op.get("params", {})
            if not isinstance(stored_params, dict):
                stored_params = {}
            
            # 检查是否已经是 enriched 格式（包含 init 和 run 键）
            if "init" in stored_params and "run" in stored_params:
                # 已经是 enriched 格式，直接使用
                enriched_operators.append(op_copy)
                continue
            
            op_details = container.operator_registry.get_op_details(op_name)
            
            # 获取该 operator 在 pipeline 代码中的实际参数值
            actual_init_params = pipeline_init_params.get(op_name, {})
            actual_run_params = pipeline_run_params.get(op_name, {})
            
            enriched_params = {
                "init": [],
                "run": []
            }
            
            if op_details:
                # Process init parameters
                init_defs = op_details.get("parameter", {}).get("init", [])
                processed_init_names = set()
                
                for param_def in init_defs:
                    p_name = param_def.get("name")
                    if not p_name:
                        continue
                    processed_init_names.add(p_name)
                    
                    # Priority: 
                    # 1. actual value from pipeline code (__init__)
                    # 2. stored params (user customized)
                    # 3. default value from operator definition
                    p_val = actual_init_params.get(p_name)
                    if p_val is None:
                        p_val = stored_params.get(p_name)
                    if p_val is None:
                        p_val = param_def.get("default_value")
                    if p_val is None and param_def.get("name") == "prompt_template":
                        # Get @prompt_restrict decorator from operator class
                        if op_details.get("allowed_prompts"):
                            p_val = op_details["allowed_prompts"][0]
                    # Create enriched param object
                    enriched_param = param_def.copy()
                    enriched_param["value"] = p_val
                    enriched_params["init"].append(enriched_param)

                # Process run parameters
                run_defs = op_details.get("parameter", {}).get("run", [])
                processed_run_names = set()
                
                for param_def in run_defs:
                    p_name = param_def.get("name")
                    if not p_name:
                        continue
                    processed_run_names.add(p_name)
                    
                    # Priority:
                    # 1. actual value from pipeline code (forward method's .run() call)
                    # 2. stored params (user customized)
                    # 3. default value from operator definition
                    p_val = actual_run_params.get(p_name)
                    if p_val is None:
                        p_val = stored_params.get(p_name)
                    if p_val is None:
                        p_val = param_def.get("default_value")
                        
                    # Create enriched param object
                    enriched_param = param_def.copy()
                    enriched_param["value"] = p_val
                    enriched_params["run"].append(enriched_param)
                
                # Add any stored params that were not in definition (dynamic params)
                # We put them in 'run' by default as they are likely runtime params
                for k, v in stored_params.items():
                    if k not in processed_init_names and k not in processed_run_names:
                        enriched_params["run"].append({
                            "name": k,
                            "value": v,
                            "default_value": None,
                            "kind": "DYNAMIC",
                            "description": "Dynamic parameter"
                        })
            else:
                # Operator not found in registry, just return stored params in 'run'
                for k, v in stored_params.items():
                    enriched_params["run"].append({
                        "name": k,
                        "value": v
                    })
            
            op_copy["params"] = enriched_params
            enriched_operators.append(op_copy)
            
        pipeline["config"]["operators"] = enriched_operators
        return pipeline