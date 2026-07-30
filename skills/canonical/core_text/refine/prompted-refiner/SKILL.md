---
name: prompted-refiner
description: >-
  Reference documentation for the PromptedRefiner operator.

  Use when: refining text with LLM, overwriting original column.
---

# PromptedRefiner Operator Reference

`PromptedRefiner` uses an LLM to refine/rewrite text in a column and overwrites the original column with refined results.

## 1. Import

```python
from dataflow.operators.core_text import PromptedRefiner
```

## 2. Constructor

```python
PromptedRefiner(
    llm_serving=llm_serving,
    system_prompt="You are a helpful agent.",
)
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `llm_serving` | Yes | None | LLM service object |
| `system_prompt` | No | `"You are a helpful agent."` | Instruction for text refinement |

## 3. run() Signature

```python
op.run(
    storage=self.storage.step(),
    input_key="raw_content",
)
# returns: None
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `storage` | Yes | None | Storage step object |
| `input_key` | No | `"raw_content"` | Column to refine (overwritten in place) |

## 4. Usage Example

```python
from dataflow.operators.core_text import PromptedRefiner
from dataflow.serving import APILLMServing_request
from dataflow.utils.storage import FileStorage

class MyPipeline:
    def __init__(self):
        self.storage = FileStorage(
            first_entry_file_name="./data/input.jsonl",
            cache_path="./cache",
            file_name_prefix="step",
            cache_type="jsonl"
        )

        self.llm_serving = APILLMServing_request(
            api_url="https://api.openai.com/v1/chat/completions",
            key_name_of_api_key="DF_API_KEY",
            model_name="gpt-4o",
            max_workers=10
        )

        self.refiner = PromptedRefiner(
            llm_serving=self.llm_serving,
            system_prompt="Refine the following text for clarity."
        )

    def forward(self):
        self.refiner.run(
            storage=self.storage.step(),
            input_key="content"
        )

if __name__ == "__main__":
    pipeline = MyPipeline()
    pipeline.forward()
```

## 5. Runtime Logic

1. Read DataFrame from storage.
2. Extract text from `input_key` column.
3. For each non-empty row, concatenate `system_prompt + text` as LLM input.
4. Call LLM to generate refined text.
5. Overwrite `input_key` column with refined results.
6. Empty/falsy rows are skipped (not sent to LLM).
7. Return None.

## 6. Important Notes

- Overwrites `input_key` column in place (original text is lost)
- To preserve original text, copy column first using PandasOperator
- Empty rows in `input_key` are skipped but remain in DataFrame
- No `output_key` parameter exists
