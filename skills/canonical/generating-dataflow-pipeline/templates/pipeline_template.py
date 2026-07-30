"""
Standard DataFlow Pipeline Template
Follow this structure for all generated pipelines
"""

from dataflow.operators.core_text import PromptedGenerator, PromptedFilter
from dataflow.serving import APILLMServing_request
from dataflow.utils.storage import FileStorage

class CustomPipeline:
    """
    Standard pipeline structure following repository conventions.
    Replace CustomPipeline with descriptive name based on task.
    """
    def __init__(self):
        # Storage configuration
        # REQUIRED: first_entry_file_name must point to a JSONL file (one JSON object per line)
        # NOT a JSON array. Example JSONL format:
        # {\"field1\": \"value1\", \"field2\": \"value2\"}
        # {\"field1\": \"value3\", \"field2\": \"value4\"}
        self.storage = FileStorage(
            first_entry_file_name="path/to/input.jsonl",
            cache_path="./cache",
            file_name_prefix="step",
            cache_type="jsonl"
        )

        # LLM serving configuration
        self.llm_serving = APILLMServing_request(
            api_url="https://api.openai.com/v1/chat/completions",
            model_name="gpt-4o",
            max_workers=10
        )

        # Define operator instances here
        # Replace with actual operators needed for your pipeline
        # Import additional operators as needed from dataflow.operators.*

    def forward(self):
        """
        Execute pipeline steps sequentially.
        Each step uses storage.step() to create checkpoint.
        """
        # Add operator.run() calls here in execution order
        # Each run() should specify:
        # - storage=self.storage.step()
        # - input_key (field from sample or previous step)
        # - output_key (new field to create)
        pass

if __name__ == "__main__":
    pipeline = CustomPipeline()
    pipeline.forward()
