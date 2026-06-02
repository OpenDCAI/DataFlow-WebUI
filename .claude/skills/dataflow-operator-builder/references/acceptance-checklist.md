# Acceptance Checklist (Runtime-Aligned)

Use this checklist to mirror script validation output.

ZH: 本清单与脚本运行时校验结果一一对应。

## Validation: `basic`

- [ ] Operator module imports successfully.
- [ ] Class exists in `OPERATOR_REGISTRY`.
- [ ] `OPERATOR_REGISTRY.get(class_name)` resolves to the generated class.
- [ ] Generated test files exist:
  - `test_<prefix>_unit.py`
  - `test_<prefix>_registry.py`
  - `test_<prefix>_smoke.py`

## Validation: `full`

- [ ] All `basic` checks passed.
- [ ] Runtime smoke executes with temporary `FileStorage` input.
- [ ] Smoke output artifact is created.
- [ ] First smoke output record contains `output_key`.

## Guardrail + Summary

- [ ] File plan shows CREATE/UPDATE status.
- [ ] Existing target files are listed before write.
- [ ] Effective overwrite strategy is printed.
- [ ] Explicit write confirmation (`y/N`) is required.
- [ ] Final summary includes written/skipped paths and validation result.

## Logging

- [ ] Usage log file is appended unless `--no-log`.
- [ ] Required event names are emitted when applicable:
  - `dry_run`
  - `generate_start`
  - `generate_done`
  - `validate_done`
  - `cancelled`
  - `error`
