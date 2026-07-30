# Bad Examples: FormatStrPromptedGenerator

## kwarg key in run() does not match the template placeholder name

```python
self.generator = FormatStrPromptedGenerator(
    llm_serving=self.llm_serving,
    system_prompt="You are a summarizer.",
    prompt_template=FormatStrPrompt(
        f_str_template="Title: {title}\n\nBody: {content}"
    )
)

self.generator.run(
    storage=self.storage.step(),
    output_key="summary",
    headline="title",    # key is 'headline' but placeholder is {title}
    content="body"
)
```

The kwarg name `headline` does not match `{title}` in the template. In the current source, this does **not** reliably raise a template-field validation error. Instead, `{title}` can remain unreplaced in the final prompt, which is worse because the request may still run with a malformed prompt.

---

## prompt_template is None or omitted, or the class is passed instead of an instance

```python
FormatStrPromptedGenerator(
    llm_serving=self.llm_serving,
    prompt_template=None
)

FormatStrPromptedGenerator(
    llm_serving=self.llm_serving
    # prompt_template omitted
)

FormatStrPromptedGenerator(
    llm_serving=self.llm_serving,
    prompt_template=FormatStrPrompt
)
```

- `prompt_template=None` raises `ValueError`
- omitting `prompt_template` can raise `TypeError` because the source default is the class object `FormatStrPrompt`
- passing `FormatStrPrompt` directly is also invalid because it is a class, not an instantiated template
