# Example: Filter Generated Content by Score and Length

## User Request
"Filter out generated content with a score below 4 and text length shorter than 20 characters"

## Sample Data
```jsonl
{"text": "Good.", "score": 3}
{"text": "This is a well-written and informative summary of the topic.", "score": 5}
{"text": "Short.", "score": 4}
{"text": "A comprehensive analysis with clear structure and accurate facts.", "score": 4}
```

## Field Mapping
```
Available in sample:
  - text  (text column)
  - score (numeric score column)

Filter conditions (AND):
  1. score >= 4
  2. len(text) >= 20

Field flow:
  text + score → [GeneralFilter] → filtered rows (no new columns added)
```

## Complete Pipeline Code

```python
from dataflow.operators.core_text import GeneralFilter
from dataflow.utils.storage import FileStorage


class QualityFilterPipeline:
    def __init__(self):
        self.storage = FileStorage(
            first_entry_file_name="generated.jsonl",
            cache_path="./cache",
            file_name_prefix="filter_step",
            cache_type="jsonl"
        )

        self.filter = GeneralFilter(
            filter_rules=[
                lambda df: df["score"] >= 4,
                lambda df: df["text"].str.len() >= 20,
            ]
        )

    def forward(self):
        self.filter.run(
            storage=self.storage.step()
        )


if __name__ == "__main__":
    pipeline = QualityFilterPipeline()
    pipeline.forward()
```

## Output

4 input rows; after filtering, only rows satisfying **all conditions** are kept:

| text | score | Kept? |
|------|-------|-------|
| `"Good."` | 3 | No — score < 4 |
| `"This is a well-written..."` | 5 | Yes |
| `"Short."` | 4 | No — len < 20 |
| `"A comprehensive analysis..."` | 4 | Yes |

## Debugging
- `cache/filter_step_step1.jsonl` — contains only kept rows; column structure unchanged; no new columns added
