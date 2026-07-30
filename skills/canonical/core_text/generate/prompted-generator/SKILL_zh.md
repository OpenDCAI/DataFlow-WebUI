---
name: prompted-generator
description: >-
  PromptedGenerator 算子的参考文档。涵盖构造参数、run() 签名、真实逐行处理逻辑
  与 pipeline 接入说明。
  适用场景：在 DataFlow pipeline 中接入单字段 LLM 生成算子。
---

# PromptedGenerator 算子参考

`PromptedGenerator` 是 DataFlow 中最基础的单字段 LLM 生成算子。

它会从当前 DataFrame 中按行读取 `input_key` 对应的值；如果该值为真值，就构造一条LLM 输入：

```python
user_prompt + str(row[input_key])
```

然后批量调用 `llm_serving.generate_from_input(...)`，并把生成结果写入 `output_key`。

## 1. 导入方式

```python
from dataflow.operators.core_text import PromptedGenerator
```

## 2. 构造函数

```python
PromptedGenerator(
    llm_serving,                               # 必填
    system_prompt="You are a helpful agent.",  # 可选
    user_prompt="",                            # 可选
    json_schema=None,                          # 可选
)
```

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `llm_serving` | 是 | None | 实现了 `generate_from_input(...)` 的 LLM 服务对象 |
| `system_prompt` | 否 | `"You are a helpful agent."` | 传给 serving 层的 system prompt |
| `user_prompt` | 否 | `""` | 会直接拼接在每个有效输入文本前面 |
| `json_schema` | 否 | `None` | 可选，会原样透传给 serving 层 |

## 3. run() 签名

```python
op.run(
    storage=self.storage.step(),
    input_key="raw_content",
    output_key="generated_content",
)
# 返回值：output_key
```

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `storage` | 是 | None | 当前算子步骤对应的 storage 对象 |
| `input_key` | 否 | `"raw_content"` | 从当前 DataFrame 读取的列名 |
| `output_key` | 否 | `"generated_content"` | 回写到 DataFrame 的列名 |

## 4. 真实执行逻辑

这个算子实际会执行以下步骤：

1. 从 `storage` 读取当前 DataFrame。
2. 按行遍历 DataFrame。
3. 对每一行读取 `raw_content = row.get(input_key, "")`。
4. 只有当 `raw_content` 为真值时，才会把 `user_prompt + str(raw_content)` 加入批量 LLM 输入列表。
5. 调用：

```python
llm_serving.generate_from_input(
    user_inputs=llm_inputs,
    system_prompt=system_prompt,
    json_schema=json_schema,
)
```

6. 将生成结果写入 `dataframe[output_key]`。
7. 通过 `storage.write(dataframe)` 持久化更新后的 DataFrame。
8. 返回 `output_key`。

## 5. 关键规则

1. `input_key` 必须已经存在于当前 DataFrame 中。
2. `user_prompt` 只是普通字符串前缀，不是模板引擎。
3. 实现中会跳过 `input_key` 值为空字符串、`None` 或其他假值的行，不会为这些行构造 LLM 输入。


## 6. 典型用法

```python
from dataflow.operators.core_text import PromptedGenerator

prompted_gen = PromptedGenerator(
    llm_serving=self.llm_serving,
    system_prompt="You are a helpful agent.",
    user_prompt="请将下面内容总结成一句话：\n",
)

prompted_gen.run(
    storage=self.storage.step(),
    input_key="raw_content",
    output_key="summary",
)
```

## 7. 返回值

```python
return output_key
```

该返回值通常用于下游算子继续引用。
