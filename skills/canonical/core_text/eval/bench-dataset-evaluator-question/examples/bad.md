# Bad Examples: BenchDatasetEvaluatorQuestion

## Comparing answer_match_result to a boolean when support_subquestions=True

```python
evaluator = BenchDatasetEvaluatorQuestion(support_subquestions=True, ...)
evaluator.run(...)

df[df["answer_match_result"] == True]   # always empty — value is a string, not a bool
```

When `support_subquestions=True` the `answer_match_result` column contains strings in `"correct/total"` format, not booleans; comparing to `True` always yields `False`.

---

## Using BenchDatasetEvaluatorQuestion when no question field is needed

```python
BenchDatasetEvaluatorQuestion(...)   # data has no question column
```

When `input_question_key` is not relevant to the evaluation task, using this operator adds unnecessary complexity; `BenchDatasetEvaluator` handles the common case without requiring a question column.
