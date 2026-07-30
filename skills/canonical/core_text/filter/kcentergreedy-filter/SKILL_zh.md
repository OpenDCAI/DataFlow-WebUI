---
name: kcentergreedy-filter
description: >-
  KCenterGreedyFilter 算子参考文档。涵盖构造函数、K-Center Greedy 算法行为、
  embedding serving 要求、以及流水线使用说明。

  使用场景：使用 embedding 向量通过语义多样性对大型数据集进行降采样。
---

# KCenterGreedyFilter 算子参考

`KCenterGreedyFilter` 使用 K-Center Greedy 算法选择最多样化的 `num_samples` 行，删除所有其他行。

## 1. 导入

```python
from dataflow.operators.core_text import KCenterGreedyFilter
from dataflow.serving import APILLMServing_request
```

## 2. Embedding Serving 选项

### 选项 A: 使用 `APILLMServing_request` 的远程 API

```python
APILLMServing_request(
    api_url="https://api.openai.com/v1/embeddings",
    key_name_of_api_key="DF_API_KEY",
    model_name="text-embedding-3-small",
    max_workers=20,
)
```

### 选项 B: 使用 `LocalEmbeddingServing` 的本地模型

```python
LocalEmbeddingServing(
    model_name="all-MiniLM-L6-v2",
    device=None,
    max_workers=2,
)
```

### 选项 C: 使用 `LiteLLMServing` 的通用 API

```python
LiteLLMServing(
    serving_type="embedding",
    model_name="text-embedding-3-small",
    key_name_of_api_key="DF_API_KEY",
    max_workers=10,
)
```

### 选项 D: 使用 `LocalModelLLMServing_vllm` 的本地 vLLM

```python
LocalModelLLMServing_vllm(
    hf_model_name_or_path="your-embedding-capable-model",
    vllm_tensor_parallel_size=1,
)
```

### Serving 说明

算子调用 `embedding_serving.generate_embedding_from_input(texts)`。任何实现此方法的 serving 对象均可使用。

支持：`APILLMServing_request`、`LocalEmbeddingServing`、`LiteLLMServing`、`LocalModelLLMServing_vllm`

不支持：`LocalModelLLMServing_sglang`（抛出 `NotImplementedError`）

## 3. 构造函数

```python
KCenterGreedyFilter(
    num_samples=1000,
    embedding_serving=embedding_serving,
)
```

| 参数 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `num_samples` | 是 | None | 要保留的行数；必须 ≤ DataFrame 总行数。 |
| `embedding_serving` | 否 | `None` | 实现 `generate_embedding_from_input(...)` 的 embedding 服务对象。如使用 `APILLMServing_request`，必须指向 `/v1/embeddings` 端点。 |

### 构造函数重要说明

1. **参数顺序**：源码签名为 `__init__(self, num_samples, embedding_serving=None)`。
2. `num_samples` 是第一个位置参数。
3. `embedding_serving` 是第二个参数，默认值为 `None`。

### Serving 说明

算子调用 `embedding_serving.generate_embedding_from_input(texts)`。serving 对象必须实现此方法。

## 4. run() 方法签名

```python
selected_keys = op.run(
    storage=self.storage.step(),
    input_key="content",
)
# 返回值: [input_key]
```

| 参数 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `storage` | 是 | None | `DataFlowStorage` 步骤对象。 |
| `input_key` | 否 | `"content"` | 用于计算 embedding 的文本列；必须已存在。 |

### 返回值

返回 `[self.input_key]`（列表）。流水线 `forward()` 方法不应返回值。

## 5. 实际运行逻辑

源码行为：

1. 将 `input_key` 存储到 `self.input_key`。
2. 从 `storage.read("dataframe")` 读取 DataFrame。
3. 验证 `input_key` 列存在。
4. 提取文本列表：`texts = dataframe[input_key].tolist()`。
5. 调用 `self.embedding_serving.generate_embedding_from_input(texts)` 获取 embeddings。
6. 将 embeddings 转换为 torch tensor。
7. 计算 `sampling_ratio = num_samples / len(texts)`。
8. 使用 `KCenterGreedy` 算法选择 `num_samples` 个多样化的行索引。
9. 创建二进制掩码，仅保留选中的行。
10. 通过 `storage.write(dataframe)` 写回过滤后的 DataFrame。
11. 返回 `[self.input_key]`。

### 关键行为说明

1. `num_samples` 必须 ≤ 当前 DataFrame 行数。
2. `embedding_serving` 必须实现 `generate_embedding_from_input(...)`。
3. 对于 `APILLMServing_request`，`api_url` 必须指向 `/v1/embeddings`，而非 `/v1/chat/completions`。
4. 过滤不可逆——未选中的行将被永久删除。

## 6. 流水线使用示例

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

注意：`forward()` 无返回值，遵循标准流水线模式。
