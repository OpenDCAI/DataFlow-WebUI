# DataFlow Operator Contract

## Core Interface

All generated operators must follow this baseline:

```python
@OPERATOR_REGISTRY.register()
class XxxOperator(OperatorABC):
    @staticmethod
    def get_desc(lang: str = "zh") -> str:
        ...

    def run(self, storage: DataFlowStorage, ...) -> str | None:
        ...
```

ZH: 所有生成的 operator 必须遵循以上核心接口。

## Required Behavior

- `run` reads from `storage.read("dataframe")`.
- `run` validates required input columns.
- `run` writes dataframe back via `storage.write(dataframe)`.
- `run` returns output key (or `None` for dataset-level evaluation).

ZH:
- `run` 从 dataframe 读取输入。
- 必须先校验输入列。
- 处理后写回 dataframe。
- 返回输出列名（或在数据集级评估时返回 `None`）。

## Data Contract

- Input/output should be column-based dataframe transformations.
- Keep operator core independent from CLI-specific interaction.
- When LLM is disabled, behavior must remain deterministic.

ZH:
- 输入输出应以 dataframe 列变换为中心。
- operator 核心逻辑不得耦合 CLI 交互。
- 关闭 LLM 时行为应保持确定性。

## Description Contract (Required)

`get_desc` must include:
- Chinese description (`lang="zh"`)
- English description (`lang="en"`)
- Fallback short string for unknown language code

ZH: `get_desc` 必须同时支持 `zh/en`，并提供未知语言兜底描述。
