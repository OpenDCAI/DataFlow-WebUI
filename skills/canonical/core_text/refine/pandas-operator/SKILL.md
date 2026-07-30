---
name: pandas-operator
description: >-
  Reference documentation for the PandasOperator operator.

  Use when: applying custom DataFrame transformations without LLM.
---

# PandasOperator Operator Reference

`PandasOperator` applies a list of transformation functions to a DataFrame sequentially. Each function receives a DataFrame and returns a modified DataFrame.

## 1. Import

```python
from dataflow.operators.core_text import PandasOperator
```

## 2. Constructor

```python
PandasOperator(
    process_fn=[
        lambda df: df.rename(columns={"old": "new"}),
        lambda df: df[df["score"] > 0],
    ]
)
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `process_fn` | Yes | None | List of transformation functions, each with signature `(df: DataFrame) -> DataFrame` |

## 3. run() Signature

```python
op.run(
    storage=self.storage.step(),
)
# returns: empty string ""
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `storage` | Yes | None | Storage step object |

## 4. Usage Example

```python
from dataflow.operators.core_text import PandasOperator
from dataflow.utils.storage import FileStorage

class MyPipeline:
    def __init__(self):
        self.storage = FileStorage(
            first_entry_file_name="./data/input.jsonl",
            cache_path="./cache",
            file_name_prefix="step",
            cache_type="jsonl"
        )

        self.transformer = PandasOperator(
            process_fn=[
                lambda df: df.assign(score2=df["score"] * 2),
                lambda df: df.sort_values("score", ascending=False),
                lambda df: df.drop(columns=["temp_col"])
            ]
        )

    def forward(self):
        self.transformer.run(
            storage=self.storage.step()
        )

if __name__ == "__main__":
    pipeline = MyPipeline()
    pipeline.forward()
```

## 5. Runtime Logic

1. Read DataFrame from storage.
2. Apply each function in `process_fn` sequentially.
3. Each function receives the output DataFrame from the previous function.
4. Validate each function is callable and returns a DataFrame.
5. Write final DataFrame to storage.
6. Return empty string.

## 6. Important Notes

- Each function in `process_fn` must return a `pd.DataFrame`
- Functions are applied in list order
- No `input_key` or `output_key` parameters (column operations are in lambda functions)
- Does not call LLM (pure pandas operations)
