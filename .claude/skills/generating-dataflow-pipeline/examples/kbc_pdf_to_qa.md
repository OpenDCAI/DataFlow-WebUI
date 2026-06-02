# Example: File Path to QA Pipeline (Knowledge Base Cleaning)

## User Request
"Extract multi-hop QA pairs from documents after cleaning and chunking"

## Note
KBC supports multiple file types: `.pdf`, `.png`, `.jpg`, `.jpeg`, `.webp`, `.gif` (→ MinerU), `.html`, `.xml` (→ trafilatura), `.txt`, `.md` (→ passed through directly to chunking). This example uses PDF paths, but the same pipeline works for `.md` or `.txt` paths — Step 1 simply skips conversion for those types.

## Sample Data
```jsonl
{"pdf_path": "/data/research_paper.pdf"}
{"pdf_path": "/data/technical_doc.pdf"}
```

## Response

### Intermediate Operator Decision
```json
{
  "ops": ["FileOrURLToMarkdownConverterFlash", "KBCChunkGenerator", "KBCTextCleaner", "Text2MultiHopQAGenerator", "PromptedFilter"],
  "field_flow": "pdf_path -> text_path -> raw_chunk -> cleaned_chunk -> QA_pairs -> qa_eval (score & filter)",
  "reason": "Input is PDF file paths, so the KBC trio is required in order. Text2MultiHopQAGenerator produces multi-hop QA pairs from cleaned chunks. The QA_pairs column is a nested list of dicts per row (question, reasoning_steps, answer, supporting_facts, type) — NOT separate dataframe columns. PromptedFilter scores the serialized QA_pairs list as a whole per chunk and filters out low-quality rows. FormatStrPromptedGenerator is NOT usable here because question/answer are not separate columns."
}
```

### 1. Field Mapping
```
Available in sample:
  - pdf_path (file path — valid for KBC trio)

To be generated:
  - text_path   (output from FileOrURLToMarkdownConverterFlash)
  - raw_chunk   (output from KBCChunkGenerator)
  - cleaned_chunk (output from KBCTextCleaner)
  - QA_pairs    (output from Text2MultiHopQAGenerator — nested list of {question, reasoning_steps, answer, supporting_facts, type} dicts per row)
  - qa_eval     (output from PromptedFilter — numeric score; rows outside threshold are dropped)

Field flow:
  pdf_path → [Flash] → text_path → [Chunk] → raw_chunk → [Clean] → cleaned_chunk
           → [MultiHopQA] → QA_pairs → [PromptedFilter] → qa_eval (filtered)
```

### 2. Ordered Operator List
1. **FileOrURLToMarkdownConverterFlash**: Convert PDF to Markdown
   - Why: Input is a file path; must convert before chunking
   - Input: pdf_path (exists in sample, is file path)
   - Output: text_path

2. **KBCChunkGenerator**: Split Markdown into text chunks
   - Why: Downstream QA generation requires bounded-size text segments
   - Input: text_path (created by step 1)
   - Output: raw_chunk

3. **KBCTextCleaner**: LLM-clean each raw chunk
   - Why: Remove noise, OCR artifacts, formatting issues before QA generation
   - Input: raw_chunk (created by step 2)
   - Output: cleaned_chunk

4. **Text2MultiHopQAGenerator**: Generate multi-hop QA pairs from chunks
   - Why: Domain-specific operator for multi-hop QA construction from clean text
   - Input: cleaned_chunk (created by step 3)
   - Output: QA_pairs (nested list of dicts per row), QA_metadata

5. **PromptedFilter**: Score and filter QA pair quality per chunk
   - Why: QA_pairs is a single column (nested list), so PromptedFilter can score it directly. FormatStrPromptedGenerator is NOT usable here because question/answer are nested inside the list, not separate dataframe columns.
   - Input: QA_pairs (created by step 4)
   - Output: qa_eval (numeric score; rows outside [min_score, max_score] are dropped)

### 3. Reasoning Summary
- The KBC trio is required because `pdf_path` is a file path (not text content); all three steps must run in order.
- `Text2MultiHopQAGenerator` is preferred over generic `PromptedGenerator` for multi-hop QA construction.
- `Text2MultiHopQAGenerator` outputs a **nested list** of QA dicts in the `QA_pairs` column — `question` and `answer` are NOT separate dataframe columns. Therefore `FormatStrPromptedGenerator` cannot reference them as kwargs.
- `PromptedFilter` works here because it takes a single `input_key` (`QA_pairs`). The LLM sees the serialized QA list and scores overall quality per chunk.
- Field dependencies are properly ordered: each step consumes fields created by previous steps.
- Total pipeline: 5 operators, semantically complete dataflow.

### 4. Complete Standard Pipeline Code
```python
from dataflow.operators.core_text import Text2MultiHopQAGenerator, PromptedFilter
from dataflow.operators.knowledge_cleaning import FileOrURLToMarkdownConverterFlash, KBCChunkGenerator, KBCTextCleaner
from dataflow.serving import APILLMServing_request
from dataflow.utils.storage import FileStorage

class PDFtoQAPipeline:
    def __init__(self):
        # Input file MUST be JSONL format (one JSON object per line):
        # {"pdf_path": "/data/paper1.pdf"}
        # {"pdf_path": "/data/paper2.pdf"}
        self.storage = FileStorage(
            first_entry_file_name="pdf_list.jsonl",
            cache_path="./cache_pdf_qa",
            file_name_prefix="pdf_step",
            cache_type="jsonl"
        )

        self.llm_serving = APILLMServing_request(
            api_url="https://api.openai.com/v1/chat/completions",
            model_name="gpt-4o",
            max_workers=10
        )

        # Step 1: Convert file paths to Markdown
        self.converter = FileOrURLToMarkdownConverterFlash(
            intermediate_dir="./cache_pdf_qa/markdown",
            mineru_model_path="opendatalab/MinerU2.5-2509-1.2B",
            batch_size=4,
            replicas=1,
            num_gpus_per_replica=1.0,
        )

        # Step 2: Split Markdown into chunks
        self.chunker = KBCChunkGenerator(
            chunk_size=512,
            chunk_overlap=50,
            split_method="token",
            min_tokens_per_chunk=100,
            tokenizer_name="bert-base-uncased",
        )

        # Step 3: LLM-clean each chunk
        self.cleaner = KBCTextCleaner(
            self.llm_serving,
            lang="en",
        )

        # Step 4: Generate multi-hop QA pairs
        self.qa_generator = Text2MultiHopQAGenerator(
            llm_serving=self.llm_serving,
            seed=0,
            lang="en",
            num_q=5,
        )

        # Step 5: Score and filter QA pair quality per chunk
        # QA_pairs is a nested list column — PromptedFilter scores it as a whole
        self.qa_filter = PromptedFilter(
            llm_serving=self.llm_serving,
            system_prompt=(
                "You are a QA quality evaluator. "
                "You will receive a list of question-answer pairs generated from a text chunk. "
                "Rate the overall quality on a scale of 1-5. "
                "Consider: question clarity, answer accuracy, answer completeness, "
                "multi-hop reasoning quality, and relevance to source. "
                "Output only the numeric score."
            ),
            min_score=4,
            max_score=5,
        )

    def forward(self):
        # Step 1: PDF → Markdown path
        self.converter.run(
            storage=self.storage.step(),
            input_key="pdf_path",
            output_key="text_path"
        )

        # Step 2: Markdown → raw chunks
        self.chunker.run(
            storage=self.storage.step(),
            input_key="text_path",
            output_key="raw_chunk"
        )

        # Step 3: raw chunks → cleaned chunks
        self.cleaner.run(
            storage=self.storage.step(),
            input_key="raw_chunk",
            output_key="cleaned_chunk"
        )

        # Step 4: cleaned chunks → multi-hop QA pairs
        self.qa_generator.run(
            storage=self.storage.step(),
            input_key="cleaned_chunk",
            output_key="QA_pairs",
            output_meta_key="QA_metadata"
        )

        # Step 5: score and filter QA pairs per chunk
        self.qa_filter.run(
            storage=self.storage.step(),
            input_key="QA_pairs",
            output_key="qa_eval"
        )

if __name__ == "__main__":
    pipeline = PDFtoQAPipeline()
    pipeline.forward()
```

### 5. Adjustable Parameters / Caveats

**Tunable Parameters**:
- `chunk_size`: Increase to 1024 for longer context
- `chunk_overlap`: Increase to 100 for better continuity
- `num_q`: Max QA pairs to keep per chunk (truncates; actual count depends on sentence triples in text)
- `lang`: Set to `"zh"` for Chinese documents
- `min_score` in `PromptedFilter`: Lower to 3 for more lenient filtering
- `max_workers`: Increase for faster LLM throughput

**Fallback Strategies**:
- If < 30% pass filter: Increase `chunk_size` to 1024 for more context per QA
- If questions too generic: Reduce `num_q` or use a custom `prompt_template`
- If answers incomplete: Increase `chunk_size` or `chunk_overlap`

**Caveats**:
- `FileOrURLToMarkdownConverterFlash` requires GPU for PDF/image inputs; `.md`/`.txt` skip MinerU
- `mineru_model_path` must be a valid HuggingFace model ID or local path — `None` raises `ValueError`
- Each document generates multiple chunks; each chunk produces up to `num_q` QA pairs (actual count depends on sentence triples)
- The KBC trio must always run in full — do not skip any of the three steps
- Input text must be 100–200,000 chars, have ≥2 sentences, and ≤30% special chars — otherwise `qa_pairs` will be empty

**Debugging**:
- `cache_pdf_qa/pdf_step_1.jsonl` — Markdown paths after conversion
- `cache_pdf_qa/pdf_step_2.jsonl` — raw chunks after splitting
- `cache_pdf_qa/pdf_step_3.jsonl` — cleaned chunks
- `cache_pdf_qa/pdf_step_4.jsonl` — QA pairs (nested list per row)
- `cache_pdf_qa/pdf_step_5.jsonl` — filtered results (low-quality chunks removed)
- Monitor pass rate by comparing row counts between steps
