---
name: random-domain-knowledge-row-generator
description: >-
  Reference documentation for the RandomDomainKnowledgeRowGenerator operator.

  [Purpose] Calls an LLM repeatedly with the same domain-generation prompt and
  writes the generated results into one column of an existing DataFrame.

  [When to use] Use it when you already have a seed DataFrame with the exact
  target row count and want to fill one output column with domain-specific
  generated content. If you need to build prompts from existing row fields, use
  PromptedGenerator or FormatStrPromptedGenerator instead.
---

# RandomDomainKnowledgeRowGenerator Operator Reference

`RandomDomainKnowledgeRowGenerator` does not read any input column values, but it still reads the input DataFrame itself. The operator builds `generation_num` prompts from `domain_keys`, calls `llm_serving.generate_from_input(...)`, and assigns the returned list into `dataframe[output_key]`.

See `examples/good.md` for a runnable example and `examples/bad.md` for common failure cases.

---

## 1. Import

```python
from dataflow.operators.core_text import RandomDomainKnowledgeRowGenerator
from dataflow.prompts.general_text import SFTFromScratchGeneratorPrompt
```

---

## 2. Constructor

```python
RandomDomainKnowledgeRowGenerator(
    llm_serving=llm,
    generation_num=200,
    domain_keys="machine learning, deep learning, neural networks",
    prompt_template=SFTFromScratchGeneratorPrompt(),
)
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `llm_serving` | Yes | None | LLM serving object. It must implement `generate_from_input(user_inputs, ...)`. Examples in `dataflow.serving` include `APILLMServing_request`, `LiteLLMServing`, and `LocalModelLLMServing_vllm`. |
| `generation_num` | Yes | None | Number of prompts to build and number of outputs expected from the LLM call. |
| `domain_keys` | Yes | None | Domain description passed directly into `SFTFromScratchGeneratorPrompt.build_prompt(domain_keys)`. The source annotation is `str`, so use a string such as `"finance, accounting, tax"`. |
| `prompt_template` | No in signature, but effectively required | `None` | Prompt object used for every generation call. In practice you must pass an instantiated `SFTFromScratchGeneratorPrompt()` or another prompt allowed by `@prompt_restrict(...)`. Leaving it as `None` will fail before generation starts. |

### Important Constructor Notes

1. `prompt_template=None` is not a safe fallback. The code calls `self.prompt_template.build_prompt(self.domain_keys)` directly, so `None` raises `AttributeError`.
2. The default prompt class is `SFTFromScratchGeneratorPrompt`, and its `build_prompt()` method expects `domain_keys: str`.
3. The prompt asks the LLM to output a single-line JSON object containing fields such as `instruction`, `input`, `output`, and `domain`.

---

## 3. run() Signature

```python
output_key = op.run(
    storage=self.storage.step(),
    output_key="generated_content",
)
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `storage` | Yes | None | `DataFlowStorage` / `FileStorage` step object. The operator reads a DataFrame from here and writes the updated DataFrame back. |
| `output_key` | No | `"generated_content"` | Column name used to store generated results. |

### Return Value

The method returns the string `output_key`.

---

## 4. Actual Runtime Logic

The source code behavior is:

1. Read the current DataFrame from `storage.read("dataframe")`.
2. Ignore all column values in that DataFrame.
3. Build `generation_num` prompts by repeatedly calling `prompt_template.build_prompt(domain_keys)`.
4. Call `llm_serving.generate_from_input(llm_inputs)`.
5. Assign the returned list to `dataframe[output_key]`.
6. Write the updated DataFrame back to storage and return `output_key`.



---

## 5. Critical Constraints

1. `len(dataframe)` should match `generation_num`. Otherwise `dataframe[output_key] = generated_outputs` can fail with a pandas length-mismatch error.
2. An empty seed file plus `generation_num > 0` is not safe for the current implementation. The operator still writes back into the existing DataFrame instead of creating rows.


---

## 6. Usage Guidance

Use this operator when:

- You want one generated sample per existing seed row.
- The row contents are irrelevant, and you only need the row count plus an output column.
- You want the default `SFTFromScratchGeneratorPrompt` behavior for domain-focused SFT sample generation.

Do not use this operator when:

- You need prompts built from existing columns.
- You expect the operator to create rows from an empty DataFrame.
- You need per-row domain variation based on different input fields.
