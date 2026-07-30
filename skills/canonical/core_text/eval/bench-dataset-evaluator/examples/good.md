# Example: BenchDatasetEvaluator — match and semantic modes

---

## Example 1: match mode (math answer verification)

### User Request
"Evaluate model-generated reasoning chains against ground truth answers on a math benchmark, and compute accuracy"

### Sample Data
```jsonl
{"question": "What is 2+2?", "golden_answer": "4", "generated_cot": "The answer is \\boxed{4}"}
{"question": "Simplify 6/8", "golden_answer": "3/4", "generated_cot": "6/8 = \\boxed{3/4}"}
{"question": "What is sqrt(9)?", "golden_answer": "3", "generated_cot": "The answer is \\boxed{5}"}
```

### Field Mapping
```
generated_cot + golden_answer → [BenchDatasetEvaluator match] → answer_match_result + JSON
```

### Pipeline Code

```python
from dataflow.operators.core_text import BenchDatasetEvaluator
from dataflow.prompts.model_evaluation.general import AnswerJudgePrompt
from dataflow.utils.storage import FileStorage


class BenchMatchPipeline:
    def __init__(self):
        self.storage = FileStorage(
            first_entry_file_name="math_results.jsonl",
            cache_path="./cache",
            file_name_prefix="eval_step",
            cache_type="jsonl",
        )
        self.evaluator = BenchDatasetEvaluator(
            compare_method="match",
            eval_result_path="./eval_stats.json",
            prompt_template=AnswerJudgePrompt(),
        )

    def forward(self):
        self.evaluator.run(
            storage=self.storage.step(),
            input_test_answer_key="generated_cot",
            input_gt_answer_key="golden_answer",
        )


if __name__ == "__main__":
    pipeline = BenchMatchPipeline()
    pipeline.forward()
```

### Output

`math_verify` extracts the `\boxed{}` answer from `generated_cot` and compares it to `golden_answer`:

| question | golden_answer | generated_cot | answer_match_result |
|---|---|---|---|
| What is 2+2? | 4 | `... \boxed{4}` | `True` |
| Simplify 6/8 | 3/4 | `... \boxed{3/4}` | `True` |
| What is sqrt(9)? | 3 | `... \boxed{5}` | `False` |

Statistics (accuracy = 0.667) saved to `eval_stats.json`.

> **Applicable to**: numbers, fractions, LaTeX expressions. For natural language answers use semantic mode (see Example 2).

---

## Example 2: semantic mode (LLM semantic judgment)

### User Request
"Evaluate model answers against ground truth on an open-domain QA benchmark using semantic matching, and compute accuracy"

### Sample Data
```jsonl
{"question": "What is the capital of France?", "golden_answer": "Paris", "generated_cot": "The capital of France is Paris."}
{"question": "Who wrote Hamlet?", "golden_answer": "Shakespeare", "generated_cot": "William Shakespeare wrote Hamlet."}
{"question": "What color is the sky?", "golden_answer": "blue", "generated_cot": "The sky is typically green."}
```

### Field Mapping
```
generated_cot + golden_answer → [BenchDatasetEvaluator semantic + LLM] → answer_match_result + JSON
```

### Pipeline Code

```python
from dataflow.operators.core_text import BenchDatasetEvaluator
from dataflow.prompts.model_evaluation.general import AnswerJudgePrompt
from dataflow.serving.api_llm_serving_request import APILLMServing_request
from dataflow.utils.storage import FileStorage


class BenchSemanticPipeline:
    def __init__(self):
        self.storage = FileStorage(
            first_entry_file_name="qa_results.jsonl",
            cache_path="./cache",
            file_name_prefix="eval_step",
            cache_type="jsonl",
        )
        self.llm_serving = APILLMServing_request(
            api_url="https://api.openai.com/v1",
            model_name="gpt-4o",
            max_workers=10,
        )
        self.evaluator = BenchDatasetEvaluator(
            compare_method="semantic",
            llm_serving=self.llm_serving,
            eval_result_path="./eval_stats.json",
            prompt_template=AnswerJudgePrompt(),
        )

    def forward(self):
        self.evaluator.run(
            storage=self.storage.step(),
            input_test_answer_key="generated_cot",
            input_gt_answer_key="golden_answer",
        )


if __name__ == "__main__":
    pipeline = BenchSemanticPipeline()
    pipeline.forward()
```

### Output

The LLM judges semantic equivalence for each row and parses the `judgement_result` field from the returned JSON:

| question | golden_answer | generated_cot | answer_match_result |
|---|---|---|---|
| What is the capital of France? | Paris | The capital of France is Paris. | `True` |
| Who wrote Hamlet? | Shakespeare | William Shakespeare wrote Hamlet. | `True` |
| What color is the sky? | blue | The sky is typically green. | `False` |

Statistics (accuracy = 0.667) saved to `eval_stats.json`.

> **Applicable to**: natural language answers, open-domain QA, multi-word answers. Requires LLM; incurs token cost.

---

## Debugging
- `cache/eval_step_step1.jsonl` — full data including the `answer_match_result` column
- `eval_stats.json` — contains `total_samples`, `matched_samples`, `accuracy`, `compare_method`, etc.
