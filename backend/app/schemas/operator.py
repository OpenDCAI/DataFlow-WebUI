from pydantic import BaseModel, Field
from typing import Optional, List, Dict

class OperatorSchema(BaseModel):
    name: str
    type: Dict[str, str]
    # allowed_prompts: List[str]
    allowed_prompts: Optional[List[str]] = []
    # init_parameters: Optional[Dict[str, str]] = {}
    # run_parameters: Optional[Dict[str, str]] = {}
    description: Optional[str] = None

