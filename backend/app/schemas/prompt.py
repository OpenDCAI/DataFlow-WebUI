from pydantic import BaseModel, Field
from typing import Optional, List, Dict

class GetPromptSchema(BaseModel):
    #allowed_prompts: Optional[List[str]] = []
    allowed_prompts: Optional[Dict[str, str]] = Field(default_factory=dict)

class PromptSourceOut(BaseModel):
    name: str
    source: str

class OperatorPromptMapOut(BaseModel):
    operator_prompts: Dict[str, List[str]]

class PromptInfoOut(BaseModel):
    operator: List[str]
    class_str: str
    primary_type: str
    secondary_type: str

class PromptInfoMapOut(BaseModel):
    prompts: Dict[str, PromptInfoOut]