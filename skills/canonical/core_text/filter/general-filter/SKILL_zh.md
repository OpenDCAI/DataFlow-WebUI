---
name: general-filter
description: >-
  GeneralFilter 算子参考文档。涵盖构造函数、基于规则的过滤逻辑、以及流水线使用说明。

  使用场景：基于列值条件过滤行，可用 lambda 函数表达，无需 LLM 调用。
---
# GeneralFilter 算子参考

`GeneralFilter` 使用自定义规则列表过滤 DataFrame 行，所有规则用 AND 组合。不添加新列——仅删除不满足所有条件的行。

## 1. 导入

```python
from dataflow.operators.core_text import GeneralFilter
```

## 2. 构造函数

```python
GeneralFilter(
    filter_rules=[
        lambda df: df["score"] >= 4,
        lambda df: df["text"].str.len() > 10,
    ]
)
```

| 参数             | 必需 | 默认值 | 说明                                                                        |
| ---------------- | ---- | ------ | --------------------------------------------------------------------------- |
| `filter_rules` | 是   | None   | 规则列表；每条规则是签名为 `(df: DataFrame) -> Series[bool]` 的可调用对象 |

每条规则返回与 DataFrame 长度相同的布尔 Series；`True` 表示保留该行。多条规则用 **AND** 组合。

## 3. run() 方法签名

```python
op.run(
    storage=self.storage.step(),
)
# 返回值: "" (空字符串)
```

| 参数        | 必需 | 默认值 | 说明                                                                            |
| ----------- | ---- | ------ | ------------------------------------------------------------------------------- |
| `storage` | 是   | None   | `DataFlowStorage` 步骤对象。算子从此读取 DataFrame 并写回过滤后的 DataFrame。 |

注意：`run()` 没有 `input_key` / `output_key` 参数。规则中引用的列名直接写在 lambda 中。

### 返回值

方法返回 `""`（空字符串）。

## 4. 实际运行逻辑

源码行为：

1. 从 `storage.read("dataframe")` 读取 DataFrame。
2. 初始化布尔掩码为 `pd.Series(True, index=df.index)`。
3. 对 `filter_rules` 中的每条规则：
   - 验证规则是可调用的。
   - 调用 `cond = rule_fn(df)`。
   - 验证 `cond` 是布尔 Series。
   - 更新掩码：`mask &= cond`。
4. 过滤 DataFrame：`filtered_df = df[mask]`。
5. 通过 `storage.write(filtered_df)` 写回过滤后的 DataFrame。
6. 返回 `""`。

### 关键行为说明

1. 每条规则必须返回布尔 `pd.Series`；否则抛出 `ValueError`。
2. 规则中引用的列必须已存在于当前步骤的 DataFrame 中。
3. 仅删除行；不添加新列。
4. 多条规则用 AND 组合——仅保留满足所有条件的行。

## 5. 流水线使用示例

```python
from dataflow.operators.core_text import GeneralFilter
from dataflow.utils.storage import FileStorage

class MyPipeline:
    def __init__(self):
        self.storage = FileStorage(
            first_entry_file_name="./data/input.jsonl",
            cache_path="./cache",
            file_name_prefix="step",
            cache_type="jsonl"
        )

        self.filter = GeneralFilter(
            filter_rules=[
                lambda df: df["score"] >= 4,
                lambda df: df["text"].str.len() > 10,
            ]
        )

    def forward(self):
        self.filter.run(storage=self.storage.step())

if __name__ == "__main__":
    pipeline = MyPipeline()
    pipeline.forward()
```
