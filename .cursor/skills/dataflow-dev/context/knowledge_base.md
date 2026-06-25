# DataFlow 知识库（Knowledge Base）

> 版本：1.0.10（main 分支）
> 仓库：https://github.com/OpenDCAI/DataFlow.git
> 官方文档：https://opendcai.github.io/DataFlow-Doc/zh/
> 本文件用于在无上下文情况下理解、使用和开发 DataFlow。
> **此文件为只读参考**，如需更新请通过 SKILL.md 的"知识库更新感知流程"操作。

---

## 一、项目总体概述

DataFlow 是一个**以数据为中心（Data-Centric AI）**的数据治理系统，面向大语言模型（LLM）的训练数据制备。核心定位：

- **修正、扩增、评估与过滤**低质量数据，生成高质量 LLM 训练数据集
- 支持 PDF 文档、纯文本、爬虫数据、多模态等多种数据来源
- 当前版本：`1.0.10`（`dataflow/version.py`）
- Python 要求：`>= 3.10`
- 包名：`open-dataflow`（PyPI）

### 四大核心组成

| 组件 | 说明 |
|------|------|
| **算子（Operator）** | 原子性数据处理单元，基于规则/DL模型/LLM |
| **流水线（Pipeline）** | 有序连接算子，针对具体数据处理场景 |
| **提示词（Prompt）** | 支持注册和映射的提示词模板 |
| **LLM Serving** | 统一封装本地模型和API推理 |

---

## 二、目录结构

```
DataFlow/
├── dataflow/
│   ├── __init__.py          # 包入口，导出 utils、operators、prompts、logger
│   ├── version.py           # 版本号 1.0.10
│   ├── logger.py            # 日志系统（colorlog，自定义 SUCCESS 级别）
│   ├── cli.py               # CLI 入口（Typer）
│   ├── core/                # 抽象基类层
│   │   ├── operator.py      # OperatorABC, get_operator()
│   │   ├── llm_serving.py   # LLMServingABC
│   │   ├── wrapper.py       # WrapperABC
│   │   ├── prompt.py        # PromptABC, DIYPromptABC, @prompt_restrict 装饰器
│   │   └── __init__.py      # 导出 OPERATOR_CLASSES, LLM_SERVING_CLASSES 等
│   ├── pipeline/
│   │   ├── Pipeline.py      # PipelineABC, BatchedPipelineABC, StreamBatchedPipelineABC
│   │   └── nodes.py         # OperatorNode, KeyNode（DAG 节点）
│   ├── operators/           # 所有算子实现
│   │   ├── general_text/    # 通用文本算子
│   │   ├── text_sft/        # SFT 指令微调算子
│   │   ├── text_pt/         # 预训练文本算子
│   │   ├── reasoning/       # 推理数据算子
│   │   ├── code/            # 代码数据算子
│   │   ├── core_text/       # 核心文本算子
│   │   ├── core_vision/     # 视觉算子
│   │   ├── core_speech/     # 语音算子
│   │   ├── agentic_rag/     # AgenticRAG 算子
│   │   ├── chemistry/       # 化学领域算子
│   │   ├── conversations/   # 对话数据算子
│   │   ├── knowledge_cleaning/ # 知识库清洗算子
│   │   ├── pdf2vqa/         # PDF→VQA 算子
│   │   └── text2sql/        # Text→SQL 算子
│   ├── prompts/             # 提示词模板
│   │   ├── general_text.py  # 通用文本 Prompt
│   │   ├── reasoning/       # 推理 Prompt
│   │   └── __init__.py
│   ├── serving/             # LLM/VLM 服务封装
│   │   ├── api_llm_serving_request.py  # 通用 HTTP API（OpenAI 兼容）
│   │   ├── lite_llm_serving.py         # LiteLLM 多提供商
│   │   ├── local_model_llm_serving.py  # vLLM / SGLang 本地模型
│   │   ├── localhost_llm_api_serving.py
│   │   ├── LocalSentenceLLMServing.py  # Embedding 服务
│   │   ├── light_rag_serving.py
│   │   ├── flash_rag_serving.py
│   │   └── __init__.py
│   ├── utils/
│   │   ├── registry.py      # Registry + LazyLoader（核心注册机制）
│   │   ├── storage.py       # DataFlowStorage, FileStorage, LazyFileStorage, DummyStorage
│   │   └── __init__.py      # 导出 OPERATOR_REGISTRY, PROMPT_REGISTRY
│   ├── wrapper/
│   │   ├── auto_op.py       # AutoOP, OPRuntime（Pipeline 编译核心）
│   │   └── batch_wrapper.py # BatchWrapper（批处理包装器）
│   ├── cli_funcs/           # CLI 子命令实现
│   ├── example/             # 示例数据文件（jsonl/json）
│   └── webui/               # WebUI 相关
└── awesome_dataflow.md      # 生态项目列表
```

---

## 三、核心抽象层（`dataflow/core/`）

### 3.1 OperatorABC

所有算子的抽象基类（`dataflow/core/operator.py`）：

```python
class OperatorABC(ABC):
    def __init__(self):
        self.logger = get_logger()
        self.ALLOWED_PROMPTS = tuple([type[DIYPromptABC | PromptABC]])

    @abstractmethod
    def run(self) -> None:
        pass
```

**实现规范**：
1. 继承 `OperatorABC`，调用 `super().__init__()`
2. 用 `@OPERATOR_REGISTRY.register()` 装饰器注册（必须在类定义上方，不能错位）
3. `__init__` 接收超参数（如 `min_words`, `llm_serving` 等）
4. 实现 `run(self, storage: DataFlowStorage, input_key: str, ...)` 方法
5. `run()` 参数命名约定：`input_*` 开头为输入 key，`output_*` 开头为输出 key，其他参数打警告（正常）
6. `run()` 必须调用 `storage.read()` 和 `storage.write()`
7. `run()` 返回输出 key 列表（如 `['instruction', 'output']`）
8. 实现 `@staticmethod get_desc(lang="zh")` 方法——**返回值为纯字符串（str），不是 dict**

**get_operator 工厂函数**：

```python
from dataflow.core import get_operator
op = get_operator("WordNumberFilter", {"min_words": 10, "max_words": 500})
```

### 3.2 LLMServingABC

所有 LLM 服务的抽象基类（`dataflow/core/llm_serving.py`）：

```python
class LLMServingABC(ABC):
    @abstractmethod
    def generate_from_input(self, user_inputs: List[str], system_prompt: str) -> List[str]: ...
    @abstractmethod
    def start_serving(self): ...
    @abstractmethod
    def cleanup(self): ...
    def load_model(self, model_name_or_path: str, **kwargs): ...
```

### 3.3 WrapperABC

包装器的抽象基类，用于对算子进行包装增强（`dataflow/core/wrapper.py`）。

### 3.4 Prompt 系统

```python
# PromptABC: 标准 Prompt 基类
class PromptABC:
    def build_prompt(self): ...

# DIYPromptABC: 用户自定义 Prompt 基类（可绕过 @prompt_restrict 白名单）
class DIYPromptABC(PromptABC): ...

# @prompt_restrict 装饰器: 限制算子允许使用的 Prompt 类型
# 注意：必须紧贴类定义上方，不能放在其他函数上方
@prompt_restrict(SFTGeneratorSeedPrompt)
class SFTGeneratorSeed(OperatorABC): ...
```

---

## 四、Pipeline 系统（`dataflow/pipeline/`）

### 4.1 三种 Pipeline 基类

| 类名 | 说明 |
|------|------|
| `PipelineABC` | 基础 Pipeline，`forward()` 运行一次 |
| `BatchedPipelineABC` | 支持分批处理，支持 `resume_from_last`；`forward(batch_size=N, resume_from_last=True)` |
| `StreamBatchedPipelineABC` | 流式分批，通过 `iter_chunks()` 迭代数据 |

### 4.2 两种 Pipeline 开发风格

DataFlow 存在两种合法风格，**不要混用**：

**风格 A：继承 PipelineABC（适合需要 compile() / DAG 可视化的场景）**

```python
from dataflow.pipeline.Pipeline import PipelineABC
from dataflow.utils.storage import FileStorage

class MyPipeline(PipelineABC):
    def __init__(self):
        super().__init__()
        self.op1 = WordNumberFilter(min_words=10)
        self.op2 = SFTGeneratorSeed(llm_serving=my_serving)

    def forward(self):
        storage = FileStorage("input.jsonl", cache_path="./cache", ...)
        self.op1.run(storage=storage.step(), input_key="text")
        self.op2.run(storage=storage.step(), input_key="text")

pipeline = MyPipeline()
pipeline.compile()   # 编译 DAG + key 校验
pipeline.forward()   # 运行
```

**风格 B：纯类封装（DataFlow 现有 example 实际采用，无需 compile）**

```python
# 对标 reasoning_math_pipeline.py / Reasoning_CPUPipeline
class MyCotCleanPipeline:
    def __init__(self):
        self.storage = FileStorage("./input.jsonl", cache_path="./cache", ...)
        self.llm_serving = APILLMServing_request(...)
        self.refiner_step1 = CoTLLMJudgeRefiner(llm_serving=self.llm_serving, ...)
        self.another_op_step2 = ...

    def forward(self):
        self.refiner_step1.run(storage=self.storage.step(), input_key="cot", ...)
        self.another_op_step2.run(storage=self.storage.step(), ...)

if __name__ == "__main__":
    pipeline = MyCotCleanPipeline()
    pipeline.forward()
```

**选择建议**：
- 需要 `compile()` 验证、`draw_graph()` 可视化、断点续传 → 风格 A
- 快速实验、脚本运行、不需要 DAG 功能 → 风格 B

### 4.3 Pipeline 编译机制（风格 A 专用）

`compile()` 过程：
1. 将所有 `OperatorABC` 成员变量替换为 `AutoOP` 包装
2. 执行 `forward()` 记录所有 `OPRuntime`（不实际运行算子）
3. 调用 `_build_operator_nodes_graph()` 构建有向无环图（DAG）
4. 验证 key 完整性：每个算子的 `input_*` key 必须在上游算子的 `output_*` key 或初始数据集列中存在
5. Key 验证失败会抛出 `KeyError` 并打印详细信息

### 4.4 BatchedPipeline 用法

```python
from dataflow.pipeline.Pipeline import BatchedPipelineABC

class MyBatchedPipeline(BatchedPipelineABC):
    def __init__(self): ...
    def forward(self): ...

pipeline = MyBatchedPipeline()
pipeline.compile()
pipeline.forward(
    batch_size=100,           # 每批 100 条
    resume_from_last=True     # 从上次中断处继续
)
```

断点续传机制：在 cache 目录下写 `{prefix}_last_success_step.txt`，格式为 `step,batch`。

### 4.5 DAG 可视化

```python
pipeline.compile()
pipeline.draw_graph(port=8080, hide_no_changed_keys=True)
# 需要安装: pip install pyvis
```

---

## 五、存储系统（`dataflow/utils/storage.py`）

### 5.1 存储类型

| 类名 | 说明 | 适用场景 |
|------|------|---------|
| `FileStorage` | 每次 read/write 立即落盘 | 通用，简单可靠 |
| `LazyFileStorage` | 内存中操作，进程退出时落盘（原子写） | 高性能，防止部分写 |
| `DummyStorage` | 纯内存，不落盘 | **仅供 BatchWrapper 内部使用**，不要用于 Pipeline |

### 5.2 FileStorage 使用

```python
from dataflow.utils.storage import FileStorage

storage = FileStorage(
    first_entry_file_name="./data/input.jsonl",   # 初始数据文件
    cache_path="./cache",                          # 中间结果目录
    file_name_prefix="dataflow_cache_step",        # 缓存文件前缀
    cache_type="jsonl"                             # 缓存格式: json/jsonl/csv/parquet/pickle
)
```

`first_entry_file_name` 支持：
- 本地文件路径：`./data/input.jsonl`
- HuggingFace：`hf:openai/gsm8k:main:train`
- ModelScope：`ms:modelscope/gsm8k:train`

### 5.3 storage.step() 正确用法

```python
# Pipeline forward() 中：每次 op.run() 时传入（自动递增）
self.op1.run(storage=self.storage.step(), ...)  # -1 → 0
self.op2.run(storage=self.storage.step(), ...)  # 0 → 1

# 独立测试脚本中：手动调用一次再传 storage 本身
storage = FileStorage("input.jsonl", cache_path="./cache")
storage.step()           # 手动推进：-1 → 0
op.run(storage=storage, input_key="text")   # 注意：不要再传 storage.step()
```

### 5.4 LazyFileStorage 推荐配置

```python
from dataflow.utils.storage import LazyFileStorage

storage = LazyFileStorage(
    first_entry_file_name="input.jsonl",
    cache_path="./cache",
    file_name_prefix="pipeline_cache",
    cache_type="jsonl",
    save_on_exit=True,      # 进程退出时自动 flush
    flush_all_steps=False   # 只保留最新步骤（节省磁盘）
)
```

---

## 六、LLM Serving 系统（`dataflow/serving/`）

### 6.1 可用 Serving 实现

| 类名 | 说明 |
|------|------|
| `APILLMServing_request` | 通用 HTTP API，支持 OpenAI 兼容接口，多线程并发 |
| `LiteLLMServing` | 基于 LiteLLM，支持 OpenAI/Anthropic/Azure/Bedrock 等 |
| `LocalModelLLMServing_vllm` | 本地 vLLM 推理服务 |
| `LocalModelLLMServing_sglang` | 本地 SGLang 推理服务 |
| `LocalHostLLMAPIServing_vllm` | 本地已启动的 vLLM API |
| `APIVLMServing_openai` | 视觉语言模型 API（OpenAI 格式） |
| `LocalVLMServing_vllm` | 本地 VLM（vLLM）服务 |
| `LocalEmbeddingServing` | 本地 Sentence Embedding 服务 |
| `LightRAGServing` | LightRAG 服务 |
| `PerspectiveAPIServing` | Google Perspective API |

### 6.2 APILLMServing_request 使用

```python
import os
os.environ["DF_API_KEY"] = "your-api-key"  # API key 必须通过环境变量注入，禁止硬编码

from dataflow.serving import APILLMServing_request

serving = APILLMServing_request(
    api_url="https://api.openai.com/v1/chat/completions",
    key_name_of_api_key="DF_API_KEY",   # 环境变量名
    model_name="gpt-4o",
    temperature=0.0,
    max_workers=200,      # 推荐：自建/代理 API 用 200+；官方 API 用 50-100
    max_retries=5,
    connect_timeout=10.0,
    read_timeout=120.0,
)

responses = serving.generate_from_input(
    user_inputs=["问题1", "问题2"],
    system_prompt="You are a helpful assistant",
    json_schema=None   # 可选，结构化输出
)
```

**max_workers 选择指南**：

| API 情况 | 推荐 max_workers |
|---|---|
| 官方 OpenAI / DeepSeek（有限速） | 50–100 |
| 自建/代理 API（200-400 并发支持） | 200–300 |
| 本地 vLLM（单机） | 50–100 |

默认值 10 极大低估了 API 能力，务必根据实际情况调高。

### 6.3 Serving 生命周期

- Pipeline 使用引用计数（`llm_serving_counter`）管理 Serving 生命周期
- **不要在算子中手动调用 `serving.cleanup()`**，由 Pipeline 自动管理
- 算子中持有 Serving 的成员变量**必须命名为 `self.llm_serving`**

---

## 七、算子注册系统（`dataflow/utils/registry.py`）

### 7.1 Registry 机制

```python
from dataflow.utils.registry import OPERATOR_REGISTRY, PROMPT_REGISTRY

@OPERATOR_REGISTRY.register()
class MyFilter(OperatorABC): ...

@PROMPT_REGISTRY.register()
class MyPrompt(PromptABC): ...
```

### 7.2 LazyLoader 机制与 import 路径

每个算子子模块的 `__init__.py` 采用 LazyLoader 模式，将所有子包算子**扁平注册**到父模块命名空间：

```python
# ✅ 正确：从父模块 import
from dataflow.operators.reasoning import CoTLLMJudgeRefiner
from dataflow.operators.general_text import WordNumberFilter

# ❌ 错误：直接用子包路径（会绕过 LazyLoader，报 ModuleNotFoundError）
from dataflow.operators.reasoning.refine.cot_llm_judge_refiner import CoTLLMJudgeRefiner
```

**新增算子必须**在对应模块 `__init__.py` 的 `TYPE_CHECKING` 块中声明：

```python
if TYPE_CHECKING:
    from .filter.my_new_filter import MyNewFilter
```

**验证已注册的算子**：

```python
import dataflow.operators.reasoning as r
print(r._import_structure)  # 查看 LazyLoader 管理的所有类名
```

---

## 八、算子分类与功能概述

### 8.1 `general_text`（通用文本）

**Filter（规则型）**：
`ColonEndFilter`, `SentenceNumberFilter`, `ContentNullFilter`, `SymbolWordRatioFilter`,
`AlphaWordsFilter`, `WordNumberFilter`, `CharNumberFilter`, `MeanWordLengthFilter`,
`StopWordFilter`, `NoPuncFilter`, `SpecialCharacterFilter`, `WatermarkFilter`,
`CurlyBracketFilter`, `CapitalWordsFilter`, `LoremIpsumFilter`, `UniqueWordsFilter`,
`LineStartWithBulletpointFilter`, `LineWithJavascriptFilter`, `LineEndWithEllipsisFilter`,
`HtmlEntityFilter`, `IDCardFilter`

**Filter（语言/去重）**：
`LanguageFilter`, `LLMLanguageFilter`,
`HashDeduplicateFilter`, `MinHashDeduplicateFilter`, `NgramHashDeduplicateFilter`,
`SimHashDeduplicateFilter`, `SemDeduplicateFilter`

**Filter（其他）**：
`LangkitFilter`, `LexicalDiversityFilter`, `NgramFilter`, `PresidioFilter`,
`BlocklistFilter`, `PerspectiveFilter`

**Refine**：HTML实体、URL移除、小写转换、NER、PII匿名化、引用移除、缩写扩展、
emoji移除、多余空格移除、图片引用移除、数字/标点移除、停用词移除、
拼写校正、词干化/词形还原、文本规范化等

**Eval**：Ngram、词汇多样性、Langkit、Presidio、BERT、BLEU、CIDEr、Perspective、Task2Vec、Vendi

### 8.2 `text_sft`（SFT 指令微调）

**Eval**：
`AlpagasusSampleEvaluator`, `DeitaQualitySampleEvaluator`, `DeitaComplexitySampleEvaluator`,
`InstagSampleEvaluator`, `RMSampleEvaluator`, `SuperfilteringSampleEvaluator`,
`TreeinstructSampleEvaluator`

**Filter**：对应上述各评估算子的过滤版本

**Generate**：
- `CondorGenerator`：Condor 数据生成
- `SFTGeneratorSeed`：从种子文档生成 SFT 格式 instruction-output 对

**Refine**：`CondorRefiner`

### 8.3 `reasoning`（推理数据）

**Generate**：
`ReasoningAnswerGenerator`, `ReasoningQuestionGenerator`,
`ReasoningAnswerExtractionQwenMathEvalGenerator`, `ReasoningPseudoAnswerGenerator`,
`ReasoningPretrainFormatConvertGenerator`, `ReasoningQuestionFusionGenerator`

**Eval**：
`ReasoningCategoryDatasetEvaluator`, `ReasoningDifficultyDatasetEvaluator`,
`ReasoningTokenDatasetEvaluator`,
`ReasoningQuestionCategorySampleEvaluator`, `ReasoningQuestionDifficultySampleEvaluator`,
`ReasoningQuestionSolvableSampleEvaluator`

**Filter**：
`ReasoningAnswerFormatterFilter`, `ReasoningAnswerGroundTruthFilter`,
`ReasoningAnswerNgramFilter`, `ReasoningAnswerPipelineRootFilter`,
`ReasoningAnswerTokenLengthFilter`, `ReasoningQuestionFilter`,
`ReasoningAnswerModelJudgeFilter`

**Refine（CoT 清洗）**：
`CoTLLMJudgeRefiner`（Method A）, `CoTMonteCarloRefiner`（Method B）,
`CoTChunkCompressRefiner`（Method C）, `CoTPatternRefiner`（Method D）,
`CoTMathNormRefiner`（规则型 LaTeX 标准化，无 LLM）

### 8.4 `code`（代码数据）

包含 `eval/`, `filter/`, `generate/` 三类子目录，具体算子参见对应 `__init__.py`。

### 8.5 `core_text`（核心文本）

**Generate**：`PromptedGenerator`, `FormatStrPromptedGenerator`, `Text2MultiHopQAGenerator`,
`BenchAnswerGenerator`, `ChunkedPromptedGenerator`, `EmbeddingGenerator`,
`RandomDomainKnowledgeRowGenerator`, `RetrievalGenerator`

**Filter**：`GeneralFilter`, `KCenterGreedyFilter`, `PromptedFilter`

**Eval**：`BenchDatasetEvaluator`, `BenchDatasetEvaluatorQuestion`, `PromptedEvaluator`,
`Text2QASampleEvaluator`, `UnifiedBenchDatasetEvaluator`

**Refine**：`PandasOperator`, `PromptedRefiner`

### 8.6 其他算子模块

| 模块 | 内容 |
|---|---|
| `agentic_rag` | AgenticRAG 相关算子 |
| `chemistry` | 化学领域数据算子 |
| `conversations` | 对话数据算子 |
| `knowledge_cleaning` | 知识库清洗（`FileOrURLToMarkdownConverterFlash`, `KBCChunkGenerator`, `KBCTextCleaner`） |
| `pdf2vqa` | PDF → VQA 数据生成 |
| `text2sql` | Text2SQL 数据（含 `Text2SQLCoTVotingGenerator` 等） |
| `text_pt` | 预训练文本算子 |
| `core_vision` | 视觉算子 |
| `core_speech` | 语音算子 |

---

## 九、Prompt 系统（`dataflow/prompts/`）

### 9.1 注册与使用

```python
from dataflow.utils.registry import PROMPT_REGISTRY
from dataflow.core.prompt import PromptABC

@PROMPT_REGISTRY.register()
class MyPrompt(PromptABC):
    def __init__(self, custom_param="default"):
        self.custom_param = custom_param

    def build_prompt(self, content: str) -> str:
        return f"System: {self.custom_param}\nUser: {content}"
```

### 9.2 `@prompt_restrict` 装饰器与 `DIYPromptABC`

```python
from dataflow.core.prompt import prompt_restrict, DIYPromptABC

# 限制算子只能接受特定 Prompt 类型
@prompt_restrict(MyPrompt)          # ← 必须紧贴类定义上方
@OPERATOR_REGISTRY.register()       # ← 两个装饰器顺序可互换，但都要紧贴
class MyOperator(OperatorABC): ...

# 用户自定义 Prompt，可绕过白名单
class MyCustomPrompt(DIYPromptABC):
    def build_prompt(self, content: str) -> str:
        return f"Custom: {content}"
```

---

## 十、日志系统

```python
from dataflow import get_logger
logger = get_logger()

logger.debug("debug")
logger.info("info")
logger.success("success")    # 自定义 SUCCESS 级别（绿色）
logger.warning("warning")
logger.error("error")

# 控制级别：export DF_LOGGING_LEVEL=DEBUG
```

---

## 十一、CLI 系统

```bash
dataflow --version
dataflow env
dataflow init                 # base 初始化
dataflow init repo            # 初始化仓库脚手架
# dataflow init operator      # TODO: 尚未实现
# dataflow init pipeline      # TODO: 尚未实现
dataflow eval init / api / local
dataflow pdf2model init --qa kbc
dataflow text2model init / train
dataflow webui --host 0.0.0.0 --port 8000
```

---

## 十二、常见设计模式

### 模式 1：纯规则过滤

```python
@OPERATOR_REGISTRY.register()
class MyRuleFilter(OperatorABC):
    def __init__(self, threshold=0.5):
        super().__init__()
        self.threshold = threshold

    def run(self, storage, input_key, output_key="label"):
        df = storage.read("dataframe")
        df[output_key] = df[input_key].apply(lambda x: ...)
        storage.write(df[df[output_key]])
        return [output_key]
```

### 模式 2：LLM 驱动算子

```python
@OPERATOR_REGISTRY.register()
class MyLLMOperator(OperatorABC):
    def __init__(self, llm_serving: LLMServingABC):
        super().__init__()
        self.llm_serving = llm_serving  # 必须用此名，Pipeline 据此管理生命周期

    def run(self, storage, input_key, output_key="result"):
        df = storage.read("dataframe")
        prompts = [f"处理：{row[input_key]}" for _, row in df.iterrows()]
        results = self.llm_serving.generate_from_input(prompts)
        df[output_key] = results
        storage.write(df)
        return [output_key]
```

### 模式 3：多输出 key

```python
def run(self, storage, input_key, output_instruction="instruction", output_answer="output"):
    ...
    df["instruction"] = ...
    df["output"] = ...
    storage.write(df)
    return ["instruction", "output"]
```

---

## 十三、安装说明

```bash
# 用户安装
pip install open-dataflow

# 开发者安装（可编辑模式）
git clone https://github.com/OpenDCAI/DataFlow.git
cd DataFlow
pip install -e .

# GPU 后端
pip install open-dataflow[vllm]     # vLLM
pip install open-dataflow[sglang]   # SGLang
pip install open-dataflow[litellm]  # LiteLLM
```

---

## 十四、项目来源与生态

- **主仓库**：https://github.com/OpenDCAI/DataFlow
- **文档**：https://opendcai.github.io/DataFlow-Doc/zh/
- **WebUI 仓库**：https://github.com/OpenDCAI/DataFlow-WebUI

---

*最后同步：2026-04-03（基于 v1.0.10 main 分支）*
*如需更新算子列表，运行 SKILL.md 中的"知识库更新感知流程"*
