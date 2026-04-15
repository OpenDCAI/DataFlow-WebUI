---
name: dataflow-operator-builder
description: Build production-grade DataFlow operator scaffolds (generate/filter/refine/eval) for Codex and coding agents. Trigger when users ask to create/new/scaffold operators, add OPERATOR_REGISTRY registration, generate DataFlowStorage-based CLI wrappers, or generate operator unit/registry/smoke tests.
---

# DataFlow Operator Builder

Build production-ready DataFlow operator artifacts with either interactive interview mode or direct spec mode.

ZH: 通过“交互采访模式”或“直接 spec 模式”快速生成生产可用的 DataFlow Operator。

## Usage

```bash
/dataflow-operator-builder
/dataflow-operator-builder --spec path/to/spec.json --output-root path/to/repo
/dataflow-operator-builder --dry-run --spec path/to/spec.json --output-root path/to/repo
```

## Script Directory

Agent execution instructions:
1. Resolve this `SKILL.md` directory as `SKILL_DIR`.
2. Use `${SKILL_DIR}/scripts/build_operator_artifacts.py`.

ZH:
1. 将当前 `SKILL.md` 所在目录作为 `SKILL_DIR`。
2. 使用 `${SKILL_DIR}/scripts/build_operator_artifacts.py`。

| Script | Purpose |
|--------|---------|
| `scripts/build_operator_artifacts.py` | Generate operator + CLI + tests from spec |
| `scripts/example_spec.json` | Example input spec with defaults |

## Scope

This skill targets:
- DataFlow-style operator implementation (`DataFlowStorage` + dataframe flow)
- `@OPERATOR_REGISTRY.register()` registration
- Separate CLI wrapper under `cli/`
- Minimal but production-grade tests (`unit/registry/smoke`)

ZH:
- 面向 DataFlow 风格的 operator 实现（`DataFlowStorage` + dataframe 流程）
- 自动包含 `@OPERATOR_REGISTRY.register()` 注册
- CLI 与 operator 逻辑分离
- 生成最小但可用的测试骨架（`unit/registry/smoke`）

Default families:
- `generate`
- `filter`
- `refine`
- `eval`

## Two Working Modes

### Mode A: Interactive Interview Mode

Use **AskUserQuestion** in **batch mode** with exactly two rounds:
- Round 1: structure fields
- Round 2: implementation fields

Important:
- In each question block, include recommended option + short reason.
- Ask follow-up questions only when high-impact fields are missing or contradictory.
- Do not ask one-by-one when the same round can be asked in one batch.

ZH:
- 使用 AskUserQuestion 且每轮“批量提问”，固定两轮。
- 每个问题块给出“推荐选项 + 简短理由”。
- 仅在高影响字段缺失或冲突时追问。

Interview schema:
- `references/askuserquestion-rounds.md`

### Mode B: Direct Spec Mode

When user already provides `--spec`, skip interview and run directly.

ZH: 用户已提供 `--spec` 时，直接执行，不再采访。

## Required Workflow

```text
Operator Builder Progress:
- [ ] Step 1: Load references
- [ ] Step 2: Choose mode (Interactive or Spec)
- [ ] Step 3: Build/validate spec JSON
- [ ] Step 4: Dry-run file plan
- [ ] Step 5: Confirm overwrite policy (light guardrail)
- [ ] Step 6: Generate files
- [ ] Step 7: Run validation (none/basic/full)
- [ ] Step 8: Write runtime log events
- [ ] Step 9: Report generated artifacts + validation results
```

### Step 1: Load References

Read:
- `references/operator-contract.md`
- `references/registration-rules.md`
- `references/cli-shell-guidelines.md`
- `references/gotchas.md`
- `references/acceptance-checklist.md`

### Step 2: Interview or Direct Spec

- Interactive mode: follow `references/askuserquestion-rounds.md` strictly.
- Spec mode: parse user-provided spec directly.

### Step 3: Build Spec JSON

Use:
- `scripts/example_spec.json`

Required spec fields:
- `package_name`
- `operator_type`
- `operator_class_name`
- `operator_module_name`
- `input_key`
- `output_key`
- `uses_llm`

Optional spec fields (with defaults):
- `cli_module_name` (default: `<operator_module_name>_cli`)
- `test_file_prefix` (default: `<operator_module_name>`)
- `overwrite_strategy` (default: `ask-each`)
- `validation_level` (default: `full`)

### Step 4: Dry-Run

```bash
python "${SKILL_DIR}/scripts/build_operator_artifacts.py" \
  --spec <spec.json> \
  --output-root <repo-root> \
  --dry-run
```

### Step 5: Light Guardrail (Required)

Before writing files, show:
- full create/update file list
- existing files
- selected overwrite strategy

Then ask for explicit confirmation: `y/N`.

### Step 6: Generate

```bash
python "${SKILL_DIR}/scripts/build_operator_artifacts.py" \
  --spec <spec.json> \
  --output-root <repo-root>
```

Useful flags:
- `--overwrite {ask-each,overwrite-all,skip-existing}` (override spec)
- `--validation-level {none,basic,full}`
- `--log-dir <path>`
- `--no-log`

### Step 7: Validation

- `none`: skip validation
- `basic`: import + registry + test file existence
- `full`: `basic` + runtime smoke execution

### Step 8: Runtime Logs (Light Memory)

Default log root:
- `${CLAUDE_PLUGIN_DATA}/dataflow-operator-builder/` if env exists
- else `%USERPROFILE%/.codex_plugin_data/dataflow-operator-builder/`

JSONL events:
- `dry_run`
- `generate_start`
- `generate_done`
- `validate_done`
- `cancelled`
- `error`

### Step 9: Output Summary

Report:
- operator class
- generated/updated paths
- overwrite behavior
- validation level and pass/fail details
- suggested next test command(s)

## File Layout Produced

```text
<output-root>/
├── <package_name>/
│   ├── __init__.py
│   ├── cli/
│   │   └── <cli_module_name>.py
│   └── operators/
│       ├── __init__.py
│       └── <operator_type>/
│           ├── __init__.py
│           └── <operator_module_name>.py
└── test/
    ├── test_<prefix>_unit.py
    ├── test_<prefix>_registry.py
    └── test_<prefix>_smoke.py
```

## Notes

- Keep behavior-level customization after scaffold generation.
- Keep operator description contract bilingual (`get_desc(lang='zh'/'en')`).
- Runtime messages should remain clear English.

ZH:
- 建议先生成骨架，再做行为细化。
- `get_desc` 需保持中英文双语契约。
- 终端输出信息应以英文为主，清晰可读。
