# Bad Examples: PandasOperator

## process_fn does not return a DataFrame

```python
PandasOperator(
    process_fn=[
        lambda df: df.dropna(subset=["text"], inplace=True),  # returns None
    ]
)
```

`inplace=True` returns `None`; the next step receives `None` and raises `AttributeError`.

---

## run() called with input_key or output_key

```python
self.op.run(
    storage=self.storage.step(),
    input_key="text"    # no such parameter — raises TypeError
)
```

`PandasOperator.run()` accepts only `storage`; column selection belongs inside the lambda.

---

## Referencing a column that does not exist

```python
PandasOperator(
    process_fn=[
        lambda df: df[df["content"].str.len() > 10]  # KeyError if column is "text"
    ]
)
```

The lambda references a column name that is absent from the DataFrame, raising `KeyError`.
