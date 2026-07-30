---
name: bench-answer-generator
description: >-
  BenchAnswerGenerator 算子的参考文档。涵盖构造参数、完整 run() 签名、当前源码中的真实
  生成逻辑，以及与统一 bench 评测 pipeline 的接入说明。

  适用场景：根据 benchmark 数据中的问题行生成模型答案，再将结果送入 UnifiedBenchDatasetEvaluator。
---

# BenchAnswerGenerator 算子参考

`BenchAnswerGenerator` 用于从 benchmark DataFrame 中批量生成模型答案，并与`UnifiedBenchDatasetEvaluator` 的接口保持对齐。

## 1. 导入方式

```python
from dataflow.operators.core_text import BenchAnswerGenerator
```

## 2. 构造函数

```python
BenchAnswerGenerator(
    eval_type="key2_qa",
    llm_serving=llm,
    prompt_template=FormatStrPrompt(f_str_template="Question: {question}\nAnswer:"),
    system_prompt="You are a helpful assistant specialized in generating answers to questions.",
    allow_overwrite=False,
    force_generate=False,
)
```

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `eval_type` | 否 | `"key2_qa"` | 评测类型 |
| `llm_serving` | 是 | `None` | 实现了 `generate_from_input(...)` 的 LLM 服务对象 |
| `prompt_template` | 否 | `FormatStrPrompt` | 用于构造 prompt 的对象。实际使用时应传 `FormatStrPrompt(...)` 实例、`None`，或 `DIYPromptABC` 子类实例 |
| `system_prompt` | 否 | `"You are a helpful assistant specialized in generating answers to questions."` | 在 serving 层支持时传入的 system prompt |
| `allow_overwrite` | 否 | `False` | 是否允许覆盖已存在的输出列 |
| `force_generate` | 否 | `False` | 是否对默认会跳过的部分类型强制生成 |

### 关于 `prompt_template` 的重要说明

虽然源码把默认值写成了 `FormatStrPrompt`，但这个默认值实际上是类对象而不是实例。

在正常使用中，更推荐显式传入 `FormatStrPrompt(...)` 实例，这样可以明确控制 prompt文本；`None` 也可以使用，此时算子会退回内部内置的 prompt 构造逻辑。

建议使用以下两种方式之一：

```python
from dataflow.prompts.core_text import FormatStrPrompt

prompt_template=FormatStrPrompt(
    f_str_template="Question: {question}\nAnswer:"
)
```

或：

```python
prompt_template=None
```

当 `prompt_template` 是 `FormatStrPrompt` 实例时，当前源码可能会向`build_prompt(...)` 传入这些字段：

- `eval_type`
- `question`
- `context`
- `choices`
- `choices_text`

对于 `key2_qa` 和 `key2_q_ma`，实际最常用且应保证存在的字段是 `question`。
对于 `key3_q_choices_a` 和 `key3_q_choices_as`，最常用的是 `question` 与 `choices`。
如果是选项题，建议优先在模板中使用 `{choices_text}`，而不是直接使用 `{choices}`，这样格式更稳定。

### 支持的 `eval_type`

| eval_type | 当前源码中的默认行为 |
|-----------|----------------------|
| `key1_text_score` | 跳过生成 |
| `key2_qa` | 生成 |
| `key2_q_ma` | 生成 |
| `key3_q_choices_a` | 默认跳过生成 |
| `key3_q_choices_as` | 生成 |
| `key3_q_a_rejected` | 跳过生成 |

如果设置 `force_generate=True`，当前实现会对除 `key1_text_score` 之外的类型执行生成。

## 3. run() 签名

```python
op.run(
    storage=self.storage.step(),
    input_text_key=None,
    input_question_key=None,
    input_target_key=None,
    input_targets_key=None,
    input_choices_key=None,
    input_label_key=None,
    input_labels_key=None,
    input_better_key=None,
    input_rejected_key=None,
    input_context_key=None,
    output_key="generated_ans",
)
# 返回值：[output_key] 或 []
```

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `storage` | 是 | None | 当前算子步骤对应的 storage 对象 |
| `input_text_key` | 否 | `None` | 为了和 evaluator 接口对齐而保留；当前 `run()` 实现中未使用 |
| `input_question_key` | 条件必填 | `None` | 只要当前会执行生成，就必须提供该列 |
| `input_target_key` | 否 | `None` | 为接口对齐保留；当前 `run()` 实现中未使用 |
| `input_targets_key` | 否 | `None` | 为接口对齐保留；当前 `run()` 实现中未使用 |
| `input_choices_key` | 条件必填 | `None` | 在 `key3_q_choices_a` 和 `key3_q_choices_as` 且实际生成时必填 |
| `input_label_key` | 否 | `None` | 为接口对齐保留；当前 `run()` 实现中未使用 |
| `input_labels_key` | 否 | `None` | 为接口对齐保留；当前 `run()` 实现中未使用 |
| `input_better_key` | 否 | `None` | 为接口对齐保留；当前 `run()` 实现中未使用 |
| `input_rejected_key` | 否 | `None` | 为接口对齐保留；当前 `run()` 实现中未使用 |
| `input_context_key` | 否 | `None` | 可选的上下文列名 |
| `output_key` | 否 | `"generated_ans"` | 回写到 DataFrame 的输出列名 |

## 4. 真实执行逻辑

当前实现的执行过程如下：

1. 从 `storage` 读取 DataFrame。
2. 调用 `_need_generation(eval_type)` 判断当前类型是否需要生成。
3. 如果不需要生成，则原样写回 DataFrame 并返回 `[]`。
4. 如果 `output_key` 已存在且 `allow_overwrite=False`，则原样写回 DataFrame 并返回 `[]`。
5. 只要当前需要生成，就必须检查 `input_question_key` 是否存在。
6. 对于 `key3_q_choices_a` 和 `key3_q_choices_as`，还会检查 `input_choices_key`。
7. 如果提供了 `input_context_key` 且列存在，则将其规范化为上下文字符串。
8. 对每一行优先调用 `prompt_template.build_prompt(...)` 构造 prompt；如果失败或不可用，则退回内部默认模板。
9. 调用 `llm_serving.generate_from_input(...)` 批量生成答案。
10. 将结果写入 `dataframe[output_key]`，通过 `storage.write(df)` 持久化，并返回 `[output_key]`。

## 5. 关键规则

1. 在当前源码中，`key3_q_choices_a` 默认不会生成，只有 `force_generate=True` 时才会生成。
2. 在当前源码中，`key1_text_score` 不会生成，即使设置 `force_generate=True` 也是如此。
3. 在当前实现里，真正必需的主输入列是 `input_question_key`。
4. `input_text_key`、`input_target_key`、`input_targets_key`、`input_label_key`、`input_labels_key`、`input_better_key`、`input_rejected_key` 这些参数虽然暴露在 `run()` 签名中，但当前实现并没有在内部读取它们。
5. 如果 `input_choices_key` 某一行为空或不是有效列表，当前实现会用 `[""]` 作为占位，而不是直接报错。
6. 返回值是列表：成功时通常为 `[output_key]`，跳过时为 `[]`。

## 6. 典型用法

```python
from dataflow.operators.core_text import BenchAnswerGenerator
from dataflow.prompts.core_text import FormatStrPrompt

prompt_template = FormatStrPrompt(
    f_str_template="Context: {context}\nQuestion: {question}\nAnswer:"
)

generator = BenchAnswerGenerator(
    eval_type="key2_qa",
    llm_serving=self.llm_serving,
    prompt_template=prompt_template,
    allow_overwrite=False,
)

generator.run(
    storage=self.storage.step(),
    input_question_key="question",
    input_context_key="context",
    output_key="generated_ans",
)
```
