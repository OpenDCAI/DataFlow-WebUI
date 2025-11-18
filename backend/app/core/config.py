from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 基本
    ENV: str = "dev"
    DATA_REGISTRY: str = "data/registry.yaml"
    TASK_REGISTRY: str = "data/task_registry.yaml"
    PIPELINE_REGISTRY: str = "data/pipeline_registry.json"
    DataFlow_CORE_DIR: str = "data/dataflow_core"

settings = Settings()
