# Bad Examples: RandomDomainKnowledgeRowGenerator

## Passing `input_key` to `run()`

```python
self.generator.run(
    storage=self.storage.step(),
    input_key="text",
    output_key="generated_content",
)
```

`run()` only accepts `storage` and `output_key`. Passing `input_key` raises `TypeError`.

---

## Omitting `prompt_template`

```python
RandomDomainKnowledgeRowGenerator(
    llm_serving=llm,
    generation_num=100,
    domain_keys="machine learning",
    prompt_template=None,
)
```

The current implementation calls `self.prompt_template.build_prompt(...)` directly. `None` will raise `AttributeError`.

---

## Seed Row Count Does Not Match `generation_num`

```python
RandomDomainKnowledgeRowGenerator(
    llm_serving=llm,
    generation_num=100,
    domain_keys="machine learning, deep learning",
    prompt_template=SFTFromScratchGeneratorPrompt(),
)

# But the input DataFrame only has 10 rows.
```

The operator generates 100 outputs and then tries to assign them into a 10-row DataFrame column, which can fail with a pandas length-mismatch error.
