from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 基本
    ENV: str = "dev"
    DATA_REGISTRY: str = "data/data_registry.yaml" #
    TASK_REGISTRY: str = "data/task_registry.yaml"
    PIPELINE_REGISTRY: str = "data/pipeline_registry.yaml"
    SERVING_REGISTRY: str = "data/serving_registry.yaml"
    DATAFLOW_CORE_DIR: str = "data/dataflow_core"
    OPS_JSON_PATH: str = "data/ops.json"  # op information cache

settings = Settings()
