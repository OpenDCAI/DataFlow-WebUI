# Example: 多字段评分 Prompt Template

## User Input
```text
Target: 基于 question + answer 对 QA 样本质量打分
OP_NAME: FormatStrPromptedGenerator
Constraints: 分数范围 1-5，只输出整数
Expected Output: integer string in [1, 5]
Arguments: ["question", "answer"]
Sample Cases:
- 高质量问答
- 答案与问题不相关
```

## AskUserQuestion Capture

### Round 1 (Structure)
- Task Mode: 新建 prompt_template（Recommended）
- Output constraint strength: 强约束
- Tone/Style: 严格审计型

### Round 2 (Implementation)
- template placeholders: `question`, `answer`
- Output shape: 单整数
- Validation focus: 字段一致性 + 边界样例

## Stage 1 (Decision JSON)
```json
{
  "op_name": "FormatStrPromptedGenerator",
  "prompt_class": "N/A (FormatStrPrompt object)",
  "arguments": ["question", "answer"],
  "output_contract": "single integer string from 1 to 5",
  "strategy": "multi-field-score-template",
  "reason": "FormatStrPromptedGenerator requires FormatStrPrompt(...); use named placeholders for multi-field scoring and keep deterministic score-only output.",
  "static_checks": [
    "operator_interface_aligned",
    "prompt_template_type_aligned",
    "no_invented_params",
    "output_schema_explicit"
  ]
}
```

## Stage 2 (Core Result Snippet)

### Prompt Template Code
```python
from dataflow.prompts.core_text import FormatStrPrompt

prompt_template = FormatStrPrompt(
    f_str_template="""
# Role
你是数据质量评估员。

# Task
根据问题与回答的一致性、完整性和可用性打分。

# Constraints
评分范围 1-5，5 为最高；禁止输出解释。

# Output Format (MANDATORY)
仅输出一个整数：1/2/3/4/5。

# Input
Question: {question}
Answer: {answer}
"""
)
```

### Integration Snippet
```python
self.scorer = FormatStrPromptedGenerator(
    llm_serving=self.llm_serving,
    system_prompt="You are a strict QA data evaluator.",
    prompt_template=prompt_template,
)
```

## Walkthrough
- Normal case: 逻辑一致且完整 -> 输出 `4` 或 `5`。
- Edge case: 答非所问 -> 输出 `1` 或 `2`。

## Static Acceptance Snapshot
- [x] input_completeness
- [x] operator_interface_aligned
- [x] prompt_template_type_aligned
- [x] no_invented_params
- [x] output_schema_explicit
- [x] walkthrough_consistent
