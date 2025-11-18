
from typing import Dict
from dataflow.utils.registry import OPERATOR_REGISTRY
from dataflow.utils.registry import PROMPT_REGISTRY
from app.schemas.prompt import GetPromptSchema, PromptSourceOut, OperatorPromptMapOut, PromptInfoOut, PromptInfoMapOut
from app.core.logger_setup import get_logger
import inspect
from inspect import isclass

logger = get_logger(__name__)


class PromptRegistry:
    """
    Backend wrapper for DataFlow PROMPT_REGISTRY + OPERATOR_REGISTRY
    """
    def __init__(self):
        # Prompt registry from dataflow
        self._prompt_registry = PROMPT_REGISTRY
        # Operator registry
        self._operator_registry = OPERATOR_REGISTRY

        # ensure all operators are loaded (prompt side is eager-loaded)
        self._operator_registry._get_all()

    def get_prompts(self, operator_name: str) -> GetPromptSchema:
        """
        获取某一个算子的所有 Allowed Prompts，并返回 {prompt_name: full_path} 的字典
        """
        op_map = self._operator_registry.get_obj_map()
        if operator_name not in op_map:
            return None

        operator_class = op_map[operator_name]

        allowed = getattr(operator_class, "ALLOWED_PROMPTS", None)
        if not allowed:
            return GetPromptSchema(allowed_prompts={})

        # 构造 name -> python_path 映射
        prompt_dict: Dict[str, str] = {}
        for prompt_cls in allowed:
            cls_name = prompt_cls.__name__
            cls_path = f"{prompt_cls.__module__}.{prompt_cls.__name__}"
            prompt_dict[cls_name] = cls_path

        return GetPromptSchema(allowed_prompts=prompt_dict)

    def get_prompt_source(self, prompt_name: str) -> PromptSourceOut | None:
        """
        输入 prompt 名，返回这个 prompt 类的源码字符串。
        例如：
        class ExpandScenarioPrompt(PromptABC):
            def build_prompt(...)
        """
        prompt_map = self._prompt_registry.get_obj_map()
        cls = prompt_map.get(prompt_name)

        if cls is None:
            return None

        try:
            source_code = inspect.getsource(cls)
        except OSError:
            source_code = "Source code not available for this class."

        return PromptSourceOut(
            name=prompt_name,
            source=source_code
        )

    def list_operator_prompts(self) -> OperatorPromptMapOut:
        operator_map = self._operator_registry.get_obj_map()
        result = {}

        for op_name, op_cls in operator_map.items():
            allowed = getattr(op_cls, "ALLOWED_PROMPTS", [])
            result[op_name] = [p.__name__ for p in allowed]

        return OperatorPromptMapOut(operator_prompts=result)

    def list_prompt_info(self) -> PromptInfoMapOut:

        prompt_map = self._prompt_registry.get_obj_map()
        operator_map = self._operator_registry.get_obj_map()

        # ---- 第一部分：构建 Prompt → Operators 列表 ----
        prompt_to_ops: Dict[str, List[str]] = {}

        for op_name, op_cls in operator_map.items():
            allowed = getattr(op_cls, "ALLOWED_PROMPTS", [])
            for p_cls in allowed:
                p_name = p_cls.__name__
                prompt_to_ops.setdefault(p_name, []).append(op_name)

        # ---- 第二部分：获取 Prompt 的分类信息 ----
        prompt_types = self._prompt_registry.get_type_of_objects()

        # ---- 第三部分：构造最终结构 ----
        result: Dict[str, PromptInfoOut] = {}

        for p_name, p_cls in prompt_map.items():
            if not isclass(p_cls):
                continue

            # operator list
            ops = prompt_to_ops.get(p_name, [])

            # class path string
            class_str = f"{p_cls.__module__}.{p_cls.__name__}"

            # categories
            type_path = prompt_types.get(p_name, [])
            primary_type = type_path[0] if len(type_path) > 0 else "Unknown"
            secondary_type = type_path[1] if len(type_path) > 1 else "Unknown"

            result[p_name] = PromptInfoOut(
                operator=ops,
                class_str=class_str,
                primary_type=primary_type,
                secondary_type=secondary_type
            )

        return PromptInfoMapOut(prompts=result)

# 全局单例
_PROMPT_REGISTRY = PromptRegistry()
