"""
DataFlow Prompt 骨架模板
使用方式：复制此文件，替换所有 <PLACEHOLDER> 为实际内容

说明：
  - 标准 Prompt：继承 PromptABC（受白名单限制）
  - DIY Prompt：继承 DIYPromptABC（绕过白名单，更灵活）
  - 必须加 @PROMPT_REGISTRY.register() 装饰器
  - 实现 build_prompt() 方法
  - 若算子需限制 Prompt 类型：在算子类上用 @prompt_restrict(MyPrompt)
    注意：@prompt_restrict 必须紧贴类定义（参见 known_issues.md Issue #007）
"""

from dataflow.prompts.base import DIYPromptABC, PROMPT_REGISTRY
# 标准 Prompt（受白名单限制）：
# from dataflow.prompts.base import PromptABC, PROMPT_REGISTRY


# ─── 示例 1：DIY Prompt（推荐用于大多数自定义场景）───────────────────────────

@PROMPT_REGISTRY.register()
class <PromptClassName>(DIYPromptABC):
    """
    <Prompt 功能一句话描述>

    用途：配合 <OperatorClassName> 使用
    """

    def build_prompt(
        self,
        # ── 按算子调用时传入的参数来定义签名 ──────────────────────────
        text: str,
        # extra_param: str = "",
    ) -> str:
        """
        构建发送给 LLM 的完整 Prompt。

        Args:
            text: 输入文本
            ...（其他参数）

        Returns:
            str: 完整的 Prompt 字符串
        """
        # ── System Prompt 通常在算子 __init__ 中设置 ──────────────────
        # 这里返回 user message 部分
        return f"""请对以下内容进行处理：

{text}

请按照以下格式返回结果：
<result>
你的输出
</result>"""


# ─── 示例 2：标准 Prompt（继承 PromptABC）────────────────────────────────────
#
# @PROMPT_REGISTRY.register()
# class <StandardPromptClassName>(PromptABC):
#
#     def build_prompt(self, text: str) -> str:
#         return f"请处理：{text}"
#
# ─────────────────────────────────────────────────────────────────────────────


# ─── 示例 3：带多个参数的 Prompt ─────────────────────────────────────────────
#
# @PROMPT_REGISTRY.register()
# class <MultiFieldPromptClassName>(DIYPromptABC):
#
#     def build_prompt(
#         self,
#         instruction: str,
#         input_text: str = "",
#         output: str = "",
#     ) -> str:
#         parts = [f"指令：{instruction}"]
#         if input_text.strip():
#             parts.append(f"输入：{input_text}")
#         if output.strip():
#             parts.append(f"参考答案：{output}")
#         return "\n".join(parts)
#
# ─────────────────────────────────────────────────────────────────────────────


# ─── 在算子中限制 Prompt 类型的用法示例 ──────────────────────────────────────
#
# from dataflow.operators.base import OperatorABC, prompt_restrict
# from dataflow.utils.registry import OPERATOR_REGISTRY
#
# @OPERATOR_REGISTRY.register()
# class <OperatorClassName>(OperatorABC):  # ← @prompt_restrict 必须紧贴此行
#     ...
#
# ⚠️ 注意：@prompt_restrict 的正确叠加位置，请参考 known_issues.md Issue #007
# ─────────────────────────────────────────────────────────────────────────────
