---
name: prompt-template-builder
description: Build reusable DataFlow prompt_template classes for existing operators with two-round AskUserQuestion intake, two-stage auditable outputs, and static acceptance checks. Trigger when users ask to generate/rewrite/optimize prompt_template or reuse operator logic with new prompt requirements.
version: 1.0.0
---

# Prompt Template Builder

生成可复用、可审计的 DataFlow `prompt_template` 初版产物，聚焦“算子复用 + 提示词定制 + 静态验收”。

## Goal

当用户给出 `Target` 与 `OP_NAME` 时，本 skill 必须：
1. 对齐目标算子的真实接口与参数要求。
2. 生成符合规范的 `prompt_template` 类代码。
3. 输出可审计的两阶段结果（决策 JSON + 完整产物）。
4. 使用静态验收清单完成质量门控（不执行子进程自动测试）。

## Usage

```bash
/prompt-template-builder
/prompt-template-builder --spec path/to/prompt_spec.json
```

## Scope

### In Scope

- 针对已有算子的 prompt_template 新建或改写。
- 通过 AskUserQuestion 两轮结构化采集需求。
- 生成标准化 prompt 类、集成示例、静态验收结果。
- 接收用户反馈并进行定向改写（`revise_with_feedback` 风格）。

### Out of Scope (v1)

- 自动子进程执行测试脚本。
- 自动运行 Gradio UI 或流水线脚本。
- 自动提交代码或发布。

## Input Contract (MANDATORY)

按结构化字段接收输入：

```text
Target: [业务目标/场景]
OP_NAME: [目标算子类名]
Constraints: [可选，边界/禁用项/风格约束]
Expected Output: [可选，输出格式约束]
Arguments: [可选，prompt参数列表]
Sample Cases: [可选，1-3条输入/期望行为]
```

详细字段定义见：
- `references/input-schema.md`

## Working Modes

### Mode A: AskUserQuestion Interview (default)

固定两阶段批量提问：
- Round 1: 结构层（目标、算子、输出契约、约束）
- Round 2: 实现层（参数签名、边界样例、验收偏好）

规则：
- 每个问题块提供推荐选项 + 简短理由。
- 只在高影响缺失/冲突时追问。
- 能映射到结构化字段就不提“游离问题”。

详见：
- `references/askuserquestion-rounds.md`

### Mode B: Direct Spec

若用户已提供完整 spec，跳过采访，直接进入生成与验收。

## Required Workflow

```text
Prompt Template Builder Progress:
- [ ] Step 1: Load references and parse user inputs
- [ ] Step 2: Choose mode (Interview or Spec)
- [ ] Step 3: Resolve operator contract (OP_NAME + prompt接口)
- [ ] Step 4: Build prompt template/config draft from contract
- [ ] Step 5: Build Stage 1 decision JSON
- [ ] Step 6: Build Stage 2 complete deliverable
- [ ] Step 7: Run static acceptance checklist
- [ ] Step 8: If feedback arrives, perform targeted revise and re-check
```

## Mandatory Rules

1. **Operator Interface Alignment**
   - 不得虚构 `OP_NAME` 的构造参数或 `run` 参数。
   - `prompt_template` 的调用方式必须与算子约定一致（如参数名/含义/类型）。
   - 当不同文档冲突时，以“目标算子签名说明”作为单一真源。

2. **Prompt Class Contract**
   - 若目标算子要求 `DIYPromptABC` 风格模板，则生成类应继承 `DIYPromptABC`。
   - 若目标算子要求其他模板类型（例如 `FormatStrPrompt`），必须按该类型生成并在 Stage 2 标注依据。
   - 保留 `__all__` 导出。
   - DIY 类名使用 `PascalCase + Prompt`。
   - DIY 模式下 `build_prompt` 必须返回 `str`。

3. **Output Determinism**
   - 若用户指定输出格式，Prompt 中必须给出明确强约束（字段名、类型、取值范围）。
   - 禁止仅描述“尽量输出 JSON”而不定义 schema。

4. **Field/Argument Safety**
   - `build_prompt` 中引用的变量必须来自显式参数或常量。
   - 不允许在模板中引用未声明变量。

5. **Two-Stage Output (Required)**
   - 必须先输出 Stage 1 决策 JSON。
   - 再输出 Stage 2 完整产物。

6. **Validation Gate**
   - Stage 2 必须包含静态验收结果，引用 `references/acceptance-checklist.md`。

## Output Contract (MANDATORY)

详见：
- `references/output-contract.md`
- `templates/decision_json_template.md`
- `templates/final_response_template.md`

## Progressive Disclosure Assets

- `references/input-schema.md`: 输入字段、默认值、归一化规则
- `references/output-contract.md`: 两阶段输出规范与失败态
- `references/gotchas.md`: 常见失败模式
- `references/acceptance-checklist.md`: 静态验收门槛
- `references/askuserquestion-rounds.md`: 两轮采访模板
- `templates/prompt_class_template.py.tmpl`: prompt类模板
- `examples/`: 典型场景走查

## Notes

- v1 使用“静态验收 + 示例走查”闭环；后续版本可扩展为自动子进程测试。
- 若用户反馈不满意，执行定向改写并重复 Stage 1/Stage 2 + 静态验收。
