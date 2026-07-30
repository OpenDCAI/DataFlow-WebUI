---
name: prompted-evaluator
description: >-
  Reference documentation for the PromptedEvaluator operator.

  Use when: scoring text quality with LLM without filtering rows.
---

# PromptedEvaluator Operator Reference

`PromptedEvaluator` uses an LLM to score each row of text (1-5) and writes the score into a new column without deleting any rows.

## 1. Import

```python
from dataflow.operators.core_text import PromptedEvaluator
```

## 2. Constructor

```python
PromptedEvaluator(
    llm_serving=llm_serving,
    system_prompt="Please evaluate the quality of this text on a scale from 1 to 5.",
)
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `llm_serving` | Yes | None | LLM service object |
| `system_prompt` | No | `"Please evaluate..."` | System prompt defining scoring criteria (1-5 scale) |

## 3. run() Signature

```python
op.run(
    storage=self.storage.step(),
    input_key="raw_content",
    output_key="eval",
)
# returns: output_key string
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `storage` | Yes | None | Storage step object |
| `input_key` | No | `"raw_content"` | Column containing text to evaluate |
| `output_key` | No | `"eval"` | Column to write LLM scores into |

## 4. Usage Example

```python
from dataflow.operators.core_text import PromptedEvaluator
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

        self.evaluator = PromptedEvaluator(
            llm_serving=self.llm_serving,
            system_prompt="Evaluate text quality on a scale from 1 to 5."
        )

    def forward(self):
        self.evaluator.run(
            storage=self.storage.step(),
            input_key="content",
            output_key="quality_score"
        )

if __name__ == "__main__":
    pipeline = MyPipeline()
    pipeline.forward()
```

## 5. Runtime Logic

1. Read DataFrame from storage.
2. Extract text from `input_key` column.
3. For each row, call LLM with `system_prompt` to score the text (1-5).
4. Parse LLM response to extract numeric score.
5. Write scores to `output_key` column.
6. All rows are kept (no filtering).
7. Return `output_key` string.

## 6. Key Differences from PromptedFilter

- **PromptedEvaluator**: Writes scores to `output_key` column, keeps all rows
- **PromptedFilter**: Writes scores and deletes rows below threshold in one step

Use PromptedEvaluator + GeneralFilter for two-step scoring and filtering.
