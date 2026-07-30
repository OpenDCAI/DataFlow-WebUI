# Bad Examples: ChunkedPromptedGenerator

## input_path_key column contains text content instead of file paths

```python
self.generator.run(
    storage=self.storage.step(),
    input_path_key="content",    # column holds raw text, not file paths
    output_path_key="output_path"
)
```

The operator treats each cell value as a filesystem path and tries to open it; passing text content instead of a path raises `FileNotFoundError`.

---

## File path in the column does not exist on disk

```python
{"file_path": "/nonexistent/path/file.txt"}
```

If a path in the column is not accessible at runtime, the operator raises `FileNotFoundError` for that row.
