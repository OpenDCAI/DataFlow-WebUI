# Example: Process Long Documents with ChunkedPromptedGenerator

## User Request
"Read long document files from the `file_path` column, process them chunk by chunk with an LLM, write the generated results into new text files, and store those file paths in `output_path`."

## Sample Data
```jsonl
{"doc_id": 1, "file_path": "docs/report_2024.txt"}
{"doc_id": 2, "file_path": "docs/whitepaper.txt"}
```

## Field Mapping
```
Available in sample:
  - doc_id
  - file_path

To be generated:
  - output_path

Field flow:
  file_path -> [ChunkedPromptedGenerator] -> output_path
```

## Complete Pipeline Code

```python
from pathlib import Path
import os

import pandas as pd
import tiktoken

from dataflow.operators.core_text import ChunkedPromptedGenerator
from dataflow.serving import APILLMServing_request
from dataflow.utils.storage import FileStorage


class LongDocSummaryPipeline:
    def __init__(self):
        if "DF_API_KEY" not in os.environ:
            raise ValueError("Please set DF_API_KEY before running this example.")

        docs_dir = Path("docs")
        docs_dir.mkdir(exist_ok=True)

        report_path = docs_dir / "report_2024.txt"
        whitepaper_path = docs_dir / "whitepaper.txt"

        report_path.write_text(
            "This is a long annual report. " * 2000,
            encoding="utf-8",
        )
        whitepaper_path.write_text(
            "This is a long technical whitepaper. " * 2000,
            encoding="utf-8",
        )

        input_file = Path("doc_list.jsonl")
        pd.DataFrame(
            [
                {"doc_id": 1, "file_path": str(report_path)},
                {"doc_id": 2, "file_path": str(whitepaper_path)},
            ]
        ).to_json(input_file, orient="records", lines=True, force_ascii=False)

        self.storage = FileStorage(
            first_entry_file_name=str(input_file),
            cache_path="./cache",
            file_name_prefix="chunk_step",
            cache_type="jsonl",
        )

        self.llm_serving = APILLMServing_request(
            api_url="https://api.openai.com/v1/chat/completions",
            model_name="gpt-4o",
            max_workers=4,
        )

        self.generator = ChunkedPromptedGenerator(
            llm_serving=self.llm_serving,
            system_prompt="Please summarize the following text concisely.",
            max_chunk_len=2048,
            enc=tiktoken.get_encoding("cl100k_base"),
            separator="\n\n",
        )

    def forward(self):
        return self.generator.run(
            storage=self.storage.step(),
            input_path_key="file_path",
            output_path_key="output_path",
        )


if __name__ == "__main__":
    pipeline = LongDocSummaryPipeline()
    output_key = pipeline.forward()
    print(f"Finished. Output column: {output_key}")

    result_df = pd.read_json("./cache/chunk_step_step1.jsonl", lines=True)
    print(result_df[["doc_id", "file_path", "output_path"]].head())
```

## Output

For an input file like `docs/report_2024.txt`, the current source code writes
the generated result to:

```text
docs/report_2024_llm_output.txt
```

The resulting dataframe stores that derived path in the `output_path` column.

## Debugging

- `cache/chunk_step_step1.jsonl` contains the generated `output_path` column.
- The actual generated text is written into files whose names end with `_llm_output.txt`.
