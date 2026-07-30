# Example: Article Title Generation

## User Request
"Generate a title from article abstracts"

## Sample Data
```jsonl
{"abstract": "Researchers developed a new method to compress large language models without losing accuracy."}
{"abstract": "A study shows that regular exercise significantly improves cognitive performance in elderly adults."}
```

## Field Mapping
```
Available in sample:
  - abstract (source field)

To be generated:
  - generated_title (output from PromptedGenerator)

Field flow:
  abstract → [PromptedGenerator] → generated_title
```

## Complete Pipeline Code

```python
from dataflow.operators.core_text import PromptedGenerator
from dataflow.serving import APILLMServing_request
from dataflow.utils.storage import FileStorage


class TitleGenerationPipeline:
    def __init__(self):
        self.storage = FileStorage(
            first_entry_file_name="articles.jsonl",
            cache_path="./cache",
            file_name_prefix="title_step",
            cache_type="jsonl"
        )

        self.llm_serving = APILLMServing_request(
            api_url="https://api.openai.com/v1/chat/completions",
            model_name="gpt-4o",
            max_workers=10
        )

        self.generator = PromptedGenerator(
            llm_serving=self.llm_serving,
            system_prompt="You are an academic editor. Write concise, engaging titles.",
            user_prompt="Generate a title for the following abstract:\n"
        )

    def forward(self):
        self.generator.run(
            storage=self.storage.step(),
            input_key="abstract",
            output_key="generated_title"
        )


if __name__ == "__main__":
    pipeline = TitleGenerationPipeline()
    pipeline.forward()
```

## Debugging
- `cache/title_step_step1.jsonl` — inspect generated titles; each row gains a new `generated_title` column
