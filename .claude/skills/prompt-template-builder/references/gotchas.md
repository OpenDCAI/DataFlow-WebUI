# Gotchas (Prompt Template Builder)

统一结构：现象 / 根因 / 检测 / 修复 / 预防。

## G1: build_prompt 参数与算子调用不一致

- 现象: 运行时报 `TypeError`（参数个数或命名不匹配）。
- 根因: 未对齐 `OP_NAME` 实际调用 `prompt_template.build_prompt(...)` 的参数。
- 检测: 静态检查“参数名一致性”失败。
- 修复: 按算子调用点重写 `build_prompt` 签名。
- 预防: 先做接口对齐再写 prompt 文案。

## G2: 输出格式描述模糊

- 现象: 模型输出字段漂移，难以稳定解析。
- 根因: Prompt 只写“返回 JSON”，但没有 schema。
- 检测: 验收清单 `output_schema_explicit` 失败。
- 修复: 明确字段名、类型、取值约束与错误字段。
- 预防: 在 Stage 1 固定 `output_contract` 并在 Stage 2 对齐。

## G3: 模板中引用未声明变量

- 现象: prompt 字符串格式化时报 `NameError` 或内容为空。
- 根因: 使用了不在 `build_prompt` 参数中的变量。
- 检测: 静态检查 `no_undefined_template_vars` 失败。
- 修复: 将变量纳入函数参数或改成常量。
- 预防: 代码生成后逐项对照参数与模板变量。

## G4: 机械拆分多个 prompt 类

- 现象: 产物过度复杂，维护困难。
- 根因: 将可在单个模板内完成的任务拆成多个类。
- 检测: Stage 1 策略解释无法给出必要性。
- 修复: 合并为一个职责清晰的模板类。
- 预防: 仅在语义职责显著不同时才拆分。

## G5: 忽略用户约束优先级

- 现象: 代码可运行但不满足业务约束（语气、禁用词、返回长度等）。
- 根因: 约束未进入 Prompt 明确段落。
- 检测: 验收清单 `constraints_applied` 失败。
- 修复: 在 `# Task` 或 `# Output Format` 区域显式落约束。
- 预防: Requirement Mapping 中先列约束，再映射到代码。

## G6: `prompt_template` 类型与算子不匹配

- 现象: 代码看似完整，但运行时报类型/属性错误，或算子不识别模板。
- 根因: 未按 `OP_NAME` 真实签名选择模板类型（例如该用 `FormatStrPrompt` 却生成了 `DIYPromptABC`）。
- 检测: 静态检查 `prompt_template_type_aligned` 失败；集成片段与算子签名不一致。
- 修复: 以算子签名说明为准，重写模板类型与集成代码。
- 预防: 先确认 `OP_NAME` 的构造参数与 `prompt_template` 类型，再生成 Prompt 产物。
