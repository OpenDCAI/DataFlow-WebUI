# DataFlow 开发规范、问题记录与最佳实践

> 来源：OpenDCAI/DataFlow 主仓库开发经验（持续更新）
> **此文件为可追加文档**：发现新规范/新坑时，通过 SKILL.md 的更新流程在末尾追加条目。

---

## 一、开发规范

### 1.1 分支与版本管理

- **工作仓库**：`https://github.com/OpenDCAI/DataFlow`（`main` 分支）
- 开发新特性请从 `main` 分支新建特性分支，PR 合并回 `main`

### 1.2 算子开发规范

#### 必须遵守

1. **继承 `OperatorABC`**，调用 `super().__init__()` 以初始化 `self.logger`
2. **注册算子**：`@OPERATOR_REGISTRY.register()` 装饰器加在类定义上（不能错位到其他函数上）
3. **`run()` 参数命名约定**（Pipeline 编译依赖此规则）：
   - 输入 key 参数以 `input_` 开头，值为 DataFrame 列名字符串
   - 输出 key 参数以 `output_` 开头，值为 DataFrame 列名字符串
   - `storage` 参数必须存在（第一个参数或关键字参数），类型为 `DataFlowStorage`
4. **`run()` 必须返回输出 key 列表**，如 `return ['output_col1', 'output_col2']`
5. **`run()` 必须调用 `storage.read()` 和 `storage.write()`**
6. **在 `__init__.py` 的 `TYPE_CHECKING` 块声明导入**，否则 LazyLoader 无法发现算子

#### 强烈建议

7. 实现 `@staticmethod get_desc(lang: str = "zh")` 方法，支持 `zh`/`en` 两种语言，返回**纯字符串**（不是 dict）
8. 在 `__init__` 中用 `self.logger.info(f"Initializing {self.__class__.__name__}...")` 记录初始化日志
9. 在 `run()` 中用 `self.logger.info(...)` 记录关键步骤

#### 文件命名约定

- Filter 算子文件名：`xxx_filter.py`，类名：`XxxFilter`
- Refine 算子文件名：`xxx_refiner.py`，类名：`XxxRefiner`
- Eval（sample 级别）：`xxx_sample_evaluator.py`，类名：`XxxSampleEvaluator`
- Eval（dataset 级别）：`xxx_dataset_evaluator.py`，类名：`XxxDatasetEvaluator`
- Generate 算子：`xxx_generator.py`，类名：`XxxGenerator`

### 1.3 Pipeline 开发规范

1. 两种合法风格（**不要混用**）：
   - **风格 A**：继承 `PipelineABC`（适合需要 `compile()` / DAG 可视化）
   - **风格 B**：纯类封装（适合快速实验，DataFlow 现有 example 实际采用此风格）
2. `storage` 在 `__init__` 中声明（不在 `forward()` 里临时创建）
3. 所有算子在 `__init__` 中实例化为**成员变量**（`compile()` 依赖此机制）
4. `forward()` 中每个算子调用使用独立的 `storage.step()` 副本
5. 推荐使用 `LazyFileStorage` 替代 `FileStorage` 以获得原子落盘和更好的中断安全性
6. Pipeline 文件建议放在 `dataflow/example/` 对应子目录或项目根目录下

### 1.4 Prompt 开发规范

1. 继承 `PromptABC`，注册 `@PROMPT_REGISTRY.register()`
2. 实现 `build_prompt(self, ...) -> str` 方法
3. 若算子需要限制 Prompt 类型，使用 `@prompt_restrict(...)` 装饰算子类
4. 用户自定义 Prompt 继承 `DIYPromptABC`，可绕过 `@prompt_restrict` 白名单
5. `@prompt_restrict` **必须紧贴类定义上方**（见 Issue #007）

### 1.5 LLM Serving 使用规范

1. **API key 必须通过环境变量注入**，禁止硬编码在代码中
   - 推荐环境变量名：`DF_API_KEY`（也可自定义）
2. 算子中持有 `llm_serving` 对象的成员变量**必须命名为 `self.llm_serving`**（Pipeline 通过 `isinstance` 检测此字段管理 Serving 生命周期）
3. 不要在算子内手动调用 `serving.cleanup()`，由 Pipeline 自动管理

### 1.6 代码风格

- Python 3.10+，可使用 `X | Y` 类型注解语法
- 使用 type hints
- 日志使用 `self.logger`（`get_logger()` 获取），不使用 `print()`（开发调试可临时用 `print`）
- 异常处理中记录详细日志

### 1.7 算子复用原则（避免重复造轮子）

> **核心原则：开发新算子前，必须先检查仓库中是否已有功能相同或相近的算子，优先复用，而非重复实现。**

#### 检查已有算子的方法

1. **查阅各模块 `__init__.py` 的 `TYPE_CHECKING` 块**
2. **通过 OPERATOR_REGISTRY 动态查询**：
   ```python
   from dataflow.utils.registry import OPERATOR_REGISTRY
   OPERATOR_REGISTRY._get_all()
   print(OPERATOR_REGISTRY.get_obj_map())
   ```
3. **查阅 `knowledge_base.md` §八**

#### 复用示例

| 需求 | 不要重写 | 复用 |
|------|---------|------|
| 按字数过滤文本 | ❌ 新写 TextLengthFilter | ✅ 复用 `WordNumberFilter` |
| 按字符数过滤 | ❌ 新写 | ✅ 复用 `CharNumberFilter` |
| 去除 HTML 标签 | ❌ 新写 | ✅ 复用 `HtmlEntityRefiner` |
| 推理答案生成 | ❌ 新写 LLM 调用 | ✅ 复用 `ReasoningAnswerGenerator` |

### 1.8 算子健壮性与容错规范

> **算子，尤其是依赖 LLM 输出的算子，必须做好充分的容错处理。**

#### 核心原则

1. **逐条容错**：对每个 LLM 返回值单独 try/except
2. **失败时记录日志**：使用 `self.logger.warning()` 记录原始输出和错误信息
3. **失败时给出合理默认值**：跳过该条（filter/generate），或返回 0/None（eval）
4. **类型前置检查**：先检查 `response is None` 和 `isinstance(response, str)`

#### 标准容错模板

**模板 A：generate/filter 类算子——解析失败则跳过该条**
```python
valid_rows = []
for idx, response in enumerate(responses):
    try:
        if not isinstance(response, str) or response is None:
            self.logger.warning(f"[Skipped] idx={idx}: invalid response type: {type(response)}")
            continue
        result = json.loads(self._clean_json_block(response))
        if "required_field" not in result:
            self.logger.warning(f"[Skipped] idx={idx}: missing field: {result}")
            continue
        valid_rows.append(result)
    except (json.JSONDecodeError, KeyError) as e:
        self.logger.warning(f"[Error] idx={idx}: parse failed: {e} | raw: {response[:200]}")
        continue
    except Exception as e:
        self.logger.warning(f"[Error] idx={idx}: unexpected error: {e}")
        continue
```

**模板 B：eval 类算子——解析失败则返回默认值（0/None）**
```python
def _parse_scores(self, outputs: list[str]) -> list[int]:
    results = []
    for idx, out in enumerate(outputs):
        score = 0
        try:
            if out is None:
                results.append(score)
                continue
            text = str(out).strip()
            match = re.search(r"\d+", text)
            if match:
                val = int(match.group())
                if 1 <= val <= 5:
                    score = val
        except Exception:
            score = 0
        results.append(score)
    return results
```

**模板 C：JSON 清理辅助函数**
```python
def _clean_json_block(self, item: str) -> str:
    """去除模型输出中可能包裹的 ```json ... ``` 代码块标记"""
    return item.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
```

**模板 D：多层级正则降级策略**
```python
def _extract_target(self, response: str) -> str:
    if not isinstance(response, str):
        return ""
    # 层级 1：最严格匹配
    blocks = re.findall(r"```sql\s*(.*?)\s*```", response, re.DOTALL | re.IGNORECASE)
    if blocks:
        return blocks[-1].strip()
    # 层级 2：次级匹配
    blocks = re.findall(r"```\s*(SELECT.*?)\s*```", response, re.DOTALL | re.IGNORECASE)
    if blocks:
        return blocks[-1].strip()
    # 层级 3：宽松匹配
    match = re.search(r"(SELECT\b.*)", response, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return ""
```

### 1.9 推理模型（CoT 模型）输出处理规范

> DeepSeek-R1 等 CoT 模型的 API 响应，DataFlow Serving 层会自动包装为 `<think>...</think>\n<answer>...</answer>` 格式返回给算子。

#### 何时需要剥离 CoT

| 算子类型 | 是否需要剥离 |
|---------|------------|
| 问题生成（QuestionGenerator） | ✅ 必须剥离 |
| 答案/代码生成（写入普通字段） | ✅ 必须剥离 |
| 推理数据生成（写入 `generated_cot` 字段） | ❌ 不要剥离 |
| 评估算子（数值打分） | ✅ 必须剥离 |
| 分类/判别算子 | ✅ 必须剥离 |

#### 标准 CoT 剥离函数

```python
import re

def _strip_cot(self, response: str) -> str:
    """
    剥离 DeepSeek R1 等 CoT 模型输出中的 <think>...</think> 部分。
    若符合格式，返回 <answer> 内容；否则原样返回（兼容普通模型）。
    """
    if not isinstance(response, str) or response is None:
        return response
    pattern = r"<think>.*?</think>\s*<answer>(.*?)</answer>"
    match = re.search(pattern, response, re.DOTALL)  # 必须加 re.DOTALL
    if match:
        return match.group(1).strip()
    return response  # 兼容普通模型：原样返回
```

---

## 二、已知问题

> 诊断用快速匹配表和根因分析统一维护在 `diagnostics/known_issues.md`，不在此处重复。
> 本文件 §一 的开发规范中已内联了最关键的注意事项（如 Issue #002 的 `__init__.py` 声明、Issue #004 的 `storage.step()` 用法等）。

---

## 三、开发经验与最佳实践

### 3.1 调试 Pipeline 编译

```python
pipeline = MyPipeline()
pipeline.compile()
for i, keys in enumerate(pipeline.accumulated_keys):
    print(f"After step {i}: {keys}")
pipeline.draw_graph()  # 需要 pip install pyvis
```

### 3.2 快速测试算子（不走 Pipeline）

```python
from dataflow.utils.storage import FileStorage
from dataflow.operators.general_text import WordNumberFilter

op = WordNumberFilter(min_words=5, max_words=100)
storage = FileStorage("test_data.jsonl", cache_path="./test_cache")
storage.step()  # 手动推进一次
op.run(storage, input_key="text", output_key="word_count")
```

### 3.3 DummyStorage 用于单元测试

```python
from dataflow.utils.storage import DummyStorage
import pandas as pd

storage = DummyStorage()
storage.set_data(pd.DataFrame({"text": ["hello world", "foo bar baz"]}))
storage.operator_step = 0  # 手动设置步骤

op = WordNumberFilter(min_words=2, max_words=10)
op.run(storage, input_key="text")
result = storage.read()
```

### 3.4 LazyLoader import 路径速查

```python
# ✅ 正确：从父模块 import
from dataflow.operators.reasoning import CoTLLMJudgeRefiner, CoTMonteCarloRefiner
from dataflow.operators.general_text import WordNumberFilter
from dataflow.operators.core_text import PromptedGenerator

# ❌ 错误：直接用子包路径
from dataflow.operators.reasoning.refine.cot_llm_judge_refiner import CoTLLMJudgeRefiner
```

### 3.5 环境变量配置模板

```bash
export DF_API_KEY=sk-xxxxxxxxxxxx
export DF_API_URL=http://your-api/v1/chat/completions
export DF_MODEL_NAME=gpt-4o
export DF_MAX_WORKERS=200       # 根据 API 并发能力调整
export DF_LOGGING_LEVEL=INFO    # DEBUG / INFO / WARNING / ERROR
```

---

## 四、待办与开发计划

- [ ] **修复** `sft_generator_from_seed.py` 中 `@prompt_restrict` 装饰位置错误（Issue #007）
- [ ] **修复** `cot_chunk_compress_refiner.py` 中 `re.split()` 捕获组问题（Issue #008）
- [ ] `dataflow init operator` CLI 命令尚未实现（目前输出 "not implemented yet"）
- [ ] `dataflow init pipeline` CLI 命令尚未实现
- [ ] `dataflow init prompt` CLI 命令尚未实现

---

## 五、Pipeline 开发实战指南

### 5.1 DataFlow Pipeline 的标准风格（风格 B）

DataFlow 现有 Pipeline（如 `reasoning_math_pipeline.py`）均采用**"类封装 + forward 串行调用"**风格：

```python
from dataflow.utils.storage import FileStorage
from dataflow.serving import APILLMServing_request
from dataflow.operators.reasoning import ReasoningAnswerGenerator

class MyReasoningPipeline:
    def __init__(self):
        self.storage = FileStorage(
            first_entry_file_name="./input.jsonl",
            cache_path="./cache",
            file_name_prefix="dataflow_cache",
            cache_type="jsonl",
        )
        self.llm_serving = APILLMServing_request(
            api_url="http://your-api/v1/chat/completions",
            key_name_of_api_key="DF_API_KEY",
            model_name="gpt-4o",
            max_workers=200,
        )
        self.generator_step1 = ReasoningAnswerGenerator(
            llm_serving=self.llm_serving,
        )

    def forward(self):
        self.generator_step1.run(
            storage=self.storage.step(),
            input_key="question",
            output_key="answer",
        )

if __name__ == "__main__":
    pipeline = MyReasoningPipeline()
    pipeline.forward()
```

| 要点 | 说明 |
|------|------|
| `storage` 声明在 `__init__` | 不在 `forward()` 里临时创建 |
| `storage.step()` 在 `forward()` 里调用 | 每个算子调用传一次，自动递增 |
| 算子成员变量命名 | `self.xxx_stepN`，N 为执行顺序 |
| LLM Serving 统一声明 | 多个算子可共享同一个 serving 实例 |

### 5.2 storage.step() 的正确用法

```python
# ✅ Pipeline 标准用法：在 forward() 里每次调用时传 storage.step()
self.op1.run(storage=self.storage.step(), ...)  # step: -1 → 0
self.op2.run(storage=self.storage.step(), ...)  # step: 0 → 1

# ✅ 独立测试脚本用法：手动调用一次 step()，再传 storage 本身
storage = FileStorage("input.jsonl", cache_path="./cache")
storage.step()                          # 手动推进：-1 → 0
op.run(storage=storage, input_key="cot")  # 注意传 storage，不是 storage.step()
```

### 5.3 LazyLoader 与 import 路径

```python
# ✅ 从父模块 import
from dataflow.operators.reasoning import (
    ReasoningAnswerGenerator,
    ReasoningQuestionGenerator,
    CoTLLMJudgeRefiner,
)

# 验证 LazyLoader 管理的类名
import dataflow.operators.reasoning as r
print(r._import_structure)
```

### 5.4 APILLMServing_request 并发配置

默认值 `max_workers=10` 极大低估了 API 能力，务必根据实际情况调整（自建/代理 API 推荐 200+）。

---

## 六、Python re.split() 捕获组规范

> 诊断用根因分析见 `diagnostics/known_issues.md` Issue #006。本节仅列代码规范要求。

1. **`re.split()` pattern 中一律使用 `(?:...)`**，除非明确需要捕获内容
2. 如不得不用捕获组，split 后过滤 None：
   ```python
   parts = [s for s in re.split(pattern, text) if s is not None]
   ```
3. **Code review checklist**：凡用 `re.split()` 且 pattern 含 `(`，检查是否应改为 `(?:`

---

## 七、版本变更记录

| 日期 | 事件 |
|------|------|
| 2026-03-29 | 初始化协同开发规范文件，基于主仓库 v1.0.10 |
| 2026-03-29 | 新增 §1.7 算子复用原则、§1.8 算子健壮性与容错规范、§1.9 推理模型 CoT 输出处理规范 |
| 2026-03-30 | 新增 §五 Pipeline 开发实战指南（LazyLoader 坑、storage.step() 用法、并发配置） |
| 2026-03-30 | 新增 §六 re.split() 捕获组 Bug 记录 |
| 2026-04-02 | 整理为 skill context 文件，补充 get_desc() 返回类型说明、两种 Pipeline 风格对比 |
| 2026-04-03 | 移除 CoT Refiner 专项内容（未合入主仓库）；§二已知问题归并至 known_issues.md；对齐主仓库（OpenDCAI/DataFlow main） |

---

*追加新条目时请在对应章节末尾添加，并在 §七 版本变更记录中注明日期和内容。*
