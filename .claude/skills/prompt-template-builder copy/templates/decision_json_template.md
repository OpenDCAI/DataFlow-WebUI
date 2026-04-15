# Stage 1 Decision JSON Template

```json
{
  "op_name": "{{OP_NAME}}",
  "prompt_class": "{{PROMPT_CLASS_NAME}}",
  "arguments": ["{{ARG_1}}", "{{ARG_2}}"],
  "output_contract": "{{OUTPUT_CONTRACT}}",
  "strategy": "{{STRATEGY}}",
  "reason": "{{WHY_THIS_DESIGN}}",
  "static_checks": [
    "operator_interface_aligned",
    "prompt_template_type_aligned",
    "no_invented_params",
    "no_undefined_template_vars",
    "output_schema_explicit"
  ]
}
```

## Fill Rules

- `arguments` 必须与 `build_prompt` 实际参数完全一致。
- `prompt_template` 类型必须与 `OP_NAME` 真实签名一致。
- `output_contract` 必须可机器校验，不得使用模糊描述。
- `reason` 需覆盖“算子复用依据 + 约束映射 + 风险处理”。
