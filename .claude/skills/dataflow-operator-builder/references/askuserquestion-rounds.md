# AskUserQuestion Round Design

Use exactly two rounds. Ask each round in one batch.

ZH: 固定两轮，每轮一次性批量提问。

## Round 1 (Structure)

| Block | Prompt Goal | Options (Recommended first) | Maps to Spec Key(s) | Default |
|---|---|---|---|---|
| 1 | Operator family | `generate` (Recommended: most common), `filter`, `refine`, `eval` | `operator_type` | None (required) |
| 2 | Operator identity | class name + module file name | `operator_class_name`, `operator_module_name` | None (required) |
| 3 | Repository placement | package name + output root | `package_name` + CLI `--output-root` | None (required) |
| 4 | LLM dependency | `yes` (Recommended when generation/refine/eval), `no` | `uses_llm` | None (required) |
| 5 | CLI module | `<operator_module_name>_cli` (Recommended), custom name | `cli_module_name` | `<operator_module_name>_cli` |

ZH:
- 第一轮聚焦结构字段，不进入实现细节。
- 输出必须一一映射到 spec 字段，不允许“游离信息”。

## Round 2 (Implementation Details)

| Block | Prompt Goal | Options (Recommended first) | Maps to Spec Key(s) | Default |
|---|---|---|---|---|
| 1 | IO keys | explicit input/output column names | `input_key`, `output_key` | None (required) |
| 2 | Description style | `bilingual zh/en` (Recommended), `zh only`, `en only` | generation preference (non-spec, used for prompting only) | `bilingual zh/en` |
| 3 | Extra CLI args | `default-only` (Recommended), `add custom args` | custom extension notes (non-spec) | `default-only` |
| 4 | Test file prefix | from module name (Recommended), custom | `test_file_prefix` | `<operator_module_name>` |
| 5 | Overwrite strategy | `ask-each` (Recommended: safest), `overwrite-all`, `skip-existing` | `overwrite_strategy` | `ask-each` |
| 6 | Validation level | `full` (Recommended: highest confidence), `basic`, `none` | `validation_level` | `full` |

ZH:
- 第二轮聚焦实现字段与运行策略。
- 覆盖策略和验证级别必须进入 spec。

## Follow-up Rule (Important)

Ask follow-up questions only if high-impact fields are:
- missing (`operator_type`, class/module/package name, input/output key, uses_llm), or
- contradictory (e.g., invalid identifier, output key empty, incompatible naming).

Do not ask low-impact follow-up if defaults are available.

ZH:
- 仅在高影响字段缺失/冲突时追问。
- 能用默认值解决的低影响项不追问。

## AskUserQuestion Quality Rules

- Include recommended option + short reason in every block.
- Keep options mutually exclusive and meaningful.
- Avoid one-by-one questioning when batch is possible.
- Keep final parsed answers strictly mappable to spec fields.

ZH:
- 每个问题块必须有推荐项和简短理由。
- 选项要互斥且有意义。
- 能批量提问就不要单题轮询。
