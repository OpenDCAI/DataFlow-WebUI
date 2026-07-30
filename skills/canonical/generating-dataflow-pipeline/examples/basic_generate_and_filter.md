# Example: Product Description Generation

## User Request
"Generate product descriptions from product names and filter high-quality ones"

## Sample Data
```jsonl
{"product_name": "Laptop", "category": "Electronics"}
{"product_name": "Coffee Maker", "category": "Appliances"}
```

## Response

### Intermediate Operator Decision
```json
{
  "ops": ["PromptedGenerator", "PromptedFilter"],
  "field_flow": "product_name -> generated_description -> quality_score",
  "reason": "Target requires generation + quality filtering. PromptedGenerator is sufficient (single input field 'product_name'). PromptedFilter evaluates and filters by quality score. No need for FormatStrPromptedGenerator since we only use one input field. Field dependencies satisfied: product_name exists in sample, generated_description created before filtering."
}
```

### 1. Field Mapping
```
Available in sample:
  - product_name (source field)
  - category (available but not used)

To be generated:
  - generated_description (output from step 1)
  - quality_score (output from step 2)

Field flow:
  product_name → [PromptedGenerator] → generated_description → [PromptedFilter] → quality_score
```

### 2. Ordered Operator List
1. **PromptedGenerator**: Generate descriptions from product_name
   - Why: Single input field, simple generation task
   - Input: product_name (exists in sample)
   - Output: generated_description

2. **PromptedFilter**: Score and filter descriptions
   - Why: Need LLM-based quality evaluation
   - Input: generated_description (created by step 1)
   - Output: quality_score
   - Filter: Keep only score >= 4

### 3. Reasoning Summary
- Task is straightforward: generate text → filter by quality
- PromptedGenerator chosen over FormatStrPromptedGenerator because only one input field needed
- No need for additional operators (Text2MultiHopQAGenerator, KBC trio, etc.) as they don't match requirements
- Field dependencies satisfied: generated_description created before being filtered
- Only 1 prompt-driven generator used (well within limit)

### 4. Complete Standard Pipeline Code
```python
from dataflow.operators.core_text import PromptedGenerator, PromptedFilter
from dataflow.serving import APILLMServing_request
from dataflow.utils.storage import FileStorage

class ProductDescriptionPipeline:
    def __init__(self):
        # Input file MUST be JSONL format (one JSON object per line):
        # {\"product_name\": \"Laptop\", \"category\": \"Electronics\"}
        # {\"product_name\": \"Mouse\", \"category\": \"Accessories\"}
        self.storage = FileStorage(
            first_entry_file_name="products.jsonl",
            cache_path="./cache",
            file_name_prefix="product_step",
            cache_type="jsonl"
        )

        self.llm_serving = APILLMServing_request(
            api_url="https://api.openai.com/v1/chat/completions",
            model_name="gpt-4o",
            max_workers=10
        )

        self.generator = PromptedGenerator(
            llm_serving=self.llm_serving,
            system_prompt="You are a product description writer. Write compelling, concise descriptions.",
            user_prompt="Write a product description for: "
        )

        self.filter = PromptedFilter(
            llm_serving=self.llm_serving,
            system_prompt="Evaluate product description quality on scale 1-5. Consider clarity, appeal, and completeness.",
            min_score=4,
            max_score=5
        )

    def forward(self):
        self.generator.run(
            storage=self.storage.step(),
            input_key="product_name",
            output_key="generated_description"
        )

        self.filter.run(
            storage=self.storage.step(),
            input_key="generated_description",
            output_key="quality_score"
        )

if __name__ == "__main__":
    pipeline = ProductDescriptionPipeline()
    pipeline.forward()
```

### 5. Adjustable Parameters / Caveats

**Tunable Parameters**:
- `system_prompt` (generator): Adjust tone, length, focus
- `user_prompt` (generator): Add context like "for e-commerce"
- `min_score` (filter): Lower to 3 for more lenient filtering
- `max_workers`: Increase for faster processing

**Fallback Strategies**:
- If < 50% pass filter: Enhance system_prompt with more detailed instructions
- If descriptions too generic: Add category field using FormatStrPromptedGenerator
- If quality inconsistent: Add few-shot examples to prompt

**Debugging**:
- Check `cache/product_step_1.jsonl` for generated descriptions
- Check `cache/product_step_2.jsonl` for filtered results
- Compare row counts to see pass rate
