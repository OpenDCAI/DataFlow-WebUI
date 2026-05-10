# Output Contract (Two-Stage Required)

## Stage 1: Decision JSON (MANDATORY)

必须先输出决策 JSON，建议结构如下：

```json
{
  "op_name": "ReasoningQuestionFilter",
  "prompt_class": "FinanceQuestionFilterPrompt",
  "arguments": ["question"],
  "output_contract": "JSON: {judgement_test: bool, error_type: str|null}",
  "strategy": "reuse-operator-existing-pattern",
  "reason": "why this prompt design fits target/operator constraints",
  "static_checks": [
    "operator_interface_aligned",
    "prompt_template_type_aligned",
    "no_invented_params",
    "output_schema_explicit"
  ]
}
```

### Stage 1 Rules

- 结构必须可审计：明确类名、参数、输出契约、策略、理由。
- `static_checks` 必须是可执行校验项，不得写空泛描述。
- 若有推断字段（用户未提供），必须在 `reason` 中说明。

## Stage 2: Complete Deliverable (MANDATORY)

按以下 5 个部分输出：

1. **Requirement Mapping**
   - 输入字段映射、约束映射、推断项说明。
2. **Prompt Design Summary**
   - 提示词结构、边界策略、失败处理。
   - 说明 `prompt_template` 类型选择依据（并与 `OP_NAME` 签名对齐）。
3. **Prompt Template/Config Code**
   - 完整 Python 代码（类或配置对象），可直接保存使用。
4. **Operator Integration Snippet + Walkthrough**
   - 说明如何在算子 `init` 中绑定 `prompt_template`。
   - 给出 1-2 条样例输入/期望行为走查。
5. **Static Acceptance Result + Caveats**
   - 用 checklist 逐条标记通过/风险项。

## Failure Response Contract

若无法生成（例如 `OP_NAME` 无法解析或关键信息缺失），必须返回：
- 明确失败原因
- 缺失字段列表
- 最小补充信息清单（用户补齐后可继续）

禁止返回“信息不足，无法处理”这类无行动指引的空响应。
