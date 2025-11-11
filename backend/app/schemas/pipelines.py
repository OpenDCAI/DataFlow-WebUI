from enum import Enum
from typing import List, Union
from pydantic import BaseModel, Field
from typing_extensions import Annotated
import os
from app.core.config import settings
class Pipeline(str, Enum):
    undefined = "undefined"
    Text2SQL = "text2sql"
    Reasoning = "reasoning"
    CodeGeneration = "code_generation"
    Translation = "translation"
    # 可继续扩展


def generate_pipeline_enum(path: str):
    """根据文件夹自动生成 Enum"""

    items = [
        name for name in os.listdir(path)
        if os.path.isdir(os.path.join(path, name))
    ]
    if not items:
        raise ValueError(f"No pipeline found in {path}")
    return Enum("Pipeline", {name: name for name in items})

# Pipeline = generate_pipeline_enum(os.path.join(settings.DataFlow_CORE_DIR, "example_data"))

# print("Generated Pipeline Enum with items:", list(Pipeline))
# OneOrManyPipelines = Annotated[
#     Union[Pipeline, List[Pipeline]],
#     Field(description="选择一个或多个 pipeline")
# ]