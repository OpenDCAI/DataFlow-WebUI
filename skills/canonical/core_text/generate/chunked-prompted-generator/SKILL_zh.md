---
name: chunked-prompted-generator
description: >-
  ChunkedPromptedGenerator 算子的参考文档。涵盖构造参数、基于文件路径的分块流程、
  真实 prompt 构造方式，以及输出文件写回行为。

  适用场景：DataFrame 中存放的是文件路径，文件内容可能超过单次 LLM 上下文窗口，
  且你希望将生成结果写入新的文本文件。
---

# ChunkedPromptedGenerator 算子参考

`ChunkedPromptedGenerator` 会从 DataFrame 的文件路径列中读取文件，加载文件内容，
递归切分超长文本，调用 LLM 处理所有 chunk，再用分隔符拼接每行对应的生成结果，
写入新的文本文件，并把输出文件路径写回 DataFrame。

## 1. 导入方式

```python
from dataflow.operators.core_text import ChunkedPromptedGenerator
```

## 2. 构造函数

```python
ChunkedPromptedGenerator(
    llm_serving=llm,
    system_prompt="You are a helpful agent.",
    json_schema=None,
    max_chunk_len=128000,
    enc=tiktoken.get_encoding("cl100k_base"),
    separator="\n",
)
```

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `llm_serving` | 是 | None | 实现了 `generate_from_input(...)` 的 LLM 服务对象 |
| `system_prompt` | 否 | `"You are a helpful agent."` | 会作为普通文本前缀拼接到每个 chunk 前面 |
| `json_schema` | 否 | `None` | 可选，会透传给 `generate_from_input(...)` |
| `max_chunk_len` | 否 | `128000` | 每个 chunk 的最大 token 数 |
| `enc` | 否 | `tiktoken.get_encoding("cl100k_base")` | 用于通过 `len(enc.encode(text))` 计算 token 数的编码器 |
| `separator` | 否 | `"\n"` | 用于拼接各 chunk 输出结果的分隔符 |


## 3. run() 签名

```python
op.run(
    storage=self.storage.step(),
    input_path_key="file_path",
    output_path_key="output_path",
)
# 返回值：output_path_key
```

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `storage` | 是 | None | 当前算子步骤对应的 storage 对象 |
| `input_path_key` | 是 | None | 存放输入文件路径的列名 |
| `output_path_key` | 是 | None | 用于保存生成后输出文件路径的列名 |

## 4. 真实执行逻辑

当前实现的执行过程如下：

1. 从 `storage` 读取 DataFrame。
2. 对每一行，用 `Path(row[input_path_key]).read_text(encoding="utf-8")` 读取文件内容。
3. 用 `len(enc.encode(text))` 计算 token 数。
4. 如果文本超过 `max_chunk_len`，则按字符位置二分递归切分，而不是按句子或 token 边界切分。
5. 对每个 chunk，构造一条 LLM 输入：

```python
system_prompt + "\n" + chunk
```

6. 将所有行的所有 chunk 展平成一个全局批次。
7. 调用：

```python
llm_serving.generate_from_input(all_llm_inputs)
```

如果设置了 `json_schema`，则调用：

```python
llm_serving.generate_from_input(all_llm_inputs, json_schema=json_schema)
```

8. 再按原始行把响应重新聚合回去。
9. 对每一行，用配置的分隔符把该行所有 chunk 的生成结果拼接起来。
10. 将拼接结果写入一个自动推导的新文件，路径规则为：

```python
row[input_path_key].split(".")[0] + "_llm_output.txt"
```

11. 将这个输出文件路径写入 `output_path_key`。
12. 通过 `storage.write(dataframe)` 持久化 DataFrame，并返回 `output_path_key`。

## 5. 关键规则

1. `input_path_key` 列中的值必须是可读的文件系统路径，不能是内联文本。
2. `input_path_key` 和 `output_path_key` 都是运行时必填参数，源码中没有默认值。
3. 分块策略是“基于 token 长度判定、按字符中点递归二分”，不是语义切分。
4. 输出文件名会根据输入路径自动推导，并统一追加 `_llm_output.txt` 后缀；`output_path_key` 列里原本的值不会决定实际写入位置。
5. 如果全局生成失败，当前实现仍会为每一行创建推导出的输出文件，只是文件内容为空字符串。
6. 所有行的 chunk 会先合并成一个全局批次发送给 LLM，再按行重新切回。

## 6. 典型用法

```python
import tiktoken

from dataflow.operators.core_text import ChunkedPromptedGenerator

generator = ChunkedPromptedGenerator(
    llm_serving=self.llm_serving,
    system_prompt="Please summarize the following text.",
    max_chunk_len=4096,
    enc=tiktoken.get_encoding("cl100k_base"),
    separator="\n\n",
)

generator.run(
    storage=self.storage.step(),
    input_path_key="file_path",
    output_path_key="output_path",
)
```
