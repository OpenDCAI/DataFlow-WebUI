# Acceptance Checklist (Static + Walkthrough)

## A. Input & Interview Completeness

- [ ] `Target` 与 `OP_NAME` 已确认。
- [ ] 两阶段 AskUserQuestion 已执行（或明确走 Direct Spec）。
- [ ] 高影响缺失/冲突项已追问并解决。

## B. Interface Safety

- [ ] `build_prompt` 参数与算子调用契约一致。
- [ ] `prompt_template` 类型与 `OP_NAME` 契约一致（如 `DIYPromptABC` / `FormatStrPrompt`）。
- [ ] 未虚构算子参数或字段。
- [ ] 模板变量全部已声明（无未定义引用）。

## C. Prompt Quality

- [ ] Prompt 包含角色、任务、边界条件。
- [ ] 输出格式可机器校验（字段名/类型明确）。
- [ ] 失败场景有明确处理约束（例如 `error_type`）。

## D. Output Contract

- [ ] Stage 1 决策 JSON 完整。
- [ ] Stage 2 五段产物完整。
- [ ] Stage 2 给出静态验收结果与剩余风险。

## E. Example Walkthrough

- [ ] 至少 1 条正常样例走查。
- [ ] 至少 1 条边界/失败样例走查。
- [ ] 示例行为与输出契约一致。

## Pass Rule

- A/B/C/D 全部通过才视为可交付。
- E 至少通过前两项（v1 可选第 3 项为“建议通过”）。
