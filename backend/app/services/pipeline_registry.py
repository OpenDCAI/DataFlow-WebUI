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

class PipelineRegistry:
    def __init__(self, path: str | None = None):
        """
        初始化Pipeline注册表
        加载api_pipelines目录中的所有py文件并提取operator执行顺序
        """
        self.path = path or settings.PIPELINE_REGISTRY
        self.execution_path = settings.PIPELINE_EXECUTION_PATH

        self._ensure()
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

    def _ensure(self):
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
                            operators = get_pipeline_operators_from_file(file_path)
                            
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
                                "tags": ["api"],
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
                    file_path = pipeline_data.get("config", {}).get("file_path")
                    if file_path and os.path.exists(file_path):
                        # 提取operator执行顺序
                        operators = get_pipeline_operators_from_file(file_path)
                        
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
    
    def _parse_frontend_params(self, params_list):
        """
        将前端 [{name: xxx, value: yyy}] 解析成字典 {xxx: yyy}
        """
        if not params_list:
            return {}

        parsed = {}
        for item in params_list:
            # item = {"name": "...", "value": ...}
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
        self._update_all_api_pipelines_operators()
        
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
        pipeline = {
            "id": pipeline_id,
            "name": pipeline_data.get("name", ""),
            "config": pipeline_data.get("config", {}),
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
                    operators = get_pipeline_operators_from_file(file_path)
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
                for op in updated_pipeline["config"]["operators"]:
                    op_map[op.get("name")] = op
                
                updated_operators = []
                for op in new_pipeline_config["operators"]:
                    old_op_info = op_map.get(op.get("name"), None)
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
            pipeline_init_params = extract_operator_params_from_pipeline(file_path)
            pipeline_run_params = extract_operator_run_params_from_pipeline(file_path)
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

def _ast_node_to_value(node: ast.AST) -> Any:
    """
    将 AST 节点转换为 Python 值
    """
    if isinstance(node, ast.Constant):
        return node.value
    elif isinstance(node, ast.Num):  # Python < 3.8
        return node.n
    elif isinstance(node, ast.Str):  # Python < 3.8
        return node.s
    elif isinstance(node, ast.NameConstant):  # Python < 3.8
        return node.value
    elif isinstance(node, ast.List):
        return [_ast_node_to_value(elt) for elt in node.elts]
    elif isinstance(node, ast.Tuple):
        return tuple(_ast_node_to_value(elt) for elt in node.elts)
    elif isinstance(node, ast.Dict):
        return {_ast_node_to_value(k): _ast_node_to_value(v) for k, v in zip(node.keys, node.values)}
    elif isinstance(node, ast.Name):
        # 变量引用，返回 None (让系统使用默认值)
        # 因为我们无法在静态分析时获取变量的实际值
        return None
    elif isinstance(node, ast.Attribute):
        # 属性访问，如 self.llm_serving 或 module.Class
        # 对于 self.xxx，返回 None
        if hasattr(node, 'value') and isinstance(node.value, ast.Name) and node.value.id == 'self':
            return None
        # 对于 module.Class()，保留类名字符串用于 prompt_template 等
        value_str = _ast_node_to_value(node.value) if hasattr(node, 'value') else ""
        full_name = f"{value_str}.{node.attr}" if value_str else node.attr
        # 去除 <var:> 前缀
        full_name = full_name.replace("<var:", "").replace(">", "")
        return f"<class '{full_name}'>"
    elif isinstance(node, ast.Call):
        # 函数调用，如 GeneralQuestionFilterPrompt()
        func_name = None
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
        
        # 对于 Prompt 类的实例化，返回类名字符串
        if func_name and "Prompt" in func_name:
            return f"<class 'dataflow.prompts.{func_name}'>"
        # 其他调用返回 None，让系统使用默认值
        return None
    else:
        # 无法解析的节点，返回 None
        return None

def extract_operator_params_from_pipeline(file_path: str) -> Dict[str, Dict[str, Any]]:
    """
    从 pipeline 文件中提取每个 operator 初始化时的实际参数值
    返回: {operator_class_name: {param_name: param_value}}
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
        
        tree = ast.parse(file_content)
        operator_params = {}
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for method in node.body:
                    if isinstance(method, ast.FunctionDef) and method.name == '__init__':
                        for stmt in method.body:
                            if isinstance(stmt, ast.Assign):
                                for target in stmt.targets:
                                    if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == 'self':
                                        if isinstance(stmt.value, ast.Call):
                                            # 获取类名
                                            class_name = None
                                            if isinstance(stmt.value.func, ast.Name):
                                                class_name = stmt.value.func.id
                                            elif isinstance(stmt.value.func, ast.Attribute):
                                                class_name = stmt.value.func.attr
                                            
                                            if class_name:
                                                # 提取参数
                                                params = {}
                                                
                                                # 提取位置参数 (暂不处理，因为需要知道参数名)
                                                # for i, arg in enumerate(stmt.value.args):
                                                #     params[f"arg_{i}"] = _ast_node_to_value(arg)
                                                
                                                # 提取关键字参数
                                                for keyword in stmt.value.keywords:
                                                    param_name = keyword.arg
                                                    param_value = _ast_node_to_value(keyword.value)
                                                    params[param_name] = param_value
                                                
                                                operator_params[class_name] = params
                                                logger.debug(f"Extracted params for {class_name}: {params}")
        
        return operator_params
    except Exception as e:
        logger.error(f"Error extracting operator params from {file_path}: {e}", exc_info=True)
        return {}

def extract_operator_run_params_from_pipeline(file_path: str) -> Dict[str, Dict[str, Any]]:
    """
    从 pipeline 文件的 forward 方法中提取每个 operator 的 run() 参数
    返回: {operator_class_name: {param_name: param_value}}
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
        
        tree = ast.parse(file_content)
        
        # 首先建立变量名到类名的映射
        var_to_class_map = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for method in node.body:
                    if isinstance(method, ast.FunctionDef) and method.name == '__init__':
                        for stmt in method.body:
                            if isinstance(stmt, ast.Assign):
                                for target in stmt.targets:
                                    if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == 'self':
                                        var_name = target.attr
                                        if isinstance(stmt.value, ast.Call):
                                            if isinstance(stmt.value.func, ast.Name):
                                                class_name = stmt.value.func.id
                                                var_to_class_map[var_name] = class_name
                                            elif isinstance(stmt.value.func, ast.Attribute):
                                                class_name = stmt.value.func.attr
                                                var_to_class_map[var_name] = class_name
        
        # 然后提取 forward 方法中的 run() 调用参数
        operator_run_params = {}
        
        def extract_run_params_from_node(node):
            """递归提取 run() 调用的参数"""
            if isinstance(node, ast.Call):
                # 检查是否是 self.xxx.run() 的形式
                if isinstance(node.func, ast.Attribute) and node.func.attr == 'run':
                    if isinstance(node.func.value, ast.Attribute) and isinstance(node.func.value.value, ast.Name) and node.func.value.value.id == 'self':
                        var_name = node.func.value.attr
                        if var_name in var_to_class_map:
                            class_name = var_to_class_map[var_name]
                            
                            # 提取 run() 的关键字参数
                            run_params = {}
                            for keyword in node.keywords:
                                param_name = keyword.arg
                                param_value = _ast_node_to_value(keyword.value)
                                run_params[param_name] = param_value
                            
                            operator_run_params[class_name] = run_params
                            logger.debug(f"Extracted run params for {class_name}: {run_params}")
            
            # 递归处理子节点
            for child in ast.iter_child_nodes(node):
                extract_run_params_from_node(child)
        
        # 遍历 forward 方法
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for method in node.body:
                    if isinstance(method, ast.FunctionDef) and method.name == 'forward':
                        for stmt in method.body:
                            extract_run_params_from_node(stmt)
        
        return operator_run_params
    except Exception as e:
        logger.error(f"Error extracting operator run params from {file_path}: {e}", exc_info=True)
        return {}

def _extract_run_calls_from_node(node: ast.AST, var_to_class_map: Dict[str, str], operator_class_names: List[str]):
    """递归提取所有 self.xxx.run() 调用"""
    if isinstance(node, ast.Call):
        # 检查是否是self.var.run()的形式
        if isinstance(node.func, ast.Attribute) and node.func.attr == 'run':
            if isinstance(node.func.value, ast.Attribute) and isinstance(node.func.value.value, ast.Name) and node.func.value.value.id == 'self':
                var_name = node.func.value.attr
                if var_name in var_to_class_map:
                    operator_class_names.append(var_to_class_map[var_name])
                    logger.debug(f"Found operator execution: {var_name}.run() -> {var_to_class_map[var_name]}")
    
    # 递归处理子节点
    for child in ast.iter_child_nodes(node):
        _extract_run_calls_from_node(child, var_to_class_map, operator_class_names)

def extract_operator_execution_order(file_path: str) -> List[str]:
    """
    使用ast模块解析Python文件，提取pipeline中operator的执行顺序
    从forward方法中按顺序提取所有.run()调用的对象类名
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
        
        # 解析Python代码为AST
        tree = ast.parse(file_content)
        
        # 存储找到的operator类名
        operator_class_names = []
        
        # 存储变量名到类名的映射
        var_to_class_map = {}
        
        # 首先，找出所有在__init__方法中创建的operator实例
        for node in ast.walk(tree):
            # 查找类定义
            if isinstance(node, ast.ClassDef):
                # 查找__init__方法
                for method in node.body:
                    if isinstance(method, ast.FunctionDef) and method.name == '__init__':
                        # 分析__init__方法中的赋值语句
                        for stmt in method.body:
                            if isinstance(stmt, ast.Assign):
                                for target in stmt.targets:
                                    # 检查是否是self.var = Class()的形式
                                    if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == 'self':
                                        var_name = target.attr
                                        # 检查右侧是否是调用表达式
                                        if isinstance(stmt.value, ast.Call):
                                            # 获取类名
                                            if isinstance(stmt.value.func, ast.Name):
                                                class_name = stmt.value.func.id
                                                var_to_class_map[var_name] = class_name
                                                logger.debug(f"Found operator: {var_name} = {class_name}")
                                            elif isinstance(stmt.value.func, ast.Attribute):
                                                # 处理形如module.Class()的情况
                                                class_name = stmt.value.func.attr
                                                var_to_class_map[var_name] = class_name
                                                logger.debug(f"Found operator: {var_name} = {class_name}")
            
            # 查找forward方法
            if isinstance(node, ast.ClassDef):
                for method in node.body:
                    if isinstance(method, ast.FunctionDef) and method.name == 'forward':
                        # 按顺序遍历 forward 方法中的语句
                        for stmt in method.body:
                            # 递归检查语句中的所有 Call 节点，保持顺序
                            _extract_run_calls_from_node(stmt, var_to_class_map, operator_class_names)
        
        return operator_class_names
    except Exception as e:
        logger.error(f"Error parsing file {file_path}: {e}", exc_info=True)
        return []

def get_pipeline_operators_from_file(file_path: str) -> List[Dict[str, Any]]:
    """
    从pipeline文件中提取operator列表
    """
    operator_class_names = extract_operator_execution_order(file_path)
    # 将类名转换为PipelineOperator格式
    return [{'name': class_name, 'params': {}} for class_name in operator_class_names]
