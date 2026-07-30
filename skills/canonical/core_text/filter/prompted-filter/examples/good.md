# Example: Filter Generated Descriptions by LLM Quality Score

## User Request
"Use LLM to score generated product descriptions; keep only content with a quality score of 4 or above"

## Sample Data
```jsonl
{"product_name": "Laptop", "generated_description": "A laptop."}
{"product_name": "Coffee Maker", "generated_description": "This premium coffee maker brews rich, aromatic coffee with customizable strength settings."}
```

## Field Mapping
```
Available in sample:
  - product_name        (source field)
  - generated_description (text to evaluate)

To be generated:
  - quality_score (LLM score, written by PromptedFilter)

Filter condition:
  quality_score in [4, 5]

Field flow:
  generated_description → [PromptedFilter] → quality_score (+ rows outside range deleted)
```

## Complete Pipeline Code

```python
from dataflow.operators.core_text import PromptedFilter
from dataflow.serving import APILLMServing_request
from dataflow.utils.storage import FileStorage


class DescriptionQualityPipeline:
    def __init__(self):
        self.storage = FileStorage(
            first_entry_file_name="products.jsonl",
            cache_path="./cache",
            file_name_prefix="filter_step",
            cache_type="jsonl"
        )

        self.llm_serving = APILLMServing_request(
            api_url="https://api.openai.com/v1/chat/completions",
            model_name="gpt-4o",
            max_workers=10
        )

        self.filter = PromptedFilter(
            llm_serving=self.llm_serving,
            system_prompt="Evaluate the quality of this product description on a scale from 1 to 5. "
                          "Consider clarity, detail, and appeal. Return only the integer score.",
            min_score=4,
            max_score=5
        )

    def forward(self):
        self.filter.run(
            storage=self.storage.step(),
            input_key="generated_description",
            output_key="quality_score"
        )


if __name__ == "__main__":
    pipeline = DescriptionQualityPipeline()
    pipeline.forward()
```

## Output

2 input rows; after LLM scoring, rows with `quality_score < 4` are deleted:

| generated_description | quality_score | Kept? |
|-----------------------|---------------|-------|
| `"A laptop."` | 1 | No — below min_score=4 |
| `"This premium coffee maker..."` | 5 | Yes |

The output DataFrame retains all original columns and adds the `quality_score` column.

## Debugging
- `cache/filter_step_step1.jsonl` — contains only rows with quality_score ∈ [4, 5], including the quality_score column
