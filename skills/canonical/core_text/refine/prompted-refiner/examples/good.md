# Example: Refine Product Descriptions with PromptedRefiner

## User Request
"用 LLM 改写 `description` 列，让文案更简洁专业，改写结果覆盖原列"

## Sample Data
```jsonl
{"product_name": "Laptop", "description": "This is a laptop it has good stuff and works well."}
{"product_name": "Coffee Maker", "description": "Makes coffee. Is good. People like it."}
```

## Field Mapping
```
Available in sample:
  - product_name  (源字段，不变)
  - description   (待改写列，改写后原地覆盖)

Field flow:
  description → [PromptedRefiner] → description (覆盖，内容已改写)
```

## Complete Pipeline Code

```python
from dataflow.operators.core_text import PromptedRefiner
from dataflow.serving import APILLMServing_request
from dataflow.utils.storage import FileStorage


class DescriptionRefinerPipeline:
    def __init__(self):
        self.storage = FileStorage(
            first_entry_file_name="products.jsonl",
            cache_path="./cache",
            file_name_prefix="refine_step",
            cache_type="jsonl"
        )

        self.llm_serving = APILLMServing_request(
            api_url="https://api.openai.com/v1/chat/completions",
            model_name="gpt-4o",
            max_workers=10
        )

        self.refiner = PromptedRefiner(
            llm_serving=self.llm_serving,
            system_prompt="Rewrite the following product description to be concise and professional. "
                          "Return only the rewritten description."
        )

    def forward(self):
        self.refiner.run(
            storage=self.storage.step(),
            input_key="description"
        )


if __name__ == "__main__":
    pipeline = DescriptionRefinerPipeline()
    pipeline.forward()
```

## Output

输入 2 行，`description` 列被 LLM 改写后原地覆盖：

| product_name | description（改写后） |
|---|---|
| `"Laptop"` | `"A high-performance laptop designed for productivity."` |
| `"Coffee Maker"` | `"A reliable coffee maker beloved by coffee enthusiasts."` |

输出 DataFrame 所有列结构不变，`description` 列内容已替换，无新增列。

## Debugging
- `cache/refine_step_step1.jsonl` — 含改写后的 `description` 列，无原始内容
