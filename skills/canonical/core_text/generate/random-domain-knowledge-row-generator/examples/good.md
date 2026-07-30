# Example: Generate Domain SFT Samples into an Existing DataFrame

## Use Case

"I need 200 synthetic SFT samples in the machine learning domain, and I want the results written into a new column."

## Important Behavior

`RandomDomainKnowledgeRowGenerator` does not create rows by itself. It reads the existing DataFrame from storage, generates `generation_num` outputs, and assigns them into one column. Therefore, the seed DataFrame row count should match `generation_num`.

## Field Mapping

```text
Input rows:
  - seed_id (only used to provide row count)

Generated column:
  - generated_content

Field flow:
  seed rows (200) -> RandomDomainKnowledgeRowGenerator -> generated_content
```

## Complete Pipeline Code

```python
import json
import os

from dataflow.operators.core_text import RandomDomainKnowledgeRowGenerator
from dataflow.prompts.general_text import SFTFromScratchGeneratorPrompt
from dataflow.serving import APILLMServing_request
from dataflow.utils.storage import FileStorage


class DomainKnowledgePipeline:
    def __init__(self):
        if not os.getenv("DF_API_KEY"):
            raise EnvironmentError("Please set DF_API_KEY before running this example.")

        generation_num = 200
        seed_file = "seed.jsonl"

        # The current operator writes one generated result per existing row,
        # so prepare exactly `generation_num` seed rows.
        with open(seed_file, "w", encoding="utf-8") as f:
            for i in range(generation_num):
                f.write(json.dumps({"seed_id": i}, ensure_ascii=False) + "\n")

        self.storage = FileStorage(
            first_entry_file_name=seed_file,
            cache_path="./cache",
            file_name_prefix="domain_step",
            cache_type="jsonl",
        )

        self.llm_serving = APILLMServing_request(
            api_url="https://api.openai.com/v1/chat/completions",
            model_name="gpt-4o",
            max_workers=10,
        )

        self.generator = RandomDomainKnowledgeRowGenerator(
            llm_serving=self.llm_serving,
            generation_num=generation_num,
            domain_keys="machine learning, deep learning, neural networks",
            prompt_template=SFTFromScratchGeneratorPrompt(),
        )

    def forward(self):
        output_key = self.generator.run(
            storage=self.storage.step(),
            output_key="generated_content",
        )
        print(f"Generated column: {output_key}")


if __name__ == "__main__":
    pipeline = DomainKnowledgePipeline()
    pipeline.forward()
```

## Expected Output Shape

After running, the cached DataFrame still has 200 rows and now includes a `generated_content` column. Each cell is one LLM-generated JSON string produced from the same domain prompt family.

## Debugging

- If the seed file has 0 rows but `generation_num > 0`, column assignment can fail.
- If the seed file has 50 rows and `generation_num=200`, column assignment can fail because the lengths do not match.
- If `prompt_template=None`, the operator fails before calling the LLM.
