# AskUserQuestion Round Design (Prompt Template Builder)

固定两轮批量提问：先结构、后细节。

## Round 1: Structure Fields

| Block | 目标 | 推荐选项（含理由） | 映射字段 |
|---|---|---|---|
| 1 | 任务类型 | 新建 prompt_template（Recommended，首版最稳）/ 改写已有 prompt / 多轮迭代优化 | `Task Mode` |
| 2 | 目标算子 | 指定单一 `OP_NAME`（Recommended，避免职责扩散） | `OP_NAME` |
| 3 | 输出约束强度 | 强约束 schema（Recommended，提升可解析性）/ 中约束 / 轻约束 | `Expected Output` |
| 4 | 风格与语气 | 专业简洁（Recommended）/ 教学解释型 / 严格审计型 | `Tone/Style` |
| 5 | 约束来源 | 业务规则优先（Recommended）/ 样例优先 / 参考案例优先 | `Constraints` |

## Round 2: Implementation Fields

| Block | 目标 | 推荐选项（含理由） | 映射字段 |
|---|---|---|---|
| 1 | `build_prompt` 入参 | 显式列全部参数（Recommended，避免变量漂移） | `Arguments` |
| 2 | 输出格式细节 | JSON + 明确字段类型（Recommended）/ 文本段落 / 列表结构 | `Expected Output` |
| 3 | 样例覆盖 | 1 正常 + 1 边界（Recommended）/ 仅正常 / 多边界集 | `Sample Cases` |
| 4 | 验收重点 | 接口一致性优先（Recommended）/ 文案质量优先 / 结构完整优先 | `Validation Focus` |

## Follow-up Trigger Rule

仅在以下情况追问：
- 缺少 `Target` 或 `OP_NAME`
- `Arguments` 与模板变量映射冲突
- 输出约束互相矛盾（例如要求 JSON 且禁止结构化字段）

能用默认值解决的低影响项，不追问。

## Quality Rules

- 每轮一次性批量提问，不逐题轮询。
- 每个问题块都给推荐项与理由。
- 回答结果必须能回填到 `references/input-schema.md` 字段。
