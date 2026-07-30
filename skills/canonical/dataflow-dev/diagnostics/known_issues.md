# DataFlow 已知问题数据库

> **文件状态**：可追加更新
> **格式约定**：每条 Issue 包含：编号、标题、症状关键词、根因、解决方案、修复代码示例
> **使用方式**：诊断时先按"症状关键词"匹配，命中则直接给出根因和方案

---

## Issue #001 — 配置参数命名警告（非错误）

**标题**：`Unexpected key 'xxx' in operator` 警告

**症状关键词**：
- `Unexpected key`
- `in operator`
- `UserWarning`

**根因**：

`OPERATOR_REGISTRY.register()` 会校验 Pipeline 配置文件（YAML/JSON）中传入的 key 是否在算子的 `__init__` 参数列表中。若 key 不匹配（如大小写不同、多余参数），会抛出 `UserWarning`，但**不会中断执行**。

**解决方案**：

检查 Pipeline 配置文件中对应算子的参数名拼写，确保与算子 `__init__` 参数名完全一致（区分大小写）。

**修复示例**：

```yaml
# ❌ 错误
operators:
  - type: MyFilter
    input_Key: "text"   # 大小写错误

# ✅ 正确
operators:
  - type: MyFilter
    input_key: "text"
```

---

## Issue #002 — 算子注册缺失

**标题**：`No object named 'Xxx' found in 'operators' registry`

**症状关键词**：
- `No object named`
- `found in 'operators' registry`
- `RegistryError`

**根因**：

新建算子文件后，未在对应模块的 `__init__.py` 的 `TYPE_CHECKING` 块中注册。LazyLoader 依赖此注册才能找到类。

**解决方案**：

在对应模块的 `__init__.py` 中添加 import：

```python
# dataflow/operators/<module>/__init__.py

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .filter.my_new_filter import MyNewFilter
```

**修复示例**：

```python
# dataflow/operators/general_text/__init__.py
if TYPE_CHECKING:
    from .filter.my_new_filter import MyNewFilter  # ← 新增这行
```

---

## Issue #003 — Pipeline key 不一致

**标题**：`Key Matching Error` / `does not match any output keys`

**症状关键词**：
- `Key Matching Error`
- `does not match any output keys`
- `KeyError` + Pipeline 上下文

**根因**：

Pipeline 中前一个算子的 `output_key` 与后一个算子的 `input_key` 不一致，或 `storage.write()` 写入的列名与后续 `storage.read()` 读取的列名不匹配。

**解决方案**：

逐步检查 `forward()` 中每个算子调用的 `input_key` / `output_key`，确保相邻步骤的字段名严格一致。

**修复示例**：

```python
# ❌ 错误：step1 输出 "result"，step2 读取 "output"
self.step1_op.run(storage=self.storage.step(), output_key="result")
self.step2_op.run(storage=self.storage.step(), input_key="output")  # 找不到 "output"

# ✅ 正确：保持一致
self.step1_op.run(storage=self.storage.step(), output_key="cleaned_text")
self.step2_op.run(storage=self.storage.step(), input_key="cleaned_text")
```

---

## Issue #004 — 缺少 storage.step()

**标题**：`You must call storage.step() before`

**症状关键词**：
- `You must call storage.step() before`
- `storage has not been stepped`
- `AssertionError` + storage 上下文

**根因**：

在 Pipeline `forward()` 中调用算子时，没有在每个 `run()` 调用时传递 `storage=self.storage.step()`，或使用了错误的用法（如 `self.storage` 而非 `self.storage.step()`）。

**解决方案**：

- Pipeline `forward()` 中：每次 `op.run()` 都传 `storage=self.storage.step()`
- 独立测试脚本中：先调用 `storage.step()`，再传给 `op.run()`

**修复示例**：

```python
# ❌ 错误（Pipeline 中）
self.op.run(storage=self.storage, input_key="text")

# ✅ 正确（Pipeline 中）
self.op.run(storage=self.storage.step(), input_key="text")

# ✅ 正确（独立测试脚本中）
storage = FileStorage(...)
storage.step()  # 手动推进一步
op.run(storage=storage, input_key="text")
```

---

## Issue #005 — DummyStorage 不支持 get_keys_from_dataframe

**标题**：`DummyStorage` + `AttributeError` / `TypeError`

**症状关键词**：
- `DummyStorage`
- `AttributeError: 'DummyStorage' object has no attribute`
- `TypeError` + DummyStorage 上下文

**根因**：

`DummyStorage` 是一个测试用 stub，不实现 `get_keys_from_dataframe()` 及其他完整 Storage 方法。在 Pipeline 中使用 `DummyStorage` 会导致算子调用这些方法时抛出错误。

**解决方案**：

- Pipeline 中**必须**使用 `FileStorage`，禁止使用 `DummyStorage`
- `DummyStorage` 仅用于极简单元测试，不涉及 dataframe 操作时才可使用

**修复示例**：

```python
# ❌ 错误（Pipeline 中使用 DummyStorage）
from dataflow.utils.storage import DummyStorage
storage = DummyStorage()

# ✅ 正确（Pipeline 中使用 FileStorage）
from dataflow.utils.storage import FileStorage
storage = FileStorage(
    first_entry_file_name="./data/input.jsonl",
    cache_path="./cache",
    file_name_prefix="dataflow_cache_step",
    cache_type="jsonl",
)
```

---

## Issue #006 — re.split() 捕获组产生 None

**标题**：`AttributeError: 'NoneType' object has no attribute 'strip'` + `re.split`

**症状关键词**：
- `AttributeError: 'NoneType' object has no attribute 'strip'`
- `re.split`
- `NoneType` + 字符串操作

**根因**：

在 `re.split()` 的 pattern 中使用了**捕获组** `(...)`（包括可选捕获组 `(...)?`）。Python 的 `re.split()` 在使用捕获组时，会把匹配到的分隔符（或 `None`，若是可选组未匹配）插入结果列表中，导致列表中存在 `None` 值，后续调用 `.strip()` 等字符串方法时报错。

**解决方案**：

将所有 `re.split()` pattern 中的捕获组 `(...)` 改为**非捕获组** `(?:...)`。

**修复示例**：

```python
import re

text = "Step 1: foo\nStep 2: bar"

# ❌ 错误：捕获组导致 None 混入结果
parts = re.split(r"(Step \d+:)", text)
# ['', 'Step 1:', ' foo\n', 'Step 2:', ' bar']
# 结果中包含分隔符本身，可能混入 None（尤其是可选组）

# ❌ 更危险：可选捕获组
parts = re.split(r"(\n+)?##", text)
# None 会出现在 \n 未匹配时

# ✅ 正确：非捕获组
parts = re.split(r"(?:Step \d+:)", text)
parts = re.split(r"(?:\n+)?##", text)

# 或者直接过滤 None
parts = [p for p in re.split(r"(Step \d+:)", text) if p is not None]
```

---

## Issue #007 — @prompt_restrict 装饰器位置错误

**标题**：`@prompt_restrict` 未生效或报错

**症状关键词**：
- `prompt_restrict`
- 装饰器未生效
- Prompt 类型限制失效

**根因**：

`@prompt_restrict(MyPrompt)` 装饰器必须**紧贴类定义上方**。若在 `@prompt_restrict` 和 `class MyOperator` 之间插入了其他装饰器（如 `@OPERATOR_REGISTRY.register()`），则 `@prompt_restrict` 作用于了 `register()` 的返回值而非类本身，导致限制失效。

**解决方案**：

确保装饰器顺序为：`@OPERATOR_REGISTRY.register()` 在最外层，`@prompt_restrict` 紧贴类定义：

```python
# ❌ 错误：@prompt_restrict 被 @register 隔开
@OPERATOR_REGISTRY.register()
@prompt_restrict(MyPrompt)
class MyOperator(OperatorABC):
    ...

# ✅ 正确：@prompt_restrict 紧贴类
@OPERATOR_REGISTRY.register()
class MyOperator(OperatorABC):
    ...
# 注：实际上 @prompt_restrict 应在类定义上方、@register 下方
# 请查阅最新 DataFlow 源码确认正确的叠加顺序
```

**注**：该 Issue 的准确修复依赖具体 DataFlow 版本，建议查阅最新源码中 `@prompt_restrict` 的实际用法示例。

---

## Issue #008 — LazyLoader 子包路径 import 失败

**标题**：`ModuleNotFoundError` + `dataflow.operators.reasoning.refine`

**症状关键词**：
- `ModuleNotFoundError`
- `dataflow.operators.reasoning.refine`
- `ImportError` + 算子类名

**根因**：

DataFlow 使用 LazyLoader 机制，算子类通过父模块的 `__init__.py` 注册并懒加载。直接 import 子包路径（如 `from dataflow.operators.reasoning.refine.cot_llm_judge_refiner import CoTLLMJudgeRefiner`）会绕过 LazyLoader，在部分场景下导致 `ModuleNotFoundError`。

**解决方案**：

必须从父模块 import：

```python
# ✅ 正确
from dataflow.operators.reasoning import CoTLLMJudgeRefiner

# ❌ 错误
from dataflow.operators.reasoning.refine.cot_llm_judge_refiner import CoTLLMJudgeRefiner
```

---

## Issue #009 — json_schema 缺少 additionalProperties: false 导致 API 500 无限重试

**标题**：`Invalid schema for response_format 'custom_response': additionalProperties is required`

**症状关键词**：
- `Invalid schema for response_format`
- `additionalProperties is required to be supplied and to be false`
- `API request failed status=500`
- `response_format`
- `custom_response`

**根因**：

`FormatStrPromptedGenerator` 或 `PromptedGenerator` 使用 `json_schema` 参数约束 LLM 输出格式时，
DataFlow 将 schema 直接传递给 LLM API 的 `response_format` 参数。OpenAI 兼容 API 要求所有
`"type": "object"` 层级**必须**包含 `"additionalProperties": false`。缺少此字段会导致 API
返回 HTTP 500 错误，而 DataFlow 的重试机制会无限重试，**阻塞整个 pipeline 执行甚至 WebUI 后端**。

**影响范围**：

- 本地 Pipeline（`pipeline.py`）执行时，step 会卡住无限重试
- WebUI 执行时，后端进程被阻塞，无法响应新请求，需要重启服务

**解决方案**：

在 `json_schema` 的**每一层** `"type": "object"` 中添加 `"additionalProperties": false`（Python 中为 `False`）。

**修复示例**：

```python
# ❌ 错误：缺少 additionalProperties，API 返回 500 并无限重试
json_schema={
    "type": "object",
    "properties": {
        "score": {"type": "number"},
        "label": {"type": "string"},
    },
    "required": ["score", "label"],
}

# ✅ 正确：包含 additionalProperties: False
json_schema={
    "type": "object",
    "properties": {
        "score": {"type": "number"},
        "label": {"type": "string"},
    },
    "required": ["score", "label"],
    "additionalProperties": False,   # ← 必须添加
}
```

**operators.json（WebUI 部署配置）中的正确写法**：

```json
{"name": "json_schema", "value": {
    "type": "object",
    "properties": {
        "score": {"type": "number"},
        "label": {"type": "string"}
    },
    "required": ["score", "label"],
    "additionalProperties": false
}}
```

**嵌套对象** — 每一层都需要：

```python
json_schema={
    "type": "object",
    "properties": {
        "result": {
            "type": "object",
            "properties": {"value": {"type": "number"}},
            "required": ["value"],
            "additionalProperties": False,  # ← 内层对象也需要
        },
    },
    "required": ["result"],
    "additionalProperties": False,          # ← 外层对象
}
```

---

## 快速匹配表

| 报错关键词 | Issue 编号 |
|---|---|
| `Unexpected key 'xxx' in operator` | #001 |
| `No object named 'Xxx' found in 'operators' registry` | #002 |
| `Key Matching Error` / `does not match any output keys` | #003 |
| `You must call storage.step() before` | #004 |
| `DummyStorage` + `AttributeError` / `TypeError` | #005 |
| `'NoneType' object has no attribute 'strip'` + `re.split` | #006 |
| `prompt_restrict` 未生效 | #007 |
| `ModuleNotFoundError` + `dataflow.operators.reasoning.refine` | #008 |
| `Invalid schema for response_format` / `additionalProperties` | #009 |

---

*本文件由 dataflow-dev skill 维护，新增 Issue 时请同步更新 SKILL.md 诊断流程的快速匹配表。*
