---
name: text2qa-sample-evaluator
description: >-
  Text2QASampleEvaluator 算子参考文档。

  使用场景：对问答对进行多维度质量评测。
---
# Text2QASampleEvaluator 算子参考

`Text2QASampleEvaluator` 对 QA 对从 4 个维度评测，生成 8 个输出列（每维度的评分和反馈）。

## 1. 导入

```python
from dataflow.operators.core_text import Text2QASampleEvaluator
```

## 2. 构造函数

```python
Text2QASampleEvaluator(
    llm_serving=llm_serving,
)
```

| 参数            | 必需 | 默认值 | 说明        |
| --------------- | ---- | ------ | ----------- |
| `llm_serving` | 是   | None   | LLM服务对象 |

## 3. run() 方法签名

```python
op.run(
    storage=self.storage.step(),
    input_question_key="question",
    input_answer_key="answer",
)
# 返回: 8个输出列名的列表
```

| 参数                   | 必需 | 默认值                   | 说明             |
| ---------------------- | ---- | ------------------------ | ---------------- |
| `storage`            | 是   | None                     | Storage 步骤对象 |
| `input_question_key` | 否   | `"generated_question"` | 问题列名         |
| `input_answer_key`   | 否   | `"generated_answer"`   | 答案列名         |

## 4. 输出列（8列）

| 列名（默认）                       | 说明             |
| ---------------------------------- | ---------------- |
| `question_quality_grades`        | 问题质量评分     |
| `question_quality_feedbacks`     | 问题质量反馈     |
| `answer_alignment_grades`        | 答案对齐度评分   |
| `answer_alignment_feedbacks`     | 答案对齐度反馈   |
| `answer_verifiability_grades`    | 答案可验证性评分 |
| `answer_verifiability_feedbacks` | 答案可验证性反馈 |
| `downstream_value_grades`        | 下游使用价值评分 |
| `downstream_value_feedbacks`     | 下游使用价值反馈 |

注意：列名后缀是复数形式（grades/feedbacks），不是单数。

## 5. 使用示例

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

## 6. 重要说明

- 每行调用 4 次 LLM（每维度 1 次），成本较高
- 所有 8 个输出列在调用前不能已存在
- 不存在 `input_key` 参数（传入会抛 `TypeError`）

## 6. 运行逻辑

1. 从 storage 读取 DataFrame。
2. 验证 `input_question_key` 和 `input_answer_key` 列存在。
3. 验证所有 8 个输出列不存在（否则抛出 `ValueError`）。
4. 对每行，调用 LLM 4 次（每维度 1 次）：
   - 问题质量评估
   - 答案对齐度评估
   - 答案可验证性评估
   - 下游使用价值评估
5. 每次 LLM 调用返回评分（数值）和反馈（文本）。
6. 将结果写入 8 个输出列。
7. 返回 8 个输出列名的列表。

### 文本限制

- `input_question_key` 和 `input_answer_key` 必须包含非空文本
- 受 LLM 上下文窗口限制（通常 4K-128K tokens）
