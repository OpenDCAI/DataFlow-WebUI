# Bad Examples: GeneralFilter

## Rule function returns a scalar instead of a boolean Series

```python
GeneralFilter([
    lambda df: True,            # scalar — raises ValueError
    lambda df: len(df) > 0,     # scalar — raises ValueError
])
```

Each rule must return a boolean `pd.Series` with one value per row; returning a scalar bool raises `ValueError`.

---

## run() called with input_key

```python
self.filter.run(
    storage=self.storage.step(),
    input_key="text"    # no such parameter — raises TypeError
)
```

`GeneralFilter.run()` accepts only `storage`; column references belong inside the lambda at construction time.
