# Example: Article Summary Generation from Title and Body

## User Request
"Combine article title and body to generate a summary."

## Sample Data
```jsonl
{"title": "New AI Method Compresses LLMs Without Accuracy Loss", "body": "Researchers at MIT developed a pruning technique that reduces model size by 40% while maintaining benchmark performance..."}
{"title": "Exercise Boosts Cognitive Performance in Elderly", "body": "A longitudinal study involving 500 participants aged 65+ found that 30 minutes of daily aerobic exercise improved memory scores by 25%..."}
```

## Field Mapping
```
Available in sample:
  - title
  - body

To be generated:
  - summary

Template:
  f_str_template = "Title: {title}\n\nBody: {body}\n\nPlease write a concise summary."

Placeholder -> Column mapping:
  title = "title"
  body = "body"

Field flow:
  title + body -> [FormatStrPromptedGenerator] -> summary
```

## Complete Pipeline Code

```python
from pathlib import Path
import os

import pandas as pd

from dataflow.operators.core_text import FormatStrPromptedGenerator
from dataflow.prompts.core_text import FormatStrPrompt
from dataflow.serving import APILLMServing_request
from dataflow.utils.storage import FileStorage


class ArticleSummaryPipeline:
    def __init__(self):
        if "DF_API_KEY" not in os.environ:
            raise ValueError("Please set DF_API_KEY before running this example.")

        input_file = Path("articles.jsonl")
        pd.DataFrame(
            [
                {
                    "title": "New AI Method Compresses LLMs Without Accuracy Loss",
                    "body": "Researchers at MIT developed a pruning technique that reduces model size by 40% while maintaining benchmark performance...",
                },
                {
                    "title": "Exercise Boosts Cognitive Performance in Elderly",
                    "body": "A longitudinal study involving 500 participants aged 65+ found that 30 minutes of daily aerobic exercise improved memory scores by 25%...",
                },
            ]
        ).to_json(input_file, orient="records", lines=True, force_ascii=False)

        self.storage = FileStorage(
            first_entry_file_name=str(input_file),
            cache_path="./cache",
            file_name_prefix="summary_step",
            cache_type="jsonl",
        )

        self.llm_serving = APILLMServing_request(
            api_url="https://api.openai.com/v1/chat/completions",
            model_name="gpt-4o",
            max_workers=10,
        )

        prompt_template = FormatStrPrompt(
            f_str_template="Title: {title}\n\nBody: {body}\n\nPlease write a concise summary."
        )

        self.generator = FormatStrPromptedGenerator(
            llm_serving=self.llm_serving,
            system_prompt="You are a professional editor. Write concise, informative summaries.",
            prompt_template=prompt_template,
        )

    def forward(self):
        return self.generator.run(
            storage=self.storage.step(),
            output_key="summary",
            title="title",
            body="body",
        )


if __name__ == "__main__":
    pipeline = ArticleSummaryPipeline()
    output_key = pipeline.forward()
    print(f"Finished. Output column: {output_key}")

    result_df = pd.read_json("./cache/summary_step_step1.jsonl", lines=True)
    print(result_df[["title", "body", "summary"]].head())
```

## Debugging

- `cache/summary_step_step1.jsonl` contains the generated `summary` column.
