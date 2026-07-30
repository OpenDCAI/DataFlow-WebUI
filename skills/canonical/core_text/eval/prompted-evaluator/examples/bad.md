# Bad Examples: PromptedEvaluator

## input_key column contains empty-value rows

```python
self.evaluator.run(
    storage=self.storage.step(),
    input_key="summary",      # some rows are empty strings
    output_key="quality_score"
)
```

Empty rows are skipped by the LLM, so the output list is shorter than the DataFrame, raising `ValueError`.

---

## Using PromptedEvaluator when the goal is to delete low-scoring rows

```python
self.evaluator = PromptedEvaluator(
    llm_serving=llm,
    system_prompt="Rate from 1 to 5."
)
self.evaluator.run(storage=self.storage.step(), input_key="text", output_key="score")
# all rows are retained; low-score rows are not removed
```

`PromptedEvaluator` only annotates scores; it never removes rows. Using it when filtering is the goal leaves unwanted rows in the dataset.
