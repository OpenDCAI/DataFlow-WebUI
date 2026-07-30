# Bad Examples: UnifiedBenchDatasetEvaluator

## eval_type mismatch with BenchAnswerGenerator

```python
generator = BenchAnswerGenerator(eval_type="key2_qa", llm_serving=llm)
evaluator = UnifiedBenchDatasetEvaluator(eval_type="key3_q_choices_a")

generator.run(storage=..., input_question_key="question", output_key="generated_ans")
evaluator.run(
    storage=...,
    input_choices_key="choices",   # column absent in key2 data format
    input_label_key="label"        # column absent in key2 data format
)
```

When generator and evaluator use different `eval_type` values the expected columns are absent, causing a missing-column error.

---

## key3 type missing input_choices_key or input_label_key

```python
evaluator = UnifiedBenchDatasetEvaluator(eval_type="key3_q_choices_a")
evaluator.run(
    storage=...,
    input_question_key="question",
    input_pred_key="generated_ans"
    # input_choices_key omitted
    # input_label_key omitted
)
```

`key3_q_choices_a` requires both `input_choices_key` and `input_label_key`; omitting either raises a missing-column error.

---

## use_semantic_judge=True with llm_serving=None

```python
evaluator = UnifiedBenchDatasetEvaluator(
    eval_type="key2_qa",
    use_semantic_judge=True,
    llm_serving=None    # no LLM provided
)
```

Semantic judging requires an LLM serving instance; passing `None` raises an error when the evaluator attempts to call the model.
