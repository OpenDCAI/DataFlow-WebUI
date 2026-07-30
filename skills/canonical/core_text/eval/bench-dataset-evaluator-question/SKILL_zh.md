---
name: bench-dataset-evaluator-question
description: >-
  BenchDatasetEvaluatorQuestion 算子参考文档。
  BenchDatasetEvaluator 的扩展版本，支持问题和子问题。

  使用场景：使用问题上下文或多个子问题评估答案。
---

# BenchDatasetEvaluatorQuestion 算子参考

`BenchDatasetEvaluatorQuestion` 扩展了 `BenchDatasetEvaluator`，支持问题上下文和子问题。

## 1. 导入

```python
from dataflow.operators.core_text import BenchDatasetEvaluatorQuestion
```

## 2. Match 模式

### 构造函数

```python
BenchDatasetEvaluatorQuestion(
    eval_result_path=None,
    compare_method="match",
)
```

| 参数 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `eval_result_path` | 否 | 自动生成 | 保存评估统计的路径 |
| `compare_method` | 否 | `"match"` | 必须为 `"match"` |
| `system_prompt` | 否 | `"You are a helpful assistant..."` | match 模式下不使用 |
| `llm_serving` | 否 | `None` | match 模式下不使用 |
| `prompt_template` | 否 | `AnswerJudgePromptQuestion` | match 模式下不使用 |

### run() 方法签名

```python
op.run(
    storage=self.storage.step(),
    input_question_key="question",
    input_test_answer_key="generated_cot",
    input_gt_answer_key="golden_answer",
)
# 返回: 列名列表
```

| 参数 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `storage` | 是 | None | Storage 步骤对象 |
| `input_question_key` | 否 | `"question"` | 问题列 |
| `input_test_answer_key` | 否 | `"generated_cot"` | 预测答案列 |
| `input_gt_answer_key` | 否 | `"golden_answer"` | 标准答案列 |

### 使用示例

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

## 3. Semantic 模式

### 构造函数

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

| 参数 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `eval_result_path` | 否 | 自动生成 | 保存评估统计的路径 |
| `compare_method` | 是 | None | 必须为 `"semantic"` |
| `system_prompt` | 否 | `"You are..."` | LLM的系统提示词 |
| `llm_serving` | 是 | None | LLM服务对象 |
| `prompt_template` | 否 | `AnswerJudgePromptQuestion` | 传 `None` 使用内置回退 |
| `support_subquestions` | 否 | `False` | 启用子问题评估 |

### run() 方法签名

```python
op.run(
    storage=self.storage.step(),
    input_question_key="question",
    input_test_answer_key="generated_cot",
    input_gt_answer_key="golden_answer",
)
# 返回: 列名列表
```

| 参数 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `storage` | 是 | None | Storage 步骤对象 |
| `input_question_key` | 否 | `"question"` | 问题列 |
| `input_test_answer_key` | 否 | `"generated_cot"` | 预测答案列 |
| `input_gt_answer_key` | 否 | `"golden_answer"` | 标准答案列 |

### 使用示例

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

## 4. 与 BenchDatasetEvaluator 的主要区别

1. **问题上下文**：semantic模式在提示中包含 `question` 字段，与 `answer` 和 `reference_answer` 一起使用。
2. **子问题支持**：当 `support_subquestions=True` 时，评估每行的多个子问题。
3. **提示模板**：使用 `AnswerJudgePromptQuestion`（单问题）或 `AnswerJudgeMultipleQuestionsPrompt`（子问题）。

## 5. AnswerJudgePromptQuestion

`AnswerJudgePromptQuestion` 是 semantic 模式的默认提示模板类。

### 关于 `prompt_template` 的重要说明

虽然源码把默认值写成了 `AnswerJudgePromptQuestion`，但这个默认值实际上是类对象而不是实例。

在正常使用中，推荐使用以下两种方式之一：

**方式 1：传 `None`（推荐）**
```python
prompt_template=None
```
此时算子会使用内置回退逻辑。

**方式 2：传入实例**
```python
from dataflow.prompts.core_text import AnswerJudgePromptQuestion

prompt_template=AnswerJudgePromptQuestion()
```

### 传递给 `build_prompt(...)` 的字段

当 `prompt_template` 是 `AnswerJudgePromptQuestion` 实例时，源码会传入这些字段：

- `question`：正在评估的问题
- `answer`：待评估的预测答案
- `reference_answer`：标准答案

### LLM 响应格式要求

LLM 响应必须包含：
```json
{
  "judgement_result": true  // 或 false
}
```
