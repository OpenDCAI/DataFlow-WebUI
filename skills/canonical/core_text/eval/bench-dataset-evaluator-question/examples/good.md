# Example: Evaluate QA Benchmark with Questions and Subquestions

## User Request
"Evaluate model answers on a multi-subquestion QA set; each row contains multiple sub-questions; record correct/total per row"

## Sample Data
```jsonl
{"question": "Describe the life of Marie Curie.", "golden_answer": ["born in Warsaw", "won two Nobel Prizes", "discovered radium"], "generated_cot": "Marie Curie was born in Warsaw. She won two Nobel Prizes and discovered polonium and radium."}
{"question": "Explain photosynthesis.", "golden_answer": ["uses sunlight", "produces oxygen", "occurs in chloroplasts"], "generated_cot": "Photosynthesis uses sunlight to produce glucose."}
```

## Field Mapping
```
Available in sample:
  - question       (question column)
  - golden_answer  (list of ground truth answers, multi-subquestion format)
  - generated_cot  (model answer)

To be generated:
  - answer_match_result (format: "correct/total", e.g. "3/3" or "1/3")

Field flow:
  generated_cot + golden_answer + question → [BenchDatasetEvaluatorQuestion] → answer_match_result
```

## Complete Pipeline Code

```python
from dataflow.operators.core_text import BenchDatasetEvaluatorQuestion
from dataflow.serving import APILLMServing_request
from dataflow.utils.storage import FileStorage


class SubQuestionEvalPipeline:
    def __init__(self):
        self.storage = FileStorage(
            first_entry_file_name="qa_results.jsonl",
            cache_path="./cache",
            file_name_prefix="eval_step",
            cache_type="jsonl"
        )

        # NOTE: compare_method="match" has a source code bug (self.support_subquestions never set).
        # Use compare_method="semantic" with llm_serving until the upstream bug is fixed.
        self.llm_serving = APILLMServing_request(
            api_url="https://api.openai.com/v1/chat/completions",
            model_name="gpt-4o",
            max_workers=10
        )

        self.evaluator = BenchDatasetEvaluatorQuestion(
            compare_method="semantic",
            llm_serving=self.llm_serving,
            prompt_template=None,
            support_subquestions=True,
            eval_result_path="./eval_stats.json"
        )

    def forward(self):
        self.evaluator.run(
            storage=self.storage.step(),
            input_test_answer_key="generated_cot",
            input_gt_answer_key="golden_answer",
            input_question_key="question"
        )


if __name__ == "__main__":
    pipeline = SubQuestionEvalPipeline()
    pipeline.forward()
```

## Output

| question | answer_match_result |
|---|---|
| `"Describe the life of Marie Curie."` | `"3/3"` |
| `"Explain photosynthesis."` | `"1/3"` |

## Debugging
- `cache/eval_step_step1.jsonl` — contains the `answer_match_result` column (string format)
- `eval_stats.json` — contains summary statistics
