---
name: embedding-generator
description: >-
  Reference documentation for the EmbeddingGenerator operator. Covers the
  constructor, embedding serving requirements, actual dataframe flow, and
  runnable pipeline usage.

  Use when: converting one text column in a dataframe into embedding vectors for
  retrieval, clustering, similarity search, or downstream vector-based
  operators.
---

# EmbeddingGenerator Operator Reference

`EmbeddingGenerator` reads one text column from the current dataframe, sends the
full column as a batch into an embedding service, writes the returned vectors
into `output_key`, persists the dataframe, and returns `[output_key]`.

## 1. Imports

```python
from dataflow.operators.core_text import EmbeddingGenerator
from dataflow.serving import APILLMServing_request
from dataflow.serving import LocalEmbeddingServing
from dataflow.serving import LiteLLMServing
from dataflow.serving import LocalModelLLMServing_vllm
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

This works because `APILLMServing_request` implements:

```python
generate_embedding_from_input(texts)
```

### Option B: Local embedding model with `LocalEmbeddingServing`

```python
LocalEmbeddingServing(
    model_name="all-MiniLM-L6-v2",
    device=None,
    max_workers=2,
)
```

Requires:

```bash
pip install "open-dataflow[vectorsql]"
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

This is suitable when you want to route embedding requests through LiteLLM.

### Option D: Local vLLM backend with `LocalModelLLMServing_vllm`

```python
LocalModelLLMServing_vllm(
    hf_model_name_or_path="your-embedding-capable-model",
    vllm_tensor_parallel_size=1,
)
```

This works only if the selected vLLM model/backend supports embedding through
`llm.embed(...)`.

### Practical List of Supported Serving Examples

The following classes in `dataflow.serving` currently expose
`generate_embedding_from_input(...)` and are practical candidates for
`EmbeddingGenerator`:

- `APILLMServing_request`
- `LocalEmbeddingServing`
- `LiteLLMServing`
- `LocalModelLLMServing_vllm`

The following commonly imported serving is **not** suitable here:

- `LocalModelLLMServing_sglang`: its `generate_embedding_from_input(...)`
  currently raises `NotImplementedError`

## 3. Constructor

```python
EmbeddingGenerator(
    embedding_serving=emb,
)
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `embedding_serving` | Yes | None | Service object that provides `generate_embedding_from_input(texts)` |

### Important Serving Note

Although the constructor type annotation is `LLMServingABC`, the operator does
not call `generate_from_input(...)`. It specifically calls:

```python
embedding_serving.generate_embedding_from_input(texts)
```

So the practical requirement is not just “any `LLMServingABC`”, but a serving
object that actually implements `generate_embedding_from_input(...)`.

## 4. run() Signature

```python
op.run(
    storage=self.storage.step(),
    input_key="text",
    output_key="embeddings",
)
# returns: [output_key]
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `storage` | Yes | None | Current operator-step storage object |
| `input_key` | No | `"text"` | Existing dataframe column containing texts |
| `output_key` | No | `"embeddings"` | Column written with embedding vectors |

## 5. Actual Execution Logic

The current implementation behaves as follows:

1. Read the dataframe from `storage`.
2. Read the column `dataframe[input_key]`.
3. Convert that column into a Python list with `tolist()`.
4. Call:

```python
embedding_serving.generate_embedding_from_input(texts)
```

5. Write the returned embedding list into `dataframe[output_key]`.
6. Persist the dataframe through `storage.write(dataframe)`.
7. Return `[output_key]`.

## 6. Important Rules

1. `input_key` must already exist in the current dataframe.
2. The operator sends the full text column as one batch to `generate_embedding_from_input(...)`.
3. The operator does not perform missing-value filtering or type normalization before sending the texts.
4. `output_key` is overwritten silently if it already exists.
5. The return value is a list containing the output column name, not the bare string.
6. When using `APILLMServing_request`, `api_url` should point to an embedding endpoint such as `/v1/embeddings`, not `/v1/chat/completions`.
7. A service being an `LLMServingABC` subclass is not sufficient by itself; it must actually implement `generate_embedding_from_input(...)`.

## 7. Typical Usage

```python
from dataflow.operators.core_text import EmbeddingGenerator
from dataflow.serving import APILLMServing_request

embedding_serving = APILLMServing_request(
    api_url="https://api.openai.com/v1/embeddings",
    key_name_of_api_key="DF_API_KEY",
    model_name="text-embedding-3-small",
    max_workers=20,
)

generator = EmbeddingGenerator(
    embedding_serving=embedding_serving,
)

generator.run(
    storage=self.storage.step(),
    input_key="content",
    output_key="embedding",
)
```
