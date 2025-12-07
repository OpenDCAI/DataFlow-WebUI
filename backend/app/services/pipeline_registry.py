import json
import uuid
import datetime
import os
import yaml
import ast
import re
import hashlib
from typing import List, Optional, Dict, Any, Tuple
from app.core.logger_setup import get_logger
from app.core.config import settings
from app.services.operator_registry import _op_registry

logger = get_logger(__name__)

class PipelineRegistry:
    def __init__(self, path: str | None = None):
        """
        初始化Pipeline注册表
        加载api_pipelines目录中的所有py文件并提取operator执行顺序
        """
        self.path = path or settings.PIPELINE_REGISTRY
        self._ensure()
        # 初始化后，更新所有api pipeline的operators列表
        self._update_all_api_pipelines_operators()
    
    def _ensure(self):
        """
        确保注册表文件存在，并加载api_pipelines目录中的所有py文件
        """
        if not os.path.exists(self.path):
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            
            # 创建初始数据结构
            initial_data = {"pipelines": {}, "executions": {}}
            
            # 尝试加载api_pipelines目录中的py文件
            try:
                # 直接使用settings中的路径作为相对路径的开头
                api_pipelines_dir = os.path.join(settings.DataFlow_CORE_DIR, "api_pipelines")
                
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
                            pipeline_id = f"api_pipeline_{filename[:-3]}"
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
                else:
                    logger.warning(f"API pipelines directory not found: {api_pipelines_dir}")
            except Exception as e:
                logger.error(f"Error loading API pipelines: {e}", exc_info=True)
                # 即使出错，仍然创建基本的注册表文件
            
            # 写入初始数据到文件
            with open(self.path, "w", encoding="utf-8") as f:
                yaml.safe_dump(initial_data, f, allow_unicode=True)
    
    def _find_dataset_id(self, pipeline_file_path: str) -> str:
        """
        从pipeline文件中查找first_entry_file_name，并找到对应的数据集ID
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
                from app.services.dataset_registry import DatasetRegistry
                ds_registry = DatasetRegistry()
                
                # 1. 尝试通过路径匹配
                all_datasets = ds_registry.list()
                for ds in all_datasets:
                    if ds.get("root") == rel_path_from_cwd:
                        return ds.get("id")
                
                # 2. 如果没找到，尝试计算ID查找 (作为备选)
                ds_id = hashlib.md5(rel_path_from_cwd.encode("utf-8")).hexdigest()[:10]
                if ds_registry.get(ds_id):
                    return ds_id
                    
        except Exception as e:
            logger.warning(f"Failed to find dataset for pipeline {pipeline_file_path}: {e}")
        
        return ""

    def _update_all_api_pipelines_operators(self):
        """
        更新所有api pipeline的operators列表和input_dataset
        """
        try:
            data = self._read()
            api_pipelines_dir = os.path.join(settings.DataFlow_CORE_DIR, "api_pipelines")
            
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
                            pipeline_data["updated_at"] = self.get_current_time()
                            updated = True
                            logger.info(f"Updated pipeline {pipeline_id}")
            
            # 如果有更新，保存到文件
            if updated:
                self._write(data)
        except Exception as e:
            logger.error(f"Error updating API pipeline operators: {e}", exc_info=True)
    
    def _read(self) -> Dict:
        """读取注册表文件"""
        with open(self.path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {"pipelines": {}, "executions": {}}
    
    def _write(self, data: Dict):
        """写入注册表文件"""
        with open(self.path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)
    
    def parse_frontend_params(self, params_list):
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
        # 先更新所有api pipeline的operators列表
        self._update_all_api_pipelines_operators()
        
        data = self._read()
        pipelines = list(data.get("pipelines", {}).values())
        
        # Enrich pipelines with operator details
        return [self._enrich_pipeline_operators(p) for p in pipelines]
    
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
        
        # 直接保存到文件
        data["pipelines"][pipeline_id] = pipeline
        self._write(data)
        
        logger.info(f"Successfully created pipeline: {pipeline_id} with name: {pipeline_data.get('name', '')}")
        return self._enrich_pipeline_operators(pipeline)
    
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
                    pipeline_data["config"]["operators"] = operators
            
            # Enrich with operator details
            return self._enrich_pipeline_operators(pipeline_data)
        return None
    
    def update_pipeline(self, pipeline_id: str, pipeline_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新指定的Pipeline"""
        data = self._read()
        
        if pipeline_id not in data.get("pipelines", {}):
            raise ValueError(f"Pipeline with id {pipeline_id} not found")
        
        # 获取当前Pipeline数据并直接更新
        updated_pipeline = data["pipelines"][pipeline_id].copy()
        
        # 更新字段，保留创建时间和状态
        updated_pipeline.update({
            "name": pipeline_data.get("name", updated_pipeline.get("name", "")),
            "config": pipeline_data.get("config", updated_pipeline.get("config", {})),
            "tags": pipeline_data.get("tags", updated_pipeline.get("tags", [])),
            "updated_at": self.get_current_time()
            # 保持created_at和status不变
        })
        
        # 直接保存到文件
        data["pipelines"][pipeline_id] = updated_pipeline
        self._write(data)
        
        logger.info(f"Updated pipeline: {pipeline_id}")
        return self._enrich_pipeline_operators(updated_pipeline)
    
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
    
    async def execute_pipeline_task(self, execution_id: str, pipeline_config: Dict[str, Any]):
        """异步执行Pipeline的任务"""
        logs = []
        output = {}
        status = "running"
        logger.info(f"Starting background execution task for execution_id: {execution_id}")
        
        try:
            # 记录开始执行
            logs.append(f"[{self.get_current_time()}] Starting pipeline execution")
            logs.append(f"[{self.get_current_time()}] Input dataset: {pipeline_config.get('input_dataset', '')}")
            logs.append(f"[{self.get_current_time()}] Run config: {json.dumps(pipeline_config.get('run_config', {}))}")
            
            # 模拟数据加载
            logs.append(f"[{self.get_current_time()}] Loading dataset: {pipeline_config.get('input_dataset', '')}")
            
            # 按顺序执行算子
            current_data = {"dataset_id": pipeline_config.get('input_dataset', ''), "data": {}}
            operators = pipeline_config.get('operators', [])
            for i, operator in enumerate(operators):
                op_name = operator.get('name', 'Unknown')
                op_params = operator.get('params', {})
                logs.append(f"[{self.get_current_time()}] Executing operator {i+1}/{len(operators)}: {op_name}")
                logs.append(f"[{self.get_current_time()}] Operator params: {json.dumps(op_params)}")
                
                try:
                    # 模拟算子执行
                    current_data["data"] = {
                        "operator": op_name,
                        "params": op_params,
                        "output": f"Processed by {op_name}"
                    }
                    logs.append(f"[{self.get_current_time()}] Operator {op_name} executed successfully")
                except Exception as op_error:
                    error_msg = f"Operator {op_name} failed: {op_error}"
                    logs.append(f"[{self.get_current_time()}] ERROR: {error_msg}")
                    status = "failed"
                    output["error"] = error_msg
                    break
            
            # 更新执行结果
            if status != "failed":
                status = "completed"
                output["result"] = current_data
                logs.append(f"[{self.get_current_time()}] Pipeline execution completed successfully")
            
        except Exception as e:
            status = "failed"
            error_msg = f"Pipeline execution failed: {e}"
            logs.append(f"[{self.get_current_time()}] ERROR: {error_msg}")
            output["error"] = error_msg
        
        # 直接保存执行结果到文件
        execution_result = {
            "execution_id": execution_id,
            "status": status,
            "output": output,
            "logs": logs
        }
        
        data = self._read()
        data["executions"][execution_id] = execution_result
        self._write(data)
    
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
        data = self._read()
        data["executions"][execution_id] = initial_result
        self._write(data)
        
        return execution_id, pipeline_config, initial_result
    
    def get_execution_result(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """获取Pipeline执行结果"""
        data = self._read()
        execution_data = data.get("executions", {}).get(execution_id)
        if execution_data:
            return execution_data.copy()  # 返回副本避免修改原数据
        return None
    
    def list_executions(self) -> List[Dict[str, Any]]:
        """列出所有Pipeline执行记录"""
        data = self._read()
        # 直接返回字典列表，不需要转换为对象
        return list(data.get("executions", {}).values())

    def _enrich_pipeline_operators(self, pipeline_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich pipeline operators with detailed parameter info from registry.
        """
        # Deep copy to avoid modifying original data
        pipeline = json.loads(json.dumps(pipeline_data))
        config = pipeline.get("config", {})
        operators = config.get("operators", [])
        
        enriched_operators = []
        for op in operators:
            op_copy = op.copy()
            op_name = op.get("name")
            stored_params = op.get("params", {})
            if not isinstance(stored_params, dict):
                stored_params = {} 
            
            op_details = _op_registry.get_op_details(op_name)
            
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
                    
                    # Get value from stored params, or use default
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
                    
                    # Get value from stored params, or use default
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

def extract_operator_execution_order(file_path: str) -> List[str]:
    """
    使用ast模块解析Python文件，提取pipeline中operator的执行顺序
    从forward方法中提取所有.run()调用的对象类名
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
                        # 分析forward方法中的.run()调用
                        for stmt in ast.walk(method):
                            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                                # 检查是否是self.var.run()的形式
                                if isinstance(stmt.value.func, ast.Attribute) and stmt.value.func.attr == 'run':
                                    if isinstance(stmt.value.func.value, ast.Attribute) and isinstance(stmt.value.func.value.value, ast.Name) and stmt.value.func.value.value.id == 'self':
                                        var_name = stmt.value.func.value.attr
                                        if var_name in var_to_class_map:
                                            operator_class_names.append(var_to_class_map[var_name])
                                            logger.debug(f"Found operator execution: {var_name}.run() -> {var_to_class_map[var_name]}")
        
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

# 创建全局服务实例
_PIPELINE_REGISTRY = PipelineRegistry()