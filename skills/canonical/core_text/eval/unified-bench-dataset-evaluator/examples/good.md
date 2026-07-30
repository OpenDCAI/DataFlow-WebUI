# Example: Unified Bench Evaluation with UnifiedBenchDatasetEvaluator

## User Request
"对 QA 评测集上生成的回答做统一评测，计算准确率，结果写入评分列"

## Sample Data
```jsonl
{"question": "What is the capital of France?", "golden_answer": "Paris", "generated_ans": "The capital of France is Paris."}
{"question": "Who invented the telephone?", "golden_answer": "Alexander Graham Bell", "generated_ans": "Alexander Graham Bell invented the telephone."}
{"question": "What is H2O?", "golden_answer": "Water", "generated_ans": "H2O is the chemical formula for water."}
```

## Field Mapping
```
Available in sample:
  - question       (问题列)
  - golden_answer  (标准答案)
  - generated_ans  (模型生成回答，来自 BenchAnswerGenerator)

To be generated:
  - eval_valid   (评测是否有效，布尔)
  - eval_error   (错误信息，字符串)
  - eval_pred    (解析后的预测答案)
  - eval_score   (数值评分，0 或 1)

Field flow:
  generated_ans + question + golden_answer → [UnifiedBenchDatasetEvaluator] → 4 个评测列
```

## Complete Pipeline Code

```python
from dataflow.operators.core_text import UnifiedBenchDatasetEvaluator
from dataflow.utils.storage import FileStorage


class UnifiedEvalPipeline:
    def __init__(self):
        self.storage = FileStorage(
            first_entry_file_name="qa_with_answers.jsonl",
            cache_path="./cache",
            file_name_prefix="unified_eval_step",
            cache_type="jsonl"
        )

        self.evaluator = UnifiedBenchDatasetEvaluator(
            eval_type="key2_qa",
            eval_result_path="./eval_stats.json"
        )

    def forward(self):
        self.evaluator.run(
            storage=self.storage.step(),
            input_question_key="question",
            input_target_key="golden_answer",
            input_pred_key="generated_ans"
        )


if __name__ == "__main__":
    pipeline = UnifiedEvalPipeline()
    pipeline.forward()
```

## Output

输入 3 行，评测后新增 4 列：

| question | eval_valid | eval_score | eval_pred | eval_error |
|---|---|---|---|---|
| `"What is the capital..."` | `True` | `1` | `"Paris"` | `""` |
| `"Who invented the telephone?"` | `True` | `1` | `"Alexander Graham Bell"` | `""` |
| `"What is H2O?"` | `True` | `1` | `"water"` | `""` |

统计结果（准确率 = 3/3 = 1.0）保存到 `eval_stats.json`。

## Debugging
- `cache/unified_eval_step_step1.jsonl` — 含 4 个评测列
- `eval_stats.json` — 含准确率等汇总指标
