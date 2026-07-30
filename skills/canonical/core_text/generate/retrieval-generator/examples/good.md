# Example: RetrievalGenerator with LightRAGServing

## User Request

"For each question, retrieve relevant content from the knowledge base and generate an answer using LightRAG, writing results to the `rag_answer` column."

## Sample Data

```jsonl
{"question_id": 1, "raw_content": "What are the main causes of climate change?"}
{"question_id": 2, "raw_content": "How does photosynthesis work?"}
```

## Field Mapping

```text
Available in sample:
  - question_id  (preserved, unchanged)
  - raw_content  (query text sent into RetrievalGenerator)

To be generated:
  - rag_answer   (retrieval-augmented generated answer)

Field flow:
  raw_content -> RetrievalGenerator -> rag_answer
```

## Complete Pipeline Code

```python
import asyncio

from dataflow.operators.core_text import RetrievalGenerator
from dataflow.serving import LightRAGServing
from dataflow.utils.storage import FileStorage


class RetrievalRAGPipeline:
    def __init__(self):
        self.storage = FileStorage(
            first_entry_file_name="questions.jsonl",
            cache_path="./cache",
            file_name_prefix="rag_step",
            cache_type="jsonl"
        )

        # LightRAGServing.create(...) is async, so initialize it later.
        self.llm_serving = None
        self.generator = None

    async def initialize(self):
        self.llm_serving = await LightRAGServing.create(
            api_url="https://api.openai.com/v1",
            llm_model_name="gpt-4o",
            embed_model_name="bge-m3:latest",
            embed_binding_host="http://localhost:11434",
            document_list=["knowledge_base.txt"]
        )
        if self.llm_serving is None:
            raise RuntimeError("LightRAGServing initialization failed.")

        self.generator = RetrievalGenerator(
            llm_serving=self.llm_serving,
            system_prompt="Answer the question based on the retrieved knowledge."
        )

    async def forward(self):
        if self.generator is None:
            await self.initialize()

        await self.generator.run(
            storage=self.storage.step(),
            input_key="raw_content",
            output_key="rag_answer"
        )


async def main():
    pipeline = RetrievalRAGPipeline()
    await pipeline.initialize()
    await pipeline.forward()


if __name__ == "__main__":
    asyncio.run(main())
```

## Output

After running, the cached result keeps the original rows and adds a new `rag_answer` column.

## Debugging

- `LightRAGServing` should be created with `await LightRAGServing.create(...)`, not `LightRAGServing(host=..., port=...)`.
- `RetrievalGenerator.run()` is async and must be awaited.
- If any `raw_content` row is empty, the operator may fail when assigning outputs back to the DataFrame.
