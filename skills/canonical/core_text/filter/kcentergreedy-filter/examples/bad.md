# Bad Examples: KCenterGreedyFilter

## api_url points to the chat completions endpoint

```python
KCenterGreedyFilter(
    embedding_serving=APILLMServing_request(
        api_url="https://api.openai.com/v1/chat/completions",  # wrong endpoint
        model_name="text-embedding-3-small",
    ),
    num_samples=500
)
```

The chat completions endpoint returns a different response format than the embeddings endpoint; parsing the response will fail.

---

## num_samples exceeds the DataFrame row count

```python
KCenterGreedyFilter(
    embedding_serving=emb,
    num_samples=500   # DataFrame only has 100 rows
)
```

Requesting more samples than there are rows means the algorithm cannot complete and raises an error.
