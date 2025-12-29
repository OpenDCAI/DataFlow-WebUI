from dataflow.serving import APILLMServing_request
from dataflow.utils.text2sql.database_manager import DatabaseManager
from dataflow.utils.storage import FileStorage
from dataflow.pipeline import PipelineABC
from dataflow.utils.registry import PROMPT_REGISTRY, OPERATOR_REGISTRY
from dataclasses import dataclass
from app.services.serving_registry import SERVING_CLS_REGISTRY
from app.core.config import settings
from app.core.container import container
from app.core.logger_setup import get_logger
from typing import Dict, Any, List, Optional
import os
import traceback
from datetime import datetime
import ray
import asyncio

logger = get_logger(__name__)

class DataFlowEngineError(Exception):
    """DataFlow Engine 自定义异常类"""
    def __init__(self, message: str, context: Dict[str, Any] = None, original_error: Exception = None):
        self.message = message
        self.context = context or {}
        self.original_error = original_error
        self.traceback_str = traceback.format_exc() if original_error else None
        super().__init__(self.message)
    
    def to_dict(self):
        """转换为字典格式，方便序列化"""
        return {
            "error": self.message,
            "context": self.context,
            "original_error": str(self.original_error) if self.original_error else None,
            "traceback": self.traceback_str
        }

def extract_class_name(value: Any) -> Any:
    """
    从类字符串中提取类名，如果不是类字符串则返回原值
    
    Examples:
        "<class 'dataflow.prompts.GeneralQuestionFilterPrompt'>" -> "GeneralQuestionFilterPrompt"
        "some_string" -> "some_string"
        123 -> 123
    """
    if isinstance(value, str) and "<class '" in value and "'>" in value:
        try:
            # 提取引号中的完整路径
            class_path = value.split("'")[1]
            # 获取最后一个点后面的类名
            class_name = class_path.split(".")[-1]
            return class_name
        except (IndexError, AttributeError):
            return value
    return value

@dataclass
class ExecutionStatus:
    pid: str
    status: str
    start_time: str
    end_time: str

class DataFlowEngine:
    
    def __init__(self):
        self.execution_map : Dict[str, ExecutionStatus] = {}
        
    def init_serving_instance(self, serving_id: Any, is_embedding: bool = False) -> APILLMServing_request:
        """初始化 Serving 实例"""
        try:
            params_dict = {}
            if serving_id is None:
                if settings.DEFAULT_SERVING_FILLING:
                    # Get The first serving in SERVING_REGISTRY
                    all_servings = container.serving_registry._get_all()
                    if not all_servings:
                        raise DataFlowEngineError(
                            f"没有可用的Serving配置",
                            context={"serving_id": serving_id}
                        )
                    # Get the first serving ID from the dictionary
                    if is_embedding:
                        first_serving_id = list(all_servings.keys())[1]
                    else:
                        first_serving_id = next(iter(all_servings))
                    serving_info = container.serving_registry._get(first_serving_id)
                    logger.info(f"Using default serving: {first_serving_id}", serving_info)
                else:
                    raise DataFlowEngineError(
                        f"Serving配置未找到",
                        context={"serving_id": serving_id}
                    )
            else:
                serving_info = container.serving_registry._get(serving_id)
            
            ## This part of code is only for APILLMServing_request
            if serving_info['cls_name'] == 'APILLMServing_request':
                api_key_val = None
                # Use the serving_id from serving_info (set by _get method)
                actual_serving_id = serving_info.get('id', serving_id)
                key_name_var = f"DF_API_KEY_{actual_serving_id}"
                
                # First pass: find values
                for params in serving_info['params']:
                    # Check 'value' first, then fallback to 'default_value'
                    current_val = params.get('value') if params.get('value') is not None else params.get('default_value')
                    
                    if params['name'] == 'api_key':
                        api_key_val = current_val
                    elif params['name'] == 'key_name_of_api_key':
                        key_name_var = current_val
                        params['value'] = key_name_var
                    
                # Build params dict for init
                for params in serving_info['params']:
                    if params['name'] != 'api_key':
                        params_dict[params['name']] = params.get('value') if params.get('value') is not None else params.get('default_value')
                
                logger.info(f"Initializing serving with params: {params_dict}")
                os.environ[key_name_var] = api_key_val
                logger.info(f"Environment variable {key_name_var} set to {api_key_val}")
                serving_instance = SERVING_CLS_REGISTRY[serving_info['cls_name']](**params_dict)
                
            return serving_instance
            
        except DataFlowEngineError:
            raise
        except Exception as e:
            raise DataFlowEngineError(
                f"初始化Serving实例失败",
                context={
                    "serving_id": serving_id,
                    "serving_info": serving_info if 'serving_info' in locals() else None,
                    "params_dict": params_dict if 'params_dict' in locals() else None
                },
                original_error=e
            )

    def init_database_manager(self, db_manager_id: str) -> DatabaseManager:
        db_manager_info = container.text2sql_database_manager_registry._get(db_manager_id)
        if not db_manager_info:
            raise ValueError(f"database_manager config not found: {db_manager_id}")

        db_type = db_manager_info.get("db_type") or "sqlite"
        config = db_manager_info.get("config")

        if config is None:
            if db_type == "sqlite":
                config = {"root_path": container.text2sql_database_registry.sqlite_root}
            else:
                raise KeyError("config")

        db_manager_instance = DatabaseManager(db_type=db_type, config=config)
        selected = db_manager_info.get("selected_db_ids") or []
        db_manager_instance.databases = {
            db_id: info for db_id, info in db_manager_instance.databases.items() if db_id in selected
        }
        return db_manager_instance

    
    def run(self, pipeline_config: Dict[str, Any], execution_id: str, execution_path: Optional[str] = None) -> Dict[str, Any]:
        """
        执行 Pipeline
        
        Args:
            pipeline_config: Pipeline 配置
            execution_id: 执行 ID
            execution_path: 执行记录文件路径（可选，用于实时更新状态）
        
        Returns:
            Dict: 符合 PipelineExecutionResult 格式的执行结果
                - execution_id: str
                - status: str (queued/running/completed/failed)
                - output: Dict[str, Any]
                - logs: List[str]
                - started_at: str
                - completed_at: str
        """
        started_at = datetime.now().isoformat()
        logs: List[str] = []
        output: Dict[str, Any] = {}
        # ✅ 新增：按算子分组的日志
        # ✅ 新增：stage -> operator -> logs
        stage_operator_logs: Dict[str, Dict[str, List[str]]] = {
            "global": {"__pipeline__": []},
            "init": {},
            "run": {},
        }
        
        # ✅ 新增：算子粒度状态追踪
        operator_progress: Dict[str, Dict[str, Any]] = {
            "init": {},
            "run": {}
        }

        # ✅ 新增：实时更新执行状态到文件
        def update_execution_status(status: str = None, partial_output: Dict[str, Any] = None):
            """实时更新执行状态到文件"""
            if not execution_path:
                return
            try:
                import json
                with open(execution_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if execution_id in data.get("executions", {}):
                    if status:
                        data["executions"][execution_id]["status"] = status
                    if partial_output:
                        # 更新 output 中的内容
                        data["executions"][execution_id]["output"].update(partial_output)
                        # 同时更新顶层的 operator_progress 字段（用于 get_execution_status 查询）
                        if "operator_progress" in partial_output:
                            data["executions"][execution_id]["operator_progress"] = partial_output["operator_progress"]
                    with open(execution_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2)
            except Exception as e:
                logger.error(f"Failed to update execution status: {e}")

        # ✅ 新增：统一写日志（同时写到全局 logs 和该算子的 logs）
        def add_log(stage: str, message: str, op_name: str = "__pipeline__"):
            """同时写入：全局流水 logs + 分stage/分operator日志"""
            ts_msg = message  # 你也可以在这里统一加时间戳
            logs.append(ts_msg)
            stage_operator_logs.setdefault(stage, {}).setdefault(op_name, []).append(ts_msg)
        
        add_log("global", f"[{started_at}] Starting pipeline execution: {execution_id}")
        logs.append(f"[{started_at}] Starting pipeline execution: {execution_id}")
        logger.info(f"Starting pipeline execution: {execution_id}")
        
        try:
            # Step 1: 初始化 Storage
            add_log("init", f"[{datetime.now().isoformat()}] Step 1: Initializing storage...")
            logs.append(f"[{datetime.now().isoformat()}] Step 1: Initializing storage...")
            logger.info(f"Step 1: Initializing storage...")
            try:
                input_dataset = pipeline_config["input_dataset"]
                if isinstance(input_dataset, dict):
                    input_dataset_id = input_dataset.get("id")
                else:
                    input_dataset_id = input_dataset
                    
                if not input_dataset_id:
                    raise DataFlowEngineError(
                        "Pipeline配置缺少input_dataset",
                        context={"pipeline_config": pipeline_config}
                    )
                
                dataset = container.dataset_registry.get(input_dataset_id)
                if not dataset:
                    raise DataFlowEngineError(
                        f"数据集未找到",
                        context={"dataset_id": input_dataset_id}
                    )
                
                from app.core.config import settings
                
                cache_path = settings.CACHE_DIR
                
                # 确保 cache 目录存在
                os.makedirs(cache_path, exist_ok=True)
                logger.info(f"Cache directory: {cache_path}, exists: {os.path.exists(cache_path)}")
                
                storage = FileStorage(
                    first_entry_file_name=os.path.abspath(dataset['root']),
                    cache_path=os.path.join(settings.BASE_DIR, "cache_local"),
                    file_name_prefix="dataflow_cache_step",
                    cache_type="jsonl",
                )
                add_log("init", f"Storage initialized with dataset: {dataset['root']}")
                logs.append(f"[{datetime.now().isoformat()}] Storage initialized with dataset: {dataset['root']}")
                logger.info(f"Storage initialized with dataset: {dataset['root']}")
                
            except DataFlowEngineError:
                raise
            except Exception as e:
                raise DataFlowEngineError(
                    "初始化Storage失败",
                    context={
                        "input_dataset": input_dataset_id if 'input_dataset_id' in locals() else None,
                        "dataset": dataset if 'dataset' in locals() else None
                    },
                    original_error=e
                )
            
            # Step 2: 初始化所有 Operators
            add_log("init", f"[{datetime.now().isoformat()}] Step 2: Initializing operators...")
            logs.append(f"[{datetime.now().isoformat()}] Step 2: Initializing operators...")
            logger.info(f"Step 2: Initializing operators...")
            
            serving_instance_map: Dict[str, APILLMServing_request] = {}
            embedding_serving_instance_map: Dict[str, APILLMServing_request] = {}
            db_manager_instance_map: Dict[Any, DatabaseManager] = {}
            run_op = []
            operators = pipeline_config.get("operators", [])
            
            add_log("init", f"[{datetime.now().isoformat()}] Found {len(operators)} operators to initialize")
            logs.append(f"[{datetime.now().isoformat()}] Found {len(operators)} operators to initialize")
            logger.info(f"Initializing {len(operators)} operators...")
            
            for op_idx, op in enumerate(operators):
                op_name = op.get("name", f"Operator_{op_idx}")
                add_log("init", f"[{datetime.now().isoformat()}] [{op_idx+1}/{len(operators)}] Initializing operator: {op_name}", op_name)
                logs.append(f"[{datetime.now().isoformat()}] [{op_idx+1}/{len(operators)}] Initializing operator: {op_name}")
                logger.info(f"[{op_idx+1}/{len(operators)}] Initializing operator: {op_name}")
                try:
                    init_params = {}
                    run_params = {}
                    
                    # 处理 init 参数
                    for param in op.get("params", {}).get("init", []):
                        param_name = param.get("name")
                        param_value = param.get("value")
                        
                        try:
                            if param_name == "llm_serving":
                                serving_id = param_value
                                logger.info(f"Operator {op_name}: initializing serving {serving_id}")
                                add_log("init", f"[{datetime.now().isoformat()}]   - Initializing LLM serving: {serving_id}", op_name)
                                logs.append(f"[{datetime.now().isoformat()}]   - Initializing LLM serving: {serving_id}")
                                if serving_id not in serving_instance_map:
                                    serving_instance_map[serving_id] = self.init_serving_instance(serving_id)
                                param_value = serving_instance_map[serving_id]

                            elif param_name == "embedding_serving":
                                serving_id = param_value
                                logger.info(f"Operator {op_name}: initializing embedding serving {serving_id}")
                                add_log("init", f"[{datetime.now().isoformat()}]   - Initializing embedding serving: {serving_id}", op_name)
                                logs.append(f"[{datetime.now().isoformat()}]   - Initializing embedding serving: {serving_id}")
                                if serving_id not in embedding_serving_instance_map:
                                    embedding_serving_instance_map[serving_id] = self.init_serving_instance(serving_id, is_embedding=True)
                                param_value = embedding_serving_instance_map[serving_id]

                            elif param_name == "database_manager":
                                dm_val = param_value
                                if isinstance(dm_val, list) or dm_val is None:
                                    cache_key = tuple(dm_val) if isinstance(dm_val, list) else None
                                    if cache_key not in db_manager_instance_map:
                                        db_manager_instance_map[cache_key] = container.text2sql_database_registry.get_manager(dm_val)
                                    param_value = db_manager_instance_map[cache_key]
                                else:
                                    db_manager_id = dm_val
                                    if db_manager_id not in db_manager_instance_map:
                                        db_manager_instance_map[db_manager_id] = self.init_database_manager(db_manager_id)
                                    param_value = db_manager_instance_map[db_manager_id]
                            
                            elif param_name == "prompt_template":
                                prompt_cls_name = extract_class_name(param_value)
                                add_log("init", f"[{datetime.now().isoformat()}]   - Loading prompt template: {prompt_cls_name}", op_name)
                                logs.append(f"[{datetime.now().isoformat()}]   - Loading prompt template: {prompt_cls_name}")
                                prompt_cls = PROMPT_REGISTRY.get(prompt_cls_name)
                                if not prompt_cls:
                                    raise DataFlowEngineError(
                                        f"Prompt类未找到: {prompt_cls_name}",
                                        context={"operator": op_name, "param": param_name}
                                    )
                                param_value = prompt_cls()
                            
                            init_params[param_name] = param_value
                            
                        except DataFlowEngineError:
                            raise
                        except Exception as e:
                            raise DataFlowEngineError(
                                f"处理参数失败: {param_name}",
                                context={
                                    "operator": op_name,
                                    "operator_index": op_idx,
                                    "param_name": param_name,
                                    "param_value": str(param_value)[:100]  # 限制长度
                                },
                                original_error=e
                            )
                    
                    # 处理 run 参数
                    for param in op.get("params", {}).get("run", []):
                        param_name = param.get("name")
                        param_value = param.get("value")
                        run_params[param_name] = param_value
                    
                    # 实例化 Operator
                    operator_cls_name = extract_class_name(op_name)
                    operator_cls = OPERATOR_REGISTRY.get(operator_cls_name)
                    
                    if not operator_cls:
                        raise DataFlowEngineError(
                            f"Operator类未找到: {operator_cls_name}",
                            context={"operator": op_name, "operator_index": op_idx}
                        )
                    
                    operator_instance = operator_cls(**init_params)
                    run_op.append((operator_instance, run_params, op_name))
                    add_log("init", f"[{datetime.now().isoformat()}] [{op_idx+1}/{len(operators)}] {op_name} initialized successfully", op_name)
                    logs.append(f"[{datetime.now().isoformat()}] [{op_idx+1}/{len(operators)}] {op_name} initialized successfully")
                    logger.info(f"Operator {op_name} initialized successfully")
                    
                except DataFlowEngineError:
                    raise
                except Exception as e:
                    raise DataFlowEngineError(
                        f"初始化Operator失败: {op_name}",
                        context={
                            "operator": op_name,
                            "operator_index": op_idx,
                            "init_params": {k: str(v)[:50] for k, v in init_params.items()} if 'init_params' in locals() else None
                        },
                        original_error=e
                    )
            
            # Step 3: 执行所有 Operators
            add_log("run", f"[{datetime.now().isoformat()}] Step 3: Executing {len(run_op)} operators...")
            logs.append(f"[{datetime.now().isoformat()}] Step 3: Executing {len(run_op)} operators...")
            logger.info(f"Executing {len(run_op)} operators...")
            
            execution_results = []
            for op_idx, (operator, run_params, op_name) in enumerate(run_op):
                try:
                    run_params["storage"] = storage.step()
                    add_log("run", f"[{datetime.now().isoformat()}] [{op_idx+1}/{len(run_op)}] Running operator: {op_name}", op_name)
                    logs.append(f"[{datetime.now().isoformat()}] [{op_idx+1}/{len(run_op)}] Running operator: {op_name}")
                    logger.info(f"[{op_idx+1}/{len(run_op)}] Running {op_name}")
                    logger.debug(f"Run params: {list(run_params.keys())}")
                    
                    # ✅ 更新算子粒度状态：开始执行
                    op_key = f"{op_name}_{op_idx}"
                    operator_progress["run"].setdefault(op_key, []).append(f"[{datetime.now().isoformat()}] Started")
                    # ✅ 记录当前正在执行的 step
                    operator_progress["current_step"] = op_idx
                    # ✅ 实时更新状态到文件
                    update_execution_status("running", {"operator_progress": operator_progress})
                    
                    api_pipeline_path = os.path.join(settings.DATAFLOW_CORE_DIR, "api_pipelines")
                    print(api_pipeline_path)
                    os.chdir(api_pipeline_path)
                    operator.run(**run_params)
                    os.chdir(settings.BASE_DIR)
                    
                    add_log("run", f"[{datetime.now().isoformat()}] [{op_idx+1}/{len(run_op)}] {op_name} completed successfully", op_name)
                    logs.append(f"[{datetime.now().isoformat()}] [{op_idx+1}/{len(run_op)}] {op_name} completed successfully")
                    logger.info(f"[{op_idx+1}/{len(run_op)}] {op_name} completed")
                    
                    # ✅ 更新算子粒度状态：执行完成
                    operator_progress["run"].setdefault(op_key, []).append(f"[{datetime.now().isoformat()}] Completed")
                    
                    # ✅ 记录缓存文件信息
                    from app.core.config import settings
                    cache_file = os.path.join(settings.CACHE_DIR, f"dataflow_cache_step_{op_idx}.jsonl")
                    cache_file_exists = os.path.exists(cache_file)
                    logger.info(f"[Pipeline] Operator {op_name} completed, cache_file: {cache_file}, exists: {cache_file_exists}")
                    if cache_file_exists:
                        try:
                            with open(cache_file, "r", encoding="utf-8") as f:
                                line_count = sum(1 for _ in f)
                            logger.info(f"[Pipeline] Cache file {cache_file} contains {line_count} lines")
                        except Exception as e:
                            logger.error(f"[Pipeline] Failed to read cache file: {e}")
                    
                    # ✅ 实时更新状态到文件
                    update_execution_status("running", {"operator_progress": operator_progress})
                    
                    execution_results.append({
                        "operator": op_name,
                        "status": "completed",
                        "index": op_idx
                    })
                    
                except Exception as e:
                    raise DataFlowEngineError(
                        f"执行Operator失败: {op_name}",
                        context={
                            "operator": op_name,
                            "operator_index": op_idx,
                            "total_operators": len(run_op),
                            "run_params": {k: str(v)[:50] for k, v in run_params.items() if k != "storage"}
                        },
                        original_error=e
                    )
            # os.chdir(settings.BASE_DIR)
            # 成功完成
            completed_at = datetime.now().isoformat()
            add_log("run", f"[{completed_at}] Pipeline execution completed successfully")
            logs.append(f"[{completed_at}] Pipeline execution completed successfully")
            logger.info(f"Pipeline execution completed successfully: {execution_id}")
            
            output["operators_executed"] = len(run_op)
            output["stage_operator_logs"] = stage_operator_logs
            output["operator_progress"] = operator_progress
            output["execution_results"] = execution_results
            output["success"] = True
            
            return {
                "execution_id": execution_id,
                "status": "completed",
                "output": output,
                "logs": logs,
                "started_at": started_at,
                "completed_at": completed_at
            }
            
        except DataFlowEngineError as e:
            completed_at = datetime.now().isoformat()
            error_log = f"[{completed_at}] ERROR: {e.message}"
            error_op_name = e.context.get("operator")
            if error_op_name:
                add_log("run", f"[{completed_at}] ERROR: {e.message}", error_op_name)
                # ✅ 更新算子粒度状态：执行失败
                operator_progress["run"].setdefault(error_op_name, []).append(f"[{completed_at}] Failed: {e.message}")
            logs.append(error_log)
            
            logger.error(f"Pipeline execution failed: {e.message}")
            logger.error(f"Context: {e.context}")
            if e.original_error:
                add_log("run", f"[{completed_at}] ERROR: {e.message}", error_op_name)
            
            # 返回失败结果
            output["error"] = e.message
            output["error_context"] = e.context
            output["original_error"] = str(e.original_error) if e.original_error else None
            output["stage_operator_logs"] = stage_operator_logs
            output["operator_progress"] = operator_progress

            
            return {
                "execution_id": execution_id,
                "status": "failed",
                "output": output,
                "logs": logs,
                "started_at": started_at,
                "completed_at": completed_at
            }
        
        except Exception as e:
            completed_at = datetime.now().isoformat()
            error_log = f"[{completed_at}] ERROR: Unexpected error - {str(e)}"
            logs.append(error_log)
            
            logger.error(f"Unexpected error during pipeline execution: {e}")
            logger.error(traceback.format_exc())
            
            # 返回失败结果
            output["error"] = "Pipeline执行过程中发生未预期的错误"
            output["error_message"] = str(e)
            output["stage_operator_logs"] = stage_operator_logs
            
            return {
                "execution_id": execution_id,
                "status": "failed",
                "output": output,
                "logs": logs,
                "started_at": started_at,
                "completed_at": completed_at
            }
            
dataflow_engine = DataFlowEngine()


class RayPipelineExecutor:
    """
    基于 Ray 的异步 Pipeline 执行器
    支持最大并行度为 1 的执行控制
    """
    
    def __init__(self, max_concurrency: int = 1):
        """
        初始化 Ray 执行器
        
        Args:
            max_concurrency: 最大并行度，默认为 1
        """
        self.max_concurrency = max_concurrency
        self._initialized = False
        self._semaphore = None
        logger.info(f"RayPipelineExecutor initialized with max_concurrency={max_concurrency}")
    
    def _ensure_initialized(self):
        """确保 Ray 已初始化"""
        if not self._initialized:
            if not ray.is_initialized():
                from app.core.config import settings
                
                # 获取项目根目录
                project_root = settings.BASE_DIR
                
                # 简化 Ray 初始化配置
                ray.init(
                    num_cpus=self.max_concurrency,
                    ignore_reinit_error=True,
                    log_to_driver=True,
                    logging_level="info"
                )
                logger.info("Ray initialized successfully")
                logger.info(f"Ray cluster resources: {ray.cluster_resources()}")
                logger.info(f"Ray working directory: {project_root}")
            self._initialized = True
    
    @staticmethod
    @ray.remote
    def _execute_pipeline_remote(
        pipeline_config: Dict[str, Any],
        execution_id: str,
        pipeline_registry_path: str,
        pipeline_execution_path: str
    ) -> Dict[str, Any]:
        """
        Ray 远程执行函数
        在独立的 Ray worker 中执行 Pipeline
        
        Args:
            pipeline_config: Pipeline 配置
            execution_id: 执行 ID
            pipeline_registry_path: Pipeline 注册表路径
            pipeline_execution_path: Pipeline 执行记录路径
        
        Returns:
            执行结果字典
        """
        # 立即输出日志，确认 Ray worker 启动
        print(f"[RAY WORKER] Starting execution: {execution_id}")
        
        try:
            import json
            import os
            from datetime import datetime
            from app.core.logger_setup import get_logger
            from app.core.container import container
            from app.core.config import settings
            from app.services.dataflow_engine import DataFlowEngine
            
            # 设置环境变量，标识这是 Ray worker
            os.environ["RAY_WORKER"] = "1"
            
            logger = get_logger(__name__)
            logger.info(f"[Ray Worker] Starting pipeline execution: {execution_id}")
            
            # 切换到正确的工作目录（与主进程一致）
            correct_dir = settings.BASE_DIR
            os.chdir(correct_dir)
            logger.info(f"[Ray Worker] Changed working directory to: {os.getcwd()}")
            
            logger.info(f"[Ray Worker] Starting pipeline execution: {execution_id}")
            
            logger.info(f"[Ray Worker] Current working directory: {os.getcwd()}")
            logger.info(f"[Ray Worker] BASE_DIR: {settings.BASE_DIR}")
            logger.info(f"[Ray Worker] CACHE_DIR: {settings.CACHE_DIR}")
            logger.info(f"[Ray Worker] DATA_REGISTRY: {settings.DATA_REGISTRY}")
            logger.info(f"[Ray Worker] DATAFLOW_CORE_DIR: {settings.DATAFLOW_CORE_DIR}")
            logger.info(f"[Ray Worker] DATA_REGISTRY exists: {os.path.exists(settings.DATA_REGISTRY)}")
            logger.info(f"[Ray Worker] DATAFLOW_CORE_DIR exists: {os.path.exists(settings.DATAFLOW_CORE_DIR)}")
            logger.info(f"[Ray Worker] CACHE_DIR exists: {os.path.exists(settings.CACHE_DIR)}")
            
            # 列出当前目录下的文件
            try:
                logger.info(f"[Ray Worker] Files in current directory: {os.listdir('.')[:20]}")
                if os.path.exists('data'):
                    logger.info(f"[Ray Worker] Files in data directory: {os.listdir('data')[:20]}")
                if os.path.exists(settings.CACHE_DIR):
                    logger.info(f"[Ray Worker] Files in cache directory: {os.listdir(settings.CACHE_DIR)[:20]}")
                else:
                    logger.warning(f"[Ray Worker] Cache directory does not exist: {settings.CACHE_DIR}")
            except Exception as e:
                logger.error(f"[Ray Worker] Failed to list files: {e}")
            
            container.init()
            logger.info(f"[Ray Worker] Container initialized, dataset_registry: {container.dataset_registry is not None}")
            
            # 检查数据集是否加载成功
            try:
                datasets = container.dataset_registry._read().get('datasets', {})
                logger.info(f"[Ray Worker] Dataset count: {len(datasets)}")
                logger.info(f"[Ray Worker] Dataset IDs (first 10): {list(datasets.keys())[:10]}")
                if 'input_dataset_id' in locals():
                    logger.info(f"[Ray Worker] Dataset {input_dataset_id} exists: {input_dataset_id in datasets}")
            except Exception as e:
                logger.error(f"[Ray Worker] Failed to read datasets: {e}")
                import traceback
                logger.error(traceback.format_exc())
            logger.info(f"[Ray Worker] Dataset count: {len(container.dataset_registry._read().get('datasets', {}))}")
            logger.info(f"[Ray Worker] Dataset IDs: {list(container.dataset_registry._read().get('datasets', {}).keys())[:10]}")
            
            # 更新状态为 running
            try:
                with open(pipeline_execution_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if execution_id in data.get("executions", {}):
                    data["executions"][execution_id]["status"] = "running"
                    data["executions"][execution_id]["started_at"] = datetime.now().isoformat()
                    with open(pipeline_execution_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2)
            except Exception as e:
                logger.error(f"[Ray Worker] Failed to update execution status to running: {e}")
            
            # 在 Ray worker 中创建新的 DataFlowEngine 实例
            worker_engine = DataFlowEngine()
            
            # 执行 Pipeline（传入 execution_path 以支持实时状态更新）
            result = worker_engine.run(pipeline_config, execution_id, execution_path=pipeline_execution_path)
            
            # 更新执行记录
            try:
                with open(pipeline_execution_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if execution_id in data.get("executions", {}):
                    data["executions"][execution_id].update(result)
                    with open(pipeline_execution_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2)
            except Exception as e:
                logger.error(f"[Ray Worker] Failed to update execution result: {e}")
            
            logger.info(f"[Ray Worker] Pipeline execution completed: {execution_id}")
            return result
            
        except Exception as e:
            import traceback
            logger.error(f"[Ray Worker] Pipeline execution failed: {e}")
            logger.error(traceback.format_exc())
            
            # 返回失败结果
            return {
                "execution_id": execution_id,
                "status": "failed",
                "output": {
                    "error": str(e),
                    "traceback": traceback.format_exc()
                },
                "logs": [f"ERROR: {str(e)}"],
                "started_at": datetime.now().isoformat(),
                "completed_at": datetime.now().isoformat()
            }
    
    async def submit_execution(
        self,
        pipeline_config: Dict[str, Any],
        execution_id: str,
        pipeline_registry_path: str,
        pipeline_execution_path: str
    ) -> str:
        """
        提交 Pipeline 执行任务到 Ray
        
        Args:
            pipeline_config: Pipeline 配置
            execution_id: 执行 ID
            pipeline_registry_path: Pipeline 注册表路径
            pipeline_execution_path: Pipeline 执行记录路径
        
        Returns:
            execution_id
        """
        self._ensure_initialized()
        
        logger.info(f"Submitting pipeline execution to Ray: {execution_id}")
        logger.info(f"Ray is initialized: {ray.is_initialized()}")
        
        # 提交远程任务
        try:
            future = self._execute_pipeline_remote.remote(
                pipeline_config,
                execution_id,
                pipeline_registry_path,
                pipeline_execution_path
            )
            
            logger.info(f"Pipeline execution submitted: {execution_id}, future: {future}")
            logger.info(f"Ray cluster resources: {ray.cluster_resources()}")
            logger.info(f"Ray available resources: {ray.available_resources()}")
            
            # 检查任务是否在队列中
            logger.info(f"Checking task status...")
            try:
                task_status = ray.get(future, timeout=1)
                logger.info(f"Task completed immediately: {task_status}")
            except Exception as e:
                logger.info(f"Task is still running: {e}")
            
            # 等待任务开始执行（最多等待 10 秒）
            logger.info(f"Waiting for Ray worker to start...")
            for i in range(10):
                await asyncio.sleep(1)
                logger.info(f"Waiting for Ray worker... {i+1}/10")
            
            return execution_id
            
        except Exception as e:
            logger.error(f"Failed to submit pipeline execution: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    async def get_execution_status(
        self,
        execution_id: str,
        pipeline_execution_path: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取执行状态
        
        Args:
            execution_id: 执行 ID
            pipeline_execution_path: Pipeline 执行记录路径
        
        Returns:
            执行状态字典，如果不存在则返回 None
        """
        try:
            import json
            with open(pipeline_execution_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("executions", {}).get(execution_id)
        except Exception as e:
            logger.error(f"Failed to get execution status for {execution_id}: {e}")
            return None
    
    def shutdown(self):
        """关闭 Ray"""
        if ray.is_initialized():
            ray.shutdown()
            self._initialized = False
            logger.info("Ray shutdown completed")


# 创建全局 Ray 执行器实例
ray_executor = RayPipelineExecutor(max_concurrency=1)
