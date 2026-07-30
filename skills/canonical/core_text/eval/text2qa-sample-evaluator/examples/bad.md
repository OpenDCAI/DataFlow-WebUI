# Bad Examples: Text2QASampleEvaluator

## Passing input_key instead of input_question_key and input_answer_key

```python
self.evaluator.run(
    storage=self.storage.step(),
    input_key="generated_question_answer"  # no such parameter — raises TypeError
)
```

`Text2QASampleEvaluator` has no `input_key`; the constructor requires `input_question_key` and `input_answer_key` as separate parameters.

---

## Expecting singular output column names (grade, feedback)

```python
# Downstream code references columns "question_quality_grade" expecting singular suffix
df["question_quality_grade"]   # KeyError if the column was never produced under that name
```

Output columns use the plural suffixes `grades` and `feedbacks` (e.g., `question_quality_grades`, `question_quality_feedbacks`); referencing the singular form raises `KeyError`.

---

## Output columns already exist in the DataFrame

```python
self.evaluator.run(
    storage=self.storage.step(),
    input_question_key="question",
    input_answer_key="answer"
    # DataFrame already has "question_quality_grades" from a previous run
)
```

If any of the output columns already exist, `ValueError` is raised immediately before any evaluation runs.
