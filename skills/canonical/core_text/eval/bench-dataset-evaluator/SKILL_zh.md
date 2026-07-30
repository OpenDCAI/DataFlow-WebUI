---
name: bench-dataset-evaluator
description: >-
  BenchDatasetEvaluator 算子参考文档。涵盖构造函数、两种比较模式（match/semantic）、以及流水线使用。

  使用场景：在基准评估中比较预测答案与标准答案。
---
# BenchDatasetEvaluator 算子参考

`BenchDatasetEvaluator` 使用两种模式比较预测答案与标准答案：`match`（数学验证）或 `semantic`（基于LLM）。

## 1. 导入

```python
from dataflow.operators.core_text import BenchDatasetEvaluator
```

## 2. 构造函数

```python
BenchDatasetEvaluator(
    eval_result_path=None,
    compare_method="match",
    system_prompt="You are a helpful assistant specialized in evaluating answer correctness.",
    llm_serving=None,
    prompt_template=AnswerJudgePrompt,
)
```

| 参数                 | 必需 | 默认值                               | 说明                                       |
| -------------------- | ---- | ------------------------------------ | ------------------------------------------ |
| `eval_result_path` | 否   | 自动生成                             | 保存评估统计JSON文件的路径                 |
| `compare_method`   | 否   | `"match"`                          | 比较模式：`"match"` 或 `"semantic"`    |
| `system_prompt`    | 否   | `"You are a helpful assistant..."` | semantic模式的系统提示词                   |
| `llm_serving`      | 否   | `None`                             | semantic模式的LLM服务；match模式不使用     |
| `prompt_template`  | 否   | `AnswerJudgePrompt`                | semantic模式的提示模板；传 `None` 或实例 |

### 构造函数重要说明

1. **Match模式**：仅需 `compare_method="match"`。`llm_serving` 和 `prompt_template` 被忽略。
2. **Semantic模式**：需要 `compare_method="semantic"`、`llm_serving`，以及可选的 `prompt_template`。
3. `prompt_template` 默认值是类 `AnswerJudgePrompt`。传 `None` 使用内置回退或传实例。

## 3. run() 方法签名

```python
op.run(
    storage=self.storage.step(),
    input_test_answer_key="generated_cot",
    input_gt_answer_key="golden_answer",
)
# 返回: [input_test_answer_key, input_gt_answer_key, 'answer_match_result']
```

| 参数                      | 必需 | 默认值              | 说明                         |
| ------------------------- | ---- | ------------------- | ---------------------------- |
| `storage`               | 是   | None                | `DataFlowStorage` 步骤对象 |
| `input_test_answer_key` | 否   | `"generated_cot"` | 包含预测答案的列             |
| `input_gt_answer_key`   | 否   | `"golden_answer"` | 包含标准答案的列             |

## 4. 实际运行逻辑

### Match 模式 (`compare_method="match"`)

1. 从 storage 读取 DataFrame。
2. 创建 `answer_match_result` 列，初始化为 `False`。
3. 对每行，使用 `AnswerExtractor` 提取答案，用 `math_verify_compare()` 与标准答案比较。
4. 将结果写入 `answer_match_result` 列。
5. 保存统计信息到 `eval_result_path`。
6. 返回列名列表。

### Semantic 模式 (`compare_method="semantic"`)

1. 从 storage 读取 DataFrame。
2. 创建 `answer_match_result` 列，初始化为 `False`。
3. 跳过标准答案为空/NaN的行。
4. 仅使用 `answer` 和 `reference_answer` 字段构建提示。
5. 调用 LLM 判断正确性。
6. 解析 LLM 响应中的 `"judgement_result": true/false`。
7. 将结果写入 `answer_match_result` 列。
8. 保存统计信息到 `eval_result_path`。
9. 返回列名列表。

## 5. 流水线使用示例

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

        # Match模式 - 无需LLM
        self.evaluator_match = BenchDatasetEvaluator(
            compare_method="match",
            eval_result_path="./results/match_eval.json"
        )

        # Semantic模式 - 需要LLM
        self.llm_serving = APILLMServing_request(
            api_url="https://api.openai.com/v1/chat/completions",
            key_name_of_api_key="DF_API_KEY",
            model_name="gpt-4o",
            max_workers=10
        )

        self.evaluator_semantic = BenchDatasetEvaluator(
            compare_method="semantic",
            llm_serving=self.llm_serving,
            prompt_template=None,
            eval_result_path="./results/semantic_eval.json"
        )

    def forward(self):
        self.evaluator_match.run(
            storage=self.storage.step(),
            input_test_answer_key="predicted_answer",
            input_gt_answer_key="ground_truth"
        )

if __name__ == "__main__":
    pipeline = MyPipeline()
    pipeline.forward()
```
