# Example: Evaluate QA Sample Quality with Text2QASampleEvaluator

## User Request
"对 Text2QAGenerator 生成的问答对做多维度质量评测，输出 4 个维度的评分和反馈"

## Sample Data
```jsonl
{"source": "Wikipedia article on climate", "generated_question_answer": {"question": "What causes climate change?", "answer": "Greenhouse gas emissions from human activities."}}
{"source": "Science textbook", "generated_question_answer": {"question": "What is DNA?", "answer": "The molecule that carries genetic information."}}
```

## Field Mapping
```
Available in sample:
  - source                      (来源，保留)
  - generated_question_answer   (待评估的 QA 对)

To be generated (8 列，均不能已存在):
  - question_quality_grade / question_quality_feedback
  - answer_alignment_grade / answer_alignment_feedback
  - answer_verifiability_grade / answer_verifiability_feedback
  - downstream_value_grade / downstream_value_feedback

Field flow:
  generated_question_answer → [Text2QASampleEvaluator] → 8 个评分/反馈列
```

## Complete Pipeline Code

```python
from dataflow.operators.core_text import Text2QASampleEvaluator
from dataflow.serving import APILLMServing_request
from dataflow.utils.storage import FileStorage


class QASampleEvalPipeline:
    def __init__(self):
        self.storage = FileStorage(
            first_entry_file_name="qa_samples.jsonl",
            cache_path="./cache",
            file_name_prefix="qa_eval_step",
            cache_type="jsonl"
        )

        self.llm_serving = APILLMServing_request(
            api_url="https://api.openai.com/v1/chat/completions",
            model_name="gpt-4o",
            max_workers=10
        )

        self.evaluator = Text2QASampleEvaluator(
            llm_serving=self.llm_serving
        )

    def forward(self):
        self.evaluator.run(
            storage=self.storage.step(),
            input_key="generated_question_answer"
        )


if __name__ == "__main__":
    pipeline = QASampleEvalPipeline()
    pipeline.forward()
```

## Output

输入 2 行，每行新增 8 列评分和反馈：

| source | question_quality_grade | answer_alignment_grade | ... |
|---|---|---|---|
| `"Wikipedia article..."` | 4 | 5 | ... |
| `"Science textbook"` | 5 | 4 | ... |

## Debugging
- `cache/qa_eval_step_step1.jsonl` — 含原有列 + 8 个评分/反馈列
