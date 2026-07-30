# Bad Examples: Text2MultiHopQAGenerator

## `output_key` Already Exists

```python
self.generator.run(
    storage=self.storage.step(),
    input_key="cleaned_chunk",
    output_key="QA_pairs",
    output_meta_key="QA_metadata"
)
```

If `QA_pairs` already exists in the DataFrame, `run()` raises `ValueError`.

---

## Missing `input_key` Column

```python
self.generator.run(
    storage=self.storage.step(),
    input_key="missing_cleaned_chunk",
    output_key="QA_pairs",
    output_meta_key="QA_metadata"
)
```

If the input column does not exist, `run()` raises `ValueError`.

---

## Text Too Short or Too Low Quality

```python
{"cleaned_chunk": "Too short."}
```

This row does not survive the pipeline. The constructor produces an empty `qa_pairs` list for it, and `run()` filters that row out of the final DataFrame.

---

## Assuming One Row Will Expand into Many Rows

```python
result = self.generator.run(...)
# wrong expectation: one QA pair becomes one output row
```

The current source stores a list of QA dicts inside `QA_pairs` for each row. It does not explode QA pairs into separate rows.
