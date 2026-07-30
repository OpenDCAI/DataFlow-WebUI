# Example: Diverse Sampling with KCenterGreedyFilter

## User Request
"Select 500 most representative samples by semantic diversity from 10,000 QA data rows"

## Sample Data
```jsonl
{"question": "What is photosynthesis?", "answer": "A process plants use to make food."}
{"question": "How do plants make food?", "answer": "Through photosynthesis using sunlight."}
{"question": "What is the speed of light?", "answer": "About 3×10^8 m/s."}
... (10,000 rows total)
```

## Field Mapping
```
Available in sample:
  - question   (text column used to compute embeddings)
  - answer     (preserved, not used for embedding)

Sampling condition:
  - Select the 500 most semantically diverse rows from 10,000

Field flow:
  question → [KCenterGreedyFilter] → 500-row subset (all original columns included)
```

## Complete Pipeline Code

```python
from dataflow.operators.core_text import KCenterGreedyFilter
from dataflow.serving import APILLMServing_request
from dataflow.utils.storage import FileStorage


class DiverseSamplingPipeline:
    def __init__(self):
        self.storage = FileStorage(
            first_entry_file_name="qa_pairs.jsonl",
            cache_path="./cache",
            file_name_prefix="sample_step",
            cache_type="jsonl"
        )

        self.embedding_serving = APILLMServing_request(
            api_url="https://api.openai.com/v1/embeddings",
            key_name_of_api_key="DF_API_KEY",
            model_name="text-embedding-3-small",
            max_workers=20,
        )

        self.filter = KCenterGreedyFilter(
            embedding_serving=self.embedding_serving,
            num_samples=500
        )

    def forward(self):
        self.filter.run(
            storage=self.storage.step(),
            input_key="question"
        )


if __name__ == "__main__":
    pipeline = DiverseSamplingPipeline()
    pipeline.forward()
```

## Output

10,000 input rows; the K-Center Greedy algorithm selects the 500 most semantically spread rows:

- Similar questions (e.g. "What is photosynthesis?" and "How do plants make food?") result in only one being kept
- The selected set covers as many distinct topics in the semantic space as possible

Output: 500 rows, all original columns (`question`, `answer`) included.

## Debugging
- `cache/sample_step_step1.jsonl` — contains 500 rows; column structure identical to input
