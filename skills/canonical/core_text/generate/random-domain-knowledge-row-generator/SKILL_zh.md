---
name: random-domain-knowledge-row-generator
description: >-
  RandomDomainKnowledgeRowGenerator 算子参考文档。

  [用途] 使用同一个领域生成 prompt 重复调用 LLM，并把生成结果写入已有
  DataFrame 的某一列。

  [适用场景] 当你已经有一个行数确定的 seed DataFrame，希望按固定条数生成领域
  内容并写入一个输出列时使用。如果你需要基于已有字段逐行构造 prompt，应改用
  PromptedGenerator 或 FormatStrPromptedGenerator。
---

# RandomDomainKnowledgeRowGenerator 算子说明

`RandomDomainKnowledgeRowGenerator` 不会读取任何输入列的值，但它仍然会读取输入 DataFrame 本身。该算子会根据 `domain_keys` 构造 `generation_num` 个 prompt，调用 `llm_serving.generate_from_input(...)`，然后把返回结果写入 `dataframe[output_key]`。

可运行示例见 `examples/good.md`，常见错误见 `examples/bad.md`。

---

## 1. 导入

```python
from dataflow.operators.core_text import RandomDomainKnowledgeRowGenerator
from dataflow.prompts.general_text import SFTFromScratchGeneratorPrompt
```

---

## 2. 构造函数

```python
RandomDomainKnowledgeRowGenerator(
    llm_serving=llm,
    generation_num=200,
    domain_keys="machine learning, deep learning, neural networks",
    prompt_template=SFTFromScratchGeneratorPrompt(),
)
```

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `llm_serving` | 是 | None | LLM 服务对象，必须实现 `generate_from_input(user_inputs, ...)`。`dataflow.serving` 中常见可用实现包括 `APILLMServing_request`、`LiteLLMServing`、`LocalModelLLMServing_vllm`。 |
| `generation_num` | 是 | None | 要构造多少个 prompt，也就是期望 LLM 返回多少条结果。 |
| `domain_keys` | 是 | None | 直接传给 `SFTFromScratchGeneratorPrompt.build_prompt(domain_keys)` 的领域描述。源码类型标注是 `str`，因此应传字符串，例如 `"finance, accounting, tax"`。 |
| `prompt_template` | 必须提供 | `None` | 每次生成时使用的 prompt 对象。实际使用时必须传入实例化后的 `SFTFromScratchGeneratorPrompt()`，或其他被 `@prompt_restrict(...)` 允许的 prompt。若保留为 `None`，会在生成前直接报错。 |

### 构造函数注意事项

1. `prompt_template=None` 不是安全默认值。源码会直接调用 `self.prompt_template.build_prompt(self.domain_keys)`，因此传 `None` 会触发 `AttributeError`。
2. 默认 prompt 类是 `SFTFromScratchGeneratorPrompt`，其 `build_prompt()` 期望接收 `domain_keys: str`。
3. 该 prompt 会要求 LLM 输出单行 JSON，包含 `instruction`、`input`、`output`、`domain` 等字段。

---

## 3. run() 签名

```python
output_key = op.run(
    storage=self.storage.step(),
    output_key="generated_content",
)
```

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `storage` | 是 | None | `DataFlowStorage` / `FileStorage` 的 step 对象。算子会从这里读取 DataFrame，再把更新后的 DataFrame 写回去。 |
| `output_key` | 否 | `"generated_content"` | 用于存放生成结果的列名。 |

### 返回值

该方法返回字符串 `output_key`。

---

## 4. 实际运行逻辑

源码中的真实行为是：

1. 从 `storage.read("dataframe")` 读取当前 DataFrame。
2. 忽略该 DataFrame 中所有列值。
3. 重复调用 `prompt_template.build_prompt(domain_keys)` 共 `generation_num` 次，构造 prompt 列表。
4. 调用 `llm_serving.generate_from_input(llm_inputs)`。
5. 将返回结果赋值给 `dataframe[output_key]`。
6. 把更新后的 DataFrame 写回 storage，并返回 `output_key`。



---

## 5. 关键约束

1. `len(dataframe)` 应与 `generation_num` 一致，否则 `dataframe[output_key] = generated_outputs` 可能触发 pandas 的长度不匹配错误。
2. 当前实现下，空 seed 文件配合 `generation_num > 0` 并不安全。算子依然只是往现有 DataFrame 写列，而不是自动补行。

---

## 6. 使用建议

适合使用本算子的情况：

- 你希望对现有每一行 seed 生成一条领域样本。
- 行内容本身不参与 prompt，只需要利用现有行数和一个输出列。
- 你希望使用默认的 `SFTFromScratchGeneratorPrompt` 来生成领域化 SFT 样本。

不适合使用本算子的情况：

- 你需要基于已有列构造 prompt。
- 你期待算子能从空 DataFrame 自动创建新行。
- 你需要根据不同输入字段为每一行生成不同领域内容。
