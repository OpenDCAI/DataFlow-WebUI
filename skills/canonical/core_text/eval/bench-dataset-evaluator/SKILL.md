---
name: bench-dataset-evaluator
description: >-
  Reference documentation for the BenchDatasetEvaluator operator. Covers the
  constructor, two comparison modes (match/semantic), and pipeline usage.

  Use when: comparing predicted answers against ground truth answers in benchmark evaluation.
---

# BenchDatasetEvaluator Operator Reference

`BenchDatasetEvaluator` compares predicted answers against ground truth using two modes: `match` (math verification) or `semantic` (LLM-based).

## 1. Import

```python
from dataflow.operators.core_text import BenchDatasetEvaluator
```

## 2. Match Mode

### Constructor

```python
BenchDatasetEvaluator(
    eval_result_path=None,
    compare_method="match",
)
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `eval_result_path` | No | Auto-generated | Path to save evaluation statistics JSON file |
| `compare_method` | No | `"match"` | Must be `"match"` |
| `system_prompt` | No | `"You are a helpful assistant..."` | Not used in match mode |
| `llm_serving` | No | `None` | Not used in match mode |
| `prompt_template` | No | `AnswerJudgePrompt` | Not used in match mode |

### run() Signature

```python
op.run(
    storage=self.storage.step(),
    input_test_answer_key="generated_cot",
    input_gt_answer_key="golden_answer",
)
# returns: [input_test_answer_key, input_gt_answer_key, 'answer_match_result']
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `storage` | Yes | None | `DataFlowStorage` step object |
| `input_test_answer_key` | No | `"generated_cot"` | Column containing predicted answers |
| `input_gt_answer_key` | No | `"golden_answer"` | Column containing ground truth answers |

### Runtime Logic

1. Read DataFrame from storage.
2. Create `answer_match_result` column initialized to `False`.
3. For each row, extract answer using `AnswerExtractor` and compare with ground truth using `math_verify_compare()`.
4. Write results to `answer_match_result` column.
5. Save statistics to `eval_result_path`.
6. Return column list.

### Usage Example

```python
from dataflow.operators.core_text import BenchDatasetEvaluator
from dataflow.utils.storage import FileStorage

class MyPipeline:
    def __init__(self):
        self.storage = FileStorage(
            first_entry_file_name="./data/bench.jsonl",
            cache_path="./cache",
            file_name_prefix="step",
            cache_type="jsonl"
        )

        self.evaluator = BenchDatasetEvaluator(
            compare_method="match",
            eval_result_path="./results/match_eval.json"
        )

    def forward(self):
        self.evaluator.run(
            storage=self.storage.step(),
            input_test_answer_key="predicted_answer",
            input_gt_answer_key="ground_truth"
        )

if __name__ == "__main__":
    pipeline = MyPipeline()
    pipeline.forward()
```

## 3. Semantic Mode

### Constructor

```python
BenchDatasetEvaluator(
    eval_result_path=None,
    compare_method="semantic",
    system_prompt="You are a helpful assistant specialized in evaluating answer correctness.",
    llm_serving=llm_serving,
    prompt_template=None,
)
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `eval_result_path` | No | Auto-generated | Path to save evaluation statistics JSON file |
| `compare_method` | Yes | None | Must be `"semantic"` |
| `system_prompt` | No | `"You are a helpful assistant..."` | System prompt for LLM |
| `llm_serving` | Yes | None | LLM service object |
| `prompt_template` | No | `AnswerJudgePrompt` | Pass `None` to use built-in fallback |

### run() Signature

```python
op.run(
    storage=self.storage.step(),
    input_test_answer_key="generated_cot",
    input_gt_answer_key="golden_answer",
)
# returns: [input_test_answer_key, input_gt_answer_key, 'answer_match_result']
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `storage` | Yes | None | `DataFlowStorage` step object |
| `input_test_answer_key` | No | `"generated_cot"` | Column containing predicted answers |
| `input_gt_answer_key` | No | `"golden_answer"` | Column containing ground truth answers |

### Runtime Logic

1. Read DataFrame from storage.
2. Create `answer_match_result` column initialized to `False`.
3. Skip rows where ground truth is empty/NaN.
4. Build prompts using only `answer` and `reference_answer` fields.
5. Call LLM to judge correctness.
6. Parse LLM response for `"judgement_result": true/false`.
7. Write results to `answer_match_result` column.
8. Save statistics to `eval_result_path`.
9. Return column list.

### Usage Example

```python
from dataflow.operators.core_text import BenchDatasetEvaluator
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

        self.evaluator = BenchDatasetEvaluator(
            compare_method="semantic",
            llm_serving=self.llm_serving,
            prompt_template=None,
            eval_result_path="./results/semantic_eval.json"
        )

    def forward(self):
        self.evaluator.run(
            storage=self.storage.step(),
            input_test_answer_key="predicted_answer",
            input_gt_answer_key="ground_truth"
        )

if __name__ == "__main__":
    pipeline = MyPipeline()
    pipeline.forward()
```

## 4. AnswerJudgePrompt

`AnswerJudgePrompt` is the default prompt template class for semantic mode.

### Important Notes

1. **Default value issue**: Constructor default is `prompt_template=AnswerJudgePrompt` (class, not instance).
2. **Recommended usage**: Pass `prompt_template=None` to use built-in fallback.
3. **Custom template**: Pass an instance if you need custom prompts.

### Prompt Structure

The prompt template builds a JSON-formatted request:
- `answer`: The predicted answer to evaluate
- `reference_answer`: The ground truth answer

LLM response must contain:
```json
{
  "judgement_result": true  // or false
}
```

### Custom Template Example

```python
from dataflow.prompts.core_text import AnswerJudgePrompt

custom_prompt = AnswerJudgePrompt()
# Modify if needed

evaluator = BenchDatasetEvaluator(
    compare_method="semantic",
    llm_serving=llm_serving,
    prompt_template=custom_prompt
)
```
