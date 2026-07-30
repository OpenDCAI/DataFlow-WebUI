---
name: prompted-evaluator
description: >-
  PromptedEvaluator 算子参考文档。

  使用场景：使用 LLM 对文本质量打分，不过滤行。
---

# PromptedEvaluator 算子参考

`PromptedEvaluator` 使用 LLM 对每行文本打分（1-5），将分数写入新列，不删除任何行。

## 1. 导入

```python
from dataflow.operators.core_text import PromptedEvaluator
```

## 2. 构造函数

```python
PromptedEvaluator(
    llm_serving=llm_serving,
    system_prompt="Please evaluate the quality of this text on a scale from 1 to 5.",
)
```

| 参数 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `llm_serving` | 是 | None | LLM服务对象 |
| `system_prompt` | 否 | `"Please evaluate..."` | 定义评分标准的系统提示词（1-5分制） |

## 3. run() 方法签名

```python
op.run(
    storage=self.storage.step(),
    input_key="raw_content",
    output_key="eval",
)
# 返回: output_key 字符串
```

| 参数 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `storage` | 是 | None | Storage 步骤对象 |
| `input_key` | 否 | `"raw_content"` | 包含待评估文本的列 |
| `output_key` | 否 | `"eval"` | 写入 LLM 分数的列 |

## 4. 使用示例

```python
from dataflow.operators.core_text import PromptedEvaluator
from dataflow.serving import APILLMServing_request
from dataflow.utils.storage import FileStorage

class MyPipeline:
    def __init__(self):
        self.storage = FileStorage(
            first_entry_file_name="./data/input.jsonl",
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

        self.evaluator = PromptedEvaluator(
            llm_serving=self.llm_serving,
            system_prompt="评估文本质量，打分范围 1-5。"
        )

    def forward(self):
        self.evaluator.run(
            storage=self.storage.step(),
            input_key="content",
            output_key="quality_score"
        )

if __name__ == "__main__":
    pipeline = MyPipeline()
    pipeline.forward()
```

## 5. 运行逻辑

1. 从 storage 读取 DataFrame。
2. 从 `input_key` 列提取文本。
3. 对每行，使用 `system_prompt` 调用 LLM 对文本打分（1-5）。
4. 解析 LLM 响应提取数值分数。
5. 将分数写入 `output_key` 列。
6. 保留所有行（不过滤）。
7. 返回 `output_key` 字符串。

## 6. 与 PromptedFilter 的主要区别

- **PromptedEvaluator**：将分数写入 `output_key` 列，保留所有行
- **PromptedFilter**：打分并在一步中删除低于阈值的行

使用 PromptedEvaluator + GeneralFilter 实现两步打分和过滤。
