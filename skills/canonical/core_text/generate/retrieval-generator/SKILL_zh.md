---
name: retrieval-generator
description: >-
  RetrievalGenerator 算子说明文档。

  [用途] 从 storage 的某一列读取文本，把其中非空行整理成 `llm_inputs`，
  调用 `llm_serving.generate_from_input(...)`，再把返回结果写入新的输出列。

  [默认后端] 默认使用 `LightRAGServing`。

  [重要说明] `run()` 是异步方法。算子本身不会初始化 serving 对象，
  它只会调用
  `await llm_serving.generate_from_input(llm_inputs, system_prompt)`。
---

# RetrievalGenerator 算子说明

`RetrievalGenerator` 是一个异步算子。它会从某一列读取文本，只收集 truthy 的输入值，然后调用 `await self.llm_serving.generate_from_input(llm_inputs, self.system_prompt)`，最后把返回结果写入 `output_key`。

可参考 `examples/good.md` 查看正确用法，参考 `examples/bad.md` 查看常见错误。

---

## 1. 导入

```python
from dataflow.operators.core_text import RetrievalGenerator
from dataflow.serving import LightRAGServing
```

---

## 2. 构造函数

```python
RetrievalGenerator(
    llm_serving=serving,
    system_prompt="You are a helpful agent.",
)
```

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `llm_serving` | 是 | None | 直接保存到 `self.llm_serving`，不会做额外校验。`run()` 中会调用 `await self.llm_serving.generate_from_input(llm_inputs, self.system_prompt)`。 |
| `system_prompt` | 否 | `"You are a helpful agent."` | 直接保存到 `self.system_prompt`，并在生成时原样传给 `generate_from_input(...)`。 |

### 说明

1. 这个算子不会替你初始化 serving 后端。
2. 调用 `run()` 前，`llm_serving` 必须已经可用。
3. 默认建议使用 `LightRAGServing`。

---

## 3. 默认 LightRAGServing 初始化方式

如果你按默认推荐使用 `LightRAGServing`，请先完成初始化，再传给 `RetrievalGenerator`：

```python
llm_serving = await LightRAGServing.create(
    api_url="https://api.openai.com/v1",
    llm_model_name="gpt-4o",
    embed_model_name="bge-m3:latest",
    embed_binding_host="http://localhost:11434",
    document_list=["knowledge_base.txt"],
)
if llm_serving is None:
    raise RuntimeError("LightRAGServing initialization failed.")
```


- `LightRAGServing.__init__()` 支持的参数是 `api_url`、`key_name_of_api_key`、`llm_model_name`、`embed_model_name`、`embed_binding_host`、`embedding_dim`、`max_embed_tokens`、`document_list`。
- `LightRAGServing.create(...)` 会创建 `self.rag` 并加载 `document_list` 中的文档。
- 环境变量里必须存在 `DF_API_KEY`，否则初始化时会抛出 `ValueError`。
- 如果 `create(...)` 中加载文档失败，会记录日志并返回 `None`。


---

## 4. run() 方法签名

```python
await op.run(
    storage=storage,
    input_key="raw_content",
    output_key="generated_content",
)
```

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `storage` | 是 | None | 会被用于 `storage.read("dataframe")` 和 `storage.write(df)`。 |
| `input_key` | 否 | `"raw_content"` | 每行通过 `row.get(input_key, "")` 读取。只有 truthy 的值才会进入 `llm_inputs`。 |
| `output_key` | 否 | `"generated_content"` | 最终通过 `df[output_key] = generated_outputs` 写回。 |

### 返回值

成功时返回字符串 `output_key`。

如果 `generate_from_input(...)` 抛异常，算子会记录日志并返回 `None`。

---

## 5. 真实运行逻辑

1. 把 `input_key` 和 `output_key` 保存到 `self`。
2. 通过 `storage.read("dataframe")` 读取 DataFrame。
3. 逐行遍历数据。
4. 每行使用 `row.get(input_key, "")` 取值。
5. 只有当该值为 truthy 时，才执行 `str(raw_content)` 并加入 `llm_inputs`。
6. 调用 `generated_outputs = await self.llm_serving.generate_from_input(llm_inputs, self.system_prompt)`。
7. 执行 `df[output_key] = generated_outputs`。
8. 通过 `storage.write(df)` 写回结果。
9. 返回 `output_key`。

对于被跳过的空行，源码没有补位逻辑。

---

## 6. 关键约束

1. `run()` 是异步方法，必须使用 `await`。
2. `input_key` 对应列中的空值或 falsy 值会在生成前被跳过。
