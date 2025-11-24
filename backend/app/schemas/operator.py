from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

# 这个模型与 service 层的 get_op_list() 方法的返回值匹配

class OperatorSchema(BaseModel):
    name: str
    type: Dict[str, str]
    allowed_prompts: Optional[List[str]] = []
    description: Optional[str] = None


# 下面的模型严格定义了 service 层的 _gather_single_operator() 
# 所创建的数据结构，也就是 ops.json 的内容。

class OperatorParameterSchema(BaseModel):
    """
    定义一个算子（在 __init__ 或 run 中）的单个参数
    (对应 _param_to_dict 的输出)
    """
    name: str
    default: Any  # 默认值可以是任何类型，所以用 Any
    kind: str     # 例如 "POSITIONAL_OR_KEYWORD"


class ParameterGroupsSchema(BaseModel):
    """
    定义一个算子的 'init' 和 'run' 参数组
    """
    init: List[OperatorParameterSchema]
    run: List[OperatorParameterSchema]


class OperatorDetailSchema(BaseModel):
    """
    定义单个算子的 *详细* 信息
    (对应 _gather_single_operator 的输出)
    """
    node: int
    name: str
    # 公共字段：与 OperatorSchema 保持结构一致
    type: Dict[str, str]
    allowed_prompts: Optional[List[str]] = []
    description: str
    parameter: ParameterGroupsSchema
    required: str
    depends_on: List[Any] # 或者 List[str]
    mode: str


# --- 3. 定义 GET /details 接口的最终响应数据类型 ---

# 这不是一个 BaseModel，而是一个类型别名 (Type Alias)
# 它表示响应数据是一个字典，Key 是类别名称 (str)，Value 是详细算子列表
OperatorDetailsResponseSchema = Dict[str, List[OperatorDetailSchema]]