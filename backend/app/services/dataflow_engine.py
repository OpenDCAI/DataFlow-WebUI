from dataflow.serving import APILLMServing_request
from dataflow.utils.storage import FileStorage
from dataflow.pipeline import PipelineABC
from dataflow.utils.registry import PROMPT_REGISTRY, OPERATOR_REGISTRY
from dataclasses import dataclass
from app.services.serving_registry import SERVING_CLS_REGISTRY
from app.core.container import container
from app.core.logger_setup import get_logger
from typing import Dict, Any, List
import os
import traceback
from datetime import datetime

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
        
    def init_serving_instance(self, serving_id: str) -> APILLMServing_request:
        """初始化 Serving 实例"""
        try:
            params_dict = {}
            serving_info = container.serving_registry._get(serving_id)
            
            if not serving_info:
                raise DataFlowEngineError(
                    f"Serving配置未找到",
                    context={"serving_id": serving_id}
                )
            
            ## This part of code is only for APILLMServing_request
            if serving_info['cls_name'] == 'APILLMServing_request':
                api_key_val = None
                key_name_var = f"DF_API_KEY_{serving_id}"
                
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
    
    def run(self, pipeline_config: Dict[str, Any], execution_id: str) -> Dict[str, Any]:
        """
        执行 Pipeline
        
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
        
        logs.append(f"[{started_at}] Starting pipeline execution: {execution_id}")
        logger.info(f"Starting pipeline execution: {execution_id}")
        
        try:
            # Step 1: 初始化 Storage
            logs.append(f"[{datetime.now().isoformat()}] Step 1: Initializing storage...")
            
            try:
                input_dataset_id = pipeline_config.get("input_dataset")
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
                
                storage = FileStorage(
                    first_entry_file_name=dataset["root"],
                    cache_path="./cache_local",
                    file_name_prefix="dataflow_cache_step",
                    cache_type="jsonl",
                )
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
            logs.append(f"[{datetime.now().isoformat()}] Step 2: Initializing operators...")
            
            serving_instance_map: Dict[str, APILLMServing_request] = {}
            run_op = []
            operators = pipeline_config.get("operators", [])
            
            logs.append(f"[{datetime.now().isoformat()}] Found {len(operators)} operators to initialize")
            logger.info(f"Initializing {len(operators)} operators...")
            
            for op_idx, op in enumerate(operators):
                op_name = op.get("name", f"Operator_{op_idx}")
                logs.append(f"[{datetime.now().isoformat()}] [{op_idx+1}/{len(operators)}] Initializing operator: {op_name}")
                
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
                                logs.append(f"[{datetime.now().isoformat()}]   - Initializing LLM serving: {serving_id}")
                                if serving_id not in serving_instance_map:
                                    serving_instance_map[serving_id] = self.init_serving_instance(serving_id)
                                param_value = serving_instance_map[serving_id]
                            
                            elif param_name == "prompt_template":
                                prompt_cls_name = extract_class_name(param_value)
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
            logs.append(f"[{datetime.now().isoformat()}] Step 3: Executing {len(run_op)} operators...")
            logger.info(f"Executing {len(run_op)} operators...")
            
            execution_results = []
            
            for op_idx, (operator, run_params, op_name) in enumerate(run_op):
                try:
                    run_params["storage"] = storage.step()
                    logs.append(f"[{datetime.now().isoformat()}] [{op_idx+1}/{len(run_op)}] Running operator: {op_name}")
                    logger.info(f"[{op_idx+1}/{len(run_op)}] Running {op_name}")
                    logger.debug(f"Run params: {list(run_params.keys())}")
                    
                    operator.run(**run_params)
                    
                    logs.append(f"[{datetime.now().isoformat()}] [{op_idx+1}/{len(run_op)}] {op_name} completed successfully")
                    logger.info(f"[{op_idx+1}/{len(run_op)}] {op_name} completed")
                    
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
            
            # 成功完成
            completed_at = datetime.now().isoformat()
            logs.append(f"[{completed_at}] Pipeline execution completed successfully")
            logger.info(f"Pipeline execution completed successfully: {execution_id}")
            
            output["operators_executed"] = len(run_op)
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
            logs.append(error_log)
            
            logger.error(f"Pipeline execution failed: {e.message}")
            logger.error(f"Context: {e.context}")
            if e.original_error:
                logger.error(f"Original error: {e.original_error}")
            
            # 返回失败结果
            output["error"] = e.message
            output["error_context"] = e.context
            output["original_error"] = str(e.original_error) if e.original_error else None
            
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
            
            return {
                "execution_id": execution_id,
                "status": "failed",
                "output": output,
                "logs": logs,
                "started_at": started_at,
                "completed_at": completed_at
            }
            
dataflow_engine = DataFlowEngine()
            
        
        
