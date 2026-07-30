# Bad Examples: BenchDatasetEvaluator

## prompt_template omitted or not passed explicitly

```python
BenchDatasetEvaluator(
    compare_method="match",
    eval_result_path="./result.json",
    # prompt_template not provided
)
```

The `@prompt_restrict` decorator raises `TypeError` at construction time when `prompt_template` is absent; it must always be passed explicitly as an `AnswerJudgePrompt()` instance.

---

## Using match mode for natural language answers

```python
BenchDatasetEvaluator(
    compare_method="match",
    prompt_template=AnswerJudgePrompt(),
)
# {"generated_cot": "Paris", "golden_answer": "Paris"} -> answer_match_result: False
```

Match mode uses `math_verify` internally; `math_verify.parse("Paris")` returns `[]`, so all natural language answers evaluate as non-matching even when they are identical.
