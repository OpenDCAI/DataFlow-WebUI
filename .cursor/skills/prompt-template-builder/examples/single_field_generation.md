# Example: 单字段生成类 Prompt Template

## User Input
```text
Target: 生成电商商品卖点描述
OP_NAME: PromptedGenerator
Constraints: 语气专业、每条不超过80字
Expected Output: 文本字符串
Arguments: ["product_name", "category"]
Sample Cases:
- product_name=降噪耳机, category=电子产品
```

## AskUserQuestion Capture

### Round 1 (Structure)
- Task Mode: 新建 prompt_template（Recommended）
- Output constraint strength: 强约束
- Tone/Style: 专业简洁

### Round 2 (Implementation)
- prompt inputs: `product_name`, `category`
- Output shape: 单行文本
- Validation focus: 接口一致性优先

## Stage 1 (Decision JSON)
```json
{
  "op_name": "PromptedGenerator",
  "prompt_class": "N/A (PromptedGenerator uses system_prompt/user_prompt)",
  "arguments": ["product_name", "category"],
  "output_contract": "plain text <= 80 Chinese chars",
  "strategy": "system-user-prompt-composition",
  "reason": "PromptedGenerator is configured by system_prompt + user_prompt in operator signature; build deterministic prompt text without custom prompt_template class.",
  "static_checks": [
    "operator_interface_aligned",
    "prompt_template_type_aligned",
    "no_invented_params",
    "output_schema_explicit"
  ]
}
```

## Stage 2 (Core Result Snippet)

### Prompt Design Code
```python
system_prompt = (
    "你是电商文案助手。"
    "语气专业，最多80字，不使用夸张承诺。"
    "只返回一行中文文本，不要 JSON，不要额外解释。"
)
user_prompt = "请基于输入内容生成一句电商卖点描述："
```

### Integration Snippet
```python
self.generator = PromptedGenerator(
    llm_serving=self.llm_serving,
    system_prompt=system_prompt,
    user_prompt=user_prompt,
)
```

## Walkthrough
- Normal case: `降噪耳机/电子产品` -> 输出一条80字内卖点文案。
- Edge case: `product_name` 为空 -> 输出应提示信息不足，不生成虚假卖点。

## Static Acceptance Snapshot
- [x] input_completeness
- [x] operator_interface_aligned
- [x] prompt_template_type_aligned
- [x] no_invented_params
- [x] output_schema_explicit
- [x] walkthrough_consistent
