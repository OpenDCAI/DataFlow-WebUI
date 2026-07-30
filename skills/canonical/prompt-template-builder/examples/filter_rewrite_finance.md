# Example: 复用过滤算子改写金融场景 Prompt

## User Input
```text
Target: 将通用推理题过滤器改写为金融问题过滤器
OP_NAME: ReasoningQuestionFilter
Constraints: 输出必须是 JSON，字段固定 judgement_test/error_type
Expected Output: {"judgement_test": bool, "error_type": string|null}
Arguments: ["question"]
Sample Cases:
- 输入为单个金融问题，语义完整
- 输入包含“翻译/改写”等额外指令
```

## AskUserQuestion Capture

### Round 1 (Structure)
- Task Mode: 改写已有 prompt（Recommended）
- Output constraint strength: 强约束 schema
- Constraint source: 业务规则优先

### Round 2 (Implementation)
- build_prompt args: `question`
- Output shape: JSON 固定字段
- Validation focus: 输出契约 + 接口一致性

## Stage 1 (Decision JSON)
```json
{
  "op_name": "ReasoningQuestionFilter",
  "prompt_class": "FinanceQuestionFilterPrompt",
  "arguments": ["question"],
  "output_contract": "JSON: {judgement_test: bool, error_type: str|null}",
  "strategy": "reuse-existing-filter-pattern",
  "reason": "Reuse operator contract in a DIYPromptABC-compatible filter and enforce deterministic JSON output for downstream filtering.",
  "static_checks": [
    "operator_interface_aligned",
    "prompt_template_type_aligned",
    "no_invented_params",
    "no_undefined_template_vars",
    "output_schema_explicit"
  ]
}
```

## Stage 2 (Core Result Snippet)

### Prompt Class Code
```python
__all__ = ['FinanceQuestionFilterPrompt']

from dataflow.core.prompt import DIYPromptABC


class FinanceQuestionFilterPrompt(DIYPromptABC):
    def __init__(self):
        pass

    def build_prompt(self, question: str) -> str:
        return f"""
# Role
你是金融问题审核助手。

# Task
判断输入是否是单个、可求解、前提充分的金融问题。

# Constraints
如果包含多任务指令（如翻译、改写、给答案），直接判定失败。

# Output Format (MANDATORY)
返回严格 JSON:
{{
  "judgement_test": true/false,
  "error_type": "<错误描述或null>"
}}

# Input
{question}
"""
```

### Integration Snippet
```python
self.reasoning_question_filter = ReasoningQuestionFilter(
    system_prompt="You are a helpful assistant.",
    llm_serving=self.llm_serving,
    prompt_template=FinanceQuestionFilterPrompt(),
)
```

## Walkthrough
- Normal case: 金融单问题 -> `judgement_test=true`。
- Edge case: 非问题或多任务请求 -> `judgement_test=false` 且 `error_type` 非空。

## Static Acceptance Snapshot
- [x] input_completeness
- [x] operator_interface_aligned
- [x] prompt_template_type_aligned
- [x] no_invented_params
- [x] no_undefined_template_vars
- [x] output_schema_explicit
