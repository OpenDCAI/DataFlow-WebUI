# Bad Examples: PromptedRefiner

## Passing output_key to run()

```python
self.refiner.run(
    storage=self.storage.step(),
    input_key="description",
    output_key="refined_description"  # no such parameter — raises TypeError
)
```

`PromptedRefiner.run()` has no `output_key`; the result always overwrites the `input_key` column in-place.

---

## Passing empty-value rows without pre-filtering

```python
self.refiner.run(
    storage=self.storage.step(),
    input_key="description"   # column contains empty-string rows
)
```

Empty rows are skipped by the LLM, so they retain their original (empty) value, producing inconsistent output silently.
