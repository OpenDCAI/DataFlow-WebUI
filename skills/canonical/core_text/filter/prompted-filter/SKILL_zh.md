---
name: prompted-filter
description: >-
  PromptedFilter 算子参考文档。涵盖构造函数、实际评分和过滤行为、以及流水线使用说明。

  使用场景：基于 LLM 语义质量判断过滤行，而非简单的规则条件。
---
# PromptedFilter 算子参考

`PromptedFilter` 内部使用 `PromptedEvaluator` 对每行文本打分，将分数写入 `output_key`，并仅保留分数在 `[min_score, max_score]` 范围内的行。

## 1. 导入

```python
from dataflow.operators.core_text import PromptedFilter
```

## 2. 构造函数

```python
PromptedFilter(
    llm_serving,
    system_prompt="Please evaluate the quality of this data on a scale from 1 to 5.",
    min_score=1,
    max_score=5,
)
```

| 参数              | 必需 | 默认值                                                                 | 说明                                                                                  |
| ----------------- | ---- | ---------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| `llm_serving`   | 是   | None                                                                   | 实现 `generate_from_input(...)` 的 LLM 服务对象。内部传递给 `PromptedEvaluator`。 |
| `system_prompt` | 否   | `"Please evaluate the quality of this data on a scale from 1 to 5."` | 定义 LLM 的评分标准。描述的评分范围应与 `min_score`/`max_score` 对齐。            |
| `min_score`     | 否   | `1`                                                                  | 保留分数范围的下界（包含）。                                                          |
| `max_score`     | 否   | `5`                                                                  | 保留分数范围的上界（包含）。                                                          |

### 构造函数重要说明

1. 算子内部创建 `PromptedEvaluator(llm_serving, system_prompt)` 实例。

## 3. run() 方法签名

```python
output_key = op.run(
    storage=self.storage.step(),
    input_key="raw_content",
    output_key="eval",
)
# 返回值: output_key
```

| 参数           | 必需 | 默认值            | 说明                                                                            |
| -------------- | ---- | ----------------- | ------------------------------------------------------------------------------- |
| `storage`    | 是   | None              | `DataFlowStorage` 步骤对象。算子从此读取 DataFrame 并写回过滤后的 DataFrame。 |
| `input_key`  | 否   | `"raw_content"` | 待评估的文本列。此列必须已存在。                                                |
| `output_key` | 否   | `"eval"`        | 写入 LLM 分数的列。如已存在则静默覆盖。                                         |

### 返回值

方法返回 `output_key`（字符串）。

## 4. 实际运行逻辑

源码行为：

1. 从 `storage.read("dataframe")` 读取 DataFrame。
2. 调用 `self.prompted_evaluator.eval(dataframe, input_key)` 获取数值分数列表。
3. 将分数写入 `dataframe[output_key]`。
4. 过滤 DataFrame：仅保留 `dataframe[output_key] >= self.min_score` 且 `dataframe[output_key] <= self.max_score` 的行。
5. 通过 `storage.write(filtered_dataframe)` 写回过滤后的 DataFrame。
6. 返回 `output_key`。

### 关键行为说明

1. `input_key` 列必须存在于当前 DataFrame 中。
2. 分数在 `[min_score, max_score]` 范围外的行将被永久删除。
3. 输出 DataFrame 保留 `output_key` 分数列和所有原始列。
4. 如果 `output_key` 已存在，将被静默覆盖。
5. 每次算子调用必须接收独立的 `self.storage.step()`；不要重用同一步骤对象。

## 5. 流水线使用示例

```python
from dataflow.operators.core_text import PromptedFilter
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

        self.filter = PromptedFilter(
            llm_serving=self.llm_serving,
            system_prompt="请对这段文本的质量进行1到5的评分。",
            min_score=4,
            max_score=5
        )

    def forward(self):
        self.filter.run(
            storage=self.storage.step(),
            input_key="content",
            output_key="quality_score"
        )

if __name__ == "__main__":
    pipeline = MyPipeline()
    pipeline.forward()
```

注意：`forward()` 无返回值，遵循标准流水线模式。
