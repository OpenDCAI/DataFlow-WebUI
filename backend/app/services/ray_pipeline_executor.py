from app.core.logger_setup import get_logger
from dataflow.serving import APILLMServing_request
from dataflow.utils.text2sql.database_manager import DatabaseManager
from dataflow.utils.storage import FileStorage
from dataflow.pipeline import PipelineABC
from dataflow.utils.registry import PROMPT_REGISTRY, OPERATOR_REGISTRY
import ray
from typing import Dict, Any, Optional, List
from app.core.config import settings
import asyncio
import json
import os
from datetime import datetime
import traceback
import io
import sys
from contextlib import redirect_stdout, redirect_stderr

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


def dataflow_pipeline_execute(pipeline_config: Dict[str, Any], dataflow_runtime: Dict[str, Any], task_id: str, execution_path: str):
    """
    Execute a DataFlow pipeline
    
    Args:
        pipeline_config: Pipeline configuration
        dataflow_runtime: DataFlow runtime configuration
        task_id: Execution ID
        execution_path: Execution path
    """
    started_at = datetime.now().isoformat()
    logs: List[str] = []
    output: Dict[str, Any] = {}
    global settings
    # ✅ 新增：按算子分组的日志
    # ✅ 新增：stage -> operator -> logs
    operator_logs: Dict[str, List[str]] = {} # keyed by op_name_index
    
    # ✅ 新增：算子粒度运行结果详情
    operators_detail: Dict[str, Dict[str, Any]] = {}

    # ✅ 新增：实时更新执行状态到文件
    def update_execution_status(status: str = None, partial_output: Dict[str, Any] = None):
        """实时更新执行状态到文件"""
        if not execution_path:
            return
        try:
            import json
            with open(execution_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if task_id in data.get("tasks", {}):
                if status:
                    data["tasks"][task_id]["status"] = status
                if partial_output:
                    if "output" not in data["tasks"][task_id]:
                             data["tasks"][task_id]["output"] = {}
                    # 更新 output 中的内容
                    data["tasks"][task_id]["output"].update(partial_output)
                    
                with open(execution_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to update execution status: {e}")

    # ✅ 新增：统一写日志（同时写到全局 logs 和该算子的 logs）
    def add_log(stage: str, message: str, op_name: str = "__pipeline__"):
        """同时写入：全局流水 logs + 分operator日志"""
        ts_msg = message
        logs.append(ts_msg)
        
        # 如果是具体的算子，记录到 operator_logs
        if op_name != "__pipeline__":
            operator_logs.setdefault(op_name, []).append(ts_msg)
    
    logger.success(f"Input dataflow runtime: {dataflow_runtime}")
    
    
    add_log("global", f"[{started_at}] Starting pipeline execution: {task_id}")
    logs.append(f"[{started_at}] Starting pipeline execution: {task_id}")
    logger.info(f"Starting pipeline execution: {task_id}")
    try:
        # Step 1: 初始化 Storage
        add_log("init", f"[{datetime.now().isoformat()}] Step 1: Initializing storage...")
        logs.append(f"[{datetime.now().isoformat()}] Step 1: Initializing storage...")
        logger.info(f"Step 1: Initializing storage...")
        try:    
            storage = FileStorage(
                first_entry_file_name=dataflow_runtime['storage']['first_entry_file_name'],
                cache_path=dataflow_runtime['storage']['cache_path'],
                file_name_prefix=dataflow_runtime['storage']['file_name_prefix'],
                cache_type=dataflow_runtime['storage']['cache_type'],
            )
            add_log("init", f"Storage initialized with dataset: {dataflow_runtime['storage']['first_entry_file_name']}")
            logs.append(f"[{datetime.now().isoformat()}] Storage initialized with dataset: {dataflow_runtime['storage']['first_entry_file_name']}")
            logger.info(f"Storage initialized with dataset: {dataflow_runtime['storage']['first_entry_file_name']}")
            
        except Exception as e:
            raise Exception(f"Failed to initialize storage: {e}")
        
        # Step 2: 初始化所有 Operators
        add_log("init", f"[{datetime.now().isoformat()}] Step 2: Initializing operators...")
        logs.append(f"[{datetime.now().isoformat()}] Step 2: Initializing operators...")
        logger.info(f"Step 2: Initializing operators...")
        
        serving_instance_map: Dict[str, Any] = {}
        embedding_serving_instance_map: Dict[str, Any] = {}
        db_manager_instance_map: Dict[Any, DatabaseManager] = {}
        run_op = []
        operators = pipeline_config.get("operators", [])
        
        add_log("init", f"[{datetime.now().isoformat()}] Found {len(operators)} operators to initialize")
        logs.append(f"[{datetime.now().isoformat()}] Found {len(operators)} operators to initialize")
        logger.info(f"Initializing {len(operators)} operators...")
        OPERATOR_REGISTRY._get_all()
        for op_idx, op in enumerate(operators):
            op_name = op.get("name", f"Operator_{op_idx}")
            op_key = f"{op_name}_{op_idx}"
            operators_detail[op_key] = {
                "name": op_name,
                "index": op_idx,
                "status": "initializing"
            }
            add_log("init", f"[{datetime.now().isoformat()}] [{op_idx+1}/{len(operators)}] Initializing operator: {op_name}", op_key)
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
                            add_log("init", f"[{datetime.now().isoformat()}]   - Initializing LLM serving: {serving_id}", op_key)
                            if serving_id not in serving_instance_map:
                                serving_info = dataflow_runtime['serving_map'][serving_id]
                                params_dict = {}
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
                                    serving_instance = APILLMServing_request(**params_dict)
                                else:
                                    raise DataFlowEngineError(f"Unsupported serving class: {serving_info['cls_name']}")
                                serving_instance_map[serving_id] = serving_instance
                            param_value = serving_instance_map[serving_id]

                        elif param_name == "embedding_serving":
                            serving_id = param_value
                            logger.info(f"Operator {op_name}: initializing embedding serving {serving_id}")
                            add_log("init", f"[{datetime.now().isoformat()}]   - Initializing embedding serving: {serving_id}", op_name)
                            logs.append(f"[{datetime.now().isoformat()}]   - Initializing embedding serving: {serving_id}")
                            if serving_id not in embedding_serving_instance_map:
                                serving_info = dataflow_runtime['embedding_serving_map'][serving_id]
                                params_dict = {}
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
                                    serving_instance = APILLMServing_request(**params_dict)
                                else:
                                    raise DataFlowEngineError(f"Unsupported serving class: {serving_info['cls_name']}")
                                embedding_serving_instance_map[serving_id] = serving_instance
                            param_value = embedding_serving_instance_map[serving_id]

                        elif param_name == "database_manager":
                            dm_val = param_value
                            if isinstance(dm_val, list) or dm_val is None:
                                cache_key = tuple(dm_val) if isinstance(dm_val, list) else None
                                if cache_key not in db_manager_instance_map:
                                    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                                    SQLITE_DB_DIR: str = os.path.join(BASE_DIR, "data", "text2sql_dbs") # where sqlite database files are stored
                                    mgr = DatabaseManager(db_type="sqlite", config={"root_path": SQLITE_DB_DIR})
                                    if dm_val is not None:
                                        allow = set(dm_val)
                                        mgr.databases = {db_id: info for db_id, info in mgr.databases.items() if db_id in allow}
                                    db_manager_instance_map[cache_key] = mgr
                                param_value = db_manager_instance_map[cache_key]
                            else:
                                db_manager_id = dm_val
                                if db_manager_id not in db_manager_instance_map:
                                    db_manager_info = dataflow_runtime['db_manager_map'][db_manager_id]
                                    db_type = db_manager_info.get("db_type") or "sqlite"
                                    config = db_manager_info.get("config")

                                    if config is None:
                                        if db_type == "sqlite":
                                            BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                                            SQLITE_DB_DIR: str = os.path.join(BASE_DIR, "data", "text2sql_dbs") # where sqlite database files are stored
                                            config = {"root_path": SQLITE_DB_DIR}
                                        else:
                                            raise KeyError("config")

                                    db_manager_instance = DatabaseManager(db_type=db_type, config=config)
                                    selected = db_manager_info.get("selected_db_ids") or []
                                    db_manager_instance.databases = {
                                        db_id: info for db_id, info in db_manager_instance.databases.items() if db_id in selected
                                    }
                                    db_manager_instance_map[db_manager_id] = db_manager_instance
                                param_value = db_manager_instance_map[db_manager_id]
                        
                        elif param_name == "prompt_template":
                            prompt_cls_name = extract_class_name(param_value)
                            add_log("init", f"[{datetime.now().isoformat()}]   - Loading prompt template: {prompt_cls_name}", op_key)
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
                run_op.append((operator_instance, run_params, op_name, op_key))
                
                operators_detail[op_key]["status"] = "initialized"
                add_log("init", f"[{datetime.now().isoformat()}] [{op_idx+1}/{len(operators)}] {op_name} initialized successfully", op_key)
                logger.info(f"Operator {op_name} initialized successfully")
                
            except DataFlowEngineError:
                operators_detail[op_key]["status"] = "failed"
                raise
            except Exception as e:
                operators_detail[op_key]["status"] = "failed"
                raise DataFlowEngineError(
                    f"初始化Operator失败: {op_name}",
                    context={
                        "operator": op_name,
                        "operator_index": op_idx,
                        "init_params": {k: str(v)[:50] for k, v in init_params.items()} if 'init_params' in locals() else None
                    },
                    original_error=e
                )
        add_log("run", f"[{datetime.now().isoformat()}] Step 3: Executing {len(run_op)} operators...")
        logger.info(f"Executing {len(run_op)} operators...")
        
        execution_results = []
        for op_idx, (operator, run_params, op_name, op_key) in enumerate(run_op):
            try:
                run_params["storage"] = storage.step()
                add_log("run", f"[{datetime.now().isoformat()}] [{op_idx+1}/{len(run_op)}] Running operator: {op_name}", op_key)
                logger.info(f"[{op_idx+1}/{len(run_op)}] Running {op_name}")
                logger.debug(f"Run params: {list(run_params.keys())}")
                
                 # ✅ 更新算子粒度状态：开始执行
                operators_detail[op_key]["status"] = "running"
                operators_detail[op_key]["started_at"] = datetime.now().isoformat()
                
                # ✅ 实时更新状态到文件
                update_execution_status("running", {
                    "operators_detail": operators_detail,
                    "operator_logs": operator_logs
                })
                
                api_pipeline_path = os.path.join(settings.DATAFLOW_CORE_DIR, "api_pipelines")
                print(api_pipeline_path)
                os.chdir(api_pipeline_path)
                
                # ✅ 捕获 stdout/stderr
                f_stdout = io.StringIO()
                f_stderr = io.StringIO()
                
                try:    
                    with redirect_stdout(f_stdout), redirect_stderr(f_stderr):
                        operator.run(**run_params)
                finally:
                    stdout_str = f_stdout.getvalue()
                    stderr_str = f_stderr.getvalue()
                    
                    if stdout_str:
                        for line in stdout_str.splitlines():
                            if line.strip():
                                add_log("run", f"[STDOUT] {line}", op_key)
                    if stderr_str:
                        for line in stderr_str.splitlines():
                            if line.strip():
                                add_log("run", f"[STDERR] {line}", op_key)

                os.chdir(settings.BASE_DIR)

                # ✅ 获取处理后的数据量
                # 尝试从 output file 获取
                sample_count = 0
                storage_obj = run_params.get("storage")
                
                if storage_obj:
                     f_path = None
                     # 尝试使用 _get_cache_file_path 推断输出文件路径
                     if hasattr(storage_obj, "_get_cache_file_path") and hasattr(storage_obj, "operator_step"):
                         try:
                             # operator_step 是输入 step，输出在 step + 1
                             f_path = storage_obj._get_cache_file_path(storage_obj.operator_step + 1)
                         except Exception:
                             pass
                     
                     if f_path and os.path.exists(f_path):
                         try:
                             with open(f_path, 'r', encoding='utf-8') as f:
                                 sample_count = sum(1 for _ in f)
                         except Exception as e:
                             logger.warning(f"Failed to count lines in {f_path}: {e}")
                             add_log("run", f"WARN: Failed to read output file: {e}", op_key)
                
                operators_detail[op_key]["sample_count"] = sample_count
                add_log("run", f"Processed {sample_count} samples", op_key)
                
                add_log("run", f"[{datetime.now().isoformat()}] [{op_idx+1}/{len(run_op)}] {op_name} completed successfully", op_key)
                logger.info(f"[{op_idx+1}/{len(run_op)}] {op_name} completed")
                
                # ✅ 更新算子粒度状态：执行完成
                operators_detail[op_key]["status"] = "completed"
                operators_detail[op_key]["completed_at"] = datetime.now().isoformat()
                
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
                update_execution_status("running", {
                    "operators_detail": operators_detail,
                    "operator_logs": operator_logs
                })
                
                execution_results.append({
                    "operator": op_name,
                    "status": "completed",
                    "index": op_idx
                })
                
            except Exception as e:
                operators_detail[op_key]["status"] = "failed"
                operators_detail[op_key]["error"] = str(e)
                update_execution_status("failed", {
                    "operators_detail": operators_detail,
                    "operator_logs": operator_logs
                })
                
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
        add_log("global", f"[{completed_at}] Pipeline execution completed successfully")
        logger.info(f"Pipeline execution completed successfully: {task_id}")
        
        output["operators_executed"] = len(run_op)
        output["operators_detail"] = operators_detail
        output["operator_logs"] = operator_logs
        output["execution_results"] = execution_results
        output["success"] = True
        
        return {
            "task_id": task_id,
            "status": "completed",
            "output": output,
            "logs": logs,
            "operator_logs": operator_logs, # Return structured logs
            "started_at": started_at,
            "completed_at": completed_at
        }
        
    except DataFlowEngineError as e:
        completed_at = datetime.now().isoformat()
        error_log = f"[{completed_at}] ERROR: {e.message}"
        error_op_name = e.context.get("operator")
        if error_op_name:
             # Find matching key in operators_detail or iterate
            target_key = None
            for k, v in operators_detail.items():
                if v["name"] == error_op_name:
                    target_key = k
                    break
            
            if target_key:
                add_log("run", f"[{completed_at}] ERROR: {e.message}", target_key)
                operators_detail[target_key]["status"] = "failed"
                operators_detail[target_key]["error"] = e.message
        
        logs.append(error_log)
        
        logger.error(f"Pipeline execution failed: {e.message}")
        logger.error(f"Context: {e.context}")
        
        # 返回失败结果
        output["error"] = e.message
        output["error_context"] = e.context
        output["original_error"] = str(e.original_error) if e.original_error else None
        output["operators_detail"] = operators_detail

        
        return {
            "task_id": task_id,
            "status": "failed",
            "output": output,
            "logs": logs,
            "operator_logs": operator_logs,
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
        output["operators_detail"] = operators_detail
        
        return {
            "task_id": task_id,
            "status": "failed",
            "output": output,
            "logs": logs,
            "started_at": started_at,
            "completed_at": completed_at
        }
    
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
        self._task_refs: Dict[str, ray.ObjectRef] = {}
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
        dataflow_runtime: Dict[str, Any],
        task_id: str,
        pipeline_registry_path: str,
        pipeline_execution_path: str
    ) -> Dict[str, Any]:
        """
        Ray 远程执行函数
        在独立的 Ray worker 中执行 Pipeline
        
        Args:
            pipeline_config: Pipeline 配置
            dataflow_runtime: Dataflow 运行时
            task_id: 执行 ID
            pipeline_registry_path: Pipeline 注册表路径
            pipeline_execution_path: Pipeline 执行记录路径
        
        Returns:
            执行结果字典
        """
        # 立即输出日志，确认 Ray worker 启动
        print(f"[RAY WORKER] Starting execution: {task_id}")
        
        try:
            import json
            import os
            from datetime import datetime
            from app.core.logger_setup import get_logger
            from app.core.config import settings
            from app.services.dataflow_engine import DataFlowEngine
            
            # 设置环境变量，标识这是 Ray worker
            os.environ["RAY_WORKER"] = "1"
            
            logger = get_logger(__name__)
            logger.info(f"[Ray Worker] Starting pipeline execution: {task_id}")
            
            # 切换到正确的工作目录（与主进程一致）
            correct_dir = settings.BASE_DIR
            os.chdir(correct_dir)
            logger.info(f"[Ray Worker] Changed working directory to: {os.getcwd()}")
            
            logger.info(f"[Ray Worker] Starting pipeline execution: {task_id}")
            
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
                        
            # 检查数据集是否加载成功
            
            # 更新状态为 running
            try:
                with open(pipeline_execution_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if task_id in data.get("tasks", {}):
                    data["tasks"][task_id]["status"] = "running"
                    data["tasks"][task_id]["started_at"] = datetime.now().isoformat()
                    with open(pipeline_execution_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2)
            except Exception as e:
                logger.error(f"[Ray Worker] Failed to update execution status to running: {e}")
                        
            # 执行 Pipeline（传入 execution_path 以支持实时状态更新）
            result = dataflow_pipeline_execute(pipeline_config, dataflow_runtime, task_id, execution_path=pipeline_execution_path)
            
            # 更新执行记录
            try:
                with open(pipeline_execution_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if task_id in data.get("tasks", {}):
                    data["tasks"][task_id].update(result)
                    with open(pipeline_execution_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2)
            except Exception as e:
                logger.error(f"[Ray Worker] Failed to update execution result: {e}")
            
            logger.info(f"[Ray Worker] Pipeline execution completed: {task_id}")
            return result
            
        except Exception as e:
            import traceback
            logger.error(f"[Ray Worker] Pipeline execution failed: {e}")
            logger.error(traceback.format_exc())
            
            # 返回失败结果
            return {
                "task_id": task_id,
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
        dataflow_runtime: Dict[str, Any],
        task_id: str,
        pipeline_registry_path: str,
        pipeline_execution_path: str
    ) -> str:
        """
        提交 Pipeline 执行任务到 Ray
        
        Args:
            pipeline_config: Pipeline 配置
            task_id: 执行 ID
            pipeline_registry_path: Pipeline 注册表路径
            pipeline_execution_path: Pipeline 执行记录路径
        
        Returns:
            task_id
        """
        self._ensure_initialized()
        
        logger.info(f"Submitting pipeline execution to Ray: {task_id}")
        logger.info(f"Ray is initialized: {ray.is_initialized()}")
        
        # 提交远程任务
        try:
            future = self._execute_pipeline_remote.remote(
                pipeline_config,
                dataflow_runtime,
                task_id,
                pipeline_registry_path,
                pipeline_execution_path
            )
            
            # 保存任务引用，用于后续kill操作
            self._task_refs[task_id] = future
            
            logger.info(f"Pipeline execution submitted: {task_id}, future: {future}")
            logger.info(f"Ray cluster resources: {ray.cluster_resources()}")
            logger.info(f"Ray available resources: {ray.available_resources()}")
            
            # 异步接口，立即返回，不等待任务开始执行
            return task_id
            
        except Exception as e:
            logger.error(f"Failed to submit pipeline execution: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    async def get_execution_status(
        self,
        task_id: str,
        pipeline_execution_path: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取执行状态
        
        Args:
            task_id: 执行 ID
            pipeline_execution_path: Pipeline 执行记录路径
        
        Returns:
            执行状态字典，如果不存在则返回 None
        """
        try:
            import json
            with open(pipeline_execution_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("tasks", {}).get(task_id)
        except Exception as e:
            logger.error(f"Failed to get execution status for {task_id}: {e}")
            return None
    
    def shutdown(self):
        """关闭 Ray"""
        if ray.is_initialized():
            ray.shutdown()
            self._initialized = False
            logger.info("Ray shutdown completed")

    def kill_execution(self, task_id: str) -> bool:
        """
        终止指定的 Pipeline 执行任务
        
        Args:
            task_id: 执行 ID
        
        Returns:
            是否成功终止
        """
        if task_id not in self._task_refs:
            logger.warning(f"Task {task_id} not found in tracked tasks")
            return False
        
        try:
            task_ref = self._task_refs[task_id]
            
            # force=True 确保即使任务已经在运行也会被强制终止
            # recursive=True 确保取消所有子任务
            ray.cancel(task_ref, force=True, recursive=True)
            
            # 从追踪字典中移除
            del self._task_refs[task_id]
            
            logger.info(f"Successfully cancelled task {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel task {task_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False


# 创建全局 Ray 执行器实例
ray_executor = RayPipelineExecutor(max_concurrency=1)
