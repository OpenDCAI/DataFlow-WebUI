---
name: prompted-generator
description: >-
  Reference documentation for the PromptedGenerator operator. Covers constructor
  parameters, run() signature, actual row-processing behavior, and pipeline
  usage notes.
  Use when: integrating PromptedGenerator into a DataFlow pipeline for
  single-field LLM generation.
---

# PromptedGenerator Operator Reference

`PromptedGenerator` is DataFlow's basic single-field LLM generation operator.

For each row in the current DataFrame, it reads the value from `input_key`. If that value is truthy, it builds one LLM input as:

```python
user_prompt + str(row[input_key])
```

It then calls `llm_serving.generate_from_input(...)` in batch and writes the
generated results into `output_key`.

## 1. Import

```python
from dataflow.operators.core_text import PromptedGenerator
```

## 2. Constructor

```python
PromptedGenerator(
    llm_serving,                               # required
    system_prompt="You are a helpful agent.",  # optional
    user_prompt="",                            # optional
    json_schema=None,                          # optional
)
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `llm_serving` | Yes | None | LLM service object implementing `generate_from_input(...)` |
| `system_prompt` | No | `"You are a helpful agent."` | System prompt passed to the serving layer |
| `user_prompt` | No | `""` | Prefix prepended directly before each valid row's input text |
| `json_schema` | No | `None` | Optional schema forwarded to the serving layer |

## 3. run() Signature

```python
op.run(
    storage=self.storage.step(),
    input_key="raw_content",
    output_key="generated_content",
)
# returns: output_key
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `storage` | Yes | None | Current operator-step storage object |
| `input_key` | No | `"raw_content"` | Column read from the current DataFrame |
| `output_key` | No | `"generated_content"` | Column written back to the DataFrame |

## 4. Actual Execution Logic

The operator performs the following steps:

1. Read the current DataFrame from `storage`.
2. Iterate over the DataFrame row by row.
3. For each row, read `raw_content = row.get(input_key, "")`.
4. Only if `raw_content` is truthy, append `user_prompt + str(raw_content)` to
   the batch LLM input list.
5. Call:

```python
llm_serving.generate_from_input(
    user_inputs=llm_inputs,
    system_prompt=system_prompt,
    json_schema=json_schema,
)
```

6. Write the generated list into `dataframe[output_key]`.
7. Persist the updated DataFrame through `storage.write(dataframe)`.
8. Return `output_key`.

## 5. Important Rules

1. `input_key` must exist in the current DataFrame.
2. `user_prompt` is a plain string prefix, not a template engine.
3. The implementation skips rows whose `input_key` value is empty, `None`, or
   otherwise falsy when building LLM inputs.


## 6. Typical Usage

```python
from dataflow.operators.core_text import PromptedGenerator

prompted_gen = PromptedGenerator(
    llm_serving=self.llm_serving,
    system_prompt="You are a helpful agent.",
    user_prompt="Summarize the following content in one sentence:\n",
)

prompted_gen.run(
    storage=self.storage.step(),
    input_key="raw_content",
    output_key="summary",
)
```

## 7. Return Value

```python
return output_key
```

This is intended for downstream operator chaining.
