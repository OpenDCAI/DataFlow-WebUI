from dataflow.serving import APILLMServing_request
from dataflow.utils.text2sql.database_manager import DatabaseManager
from dataflow.utils.storage import FileStorage
from dataflow.pipeline import PipelineABC
from dataflow.utils.registry import PROMPT_REGISTRY, OPERATOR_REGISTRY
from dataclasses import dataclass
from app.services.serving_registry import SERVING_CLS_REGISTRY
from app.core.container import container
from typing import Dict, Any
import os

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
        params_dict = {}
        serving_info = container.serving_registry._get(serving_id)
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
            print(params_dict)
            os.environ[key_name_var] = api_key_val
            serving_instance = SERVING_CLS_REGISTRY[serving_info['cls_name']](**params_dict)
        return serving_instance

    def init_database_manager(self, db_manager_id: str) -> DatabaseManager:
        db_manager_info = container.text2sql_database_manager_registry._get(db_manager_id)
        db_manager_instance = DatabaseManager(db_type=db_manager_info['db_type'], config=db_manager_info['config'])
        db_manager_instance.databases = {db_id: info for db_id, info in db_manager_instance.databases.items() if db_id in db_manager_info['selected_db_ids']}
        return db_manager_instance
    
    def run(self, pipeline_config, execution_id: str) -> str:
        serving_instance_map: Dict[str, APILLMServing_request] = {}
        db_manager_instance_map: Dict[str, DatabaseManager] = {}
        dataset = container.dataset_registry.get(pipeline_config["input_dataset"])
        storage = FileStorage(
            first_entry_file_name=dataset["root"],
            cache_path="./cache_local",
            file_name_prefix="dataflow_cache_step",
            cache_type="jsonl",
        )
        run_op = []
        for op in pipeline_config["operators"]:
            init_params = {}
            run_params = {}
            for param in op["params"]["init"]:
                if param["name"] == "llm_serving":
                    serving_id = param["value"]
                    print(serving_id)
                    if serving_id not in serving_instance_map:
                        serving_instance_map[serving_id] = self.init_serving_instance(serving_id)
                    serving_instance = serving_instance_map[serving_id]
                    param["value"] = serving_instance

                if param["name"] == "database_manager":
                    db_manager_id = param.get("value")
                    if db_manager_id not in db_manager_instance_map:
                        db_manager_instance_map[db_manager_id] = self.init_database_manager(db_manager_id)
                    database_manager_instance = db_manager_instance_map[db_manager_id]
                    param["value"] = database_manager_instance

                if param["name"] == "prompt_template":
                    # prompt_template is a string ( <class 'dataflow.prompts.GeneralQuestionFilterPrompt'> ), we need to convert it to a instance 
                    prompt_cls_name = extract_class_name(param["value"])
                    prompt_cls = PROMPT_REGISTRY.get(prompt_cls_name)
                    prompt_instance = prompt_cls()
                    param["value"] = prompt_instance
                init_params[param["name"]] = param["value"]
                
            for param in op["params"]["run"]:
                run_params[param["name"]] = param["value"]
                
            operator_cls_name = extract_class_name(op["name"])
            operator_cls = OPERATOR_REGISTRY.get(operator_cls_name)
            operator_instance = operator_cls(**init_params)
            run_op.append((operator_instance, run_params))
        
        # Real run!
        for operator, run_params in run_op:
            run_params["storage"] = storage.step()
            print(f"Running operator {operator.__class__.__name__} with params {run_params}")
            operator.run(**run_params)
            
dataflow_engine = DataFlowEngine()
            
        
        
