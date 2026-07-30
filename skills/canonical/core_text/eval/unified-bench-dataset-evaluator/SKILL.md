---
name: unified-bench-dataset-evaluator
description: >-
  Reference documentation for the UnifiedBenchDatasetEvaluator operator.

  Use when: evaluating model answers on benchmark datasets.
---

# UnifiedBenchDatasetEvaluator Operator Reference

`UnifiedBenchDatasetEvaluator` supports 6 evaluation types (eval_type), scores generated answers, and writes 4 output columns.

## 1. Import

```python
from dataflow.operators.core_text import UnifiedBenchDatasetEvaluator
```

## 2. Constructor

```python
UnifiedBenchDatasetEvaluator(
    eval_type="key2_qa",
    llm_serving=None,
    prompt_template=None,
    eval_result_path=None,
    metric_type=None,
    use_semantic_judge=False,
    system_prompt="You are a helpful assistant specialized in evaluating answer correctness.",
)
```

**IMPORTANT**: Always pass `prompt_template=None` explicitly. The default value is `AnswerJudgePrompt` (the class itself), which triggers a `TypeError`.

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `eval_type` | No | `"key2_qa"` | Evaluation type |
| `llm_serving` | Conditional | `None` | Required when `use_semantic_judge=True` |
| `prompt_template` | No | `AnswerJudgePrompt` | Pass `None` to use built-in fallback |
| `eval_result_path` | No | Auto-generated | Statistics JSON file path |
| `metric_type` | No | `None` | Evaluation metric, auto-selected if not provided |
| `use_semantic_judge` | No | `False` | Use LLM for semantic judgment |
| `system_prompt` | No | `"You are a helpful assistant..."` | System prompt for LLM (used when `use_semantic_judge=True`) |

### eval_type and Required input_xxx_key

| eval_type | Required input_xxx_key |
|-----------|------------------------|
| `key1_text_score` | `input_text_key` |
| `key2_qa` | `input_question_key`, `input_target_key` |
| `key2_q_ma` | `input_question_key`, `input_targets_key` |
| `key3_q_choices_a` | `input_question_key`, `input_choices_key`, `input_label_key` |
| `key3_q_choices_as` | `input_question_key`, `input_choices_key`, `input_labels_key` |
| `key3_q_a_rejected` | `input_question_key`, `input_better_key`, `input_rejected_key` |

## 3. run() Signature

```python
op.run(
    storage=self.storage.step(),
    input_question_key="question",
    input_target_key="golden_answer",
    input_pred_key="generated_ans",
)
# returns: list of column names
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `storage` | Yes | None | Storage step object |
| `input_pred_key` | No | `"generated_ans"` | Model generated answer column |
| `input_question_key` | Conditional | `None` | Question column |
| `input_target_key` | Conditional | `None` | Single target answer column |
| `input_targets_key` | Conditional | `None` | Multiple target answers column |
| `input_choices_key` | Conditional | `None` | Choices column |
| `input_label_key` | Conditional | `None` | Single label column |
| `input_labels_key` | Conditional | `None` | Multiple labels column |
| `input_better_key` | Conditional | `None` | Preferred answer column |
| `input_rejected_key` | Conditional | `None` | Rejected answer column |
| `input_context_key` | No | `None` | Optional context column for additional information |

## 4. Output Columns (4 columns)

- `eval_valid`: Boolean column indicating if evaluation is valid
- `eval_error`: Error message column
- `eval_pred`: Parsed prediction column
- `eval_score`: Numeric score column

## 5. Usage Example

```python
from dataflow.operators.core_text import UnifiedBenchDatasetEvaluator
from dataflow.serving import APILLMServing_request
from dataflow.utils.storage import FileStorage

class MyPipeline:
    def __init__(self):
        self.storage = FileStorage(
            first_entry_file_name="./data/bench.jsonl",
            cache_path="./cache",
            file_name_prefix="step",
            cache_type="jsonl"
        )

        self.llm_serving = APILLMServing_request(
            api_url="https://api.openai.com/v1/chat/completions",
            key_name_of_api_key="DF_API_KEY",
            model_name="gpt-4o",
            max_workers=10
        )

        self.evaluator = UnifiedBenchDatasetEvaluator(
            eval_type="key2_qa",
            llm_serving=self.llm_serving,
            prompt_template=None,
            use_semantic_judge=True
        )

    def forward(self):
        self.evaluator.run(
            storage=self.storage.step(),
            input_question_key="question",
            input_target_key="golden_answer",
            input_pred_key="generated_ans"
        )

if __name__ == "__main__":
    pipeline = MyPipeline()
    pipeline.forward()
```

## 6. Important Notes

- `eval_type` must match `BenchAnswerGenerator`'s `eval_type`
- Statistics saved to `eval_result_path` JSON file
- `use_semantic_judge=True` requires `llm_serving`

## 5. Runtime Logic

1. Read DataFrame from storage.
2. Validate required `input_xxx_key` columns exist based on `eval_type`.
3. Create 4 output columns: `eval_valid`, `eval_error`, `eval_pred`, `eval_score`.
4. For each row:
   - Extract prediction from `input_pred_key`
   - Extract ground truth based on `eval_type`
   - If `use_semantic_judge=True`: call LLM to judge correctness
   - If `use_semantic_judge=False`: use rule-based comparison
   - Parse and score the result
5. Write results to 4 output columns.
6. Save statistics to `eval_result_path` JSON file.
7. Return list of column names.

## 6. prompt_template Usage

### Important Notes

- Default value is `AnswerJudgePrompt` (class, not instance) → causes `TypeError`
- **Always pass `prompt_template=None`** to use built-in fallback
- Only used when `use_semantic_judge=True`

### Recommended Usage

```python
# Recommended: pass None
evaluator = UnifiedBenchDatasetEvaluator(
    eval_type="key2_qa",
    llm_serving=llm_serving,
    prompt_template=None,
    use_semantic_judge=True
)
```

### Custom Template Usage

```python
from dataflow.prompts.core_text import AnswerJudgePrompt

# Pass an instance for custom prompts
custom_prompt = AnswerJudgePrompt()

evaluator = UnifiedBenchDatasetEvaluator(
    eval_type="key2_qa",
    llm_serving=llm_serving,
    prompt_template=custom_prompt,
    use_semantic_judge=True
)
```

### Fields Passed to `build_prompt(...)`

When using custom `AnswerJudgePrompt` instance, the operator passes:
- `answer`: The predicted answer
- `reference_answer`: The ground truth answer

LLM response must contain:
```json
{
  "judgement_result": true  // or false
}
```
