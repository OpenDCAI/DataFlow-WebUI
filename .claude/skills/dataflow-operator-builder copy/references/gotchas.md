# Gotchas (Structured)

Each entry uses: Symptom / Root cause / Detection / Fix / Prevention.

ZH: 每条 gotcha 使用统一结构：现象 / 根因 / 检测 / 修复 / 预防。

## G1: Missing `@OPERATOR_REGISTRY.register()`

- Symptom / 现象:
  Operator class cannot be found in `OPERATOR_REGISTRY`.
- Root cause / 根因:
  Missing decorator or module not imported.
- Detection / 检测:
  Registry test fails (`class_name not in OPERATOR_REGISTRY`).
- Fix / 修复:
  Add decorator and ensure import path is reachable.
- Prevention / 预防:
  Keep registry test in generated suite and run `validation_level=basic|full`.

## G2: Wrong storage lifecycle (`storage.step()` omitted)

- Symptom / 现象:
  Operator reads empty data or output files are not created at expected step.
- Root cause / 根因:
  CLI/pipeline passes base storage instead of stepped storage.
- Detection / 检测:
  Smoke run does not produce `*_step1.*` output.
- Fix / 修复:
  Call operator with `storage=storage.step()`.
- Prevention / 预防:
  Keep CLI template and smoke test unchanged unless lifecycle is understood.

## G3: Input key mismatch

- Symptom / 现象:
  `KeyError` during run.
- Root cause / 根因:
  `input_key` not present in dataframe columns.
- Detection / 检测:
  Unit test missing-column case fails.
- Fix / 修复:
  Validate key early and include available columns in error message.
- Prevention / 预防:
  Confirm IO keys in interview Round 2 and keep defaults explicit in spec.

## G4: LLM response shape assumptions

- Symptom / 现象:
  Index errors, empty outputs, or invalid eval scores.
- Root cause / 根因:
  Assuming model output is always a non-empty list/string.
- Detection / 检测:
  Unit/smoke tests fail with dummy serving or malformed response.
- Fix / 修复:
  Normalize return values (`list/str/None`) and clamp eval scores.
- Prevention / 预防:
  Keep helper methods (`_generate_text`, `_refine_text`, `_score_with_llm`) defensive.

## G5: CLI/operator coupling

- Symptom / 现象:
  Operator becomes hard to reuse and test.
- Root cause / 根因:
  Prompting or argument parsing logic moved into operator class.
- Detection / 检测:
  Operator needs CLI args object directly or uses `input()` internally.
- Fix / 修复:
  Keep CLI-specific logic under `cli/` module only.
- Prevention / 预防:
  Follow `references/cli-shell-guidelines.md` structure.

## G6: Overwrite policy surprises

- Symptom / 现象:
  Existing files are accidentally replaced or unexpectedly skipped.
- Root cause / 根因:
  Spec overwrite strategy and CLI override not verified before generation.
- Detection / 检测:
  Generated output differs from expected plan.
- Fix / 修复:
  Always inspect dry-run plan and confirm selected overwrite strategy.
- Prevention / 预防:
  Keep guardrail step mandatory (`y/N` before write).

## G7: Validation too weak

- Symptom / 现象:
  Scaffold generated but fails at first execution.
- Root cause / 根因:
  Running without validation or using `none` for high-risk cases.
- Detection / 检测:
  Import/registry/smoke failures discovered late.
- Fix / 修复:
  Use `validation_level=full` by default.
- Prevention / 预防:
  Downgrade validation only for controlled rapid prototyping.
