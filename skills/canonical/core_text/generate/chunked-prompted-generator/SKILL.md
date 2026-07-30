---
name: chunked-prompted-generator
description: >-
  Reference documentation for the ChunkedPromptedGenerator operator. Covers the
  constructor, file-path based chunking flow, actual prompt construction, and
  output file writing behavior.

  Use when: the dataframe stores file paths, the file content may exceed a
  single LLM context window, and you want the generated results written into
  new text files.
---

# ChunkedPromptedGenerator Operator Reference

`ChunkedPromptedGenerator` reads file paths from a dataframe column, loads each
file from disk, recursively splits long content into chunks, calls the LLM on
all chunks, joins the generated outputs with a separator, writes the joined
result into a new text file, and stores that output file path back into the
dataframe.

## 1. Import

```python
from dataflow.operators.core_text import ChunkedPromptedGenerator
```

## 2. Constructor

```python
ChunkedPromptedGenerator(
    llm_serving=llm,
    system_prompt="You are a helpful agent.",
    json_schema=None,
    max_chunk_len=128000,
    enc=tiktoken.get_encoding("cl100k_base"),
    separator="\n",
)
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `llm_serving` | Yes | None | LLM service object implementing `generate_from_input(...)` |
| `system_prompt` | No | `"You are a helpful agent."` | Prepended to each chunk as plain text before the chunk content |
| `json_schema` | No | `None` | Optional schema forwarded to `generate_from_input(...)` |
| `max_chunk_len` | No | `128000` | Maximum token count per chunk |
| `enc` | No | `tiktoken.get_encoding("cl100k_base")` | Encoder used for token counting through `len(enc.encode(text))` |
| `separator` | No | `"\n"` | Join separator for chunk outputs |


## 3. run() Signature

```python
op.run(
    storage=self.storage.step(),
    input_path_key="file_path",
    output_path_key="output_path",
)
# returns: output_path_key
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `storage` | Yes | None | Current operator-step storage object |
| `input_path_key` | Yes | None | Column containing input file paths |
| `output_path_key` | Yes | None | Column used to store generated output file paths |

## 4. Actual Execution Logic

The current implementation behaves as follows:

1. Read the dataframe from `storage`.
2. For each row, read the file content from `Path(row[input_path_key]).read_text(encoding="utf-8")`.
3. Count tokens with `len(enc.encode(text))`.
4. If the text exceeds `max_chunk_len`, recursively split it into two halves by
   character position, not by sentence or token boundary.
5. For each chunk, build one LLM input as:

```python
system_prompt + "\n" + chunk
```

6. Flatten all chunks from all rows into a single global batch.
7. Call:

```python
llm_serving.generate_from_input(all_llm_inputs)
```

or, when `json_schema` is provided:

```python
llm_serving.generate_from_input(all_llm_inputs, json_schema=json_schema)
```

8. Regroup the responses back by original row.
9. For each row, join that row's chunk results with the configured separator.
10. Write the joined text into a new file whose path is derived automatically as:

```python
row[input_path_key].split(".")[0] + "_llm_output.txt"
```

11. Store that generated output file path into `output_path_key`.
12. Persist the dataframe through `storage.write(dataframe)` and return `output_path_key`.

## 5. Important Rules

1. Values in `input_path_key` must be readable filesystem paths, not inline text.
2. `input_path_key` and `output_path_key` are required runtime arguments; the source code does not define defaults for them.
3. Chunk splitting is recursive bisection by character index, guided by token counts, not semantic splitting.
4. Output files are auto-named from the input path using the `_llm_output.txt` suffix. The value already present in `output_path_key` is not used to decide the write location.
5. If global LLM generation fails, the implementation writes empty content per row into the derived output files and still writes `output_path_key` back into the dataframe.
6. All chunk requests across all rows are sent in one global batch before results are regrouped by row.

## 6. Typical Usage

```python
import tiktoken

from dataflow.operators.core_text import ChunkedPromptedGenerator

generator = ChunkedPromptedGenerator(
    llm_serving=self.llm_serving,
    system_prompt="Please summarize the following text.",
    max_chunk_len=4096,
    enc=tiktoken.get_encoding("cl100k_base"),
    separator="\n\n",
)

generator.run(
    storage=self.storage.step(),
    input_path_key="file_path",
    output_path_key="output_path",
)
```
