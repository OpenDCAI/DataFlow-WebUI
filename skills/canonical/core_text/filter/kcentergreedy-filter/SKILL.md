---
name: kcentergreedy-filter
description: >-
  Reference documentation for the KCenterGreedyFilter operator. Covers the
  constructor, K-Center Greedy algorithm behavior, embedding serving
  requirements, and pipeline usage notes.

  Use when: downsampling a large dataset by semantic diversity using embedding
  vectors.
---

# KCenterGreedyFilter Operator Reference

`KCenterGreedyFilter` uses the K-Center Greedy algorithm to select the most diverse `num_samples` rows, deleting all others.

## 1. Imports

```python
from dataflow.operators.core_text import KCenterGreedyFilter
from dataflow.serving import APILLMServing_request
```

## 2. Embedding Serving Options

### Option A: Remote API with `APILLMServing_request`

```python
APILLMServing_request(
    api_url="https://api.openai.com/v1/embeddings",
    key_name_of_api_key="DF_API_KEY",
    model_name="text-embedding-3-small",
    max_workers=20,
)
```

### Option B: Local embedding model with `LocalEmbeddingServing`

```python
LocalEmbeddingServing(
    model_name="all-MiniLM-L6-v2",
    device=None,
    max_workers=2,
)
```

### Option C: Provider-agnostic API via `LiteLLMServing`

```python
LiteLLMServing(
    serving_type="embedding",
    model_name="text-embedding-3-small",
    key_name_of_api_key="DF_API_KEY",
    max_workers=10,
)
```

### Option D: Local vLLM backend with `LocalModelLLMServing_vllm`

```python
LocalModelLLMServing_vllm(
    hf_model_name_or_path="your-embedding-capable-model",
    vllm_tensor_parallel_size=1,
)
```

### Practical Serving Note

The operator calls `embedding_serving.generate_embedding_from_input(texts)`. Any serving object implementing this method can be used.

Supported: `APILLMServing_request`, `LocalEmbeddingServing`, `LiteLLMServing`, `LocalModelLLMServing_vllm`

Not supported: `LocalModelLLMServing_sglang` (raises `NotImplementedError`)

## 3. Constructor

```python
KCenterGreedyFilter(
    num_samples=1000,
    embedding_serving=embedding_serving,
)
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `num_samples` | Yes | None | Number of rows to keep; must be ≤ total DataFrame row count. |
| `embedding_serving` | No | `None` | Embedding service object implementing `generate_embedding_from_input(...)`. Must point to `/v1/embeddings` endpoint if using `APILLMServing_request`. |

### Important Constructor Notes

1. **Parameter order**: Source code signature is `__init__(self, num_samples, embedding_serving=None)`.
2. `num_samples` is the first positional parameter.
3. `embedding_serving` is the second parameter with default `None`.

### Important Serving Note

The operator calls `embedding_serving.generate_embedding_from_input(texts)`. The serving object must implement this method.

## 4. run() Signature

```python
selected_keys = op.run(
    storage=self.storage.step(),
    input_key="content",
)
# returns: [input_key]
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `storage` | Yes | None | `DataFlowStorage` step object. |
| `input_key` | No | `"content"` | Text column to compute embeddings from; must already exist. |

### Return Value

Returns `[self.input_key]` (a list). Pipeline `forward()` methods should not return values.

## 5. Actual Runtime Logic

The source code behavior is:

1. Store `input_key` on `self.input_key`.
2. Read the DataFrame from `storage.read("dataframe")`.
3. Validate that `input_key` column exists.
4. Extract text list: `texts = dataframe[input_key].tolist()`.
5. Call `self.embedding_serving.generate_embedding_from_input(texts)` to get embeddings.
6. Convert embeddings to torch tensor.
7. Calculate `sampling_ratio = num_samples / len(texts)`.
8. Use `KCenterGreedy` algorithm to select `num_samples` diverse row indices.
9. Create a binary mask and keep only selected rows.
10. Write the filtered DataFrame back via `storage.write(dataframe)`.
11. Return `[self.input_key]`.

### Key Behavior Notes

1. `num_samples` must be ≤ the current DataFrame row count.
2. `embedding_serving` must implement `generate_embedding_from_input(...)`.
3. For `APILLMServing_request`, `api_url` must point to `/v1/embeddings`, not `/v1/chat/completions`.
4. Filtering is irreversible — unselected rows are permanently deleted.

## 6. Pipeline Usage Pattern

```python
from dataflow.operators.core_text import KCenterGreedyFilter
from dataflow.serving import APILLMServing_request
from dataflow.utils.storage import FileStorage

class MyPipeline:
    def __init__(self):
        self.storage = FileStorage(
            first_entry_file_name="./data/input.jsonl",
            cache_path="./cache",
            file_name_prefix="step",
            cache_type="jsonl"
        )

        self.embedding_serving = APILLMServing_request(
            api_url="https://api.openai.com/v1/embeddings",
            key_name_of_api_key="DF_API_KEY",
            model_name="text-embedding-3-small",
            max_workers=20
        )

        self.filter = KCenterGreedyFilter(
            num_samples=1000,
            embedding_serving=self.embedding_serving
        )

    def forward(self):
        self.filter.run(
            storage=self.storage.step(),
            input_key="content"
        )

if __name__ == "__main__":
    pipeline = MyPipeline()
    pipeline.forward()
```

Note: `forward()` has no return value, following the standard pipeline pattern.
