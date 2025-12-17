from pydantic_settings import BaseSettings

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
    DATA_REGISTRY: str = "data/data_registry.yaml" #
    TASK_REGISTRY: str = "data/task_registry.yaml"
    PIPELINE_REGISTRY: str = "data/pipeline_registry.json"
    SERVING_REGISTRY: str = "data/serving_registry.yaml"
    DATAFLOW_CORE_DIR: str = "data/dataflow_core"
    OPS_JSON_PATH: str = "data/ops.json"  # op information cache
    PIPELINE_EXECUTION_PATH: str = "data/pipeline_execution.json"
    DEFAULT_SERVING_FILLING: bool = False

settings = Settings()
