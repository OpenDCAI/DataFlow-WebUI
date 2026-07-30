# Example: Evaluate Text Quality with PromptedEvaluator

## User Request
"用 LLM 对生成的文章摘要打质量分（1-5），保存到 quality_score 列，暂不过滤"

## Sample Data
```jsonl
{"article_id": 1, "summary": "A brief summary."}
{"article_id": 2, "summary": "This comprehensive summary covers the main findings of the research, including methodology, results, and conclusions."}
{"article_id": 3, "summary": "Good summary with clear structure."}
```

## Field Mapping
```
Available in sample:
  - article_id  (保留，不变)
  - summary     (待评估的文本列)

To be generated:
  - quality_score (LLM 打分结果，PromptedEvaluator 写入)

Field flow:
  summary → [PromptedEvaluator] → quality_score (不删行，所有行保留)
```

## Complete Pipeline Code

```python
from dataflow.operators.core_text import PromptedEvaluator
from dataflow.serving import APILLMServing_request
from dataflow.utils.storage import FileStorage


class QualityEvalPipeline:
    def __init__(self):
        self.storage = FileStorage(
            first_entry_file_name="summaries.jsonl",
            cache_path="./cache",
            file_name_prefix="eval_step",
            cache_type="jsonl"
        )

        self.llm_serving = APILLMServing_request(
            api_url="https://api.openai.com/v1/chat/completions",
            model_name="gpt-4o",
            max_workers=10
        )

        self.evaluator = PromptedEvaluator(
            llm_serving=self.llm_serving,
            system_prompt="Evaluate the quality of this article summary on a scale from 1 to 5. "
                          "Consider completeness, clarity, and conciseness. Return only the integer score."
        )

    def forward(self):
        self.evaluator.run(
            storage=self.storage.step(),
            input_key="summary",
            output_key="quality_score"
        )


if __name__ == "__main__":
    pipeline = QualityEvalPipeline()
    pipeline.forward()
```

## Output

输入 3 行，LLM 打分后，**所有行保留**，新增 `quality_score` 列：

| article_id | summary | quality_score |
|---|---|---|
| 1 | `"A brief summary."` | 2 |
| 2 | `"This comprehensive summary..."` | 5 |
| 3 | `"Good summary with clear structure."` | 4 |

## Debugging
- `cache/eval_step_step1.jsonl` — 含所有 3 行及 `quality_score` 列
