---
name: prompted-filter
description: >-
  Reference documentation for the PromptedFilter operator. Covers the
  constructor, actual scoring and filtering behavior, and pipeline usage notes.

  Use when: filtering rows based on LLM semantic quality judgment rather than
  simple rule-based conditions.
---
# PromptedFilter Operator Reference

`PromptedFilter` internally uses `PromptedEvaluator` to score each row of text, writes the score into `output_key`, and keeps only rows with scores in `[min_score, max_score]`.

## 1. Import

```python
from dataflow.operators.core_text import PromptedFilter
```

## 2. Constructor

```python
PromptedFilter(
    llm_serving,
    system_prompt="Please evaluate the quality of this data on a scale from 1 to 5.",
    min_score=1,
    max_score=5,
)
```

| Parameter         | Required | Default                                                                | Description                                                                                               |
| ----------------- | -------- | ---------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| `llm_serving`   | Yes      | None                                                                   | LLM service object implementing `generate_from_input(...)`. Internally passed to `PromptedEvaluator`. |
| `system_prompt` | No       | `"Please evaluate the quality of this data on a scale from 1 to 5."` | Defines the LLM's scoring criteria. The scale described should align with `min_score`/`max_score`.    |
| `min_score`     | No       | `1`                                                                  | Lower bound of the score range to keep (inclusive).                                                       |
| `max_score`     | No       | `5`                                                                  | Upper bound of the score range to keep (inclusive).                                                       |

### Important Constructor Notes

1. The operator creates an internal `PromptedEvaluator(llm_serving, system_prompt)` instance.
2. Source code comment at line 35 incorrectly states `min_score` default is `5`; actual default is `1`.
3. Source code comment at line 36 incorrectly states `max_score` default is `5`; actual default is `5` (correct).

## 3. run() Signature

```python
output_key = op.run(
    storage=self.storage.step(),
    input_key="raw_content",
    output_key="eval",
)
# returns: output_key
```

| Parameter      | Required | Default           | Description                                                                                                       |
| -------------- | -------- | ----------------- | ----------------------------------------------------------------------------------------------------------------- |
| `storage`    | Yes      | None              | `DataFlowStorage` step object. The operator reads a DataFrame from here and writes the filtered DataFrame back. |
| `input_key`  | No       | `"raw_content"` | Text column to evaluate. This column must already exist.                                                          |
| `output_key` | No       | `"eval"`        | Column to write LLM scores into. Silently overwrites if already exists.                                           |

### Return Value

Returns `output_key` string. Pipeline `forward()` methods should not return values.

## 4. Actual Runtime Logic

The source code behavior is:

1. Read the DataFrame from `storage.read("dataframe")`.
2. Call `self.prompted_evaluator.eval(dataframe, input_key)` to get a list of numeric scores.
3. Write the scores into `dataframe[output_key]`.
4. Filter the DataFrame: keep only rows where `dataframe[output_key] >= self.min_score` AND `dataframe[output_key] <= self.max_score`.
5. Write the filtered DataFrame back via `storage.write(filtered_dataframe)`.
6. Return `output_key`.

### Key Behavior Notes

1. The `input_key` column must exist in the current DataFrame.
2. Rows with scores outside `[min_score, max_score]` are permanently deleted.
3. The output DataFrame retains both the `output_key` score column and all original columns.
4. If `output_key` already exists, it is silently overwritten.

## 5. Pipeline Usage Pattern

```python
from dataflow.operators.core_text import PromptedFilter
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

        self.filter = PromptedFilter(
            llm_serving=self.llm_serving,
            system_prompt="Evaluate the quality of this text on a scale from 1 to 5.",
            min_score=4,
            max_score=5
        )

    def forward(self):
        self.filter.run(
            storage=self.storage.step(),
            input_key="content",
            output_key="quality_score"
        )

if __name__ == "__main__":
    pipeline = MyPipeline()
    pipeline.forward()
```

Note: `forward()` has no return value, following the standard pipeline pattern.
