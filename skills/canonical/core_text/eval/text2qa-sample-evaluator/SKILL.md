---
name: text2qa-sample-evaluator
description: >-
  Reference documentation for the Text2QASampleEvaluator operator.

  Use when: evaluating QA pair quality across multiple dimensions.
---

# Text2QASampleEvaluator Operator Reference

`Text2QASampleEvaluator` evaluates QA pairs across 4 dimensions, generating 8 output columns (grades + feedbacks for each dimension).

## 1. Import

```python
from dataflow.operators.core_text import Text2QASampleEvaluator
```

## 2. Constructor

```python
Text2QASampleEvaluator(
    llm_serving=llm_serving,
)
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `llm_serving` | Yes | None | LLM service object |

## 3. run() Signature

```python
op.run(
    storage=self.storage.step(),
    input_question_key="question",
    input_answer_key="answer",
)
# returns: list of 8 output column names
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `storage` | Yes | None | Storage step object |
| `input_question_key` | No | `"generated_question"` | Question column name |
| `input_answer_key` | No | `"generated_answer"` | Answer column name |

## 4. Output Columns (8 columns)

| Column Name (Default) | Description |
|----------------------|-------------|
| `question_quality_grades` | Question quality scores |
| `question_quality_feedbacks` | Question quality feedback |
| `answer_alignment_grades` | Answer alignment scores |
| `answer_alignment_feedbacks` | Answer alignment feedback |
| `answer_verifiability_grades` | Answer verifiability scores |
| `answer_verifiability_feedbacks` | Answer verifiability feedback |
| `downstream_value_grades` | Downstream value scores |
| `downstream_value_feedbacks` | Downstream value feedback |

Note: Column names use plural suffix (grades/feedbacks), not singular.

## 5. Usage Example

```python
from dataflow.operators.core_text import Text2QASampleEvaluator
from dataflow.serving import APILLMServing_request
from dataflow.utils.storage import FileStorage

class MyPipeline:
    def __init__(self):
        self.storage = FileStorage(
            first_entry_file_name="./data/qa_pairs.jsonl",
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

        self.evaluator = Text2QASampleEvaluator(
            llm_serving=self.llm_serving
        )

    def forward(self):
        self.evaluator.run(
            storage=self.storage.step(),
            input_question_key="question",
            input_answer_key="answer"
        )

if __name__ == "__main__":
    pipeline = MyPipeline()
    pipeline.forward()
```

## 6. Runtime Logic

1. Read DataFrame from storage.
2. Validate `input_question_key` and `input_answer_key` columns exist.
3. Validate all 8 output columns do NOT exist (raises `ValueError` if they do).
4. For each row, call LLM 4 times (once per dimension):
   - Question quality evaluation
   - Answer alignment evaluation
   - Answer verifiability evaluation
   - Downstream value evaluation
5. Each LLM call returns a grade (numeric score) and feedback (text).
6. Write results to 8 output columns.
7. Return list of 8 output column names.

### Text Constraints

- `input_question_key` and `input_answer_key` must contain non-empty text
- Empty or NaN values may cause evaluation errors
- No automatic text length limits enforced by operator
- LLM context window limits apply (typically 4K-128K tokens depending on model)

## 7. Important Notes

- Calls LLM 4 times per row (once per dimension), high cost
- All 8 output columns must not exist before calling
- No `input_key` parameter (will raise `TypeError`)
