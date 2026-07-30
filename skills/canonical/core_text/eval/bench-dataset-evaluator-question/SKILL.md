---
name: bench-dataset-evaluator-question
description: >-
  Reference documentation for the BenchDatasetEvaluatorQuestion operator.
  Extended version of BenchDatasetEvaluator with question and subquestion support.

  Use when: evaluating answers with question context or multiple subquestions.
---

# BenchDatasetEvaluatorQuestion Operator Reference

`BenchDatasetEvaluatorQuestion` extends `BenchDatasetEvaluator` with support for question context and subquestions.

## 1. Import

```python
from dataflow.operators.core_text import BenchDatasetEvaluatorQuestion
```

## 2. Match Mode

### Constructor

```python
BenchDatasetEvaluatorQuestion(
    eval_result_path=None,
    compare_method="match",
)
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `eval_result_path` | No | Auto-generated | Path to save evaluation statistics |
| `compare_method` | No | `"match"` | Must be `"match"` |
| `system_prompt` | No | `"You are a helpful assistant..."` | Not used in match mode |
| `llm_serving` | No | `None` | Not used in match mode |
| `prompt_template` | No | `AnswerJudgePromptQuestion` | Not used in match mode |

### run() Signature

```python
op.run(
    storage=self.storage.step(),
    input_question_key="question",
    input_test_answer_key="generated_cot",
    input_gt_answer_key="golden_answer",
)
# returns: list of column names
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `storage` | Yes | None | Storage step object |
| `input_question_key` | No | `"question"` | Question column |
| `input_test_answer_key` | No | `"generated_cot"` | Predicted answer column |
| `input_gt_answer_key` | No | `"golden_answer"` | Ground truth column |

### Usage Example

```python
from dataflow.operators.core_text import BenchDatasetEvaluatorQuestion
from dataflow.utils.storage import FileStorage

class MyPipeline:
    def __init__(self):
        self.storage = FileStorage(
            first_entry_file_name="./data/bench.jsonl",
            cache_path="./cache",
            file_name_prefix="step",
            cache_type="jsonl"
        )

        self.evaluator = BenchDatasetEvaluatorQuestion(
            compare_method="match",
            eval_result_path="./results/match_eval.json"
        )

    def forward(self):
        self.evaluator.run(
            storage=self.storage.step(),
            input_question_key="question",
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
BenchDatasetEvaluatorQuestion(
    eval_result_path=None,
    compare_method="semantic",
    system_prompt="You are a helpful assistant specialized in evaluating answer correctness.",
    llm_serving=llm_serving,
    prompt_template=None,
    support_subquestions=False,
)
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `eval_result_path` | No | Auto-generated | Path to save evaluation statistics |
| `compare_method` | Yes | None | Must be `"semantic"` |
| `system_prompt` | No | `"You are..."` | System prompt for LLM |
| `llm_serving` | Yes | None | LLM service object |
| `prompt_template` | No | `AnswerJudgePromptQuestion` | Pass `None` to use built-in fallback |
| `support_subquestions` | No | `False` | Enable subquestion evaluation |

### run() Signature

```python
op.run(
    storage=self.storage.step(),
    input_question_key="question",
    input_test_answer_key="generated_cot",
    input_gt_answer_key="golden_answer",
)
# returns: list of column names
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `storage` | Yes | None | Storage step object |
| `input_question_key` | No | `"question"` | Question column |
| `input_test_answer_key` | No | `"generated_cot"` | Predicted answer column |
| `input_gt_answer_key` | No | `"golden_answer"` | Ground truth column |

### Usage Example

```python
from dataflow.operators.core_text import BenchDatasetEvaluatorQuestion
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

        self.evaluator = BenchDatasetEvaluatorQuestion(
            compare_method="semantic",
            llm_serving=self.llm_serving,
            prompt_template=None,
            support_subquestions=False
        )

    def forward(self):
        self.evaluator.run(
            storage=self.storage.step(),
            input_question_key="question",
            input_test_answer_key="predicted_answer",
            input_gt_answer_key="ground_truth"
        )

if __name__ == "__main__":
    pipeline = MyPipeline()
    pipeline.forward()
```

## 4. Key Differences from BenchDatasetEvaluator

1. **Question context**: Semantic mode includes `question` field in the prompt alongside `answer` and `reference_answer`.
2. **Subquestions support**: When `support_subquestions=True`, evaluates multiple subquestions per row.
3. **Prompt templates**: Uses `AnswerJudgePromptQuestion` (single question) or `AnswerJudgeMultipleQuestionsPrompt` (subquestions).

## 5. AnswerJudgePromptQuestion

`AnswerJudgePromptQuestion` is the default prompt template class for semantic mode.

### Important Notes on `prompt_template`

Although the source code sets the default value to `AnswerJudgePromptQuestion`, this default is a class object, not an instance.

In normal usage, it's recommended to use one of these two approaches:

**Option 1: Pass `None` (recommended)**
```python
prompt_template=None
```
This uses the built-in fallback logic.

**Option 2: Pass an instance**
```python
from dataflow.prompts.core_text import AnswerJudgePromptQuestion

prompt_template=AnswerJudgePromptQuestion()
```

### Fields Passed to `build_prompt(...)`

When `prompt_template` is an `AnswerJudgePromptQuestion` instance, the source code passes these fields:

- `question`: The question being evaluated
- `answer`: The predicted answer to evaluate
- `reference_answer`: The ground truth answer

### Expected LLM Response Format

LLM response must contain:
```json
{
  "judgement_result": true  // or false
}
```
