---
name: embedding-generator
description: >-
  EmbeddingGenerator 算子的参考文档。涵盖构造参数、embedding serving 的实际要求、
  真实 dataframe 执行流程，以及可运行的 pipeline 用法。

  适用场景：将 DataFrame 中的一列文本转成 embedding 向量，用于检索、聚类、
  相似度计算或下游向量类算子。
---

# EmbeddingGenerator 算子参考

`EmbeddingGenerator` 会从当前 DataFrame 中读取一列文本，将整列作为批量输入送入
embedding 服务，把返回的向量结果写入 `output_key`，持久化 DataFrame，并返回
`[output_key]`。

## 1. 导入方式

```python
from dataflow.operators.core_text import EmbeddingGenerator
from dataflow.serving import APILLMServing_request
from dataflow.serving import LocalEmbeddingServing
from dataflow.serving import LiteLLMServing
from dataflow.serving import LocalModelLLMServing_vllm
```

## 2. Embedding Serving 选项

### 方式 A：使用 `APILLMServing_request` 访问远程 API

```python
APILLMServing_request(
    api_url="https://api.openai.com/v1/embeddings",
    key_name_of_api_key="DF_API_KEY",
    model_name="text-embedding-3-small",
    max_workers=20,
)
```

之所以可用，是因为 `APILLMServing_request` 实现了：

```python
generate_embedding_from_input(texts)
```

### 方式 B：使用 `LocalEmbeddingServing` 本地 embedding 模型

```python
LocalEmbeddingServing(
    model_name="all-MiniLM-L6-v2",
    device=None,
    max_workers=2,
)
```

需要先安装：

```bash
pip install "open-dataflow[vectorsql]"
```

### 方式 C：使用 `LiteLLMServing` 作为通用 API 代理

```python
LiteLLMServing(
    serving_type="embedding",
    model_name="text-embedding-3-small",
    key_name_of_api_key="DF_API_KEY",
    max_workers=10,
)
```

适用于希望通过 LiteLLM 转发 embedding 请求的场景。

### 方式 D：使用 `LocalModelLLMServing_vllm` 本地 vLLM 后端

```python
LocalModelLLMServing_vllm(
    hf_model_name_or_path="your-embedding-capable-model",
    vllm_tensor_parallel_size=1,
)
```

只有当你选择的 vLLM 模型或后端确实支持 `llm.embed(...)` 时，这种方式才可用。

### 当前可直接使用的 Serving 示例

在 `dataflow.serving` 中，下面这些类当前明确暴露了
`generate_embedding_from_input(...)`，可以作为 `EmbeddingGenerator` 的实际候选：

- `APILLMServing_request`
- `LocalEmbeddingServing`
- `LiteLLMServing`
- `LocalModelLLMServing_vllm`

下面这个常见 serving 当前**不适合**用于该算子：

- `LocalModelLLMServing_sglang`：它的 `generate_embedding_from_input(...)`
  当前会直接抛出 `NotImplementedError`

## 3. 构造函数

```python
EmbeddingGenerator(
    embedding_serving=emb,
)
```

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `embedding_serving` | 是 | None | 提供 `generate_embedding_from_input(texts)` 方法的服务对象 |

### 关于 Serving 的重要说明

虽然构造函数的类型标注写的是 `LLMServingABC`，但这个算子内部并不会调用
`generate_from_input(...)`，而是会直接调用：

```python
embedding_serving.generate_embedding_from_input(texts)
```

因此，实际要求不只是“任意 `LLMServingABC`”，而是必须提供
`generate_embedding_from_input(...)` 方法的服务对象。

## 4. run() 签名

```python
op.run(
    storage=self.storage.step(),
    input_key="text",
    output_key="embeddings",
)
# 返回值：[output_key]
```

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `storage` | 是 | None | 当前算子步骤对应的 storage 对象 |
| `input_key` | 否 | `"text"` | 当前 DataFrame 中已存在的文本列 |
| `output_key` | 否 | `"embeddings"` | 写入 embedding 向量的列名 |

## 5. 真实执行逻辑

当前实现的执行过程如下：

1. 从 `storage` 读取 DataFrame。
2. 读取 `dataframe[input_key]` 这一列。
3. 用 `tolist()` 把该列转成 Python 列表。
4. 调用：

```python
embedding_serving.generate_embedding_from_input(texts)
```

5. 将返回的向量列表写入 `dataframe[output_key]`。
6. 通过 `storage.write(dataframe)` 持久化 DataFrame。
7. 返回 `[output_key]`。

## 6. 关键规则

1. `input_key` 必须已经存在于当前 DataFrame 中。
2. 算子会把整列文本作为一个批次发送给 `generate_embedding_from_input(...)`。
3. 当前实现不会在发送前额外做缺失值过滤或类型标准化。
4. 如果 `output_key` 已存在，会被静默覆盖。
5. 返回值是只包含输出列名的列表，不是单个字符串。
6. 使用 `APILLMServing_request` 时，`api_url` 应指向 embedding 端点，例如 `/v1/embeddings`，而不是 `/v1/chat/completions`。
7. 仅仅是 `LLMServingABC` 子类还不够，必须实际实现 `generate_embedding_from_input(...)` 方法。

## 7. 典型用法

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
