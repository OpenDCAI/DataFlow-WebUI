# Bad Examples: EmbeddingGenerator

## Using the non-existent APIEmbeddingServing class

```python
from dataflow.serving import APIEmbeddingServing  # class does not exist — ImportError

EmbeddingGenerator(
    embedding_serving=APIEmbeddingServing(...)
)
```

`APIEmbeddingServing` does not exist in `dataflow.serving`; the import itself raises `ImportError`.

---

## api_url points to the chat completions endpoint

```python
self.embedding_serving = APILLMServing_request(
    api_url="https://api.openai.com/v1/chat/completions",  # wrong endpoint
    model_name="text-embedding-3-small",
)
```

The chat completions endpoint returns a different response format than the embeddings endpoint; parsing the response will fail.
