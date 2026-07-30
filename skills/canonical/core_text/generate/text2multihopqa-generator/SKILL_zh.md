---
name: text2multihopqa-generator
description: >-
  Text2MultiHopQAGenerator 算子说明文档。

  [用途] 从某一列文本生成多跳 QA，并输出两列：`QA_pairs` 和元数据列。

  [适用场景] 适合从较长文本中构造多步推理问答数据。如果只需要简单单跳 QA，
  优先使用 `Text2QAGenerator`。
---

# Text2MultiHopQAGenerator 算子说明

`Text2MultiHopQAGenerator` 会读取一列文本，为每一行生成最多 `num_q` 条多跳 QA，把每行的 QA 列表写入 `output_key`，把元数据写入 `output_meta_key`，然后过滤掉 QA 列表为空的行。

可参考 `examples/good.md` 查看正确用法，参考 `examples/bad.md` 查看常见错误。

---

## 1. 导入

```python
from dataflow.operators.core_text import Text2MultiHopQAGenerator
```

---

## 2. 构造函数

```python
Text2MultiHopQAGenerator(
    llm_serving=llm,
    seed=0,
    lang="en",
    prompt_template=None,
    num_q=5,
)
```

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `llm_serving` | 是 | None | 传给 `ExampleConstructor`，后续会调用它的 `generate_from_input(...)`。 |
| `seed` | 否 | `0` | 用于初始化 `random.Random(seed)`。 |
| `lang` | 否 | `"en"` | 控制 prompt 构造和句子切分逻辑。 |
| `prompt_template` | 否 | `None` | 不传时默认使用 `Text2MultiHopQAGeneratorPrompt(lang=self.lang)`。 |
| `num_q` | 否 | `5` | 每行最终最多保留多少条 QA。 |

---

## 3. run() 方法签名

```python
op.run(
    storage=self.storage.step(),
    input_key="cleaned_chunk",
    output_key="QA_pairs",
    output_meta_key="QA_metadata",
)
```

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `storage` | 是 | None | 会被用于 `storage.read("dataframe")` 和 `storage.write(dataframe)`。 |
| `input_key` | 否 | `"cleaned_chunk"` | 输入文本列，必须已经存在。 |
| `output_key` | 否 | `"QA_pairs"` | 输出列，保存每一行的 QA 字典列表。该列不能预先存在。 |
| `output_meta_key` | 否 | `"QA_metadata"` | 输出列，保存每一行的 metadata 字典。 |

### 返回值

该方法返回 `[output_key]`。

---

## 4. 真实运行逻辑

源码中的执行流程如下：

1. 从 storage 读取 DataFrame。
2. 校验 `input_key` 是否存在。
3. 校验 `output_key` 是否已存在。
4. 取出 `dataframe[input_key].tolist()` 作为输入文本。
5. 通过 `process_batch(...)` 为每一行生成结果。
6. 把每行的 `qa_pairs` 截断到最多 `num_q` 条。
7. 把 QA 列表写入 `output_key`，把 metadata 写入 `output_meta_key`。
8. 过滤掉 `output_key` 为空列表的行。
9. 将过滤后的 DataFrame 写回 storage。
10. 返回 `[output_key]`。

几个关键结论：

- 这个算子不会把一行展开成多行。
- 最终行数只会小于或等于输入行数，不会增加。
- 生成不到 QA 的行会被整体删除。

---

## 5. 文本过滤规则

在 `ExampleConstructor` 中，文本在生成 QA 之前可能因为以下原因被判定失败：

- 不是字符串，
- 长度小于 `100`，
- 长度大于 `200000`，
- 未通过基础句子数量检查或特殊字符比例检查。

一旦失败，该行会先得到空的 `qa_pairs`，随后在 `run()` 中被过滤掉。

---

## 6. 关键约束

1. `input_key` 必须存在，否则 `run()` 会抛出 `ValueError`。
2. `output_key` 不能预先存在，否则 `run()` 会抛出 `ValueError`。
