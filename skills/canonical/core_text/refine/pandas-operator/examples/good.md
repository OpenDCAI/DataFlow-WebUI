# Example: Add and Clean Columns with PandasOperator

## User Request
"重命名列 `raw_text` 为 `text`，同时删除 `temp` 列，过滤掉 `text` 为空的行"

## Sample Data
```jsonl
{"raw_text": "Hello world", "temp": "x", "score": 5}
{"raw_text": "", "temp": "y", "score": 3}
{"raw_text": "Useful content here.", "temp": "z", "score": 4}
```

## Field Mapping
```
Available in sample:
  - raw_text   (源文本列，需重命名)
  - temp       (临时列，需删除)
  - score      (保留)

Transformations:
  1. rename raw_text → text
  2. drop temp column
  3. filter out rows where text is empty

Field flow:
  raw_text + temp + score → [PandasOperator] → text + score (空行已删)
```

## Complete Pipeline Code

```python
from dataflow.operators.core_text import PandasOperator
from dataflow.utils.storage import FileStorage


class CleanPipeline:
    def __init__(self):
        self.storage = FileStorage(
            first_entry_file_name="raw.jsonl",
            cache_path="./cache",
            file_name_prefix="clean_step",
            cache_type="jsonl"
        )

        self.cleaner = PandasOperator(
            process_fn=[
                lambda df: df.rename(columns={"raw_text": "text"}),
                lambda df: df.drop(columns=["temp"]),
                lambda df: df[df["text"].str.strip() != ""].reset_index(drop=True),
            ]
        )

    def forward(self):
        self.cleaner.run(
            storage=self.storage.step()
        )


if __name__ == "__main__":
    pipeline = CleanPipeline()
    pipeline.forward()
```

## Output

输入 3 行，处理后：

| text | score | 保留？ |
|------|-------|--------|
| `"Hello world"` | 5 | ✅ |
| `""` | 3 | ❌ 空文本行被删除 |
| `"Useful content here."` | 4 | ✅ |

输出 DataFrame 保留 `text` 和 `score` 列，删除了 `temp` 列。

## Debugging
- `cache/clean_step_step1.jsonl` — 含 2 行，列为 `text`、`score`
