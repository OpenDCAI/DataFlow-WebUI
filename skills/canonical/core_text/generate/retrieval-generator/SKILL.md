---
name: retrieval-generator
description: >-
  Reference documentation for the RetrievalGenerator operator.

  [Purpose] Reads one text column from storage, forwards every non-empty row to
  `llm_serving.generate_from_input(...)`, and writes the returned list into a
  new output column.

  [Default backend] Use `LightRAGServing` by default.

  [Important] `run()` is async. The operator itself does not initialize the
  serving object; it only awaits
  `llm_serving.generate_from_input(llm_inputs, system_prompt)`.
---

# RetrievalGenerator Operator Reference

`RetrievalGenerator` is an async operator. It reads text from one column, collects only truthy values, calls `await self.llm_serving.generate_from_input(llm_inputs, self.system_prompt)`, and writes the returned list into `output_key`.

See `examples/good.md` for a valid usage pattern and `examples/bad.md` for common failure cases.

---

## 1. Import

```python
from dataflow.operators.core_text import RetrievalGenerator
from dataflow.serving import LightRAGServing
```

---

## 2. Constructor

```python
RetrievalGenerator(
    llm_serving=serving,
    system_prompt="You are a helpful agent.",
)
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `llm_serving` | Yes | None | Stored on `self.llm_serving` without validation. `run()` later awaits `self.llm_serving.generate_from_input(llm_inputs, self.system_prompt)`. |
| `system_prompt` | No | `"You are a helpful agent."` | Stored on `self.system_prompt` and forwarded unchanged into `generate_from_input(...)`. |

### Notes

1. The operator does not initialize the serving backend for you.
2. Any serving object used here must already be ready before `run()` starts.
3. Default recommendation: use `LightRAGServing`.

---

## 3. Default LightRAGServing Initialization

If you use the default backend, initialize it like this before constructing `RetrievalGenerator`:

```python
llm_serving = await LightRAGServing.create(
    api_url="https://api.openai.com/v1",
    llm_model_name="gpt-4o",
    embed_model_name="bge-m3:latest",
    embed_binding_host="http://localhost:11434",
    document_list=["knowledge_base.txt"],
)
if llm_serving is None:
    raise RuntimeError("LightRAGServing initialization failed.")
```


- `LightRAGServing.__init__()` accepts `api_url`, `key_name_of_api_key`, `llm_model_name`, `embed_model_name`, `embed_binding_host`, `embedding_dim`, `max_embed_tokens`, and `document_list`.
- `LightRAGServing.create(...)` builds `self.rag` and loads documents.
- `DF_API_KEY` must exist in the environment, otherwise construction raises `ValueError`.
- If document loading fails inside `create(...)`, it logs the error and returns `None`.

---

## 4. run() Signature

```python
await op.run(
    storage=storage,
    input_key="raw_content",
    output_key="generated_content",
)
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `storage` | Yes | None | Used as `storage.read("dataframe")` and `storage.write(df)`. |
| `input_key` | No | `"raw_content"` | Column name read from each row via `row.get(input_key, "")`. Only truthy values are appended to `llm_inputs`. |
| `output_key` | No | `"generated_content"` | Column name assigned as `df[output_key] = generated_outputs`. |

### Return Value

On success, the method returns the string `output_key`.

If `generate_from_input(...)` raises an exception, the operator logs the error and returns `None`.

---

## 5. Actual Runtime Logic

1. Save `input_key` and `output_key` onto `self`.
2. Read the DataFrame from `storage.read("dataframe")`.
3. Iterate row by row.
4. Read `row.get(input_key, "")`.
5. Append `str(raw_content)` only when the value is truthy.
6. Call `generated_outputs = await self.llm_serving.generate_from_input(llm_inputs, self.system_prompt)`.
7. Assign `generated_outputs` to `df[output_key]`.
8. Write the updated DataFrame back with `storage.write(df)`.
9. Return `output_key`.

There is no placeholder output for skipped rows.

---

## 6. Critical Constraints

1. `run()` is async. You must call it with `await`.
2. Empty or falsy values in `input_key` are skipped before generation.
