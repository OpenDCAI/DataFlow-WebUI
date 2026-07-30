# Bad Examples: BenchAnswerGenerator

## prompt_template not passed explicitly

```python
BenchAnswerGenerator(
    eval_type="key2_qa",
    llm_serving=llm
    # prompt_template omitted
)
```

The `@prompt_restrict` decorator raises `TypeError` at construction time if `prompt_template` is not explicitly provided; passing `prompt_template=None` is required when no custom template is needed.

---

## eval_type mismatch with the evaluator

```python
generator = BenchAnswerGenerator(eval_type="key2_qa", llm_serving=llm)
evaluator = UnifiedBenchDatasetEvaluator(eval_type="key3_q_choices_a", ...)
```

Mismatched `eval_type` values mean the evaluator expects columns that the generator never produced, causing a missing-column error.

---

## Output column already exists with allow_overwrite=False

```python
generator = BenchAnswerGenerator(
    eval_type="key2_qa",
    llm_serving=llm,
    allow_overwrite=False    # default
)
generator.run(storage=..., output_key="generated_ans")
# DataFrame already has "generated_ans" — generation is silently skipped
```

With `allow_overwrite=False` (the default), a pre-existing output column causes the generator to return an empty list with no error, leaving stale values in place.
