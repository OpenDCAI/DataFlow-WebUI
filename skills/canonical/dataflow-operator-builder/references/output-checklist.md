# Output Checklist (Manual Quick View)

This file is a compact manual checklist. For runtime-aligned criteria, prefer `references/acceptance-checklist.md`.

ZH: 本文件是人工快速核对清单；与脚本校验严格对应的标准请优先使用 `references/acceptance-checklist.md`。

- [ ] Operator class generated in correct family directory.
- [ ] `@OPERATOR_REGISTRY.register()` exists.
- [ ] `run(storage: DataFlowStorage, ...)` reads/writes dataframe.
- [ ] `get_desc(lang)` supports both `zh` and `en`.
- [ ] CLI module generated separately under `cli/`.
- [ ] Unit, registry, smoke tests are generated.
- [ ] File plan + overwrite strategy shown before write.
- [ ] Validation output (`basic` or `full`) is reported.
