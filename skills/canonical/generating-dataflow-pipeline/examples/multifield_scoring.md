# Example: Multi-Field Scoring with `FormatStrPromptedGenerator`

## Use Case
When a task needs scoring or generation based on **multiple fields together** (instead of one field), use `FormatStrPromptedGenerator`.

## Target
"Generate SFT outputs, then score each sample using both `instruction` and `output`, and keep high-quality data."

## Sample Data
```jsonl
{"instruction": "Explain overfitting.", "output": "Overfitting happens when..."}
{"instruction": "What is gradient descent?", "output": "Gradient descent is..."}
```

## Intermediate Operator Decision
```json
{
  "ops": ["FormatStrPromptedGenerator", "GeneralFilter"],
  "field_flow": "instruction+output -> data_score -> filtered_rows",
  "reason": "Scoring depends on multiple fields at once, so FormatStrPromptedGenerator is preferred over PromptedGenerator. GeneralFilter then keeps rows by score threshold."
}
```

## Standard Pipeline Snippet
```python
from dataflow.operators.core_text import FormatStrPromptedGenerator, GeneralFilter
from dataflow.serving import APILLMServing_request
from dataflow.utils.storage import FileStorage
from dataflow.prompts.core_text import FormatStrPrompt

class ScoringPipeline:
    def __init__(self):
        # Input file MUST be JSONL format (one JSON object per line):
        # {\"instruction\": \"Explain overfitting.\", \"output\": \"Overfitting happens when...\"}
        # {\"instruction\": \"What is gradient descent?\", \"output\": \"Gradient descent is...\"}
        self.storage = FileStorage(
            first_entry_file_name="samples.jsonl",
            cache_path="./cache_scoring",
            file_name_prefix="score_step",
            cache_type="jsonl"
        )

        self.llm_serving = APILLMServing_request(
            api_url="https://api.openai.com/v1/chat/completions",
            model_name="gpt-4o",
            max_workers=10
        )

        prompt_template = FormatStrPrompt(
            f_str_template="Please rate this sample. instruction: {instruction}; output: {output}. Return only integer 1-5."
        )

        self.rater = FormatStrPromptedGenerator(
            llm_serving=self.llm_serving,
            system_prompt="You are a strict data quality evaluator.",
            prompt_template=prompt_template
        )

        self.filter = GeneralFilter([
            lambda df: df["data_score"].astype(int) >= 4
        ])

    def forward(self):
        self.rater.run(
            storage=self.storage.step(),
            output_key="data_score",
            instruction="instruction",
            output="output"
        )

        self.filter.run(storage=self.storage.step())

if __name__ == "__main__":
    pipeline = ScoringPipeline()
    pipeline.forward()
```

## Key Notes
- Use `FormatStrPromptedGenerator` when the prompt needs 2+ input fields.
- Ensure mapped columns exist (`instruction`, `output`) before calling `run()`.
- Ensure `GeneralFilter` references existing field `data_score`.
