# Example: Generate Answers for a QA Benchmark with BenchAnswerGenerator

## User Request
"Generate model answers for each question in a QA evaluation set, save them to the `generated_ans` column, and keep the file ready for later scoring."

## Sample Data
```jsonl
{"question": "What is the capital of France?", "golden_answer": "Paris"}
{"question": "Who wrote Romeo and Juliet?", "golden_answer": "William Shakespeare"}
```

## Field Mapping
```
Available in sample:
  - question
  - golden_answer

To be generated:
  - generated_ans

Field flow:
  question -> [BenchAnswerGenerator] -> generated_ans
```

## Complete Pipeline Code

```python
from pathlib import Path
import os

import pandas as pd

from dataflow.operators.core_text import BenchAnswerGenerator
from dataflow.prompts.core_text import FormatStrPrompt
from dataflow.serving import APILLMServing_request
from dataflow.utils.storage import FileStorage


class BenchAnswerPipeline:
    def __init__(self):
        if "DF_API_KEY" not in os.environ:
            raise ValueError("Please set DF_API_KEY before running this example.")

        input_file = Path("qa_bench.jsonl")
        if not input_file.exists():
            pd.DataFrame(
                [
                    {"question": "What is the capital of France?", "golden_answer": "Paris"},
                    {"question": "Who wrote Romeo and Juliet?", "golden_answer": "William Shakespeare"},
                ]
            ).to_json(input_file, orient="records", lines=True, force_ascii=False)

        self.storage = FileStorage(
            first_entry_file_name=str(input_file),
            cache_path="./cache",
            file_name_prefix="bench_step",
            cache_type="jsonl",
        )

        self.llm_serving = APILLMServing_request(
            api_url="https://api.openai.com/v1/chat/completions",
            model_name="gpt-4o",
            max_workers=10,
        )

        prompt_template = FormatStrPrompt(
            f_str_template="Question: {question}\nAnswer:"
        )

        self.generator = BenchAnswerGenerator(
            eval_type="key2_qa",
            llm_serving=self.llm_serving,
            prompt_template=prompt_template,
            allow_overwrite=False,
        )

    def forward(self):
        return self.generator.run(
            storage=self.storage.step(),
            input_question_key="question",
            output_key="generated_ans",
        )


if __name__ == "__main__":
    pipeline = BenchAnswerPipeline()
    written_keys = pipeline.forward()
    print(f"Finished. Written keys: {written_keys}")

    result_df = pd.read_json("./cache/bench_step_step1.jsonl", lines=True)
    print(result_df[["question", "golden_answer", "generated_ans"]].head())
```

## Output

After generation, the output file contains all original columns plus
`generated_ans`.

## Debugging

- `cache/bench_step_step1.jsonl` contains the generated `generated_ans` column.
