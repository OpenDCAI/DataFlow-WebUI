---
name: format-str-prompted-generator
description: >-
  FormatStrPromptedGenerator 算子的参考文档。涵盖构造参数、prompt 模板约束、
  占位符到列名的映射方式、真实 prompt 构造逻辑，以及可运行示例用法。

  适用场景：单次生成任务需要把 DataFrame 中多个字段通过模板组合成一个 prompt。
---

# FormatStrPromptedGenerator 算子参考

`FormatStrPromptedGenerator` 是 DataFlow 中基于模板的多字段 LLM 生成算子。
它会把多列 DataFrame 数据映射到模板占位符中，为每一行构造一个 prompt，调用
LLM，把结果写入 `output_key`，持久化 DataFrame，并返回 `output_key` 字符串。

## 1. 导入方式

```python
from dataflow.operators.core_text import FormatStrPromptedGenerator
from dataflow.prompts.core_text import FormatStrPrompt
```

## 2. 构造函数

```python
FormatStrPromptedGenerator(
    llm_serving,
    system_prompt="You are a helpful agent.",
    prompt_template=FormatStrPrompt(f_str_template="..."),
    json_schema=None,
)
```

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `llm_serving` | 是 | None | 实现了 `generate_from_input(...)` 的 LLM 服务对象 |
| `system_prompt` | 否 | `"You are a helpful agent."` | 传给 serving 层的 system prompt |
| `prompt_template` | 实际上必填 | `FormatStrPrompt` | 必须传实例化后的 `FormatStrPrompt(...)` 或 `DIYPromptABC` 子类实例 |
| `json_schema` | 否 | `None` | 可选，会透传给 `generate_from_input(...)` |

### 关于 `prompt_template` 的重要说明

1. 源码默认值写的是 `FormatStrPrompt`，它是类对象，不是实例。
2. 这里也不能传 `prompt_template=None`。本算子会显式抛出：

```python
ValueError("prompt_template cannot be None")
```

3. 实际安全用法是始终显式传入一个实例化模板：

```python
FormatStrPrompt(
    f_str_template="Title: {title}\n\nBody: {body}\n\nSummarize this article."
)
```

### `FormatStrPrompt` 的构造方式

```python
FormatStrPrompt(
    f_str_template="{title}\n\n{body}",
    on_missing="raise",
)
```

## 3. run() 签名

```python
op.run(
    storage=self.storage.step(),
    output_key="generated_content",
    title="title_col",
    body="body_col",
)
# 返回值：output_key
```

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `storage` | 是 | None | 当前算子步骤对应的 storage 对象 |
| `output_key` | 否 | `"generated_content"` | 写入生成结果的列名 |
| `**input_keys` | 是 | None | 从模板占位符名到 DataFrame 列名的映射 |

### 占位符映射规则

在 `run(...)` 中，每个 kwarg 遵循如下约定：

- kwarg 名称 = `f_str_template` 中的占位符名称
- kwarg 值 = 当前 DataFrame 中实际读取的列名

例如：

```python
prompt_template = FormatStrPrompt(
    f_str_template="Title: {title}\n\nBody: {body}\n\nSummarize this article."
)

generator.run(
    storage=self.storage.step(),
    output_key="summary",
    title="headline_col",
    body="article_body_col",
)
```

这意味着：

- `{title}` 会被替换成 `row["headline_col"]`
- `{body}` 会被替换成 `row["article_body_col"]`

## 4. 真实执行逻辑

当前实现的执行过程如下：

1. 从 `storage` 读取 DataFrame。
2. 收集 `need_fields = set(input_keys.keys())`。
3. 对每一行构造：

```python
key_dict = {key: row[input_keys[key]] for key in need_fields}
```

4. 调用：

```python
prompt_text = prompt_template.build_prompt(need_fields, **key_dict)
```

5. 把每一行得到的 prompt 依次加入 `llm_inputs`。
6. 调用：

```python
llm_serving.generate_from_input(
    user_inputs=llm_inputs,
    system_prompt=self.system_prompt,
    json_schema=self.json_schema,
)
```

7. 将生成结果写入 `dataframe[output_key]`。
8. 通过 `storage.write(dataframe)` 持久化。
9. 返回 `output_key`。

## 5. 关键规则

1. 始终传入实例化后的 `FormatStrPrompt(...)` 或兼容的 DIY prompt 实例。
2. 不要省略 `prompt_template`，也不要传类对象本身，更不要传 `None`。
3. `**input_keys` 中每个 value 都必须是当前 DataFrame 中真实存在的列名。
4. 该算子不会自动把模板字符串中的占位符与 `run()` 参数做反向校验。如果模板中有占位符没有被映射，它可能会原样残留在最终 prompt 中。
5. 如果 `**input_keys` 中给了一个模板中根本没用到的 placeholder 名，这个值只是在字符串替换时不会生效，不会自动报错。
6. 算子只会新增或覆盖 `output_key` 列，不会过滤行。
7. 返回值是裸字符串 `output_key`，不是列表。

## 6. 典型用法

```python
from dataflow.operators.core_text import FormatStrPromptedGenerator
from dataflow.prompts.core_text import FormatStrPrompt

prompt_template = FormatStrPrompt(
    f_str_template="Title: {title}\n\nBody: {body}\n\nPlease write a concise summary."
)

generator = FormatStrPromptedGenerator(
    llm_serving=self.llm_serving,
    system_prompt="You are a professional editor. Write concise, informative summaries.",
    prompt_template=prompt_template,
)

generator.run(
    storage=self.storage.step(),
    output_key="summary",
    title="title",
    body="body",
)
```
