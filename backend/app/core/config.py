from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 基本
    ENV: str = "dev"
    DATA_REGISTRY: str = "data/data_registry.yaml" #
    TASK_REGISTRY: str = "data/task_registry.yaml"
    PIPELINE_REGISTRY: str = "data/pipeline_registry.yaml"
    SERVING_REGISTRY: str = "data/serving_registry.yaml"
    TEXT2SQL_DATABASE_REGISTRY: str = "data/text2sql_database_registry.yaml" # text2sql database config
    TEXT2SQL_DATABASE_MANAGER_REGISTRY: str = "data/text2sql_database_manager_registry.yaml" # text2sqldatabase manager config (class)
    DATAFLOW_CORE_DIR: str = "data/dataflow_core"
    OPS_JSON_PATH: str = "data/ops.json"  # op information cache
    SQLITE_DB_DIR: str = "data/text2sql_dbs" # where sqlite database files are stored

settings = Settings()
