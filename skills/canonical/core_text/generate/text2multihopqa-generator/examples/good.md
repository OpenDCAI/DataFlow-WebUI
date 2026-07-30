# Example: Generate Multi-hop QA Pairs from Documents

## User Request

"Generate multi-hop reasoning QA pairs from cleaned document paragraphs, up to 3 QA pairs per paragraph."

## Sample Data

```jsonl
{"doc_id": 1, "cleaned_chunk": "The Eiffel Tower was built in 1889 for the World's Fair. It was designed by Gustave Eiffel and stands 330 meters tall. The tower is located in Paris, France, and attracts millions of tourists each year."}
{"doc_id": 2, "cleaned_chunk": "Marie Curie was born in Warsaw in 1867 and later moved to Paris to study physics. She discovered polonium and radium. She became the first person to win Nobel Prizes in two different sciences: physics and chemistry."}
```

## Field Mapping

```text
Available in sample:
  - doc_id
  - cleaned_chunk

To be generated:
  - QA_pairs
  - QA_metadata

Field flow:
  cleaned_chunk -> Text2MultiHopQAGenerator -> QA_pairs + QA_metadata
```

## Complete Pipeline Code

```python
from dataflow.operators.core_text import Text2MultiHopQAGenerator
from dataflow.serving import APILLMServing_request
from dataflow.utils.storage import FileStorage


class MultiHopQAPipeline:
    def __init__(self):
        self.storage = FileStorage(
            first_entry_file_name="documents.jsonl",
            cache_path="./cache",
            file_name_prefix="multihop_step",
            cache_type="jsonl"
        )

        self.llm_serving = APILLMServing_request(
            api_url="https://api.openai.com/v1/chat/completions",
            model_name="gpt-4o",
            max_workers=10
        )

        self.generator = Text2MultiHopQAGenerator(
            llm_serving=self.llm_serving,
            num_q=3
        )

    def forward(self):
        self.generator.run(
            storage=self.storage.step(),
            input_key="cleaned_chunk",
            output_key="QA_pairs",
            output_meta_key="QA_metadata"
        )


if __name__ == "__main__":
    pipeline = MultiHopQAPipeline()
    pipeline.forward()
```

## Output

The output keeps one row per surviving input record. Each remaining row gets:

- `QA_pairs`: a list of up to 3 generated QA dicts
- `QA_metadata`: a metadata dict for that row

Rows that produce no valid QA pairs are filtered out.

## Debugging

- `cleaned_chunk` must exist before running.
- `QA_pairs` must not already exist before running.
- Short or low-quality text may produce an empty QA list and then be removed from the final DataFrame.
