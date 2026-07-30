# Bad Examples: RetrievalGenerator

## Calling `run()` Without `await`

```python
async def forward(self):
    self.generator.run(
        storage=self.storage.step(),
        input_key="raw_content",
        output_key="rag_answer"
    )
```

`RetrievalGenerator.run()` is a coroutine. Without `await`, it is not executed.

---

## Constructing `LightRAGServing` with Unsupported Parameters

```python
self.llm_serving = LightRAGServing(
    host="http://localhost",
    port=9621
)
```

The current `LightRAGServing` constructor does not define `host` or `port`. Use `await LightRAGServing.create(...)` with parameters such as `api_url`, `llm_model_name`, `embed_model_name`, `embed_binding_host`, and `document_list`.

---

## Using the Operator Before Async Initialization

```python
class RetrievalRAGPipeline:
    def __init__(self):
        self.llm_serving = LightRAGServing()
        self.generator = RetrievalGenerator(llm_serving=self.llm_serving)
```

This is unsafe for two reasons:

- `LightRAGServing.__init__()` alone does not build `self.rag` or load documents.
- If required environment variables such as `DF_API_KEY` are missing, construction fails immediately.

---

## Running with Empty Query Rows

```python
await self.generator.run(
    storage=self.storage.step(),
    input_key="raw_content",
    output_key="rag_answer"
)
```

If some rows in `raw_content` are empty, the operator skips them when building `llm_inputs`, which can make `generated_outputs` shorter than the DataFrame and cause a pandas length-mismatch error during assignment.
