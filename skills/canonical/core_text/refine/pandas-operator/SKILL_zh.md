---
name: pandas-operator
description: >-
  PandasOperator 算子参考文档。

  使用场景：对 DataFrame 应用自定义变换，不使用 LLM。
---

# PandasOperator 算子参考

`PandasOperator` 对 DataFrame 依次应用变换函数列表。每个函数接收 DataFrame 并返回修改后的 DataFrame。

## 1. 导入

```python
from dataflow.operators.core_text import PandasOperator
```

## 2. 构造函数

```python
PandasOperator(
    process_fn=[
        lambda df: df.rename(columns={"old": "new"}),
        lambda df: df[df["score"] > 0],
    ]
)
```

| 参数 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `process_fn` | 是 | None | 变换函数列表，每个函数签名为 `(df: DataFrame) -> DataFrame` |

## 3. run() 方法签名

```python
op.run(
    storage=self.storage.step(),
)
# 返回: 空字符串 ""
```

| 参数 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `storage` | 是 | None | Storage 步骤对象 |

## 4. 使用示例

```python
from dataflow.operators.core_text import PandasOperator
from dataflow.utils.storage import FileStorage

class MyPipeline:
    def __init__(self):
        self.storage = FileStorage(
            first_entry_file_name="./data/input.jsonl",
            cache_path="./cache",
            file_name_prefix="step",
            cache_type="jsonl"
        )

        self.transformer = PandasOperator(
            process_fn=[
                lambda df: df.assign(score2=df["score"] * 2),
                lambda df: df.sort_values("score", ascending=False),
                lambda df: df.drop(columns=["temp_col"])
            ]
        )

    def forward(self):
        self.transformer.run(
            storage=self.storage.step()
        )

if __name__ == "__main__":
    pipeline = MyPipeline()
    pipeline.forward()
```

## 5. 运行逻辑

1. 从 storage 读取 DataFrame。
2. 按顺序依次应用 `process_fn` 中的每个函数。
3. 每个函数接收前一个函数输出的 DataFrame。
4. 验证每个函数可调用且返回 DataFrame。
5. 将最终 DataFrame 写入 storage。
6. 返回空字符串。

## 6. 重要说明

- `process_fn` 中每个函数必须返回 `pd.DataFrame`
- 函数按列表顺序执行
- 无 `input_key` 或 `output_key` 参数（列操作在 lambda 函数中）
- 不调用 LLM（纯 pandas 操作）
