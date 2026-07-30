---
name: bench-answer-generator
description: >-
  Reference documentation for the BenchAnswerGenerator operator. Covers the
  constructor, full run() signature, actual generation behavior, and integration
  notes for unified bench evaluation pipelines.

  Use when: generating model answers from benchmark question rows before passing the dataframe into UnifiedBenchDatasetEvaluator.
---

# BenchAnswerGenerator Operator Reference

`BenchAnswerGenerator` generates model answers from a benchmark dataframe and is designed to align with `UnifiedBenchDatasetEvaluator`.

## 1. Import

```python
from dataflow.operators.core_text import BenchAnswerGenerator
```

## 2. Constructor

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

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `eval_type` | No | `"key2_qa"` | Evaluation type |
| `llm_serving` | Yes | `None` | LLM service object implementing `generate_from_input(...)` |
| `prompt_template` | No | `FormatStrPrompt` | Prompt object used to build prompts. In practice, pass a `FormatStrPrompt(...)` instance, `None`, or a `DIYPromptABC` subclass instance |
| `system_prompt` | No | `"You are a helpful assistant specialized in generating answers to questions."` | System prompt forwarded to the serving layer when supported |
| `allow_overwrite` | No | `False` | Whether to overwrite an existing output column |
| `force_generate` | No | `False` | Whether to force generation for some types that are skipped by default |

### Important `prompt_template` Note

Although the source code sets the default value to `FormatStrPrompt`, that
default is the class object itself, not an instance.

In normal usage, you usually want to pass a `FormatStrPrompt(...)` instance so
you can explicitly control the prompt text. `None` is also supported and makes
the operator fall back to its built-in prompt builder.

Use one of these patterns instead:

```python
from dataflow.prompts.core_text import FormatStrPrompt

prompt_template=FormatStrPrompt(
    f_str_template="Question: {question}\nAnswer:"
)
```

or

```python
prompt_template=None
```

When `prompt_template` is a `FormatStrPrompt` instance, the current source may
pass these fields into `build_prompt(...)`:

- `eval_type`
- `question`
- `context`
- `choices`
- `choices_text`

For `key2_qa` and `key2_q_ma`, the practical required field is `question`.
For `key3_q_choices_a` and `key3_q_choices_as`, the practical required fields
are `question` and `choices`. If you want cleaner formatting for choice tasks,
prefer `{choices_text}` over `{choices}`.

### Supported `eval_type` Values

| eval_type | Default behavior in current source |
|-----------|------------------------------------|
| `key1_text_score` | Skips generation |
| `key2_qa` | Generates |
| `key2_q_ma` | Generates |
| `key3_q_choices_a` | Skips generation by default |
| `key3_q_choices_as` | Generates |
| `key3_q_a_rejected` | Skips generation |

If `force_generate=True`, the current implementation generates for all types
except `key1_text_score`.

## 3. run() Signature

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
# returns: [output_key] or []
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `storage` | Yes | None | Current operator-step storage object |
| `input_text_key` | No | `None` | Declared for evaluator API alignment; not used in current `run()` implementation |
| `input_question_key` | Conditionally required | `None` | Required whenever generation is actually performed |
| `input_target_key` | No | `None` | Declared for API alignment; not used in current `run()` implementation |
| `input_targets_key` | No | `None` | Declared for API alignment; not used in current `run()` implementation |
| `input_choices_key` | Conditionally required | `None` | Required for `key3_q_choices_a` and `key3_q_choices_as` when generation is performed |
| `input_label_key` | No | `None` | Declared for API alignment; not used in current `run()` implementation |
| `input_labels_key` | No | `None` | Declared for API alignment; not used in current `run()` implementation |
| `input_better_key` | No | `None` | Declared for API alignment; not used in current `run()` implementation |
| `input_rejected_key` | No | `None` | Declared for API alignment; not used in current `run()` implementation |
| `input_context_key` | No | `None` | Optional context column name |
| `output_key` | No | `"generated_ans"` | Output column written back into the dataframe |

## 4. Actual Execution Logic

The current implementation behaves as follows:

1. Read the dataframe from `storage`.
2. Decide whether generation is needed by calling `_need_generation(eval_type)`.
3. If generation is not needed, write the dataframe back unchanged and return `[]`.
4. If `output_key` already exists and `allow_overwrite=False`, write the dataframe back unchanged and return `[]`.
5. Require `input_question_key` to exist whenever generation is performed.
6. For `key3_q_choices_a` and `key3_q_choices_as`, also require `input_choices_key`.
7. If `input_context_key` is provided and exists, normalize it into a prompt context string.
8. Build one prompt per row using `prompt_template.build_prompt(...)` when available; otherwise fall back to an internal prompt template.
9. Call `llm_serving.generate_from_input(...)`.
10. Write the generated answers into `dataframe[output_key]`, persist via `storage.write(df)`, and return `[output_key]`.

## 5. Important Rules

1. In the current source, `key3_q_choices_a` does not generate by default. It is skipped unless `force_generate=True`.
2. In the current source, `key1_text_score` never generates, even if `force_generate=True`.
3. `input_question_key` is the only mandatory input column for generated question-answer flows in the current implementation.
4. The declared parameters `input_text_key`, `input_target_key`, `input_targets_key`, `input_label_key`, `input_labels_key`, `input_better_key`, and `input_rejected_key` are currently exposed for API compatibility, but they are not consumed inside `run()`.
5. If `input_choices_key` is present but a row contains an empty or invalid value, the implementation substitutes `[""]` instead of failing that row.
6. The return value is a list: usually `[output_key]` on success, or `[]` when skipped.

## 6. Typical Usage

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
