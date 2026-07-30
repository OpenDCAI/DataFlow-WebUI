---
name: text2multihopqa-generator
description: >-
  Reference documentation for the Text2MultiHopQAGenerator operator.

  [Purpose] Generates multi-hop QA pairs from one text column and writes two
  output columns: one for `qa_pairs` and one for metadata.

  [When to use] Use it when you want reasoning-style QA pairs derived from
  longer text chunks. If only simple single-hop QA is needed, use
  `Text2QAGenerator` instead.
---

# Text2MultiHopQAGenerator Operator Reference

`Text2MultiHopQAGenerator` reads one text column, generates up to `num_q` multi-hop QA pairs per input row, stores the per-row QA list in `output_key`, stores metadata in `output_meta_key`, then filters out rows whose generated QA list is empty.

See `examples/good.md` for a valid pipeline pattern and `examples/bad.md` for common failure cases.

---

## 1. Import

```python
from dataflow.operators.core_text import Text2MultiHopQAGenerator
```

---

## 2. Constructor

```python
Text2MultiHopQAGenerator(
    llm_serving=llm,
    seed=0,
    lang="en",
    prompt_template=None,
    num_q=5,
)
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `llm_serving` | Yes | None | LLM backend passed through to `ExampleConstructor`, which later calls `generate_from_input(...)`. |
| `seed` | No | `0` | Used to initialize `random.Random(seed)`. |
| `lang` | No | `"en"` | Controls prompt construction and sentence splitting logic. |
| `prompt_template` | No | `None` | If omitted, uses `Text2MultiHopQAGeneratorPrompt(lang=self.lang)`. |
| `num_q` | No | `5` | Maximum number of QA pairs kept per row after generation. |

---

## 3. run() Signature

```python
op.run(
    storage=self.storage.step(),
    input_key="cleaned_chunk",
    output_key="QA_pairs",
    output_meta_key="QA_metadata",
)
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `storage` | Yes | None | Used as `storage.read("dataframe")` and `storage.write(dataframe)`. |
| `input_key` | No | `"cleaned_chunk"` | Source text column. This column must already exist. |
| `output_key` | No | `"QA_pairs"` | Output column containing a list of QA dicts for each remaining row. This column must not already exist. |
| `output_meta_key` | No | `"QA_metadata"` | Output column containing metadata dicts for each remaining row. |

### Return Value

The method returns `[output_key]`.

---

## 4. Actual Runtime Logic

The source code behavior is:

1. Read the DataFrame from storage.
2. Validate that `input_key` exists.
3. Validate that `output_key` does not already exist.
4. Read all texts from `dataframe[input_key].tolist()`.
5. Generate one example record per input row via `process_batch(...)`.
6. Truncate each row's `qa_pairs` list to at most `num_q`.
7. Write QA lists to `output_key` and metadata dicts to `output_meta_key`.
8. Drop rows whose `output_key` is not a non-empty list.
9. Write the filtered DataFrame back to storage.
10. Return `[output_key]`.

Important consequences:

- The operator does not expand one row into multiple rows.
- The final row count is less than or equal to the input row count.
- Rows with empty generated QA lists are removed entirely.

---

## 5. Text Filtering Rules

Inside `ExampleConstructor`, a text can fail before QA generation if:

- it is not a string,
- its length is less than `100`,
- its length is greater than `200000`,
- it fails the basic sentence-count or special-character quality checks.

When that happens, the row gets an empty `qa_pairs` list first, and is then filtered out by `run()`.

---

## 6. Important Constraints

1. `input_key` must exist, otherwise `run()` raises `ValueError`.
2. `output_key` must not already exist, otherwise `run()` raises `ValueError`.
