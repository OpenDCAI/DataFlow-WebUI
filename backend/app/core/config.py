import os
from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    # 基本
    ENV: str = "dev"
    CORS_ORIGINS:list[str] = [
        # "http://127.0.0.1:60081",
        # "http://localhost:60081",
        # "http://127.0.0.1:60082",
        # "http://localhost:60082",
        # "http://localhost",
        # "http://127.0.0.1",
        # # "*"
    ]
    
    # 获取项目根目录
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    DATA_REGISTRY: str = os.path.join(BASE_DIR, "data", "data_registry.yaml") #
    TASK_REGISTRY: str = os.path.join(BASE_DIR, "data", "task_registry.json")
    PIPELINE_REGISTRY: str = os.path.join(BASE_DIR, "data", "pipeline_registry.json")
    SERVING_REGISTRY: str = os.path.join(BASE_DIR, "data", "serving_registry.yaml")
    TEXT2SQL_DATABASE_REGISTRY: str = os.path.join(BASE_DIR, "data", "text2sql_database_registry.yaml") # text2sql database config
    TEXT2SQL_DATABASE_MANAGER_REGISTRY: str = os.path.join(BASE_DIR, "data", "text2sql_database_manager_registry.yaml") # text2sqldatabase manager config (class)
    DATAFLOW_CORE_DIR: str = os.path.join(BASE_DIR, "data", "dataflow_core")
    OPS_JSON_PATH: str = os.path.join(BASE_DIR, "data", "ops.json")  # op information cache
    PREFERENCES_PATH: str = os.path.join(BASE_DIR, "data", "user_preferences.json") # preference information cache
    SQLITE_DB_DIR: str = os.path.join(BASE_DIR, "data", "text2sql_dbs") # where sqlite database files are stored
    CACHE_DIR: str = os.path.join(BASE_DIR, "cache_local") # cache directory for pipeline execution
    DEFAULT_SERVING_FILLING: bool = True # whether to fill default values for missing fields in serving

    # white list of preset pipelines that can be shown in the frontend pipeline template list
    _PRESET_PIPELINE_NAME_WHITELIST = {
        "Agentic Rag Pipeline",
        "Chemistry Smiles",
        "Code Code To Sft Data Pipeline",
        "Code Gen Dataset Pipeline",
        "Func Call Synthesis",
        "Reasoning General Pipeline",
        "Reasoning Math Pipeline",
        "Reasoning Pretrain Pipeline",
        "Text Conversation Synthesis Pipeline",
        "Text Sft Synthesis Pipeline",
        "Text2Qa Pipeline",
        "Text2Sql Pipeline Refine",
        "Text2Sql Pipeline Gen",
        "Double Column Input"
    }

settings = Settings()
