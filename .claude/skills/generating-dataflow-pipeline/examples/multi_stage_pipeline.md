# Example: Multi-Stage Prompted Pipeline + `GeneralFilter`

## Use Case
Complex tasks may require **multiple prompt-driven stages** (e.g., score -> refine -> rescore), then rule-based filtering.

## Target
"Perform initial quality scoring, refine medium-quality text, final scoring, then keep acceptable samples."

## Sample Data
```jsonl
{"raw_content": "Short draft text A..."}
{"raw_content": "Short draft text B..."}
```

## Intermediate Operator Decision
```json
{
  "ops": ["PromptedGenerator", "GeneralFilter", "PromptedGenerator", "PromptedGenerator", "GeneralFilter"],
  "field_flow": "raw_content -> init_score -> refine_content -> final_score -> filtered_rows",
  "reason": "This is a staged semantic workflow: initial scoring, transformation, final scoring, and deterministic filtering. Multiple PromptedGenerator steps are necessary because each stage has different responsibilities and outputs."
}
```

## Standard Pipeline Snippet
```python
from dataflow.operators.core_text import PromptedGenerator, GeneralFilter
from dataflow.serving import APILLMServing_request
from dataflow.utils.storage import FileStorage

class MultiStagePipeline:
    def __init__(self):
        # Input file MUST be JSONL format (one JSON object per line):
        # {\"raw_content\": \"Short draft text A...\"}
        # {\"raw_content\": \"Short draft text B...\"}
        self.storage = FileStorage(
            first_entry_file_name="content.jsonl",
            cache_path="./cache_multistage",
            file_name_prefix="stage_step",
            cache_type="jsonl"
        )

        self.llm_serving = APILLMServing_request(
            api_url="https://api.openai.com/v1/chat/completions",
            model_name="gpt-4o",
            max_workers=10
        )

        self.init_scorer = PromptedGenerator(
            llm_serving=self.llm_serving,
            system_prompt="Score this content from 1 to 5. Return only integer."
        )

        self.init_filter = GeneralFilter([
            lambda df: df["init_score"].astype(int) > 1
        ])

        self.refiner = PromptedGenerator(
            llm_serving=self.llm_serving,
            system_prompt="Refine this content for clarity and completeness."
        )

        self.final_scorer = PromptedGenerator(
            llm_serving=self.llm_serving,
            system_prompt="Final quality score from 1 to 5. Return only integer."
        )

        self.final_filter = GeneralFilter([
            lambda df: df["final_score"].astype(int) >= 3
        ])

    def forward(self):
        self.init_scorer.run(storage=self.storage.step(), input_key="raw_content", output_key="init_score")
        self.init_filter.run(storage=self.storage.step())
        self.refiner.run(storage=self.storage.step(), input_key="raw_content", output_key="refine_content")
        self.final_scorer.run(storage=self.storage.step(), input_key="refine_content", output_key="final_score")
        self.final_filter.run(storage=self.storage.step())

if __name__ == "__main__":
    pipeline = MultiStagePipeline()
    pipeline.forward()
```

## Key Notes
- Multiple `PromptedGenerator` stages are allowed when responsibilities differ.
- Do not split mechanically; each stage should have distinct semantic purpose.
- `GeneralFilter` rules must reference existing upstream fields (`init_score`, `final_score`).
