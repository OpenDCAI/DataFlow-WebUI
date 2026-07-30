---
name: format-str-prompted-generator
description: >-
  Reference documentation for the FormatStrPromptedGenerator operator. Covers
  the constructor, prompt template restrictions, placeholder-to-column mapping,
  actual prompt-building logic, and runnable example usage.

  Use when: one generation task needs multiple dataframe columns combined into
  a single prompt through a template.
---

# FormatStrPromptedGenerator Operator Reference

`FormatStrPromptedGenerator` is DataFlow's multi-field template-based LLM
generation operator. It maps multiple dataframe columns into template
placeholders, builds one prompt per row, calls the LLM, writes the result into
`output_key`, persists the dataframe, and returns the `output_key` string.

## 1. Imports

```python
from dataflow.operators.core_text import FormatStrPromptedGenerator
from dataflow.prompts.core_text import FormatStrPrompt
```

## 2. Constructor

```python
FormatStrPromptedGenerator(
    llm_serving,
    system_prompt="You are a helpful agent.",
    prompt_template=FormatStrPrompt(f_str_template="..."),
    json_schema=None,
)
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `llm_serving` | Yes | None | LLM service object implementing `generate_from_input(...)` |
| `system_prompt` | No | `"You are a helpful agent."` | System prompt passed to the serving layer |
| `prompt_template` | Yes in practice | `FormatStrPrompt` | Must be an instantiated `FormatStrPrompt(...)` or a `DIYPromptABC` subclass instance |
| `json_schema` | No | `None` | Optional schema forwarded to `generate_from_input(...)` |

### Important `prompt_template` Notes

1. The source code default is `FormatStrPrompt`, which is the class object, not
   an instance. Because of `@prompt_restrict`, omitting `prompt_template`
   entirely can raise `TypeError` at construction time.
2. Passing `prompt_template=None` is also invalid here. Unlike
   `BenchAnswerGenerator`, this operator explicitly raises:

```python
ValueError("prompt_template cannot be None")
```

3. The practical safe pattern is to always pass an instantiated template:

```python
FormatStrPrompt(
    f_str_template="Title: {title}\n\nBody: {body}\n\nSummarize this article."
)
```

### Constructing `FormatStrPrompt`

```python
FormatStrPrompt(
    f_str_template="{title}\n\n{body}",
    on_missing="raise",
)
```

## 3. run() Signature

```python
op.run(
    storage=self.storage.step(),
    output_key="generated_content",
    title="title_col",
    body="body_col",
)
# returns: output_key
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `storage` | Yes | None | Current operator-step storage object |
| `output_key` | No | `"generated_content"` | Output column to write |
| `**input_keys` | Yes | None | Mapping from template placeholder name to dataframe column name |

### Placeholder Mapping Rule

In `run(...)`, each kwarg uses this convention:

- kwarg name = placeholder name inside `f_str_template`
- kwarg value = dataframe column name to read from

Example:

```python
prompt_template = FormatStrPrompt(
    f_str_template="Title: {title}\n\nBody: {body}\n\nSummarize this article."
)

generator.run(
    storage=self.storage.step(),
    output_key="summary",
    title="headline_col",
    body="article_body_col",
)
```

This means:

- `{title}` is replaced with `row["headline_col"]`
- `{body}` is replaced with `row["article_body_col"]`

## 4. Actual Execution Logic

The current implementation behaves as follows:

1. Read the dataframe from `storage`.
2. Collect `need_fields = set(input_keys.keys())`.
3. For each row, build:

```python
key_dict = {key: row[input_keys[key]] for key in need_fields}
```

4. Call:

```python
prompt_text = prompt_template.build_prompt(need_fields, **key_dict)
```

5. Append all row prompts into `llm_inputs`.
6. Call:

```python
llm_serving.generate_from_input(
    user_inputs=llm_inputs,
    system_prompt=self.system_prompt,
    json_schema=self.json_schema,
)
```

7. Write generated outputs into `dataframe[output_key]`.
8. Persist via `storage.write(dataframe)`.
9. Return `output_key`.

## 5. Important Rules

1. Always pass an instantiated `FormatStrPrompt(...)` or a compatible DIY prompt instance.
2. Do not omit `prompt_template`, do not pass the class object, and do not pass `None`.
3. Every value in `**input_keys` must be an existing dataframe column name.
4. The operator does not validate template placeholders against the template string itself. If you forget to map a placeholder that appears in `f_str_template`, that placeholder can remain unreplaced in the final prompt.
5. If you provide a placeholder name in `**input_keys` that is not used in the template, the extra value is simply unused by string replacement.
6. The operator adds or overwrites `output_key`, and does not filter rows.
7. The return value is the bare `output_key` string, not a list.

## 6. Typical Usage

```python
from dataflow.operators.core_text import FormatStrPromptedGenerator
from dataflow.prompts.core_text import FormatStrPrompt

prompt_template = FormatStrPrompt(
    f_str_template="Title: {title}\n\nBody: {body}\n\nPlease write a concise summary."
)

generator = FormatStrPromptedGenerator(
    llm_serving=self.llm_serving,
    system_prompt="You are a professional editor. Write concise, informative summaries.",
    prompt_template=prompt_template,
)

generator.run(
    storage=self.storage.step(),
    output_key="summary",
    title="title",
    body="body",
)
```
