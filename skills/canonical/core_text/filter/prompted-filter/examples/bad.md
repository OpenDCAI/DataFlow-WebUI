# Bad Examples: PromptedFilter

## Scoring scale in system_prompt does not match min_score/max_score

```python
PromptedFilter(
    llm_serving=llm,
    system_prompt="Rate the quality from 1 to 10.",
    min_score=4,
    max_score=5    # LLM may return scores up to 10; scores 6-10 are all deleted
)
```

The LLM scores according to the prompt description; if `max_score` is lower than the prompt's upper bound, valid high-scoring rows are incorrectly discarded.

---

## Calling PromptedFilter on a column that already holds numeric scores

```python
PromptedFilter(llm_serving=llm, min_score=4, max_score=5).run(
    storage=self.storage.step(),
    input_key="score"   # "score" is already a numeric column
)
```

When the DataFrame already has a numeric score column, invoking the LLM again wastes cost and time; a rule-based filter is sufficient.
