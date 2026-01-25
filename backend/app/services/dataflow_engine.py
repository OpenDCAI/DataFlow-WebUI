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
                            f"No available Serving configuration",
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
                        f"Serving configuration not found",
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
                f"Failed to initialize Serving instance",
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

    @staticmethod
    def decode_hashed_arguments(pipeline_config: Dict[str, Any], task_id: str) -> Dict[str, Any]:
        """
        解码哈希化的参数
        """
        dataflow_runtime = {
            "storage": {},
            "serving_map" : {},
            "embedding_serving_map" : {},
            "db_manager_map" : {},
        }
        try:
            input_dataset = pipeline_config["input_dataset"]
            if isinstance(input_dataset, dict):
                input_dataset_id = input_dataset.get("id")
            else:
                input_dataset_id = input_dataset
                
            if not input_dataset_id:
                raise DataFlowEngineError(
                    "Pipeline configuration missing input_dataset",
                    context={"pipeline_config": pipeline_config}
                )
            
            dataset = container.dataset_registry.get(input_dataset_id)
            if not dataset:
                raise DataFlowEngineError(
                    f"Dataset not found",
                    context={"dataset_id": input_dataset_id}
                )
            
            from app.core.config import settings
            
            cache_path = settings.CACHE_DIR
            
            # 确保 cache 目录存在
            os.makedirs(cache_path, exist_ok=True)
            logger.info(f"Cache directory: {cache_path}, exists: {os.path.exists(cache_path)}")
            
            dataflow_runtime["storage"] = {
                "type": "file",
                "first_entry_file_name": os.path.abspath(dataset['root']),
                "cache_path": os.path.join(settings.BASE_DIR, "cache_local", f"{task_id}_output"),
                "file_name_prefix": "dataflow_cache_step",
                "cache_type": "jsonl",
            }

            logger.info(f"Storage initialized with dataset: {dataset['root']}")
            
        except DataFlowEngineError:
            raise
        except Exception as e:
            raise DataFlowEngineError(
                "Failed to initialize Storage",
                context={
                    "input_dataset": input_dataset_id if 'input_dataset_id' in locals() else None,
                    "dataset": dataset if 'dataset' in locals() else None
                },
                original_error=e
            )
            
        operators = pipeline_config.get("operators", [])

        for op_idx, op in enumerate(operators):
            op_name = op.get("name", f"Operator_{op_idx}")
            logger.info(f"[{op_idx+1}/{len(operators)}] Initializing operator: {op_name}")                
                # 处理 init 参数
            for param in op.get("params", {}).get("init", []):
                param_name = param.get("name")
                param_value = param.get("value")
                
                try:
                    if param_name == "llm_serving":
                        serving_id = param_value
                        logger.info(f"Operator {op_name}: initializing serving {serving_id}")
                        if serving_id not in dataflow_runtime["serving_map"]:
                            if serving_id is None:
                                if settings.DEFAULT_SERVING_FILLING:
                                    # Get The first serving in SERVING_REGISTRY
                                    all_servings = container.serving_registry._get_all()
                                    if not all_servings:
                                        raise DataFlowEngineError(
                                            f"No available Serving configuration",
                                            context={"serving_id": serving_id}
                                        )
                                    first_serving_id = next(iter(all_servings))
                                    serving_info = container.serving_registry._get(first_serving_id)
                                    logger.info(f"Using default serving: {first_serving_id}", serving_info)
                                else:
                                    raise DataFlowEngineError(
                                        f"Serving configuration not found",
                                        context={"serving_id": serving_id}
                                    )
                            else:
                                serving_info = container.serving_registry._get(serving_id)
                            dataflow_runtime["serving_map"][serving_id] = serving_info

                    elif param_name == "embedding_serving":
                        serving_id = param_value
                        logger.info(f"Operator {op_name}: initializing embedding serving {serving_id}")
                        if serving_id not in dataflow_runtime["embedding_serving_map"]:
                            if serving_id is None:
                                if settings.DEFAULT_SERVING_FILLING:
                                    # Get The first serving in SERVING_REGISTRY
                                    all_servings = container.serving_registry._get_all()
                                    if not all_servings:
                                        raise DataFlowEngineError(
                                            f"No available Serving configuration",
                                            context={"serving_id": serving_id}
                                        )
                                    first_serving_id = list(all_servings.keys())[1]
                                    serving_info = container.serving_registry._get(first_serving_id)
                                    logger.info(f"Using default serving: {first_serving_id}", serving_info)
                                else:
                                    raise DataFlowEngineError(
                                        f"Serving configuration not found",
                                        context={"serving_id": serving_id}
                                    )
                            else:
                                serving_info = container.serving_registry._get(serving_id)

                            dataflow_runtime["embedding_serving_map"][serving_id] = serving_info

                    elif param_name == "database_manager":
                        dm_val = param_value
                        if isinstance(dm_val, list) or dm_val is None:
                            cache_key = tuple(dm_val) if isinstance(dm_val, list) else None
                            if cache_key not in dataflow_runtime["db_manager_map"]:
                                pass
                                # dataflow_runtime["db_manager_map"][cache_key] = container.text2sql_database_registry.get_manager(dm_val)
                        else:
                            db_manager_id = dm_val
                            if db_manager_id not in dataflow_runtime["db_manager_map"]:
                                dataflow_runtime["db_manager_map"][db_manager_id] = container.text2sql_database_manager_registry._get(db_manager_id)
                        
                    
                except DataFlowEngineError:
                    raise
                except Exception as e:
                    raise DataFlowEngineError(
                        f"Failed to process parameter: {param_name}",
                        context={
                            "operator": op_name,
                            "operator_index": op_idx,
                            "param_name": param_name,
                            "param_value": str(param_value)[:100]  # 限制长度
                        },
                        original_error=e
                    )
        return dataflow_runtime
                            
    
    def run(self, pipeline_config: Dict[str, Any], task_id: str, execution_path: Optional[str] = None) -> Dict[str, Any]:
        """
        执行 Pipeline
        
        Args:
            pipeline_config: Pipeline 配置
            task_id: 任务 ID
            execution_path: 执行记录文件路径（可选，用于实时更新状态）
        
        Returns:
            Dict: 符合 PipelineExecutionResult 格式的执行结果
                - task_id: str
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
            # ts_msg = f"[{datetime.now().isoformat()}] {message}" # message already has timestamp mostly
            ts_msg = message
            logs.append(ts_msg)
            
            # 如果是具体的算子，记录到 operator_logs
            if op_name != "__pipeline__":
                operator_logs.setdefault(op_name, []).append(ts_msg)
        
        add_log("global", f"[{started_at}] Starting pipeline execution: {task_id}")
        logger.info(f"Starting pipeline execution: {task_id}")

        
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
                
                cache_path_output = os.path.join(settings.CACHE_DIR, f"{task_id}_output")
                
                # 确保 cache 目录存在
                os.makedirs(cache_path_output, exist_ok=True)
                logger.info(f"Cache directory: {cache_path_output}, exists: {os.path.exists(cache_path_output)}")
                
                storage = FileStorage(
                    first_entry_file_name=os.path.abspath(dataset['root']),
                    cache_path=cache_path_output,
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
                    "Failed to initialize Storage",
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
                                    serving_instance_map[serving_id] = self.init_serving_instance(serving_id)
                                param_value = serving_instance_map[serving_id]

                            elif param_name == "embedding_serving":
                                serving_id = param_value
                                logger.info(f"Operator {op_name}: initializing embedding serving {serving_id}")
                                add_log("init", f"[{datetime.now().isoformat()}]   - Initializing embedding serving: {serving_id}", op_key)
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
                        f"Failed to initialize Operator: {op_name}",
                        context={
                            "operator": op_name,
                            "operator_index": op_idx,
                            "init_params": {k: str(v)[:50] for k, v in init_params.items()} if 'init_params' in locals() else None
                        },
                        original_error=e
                    )
            
            # Step 3: 执行所有 Operators
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
                        "operator_logs": operator_logs # Sync logs to file
                    })
                    
                    api_pipeline_path = os.path.join(settings.DATAFLOW_CORE_DIR, "api_pipelines")
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
                    update_execution_status("running", {
                        "operators_detail": operators_detail,
                        "operator_logs": operator_logs
                    })

                    
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
            # Try to find the op_key if possible, or just log generally
            
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
            
dataflow_engine = DataFlowEngine()


