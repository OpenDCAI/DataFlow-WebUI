# Example: Generate Text Embeddings with EmbeddingGenerator

## User Request
"Convert the `content` column of articles into embedding vectors, store them in the `embedding` column, and keep the result ready for downstream similarity computation."

## Sample Data
```jsonl
{"id": 1, "content": "Deep learning is a subset of machine learning."}
{"id": 2, "content": "Natural language processing enables computers to understand text."}
{"id": 3, "content": "Transformers revolutionized NLP with attention mechanisms."}
```

## Field Mapping
```
Available in sample:
  - id
  - content

To be generated:
  - embedding

Field flow:
  content -> [EmbeddingGenerator] -> embedding
```

## Complete Pipeline Code

```python
from pathlib import Path
import os

import pandas as pd

from dataflow.operators.core_text import EmbeddingGenerator
from dataflow.serving import APILLMServing_request
from dataflow.utils.storage import FileStorage


class EmbeddingPipeline:
    def __init__(self):
        if "DF_API_KEY" not in os.environ:
            raise ValueError("Please set DF_API_KEY before running this example.")

        input_file = Path("articles.jsonl")
        pd.DataFrame(
            [
                {"id": 1, "content": "Deep learning is a subset of machine learning."},
                {"id": 2, "content": "Natural language processing enables computers to understand text."},
                {"id": 3, "content": "Transformers revolutionized NLP with attention mechanisms."},
            ]
        ).to_json(input_file, orient="records", lines=True, force_ascii=False)

        self.storage = FileStorage(
            first_entry_file_name=str(input_file),
            cache_path="./cache",
            file_name_prefix="embed_step",
            cache_type="jsonl",
        )

        self.embedding_serving = APILLMServing_request(
            api_url="https://api.openai.com/v1/embeddings",
            key_name_of_api_key="DF_API_KEY",
            model_name="text-embedding-3-small",
            max_workers=20,
        )

        self.generator = EmbeddingGenerator(
            embedding_serving=self.embedding_serving,
        )

    def forward(self):
        return self.generator.run(
            storage=self.storage.step(),
            input_key="content",
            output_key="embedding",
        )


if __name__ == "__main__":
    pipeline = EmbeddingPipeline()
    written_keys = pipeline.forward()
    print(f"Finished. Written keys: {written_keys}")

    result_df = pd.read_json("./cache/embed_step_step1.jsonl", lines=True)
    print(result_df[["id", "content", "embedding"]].head())
```

## Output

After generation, the output file contains all original columns plus the
`embedding` column, where each row stores one embedding vector as a Python list.

## Debugging

- `cache/embed_step_step1.jsonl` contains the generated `embedding` column.
