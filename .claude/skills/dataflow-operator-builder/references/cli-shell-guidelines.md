# CLI Shell Guidelines

## Why Separate CLI from Operator

Operators should stay composable and pipeline-friendly.
CLI wrappers should handle:
- argument parsing
- runtime parameter collection
- optional LLM serving initialization
- invoking operator with `DataFlowStorage`

ZH: operator 保持可组合、可复用；CLI 负责参数收集和运行入口。

## CLI Structure

Recommended order:
1. Parse CLI args.
2. Build storage (`FileStorage`).
3. Optionally build LLM serving backend.
4. Create operator instance.
5. Call `operator.run(storage=storage.step(), ...)`.
6. Print result key and basic completion info.

ZH: 推荐顺序为“解析参数 -> 构建存储 -> 可选 LLM -> 实例化 operator -> 执行 run -> 输出结果”。

## Language Style

- Keep CLI help text and runtime messages in clear English.
- Keep operator `get_desc` bilingual (`zh` and `en`) to satisfy DataFlow contract.

ZH:
- CLI 帮助和终端提示优先英文。
- operator 描述保持中英双语契约。

## Human-in-the-Loop

CLI may include confirmation prompts, but avoid heavy prompts inside operator core.

ZH: 人机交互提示放在 CLI 层，不放在 operator 核心逻辑中。
