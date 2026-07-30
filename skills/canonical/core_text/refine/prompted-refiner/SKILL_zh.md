---
name: prompted-refiner
description: >-
  PromptedRefiner 算子参考文档。

  使用场景：使用 LLM 改写文本，覆盖原列。
---

# PromptedRefiner 算子参考

`PromptedRefiner` 使用 LLM 对列中文本进行改写/精炼，改写结果覆盖原列。

## 1. 导入

```python
from dataflow.operators.core_text import PromptedRefiner
```

## 2. 构造函数

```python
PromptedRefiner(
    llm_serving=llm_serving,
    system_prompt="You are a helpful agent.",
)
```

| 参数 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `llm_serving` | 是 | None | LLM服务对象 |
| `system_prompt` | 否 | `"You are a helpful agent."` | 文本改写指令 |

## 3. run() 方法签名

```python
op.run(
    storage=self.storage.step(),
    input_key="raw_content",
)
# 返回: None
```

| 参数 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `storage` | 是 | None | Storage 步骤对象 |
| `input_key` | 否 | `"raw_content"` | 待改写列名（原地覆盖） |

## 4. 使用示例

```python
from dataflow.operators.core_text import PromptedRefiner
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

        self.refiner = PromptedRefiner(
            llm_serving=self.llm_serving,
            system_prompt="改写以下文本使其更清晰。"
        )

    def forward(self):
        self.refiner.run(
            storage=self.storage.step(),
            input_key="content"
        )

if __name__ == "__main__":
    pipeline = MyPipeline()
    pipeline.forward()
```

## 5. 运行逻辑

1. 从 storage 读取 DataFrame。
2. 从 `input_key` 列提取文本。
3. 对每个非空行，拼接 `system_prompt + text` 作为 LLM 输入。
4. 调用 LLM 生成改写文本。
5. 用改写结果覆盖 `input_key` 列。
6. 空值行跳过（不发送给 LLM）。
7. 返回 None。

## 6. 重要说明

- 原地覆盖 `input_key` 列（原文本丢失）
- 若需保留原文本，先用 PandasOperator 复制列
- `input_key` 中的空行跳过但保留在 DataFrame 中
- 不存在 `output_key` 参数
