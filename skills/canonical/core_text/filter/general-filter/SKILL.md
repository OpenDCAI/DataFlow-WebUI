---
name: general-filter
description: >-
  Reference documentation for the GeneralFilter operator. Covers the
  constructor, rule-based filtering logic, and pipeline usage notes.

  Use when: filtering rows based on column value conditions that can be
  expressed as lambda functions without LLM calls.
---
# GeneralFilter Operator Reference

`GeneralFilter` filters DataFrame rows using a custom rule list, combining all rules with AND. It does not add new columns — it only removes rows that do not satisfy all conditions.

## 1. Import

```python
from dataflow.operators.core_text import GeneralFilter
```

## 2. Constructor

```python
GeneralFilter(
    filter_rules=[
        lambda df: df["score"] >= 4,
        lambda df: df["text"].str.len() > 10,
    ]
)
```

| Parameter        | Required | Default | Description                                                                               |
| ---------------- | -------- | ------- | ----------------------------------------------------------------------------------------- |
| `filter_rules` | Yes      | None    | List of rules; each rule is a callable with signature `(df: DataFrame) -> Series[bool]` |

Each rule returns a boolean Series the same length as the DataFrame; `True` means keep the row. Multiple rules are combined with **AND**.

## 3. run() Signature

```python
op.run(
    storage=self.storage.step(),
)
# returns: "" (empty string)
```

| Parameter   | Required | Default | Description                                                                                                       |
| ----------- | -------- | ------- | ----------------------------------------------------------------------------------------------------------------- |
| `storage` | Yes      | None    | `DataFlowStorage` step object. The operator reads a DataFrame from here and writes the filtered DataFrame back. |

Note: `run()` has no `input_key` / `output_key` parameters. Column names referenced in rules are written directly in the lambda.

### Return Value

The method returns `""` (empty string).

## 4. Actual Runtime Logic

The source code behavior is:

1. Read the DataFrame from `storage.read("dataframe")`.
2. Initialize a boolean mask as `pd.Series(True, index=df.index)`.
3. For each rule in `filter_rules`:
   - Validate the rule is callable.
   - Call `cond = rule_fn(df)`.
   - Validate `cond` is a boolean Series.
   - Update mask: `mask &= cond`.
4. Filter the DataFrame: `filtered_df = df[mask]`.
5. Write the filtered DataFrame back via `storage.write(filtered_df)`.
6. Return `""`.

### Key Behavior Notes

1. Each rule must return a boolean `pd.Series`; otherwise raises `ValueError`.
2. Columns referenced in rules must already exist in the current step's DataFrame.
3. Only removes rows; adds no new columns.
4. Multiple rules are combined with AND — only rows satisfying all conditions are kept.

## 5. Pipeline Usage Pattern

```python
from dataflow.operators.core_text import GeneralFilter
from dataflow.utils.storage import FileStorage

class MyPipeline:
    def __init__(self):
        self.storage = FileStorage(
            first_entry_file_name="./data/input.jsonl",
            cache_path="./cache",
            file_name_prefix="step",
            cache_type="jsonl"
        )

        self.filter = GeneralFilter(
            filter_rules=[
                lambda df: df["score"] >= 4,
                lambda df: df["text"].str.len() > 10,
            ]
        )

    def forward(self):
        self.filter.run(storage=self.storage.step())

if __name__ == "__main__":
    pipeline = MyPipeline()
    pipeline.forward()
```

Note: `forward()` has no return value, following the standard pipeline pattern.
