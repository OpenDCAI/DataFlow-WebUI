---
name: dataflow-dev
description: >
  DataFlow 开发专家上下文加载器。当用户在 DataFlow 仓库中进行开发时触发，
  涵盖：新建算子/Pipeline/Prompt、诊断报错、规范审查、
  以及感知仓库变更并建议更新知识库。
  Trigger: user is developing in DataFlow repo, asks to create operator/pipeline/prompt,
  encounters errors, wants code review, or asks about operators.
---

# DataFlow 开发助手 (dataflow-dev)

> 仓库级变更策略（哪些改动被允许）不属于本技能。当你在 DataFlow-WebUI 仓库内工作时，
> 以该仓库根目录的 `CLAUDE.md` 为唯一真源。

## 激活时执行的步骤

**不要预先加载全部参考文件。** 三份参考共约 1400 行；先按意图路由，只读用得上的那一份。

1. **探测仓库状态**（在 DataFlow 仓库根目录下执行）：
   ```bash
   git branch --show-current          # 当前分支
   git log --oneline -3               # 最近提交
   git diff --name-only HEAD~1 HEAD   # 最近一次变更文件列表
   ```
2. 向用户报告当前上下文摘要（1-3行，不要冗长）
3. 判断用户意图，按下表**只读所需文件**，然后进入对应工作流

### 按需加载表

| 用户意图 | 需要读取 | 不需要读取 |
|---|---|---|
| 新建算子 / Pipeline / Prompt | `${SKILL_DIR}/context/dev_notes.md`（规范）；写算子时另加 `context/knowledge_base.md` 的 §3 算子章节 | 诊断表 |
| 报错 / 诊断 | `${SKILL_DIR}/diagnostics/known_issues.md`（先查快速匹配表，命中后只读对应 Issue 小节） | 知识库全文、开发规范 |
| 代码审查 / 规范检查 | `${SKILL_DIR}/context/dev_notes.md` | 知识库全文、诊断表 |
| 查 API / 架构问题 | `${SKILL_DIR}/context/knowledge_base.md` 中相关章节（按标题定位，不要通读） | 诊断表、开发规范 |
| 知识库更新感知 | 三份都要，因为要逐一比对 | — |

参考文件用途：

- `context/knowledge_base.md` — 架构与 API 参考（约 670 行，按章节查阅）
- `context/dev_notes.md` — 开发规范与最佳实践
- `diagnostics/known_issues.md` — 已知问题诊断表（Issue #001–#009）

<!-- @if mcp==yes -->
**有 MCP 时**：算子签名以 `get_operator_detail_by_name` 为准，它反映实际安装的版本；知识库是静态快照，冲突时以 MCP 为准。
<!-- @else -->
**离线模式**：以随技能提供的知识库和 `core_text` 静态参考为准；如果本地 DataFlow 版本不同，使用 Python 的 `inspect.signature` 做一次本地核对，并说明无法查询实时注册表。
<!-- @endif -->
---

## 子命令路由

根据用户意图，路由到对应工作流：

| 用户意图关键词 | 执行流程 |
|---|---|
| 新建算子 / new operator / create operator | → [算子创建流程](#算子创建流程) |
| 新建 Pipeline / new pipeline | → [Pipeline 创建流程](#pipeline-创建流程) |
| 新建 Prompt / new prompt | → [Prompt 创建流程](#prompt-创建流程) |
| 报错 / error / KeyError / AttributeError / Warning | → [诊断流程](#诊断流程) |
| 审查代码 / check / review / 规范检查 | → [规范审查流程](#规范审查流程) |
| 更新知识库 / sync / check updates / 仓库有新算子 | → [知识库更新感知流程](#知识库更新感知流程) |

---

## 算子创建流程

### Step 1: 防重复检查（必须）

在生成代码前，先检查是否已有功能相近算子：

```bash
# 查看各模块已注册算子
grep -r "^from \." dataflow/operators/general_text/__init__.py | grep TYPE_CHECKING -A 200 | grep "^    from"
grep -r "^    from" dataflow/operators/text_sft/__init__.py
grep -r "^    from" dataflow/operators/reasoning/__init__.py
```

对照 `context/knowledge_base.md` §八 的算子列表，确认无重复后再继续。

### Step 2: 向用户确认规格

使用 AskUserQuestion 一次性询问以下信息（合并为一轮）：
- 算子类型（filter / generate / refine / eval）
- 所属模块（general_text / text_sft / reasoning / code / 其他）
- 算子功能描述（一句话）
- 是否依赖 LLM（是/否）
- 输入列名（input_key）、输出列名（output_key）

### Step 3: 生成代码

使用 `templates/operator_template.py` 作为骨架，填入用户规格。

**硬性规范 checklist（每次生成必须逐项检查）**：
- [ ] 继承 `OperatorABC`，调用 `super().__init__()`
- [ ] 类上方有 `@OPERATOR_REGISTRY.register()` 装饰器
- [ ] `run()` 参数：输入列名以 `input_` 开头，输出列名以 `output_` 开头
- [ ] 若 run() 依赖输入列，缺列报错信息里应能暴露实际 available columns，便于上层 agent/用户修复字段绑定
- [ ] `run()` 第一个参数为 `storage: DataFlowStorage`
- [ ] `run()` 返回输出 key 列表：`return ['output_xxx']`
- [ ] `run()` 调用 `storage.read("dataframe")` 和 `storage.write(df)`
- [ ] LLM 驱动算子：`self.llm_serving` 成员变量（不能用其他名称）
- [ ] 包含 `@staticmethod get_desc(lang: str = "zh")` 方法，支持 zh/en
- [ ] LLM 响应有完整容错（参考 `context/dev_notes.md` §1.8 模板 A/B/C/D）
- [ ] 若处理 CoT 模型输出，按需剥离 `<think>` 标签（参考 §1.9）
- [ ] 配置参数放 `__init__`，列名参数放 `run()`

### Step 4: 提示注册

提醒用户在对应模块的 `__init__.py` 的 `TYPE_CHECKING` 块中添加：
```python
if TYPE_CHECKING:
    from .filter.my_new_filter import MyNewFilter  # 按实际路径
```

---

## Pipeline 创建流程

### Step 1: 向用户确认规格

- 数据来源（本地 jsonl / HuggingFace / ModelScope）
- 需要哪些算子（按功能描述，skill 来决定使用哪些算子）
- 是否需要 LLM Serving，并发量要求
- 是否需要断点续传（BatchedPipelineABC）

### Step 1.5: LLM Serving 前置检查（MANDATORY — 当 Pipeline 包含 LLM 算子时）

若 Pipeline 包含任何 LLM 依赖算子（`PromptedGenerator`、`FormatStrPromptedGenerator`、
`PromptedFilter`、`Text2MultiHopQAGenerator`、`KBCTextCleaner` 等），
**必须在生成代码前**向用户确认以下信息：

1. **API 端点** (`api_url`)：如 `https://api.openai.com/v1/chat/completions` 或自建/代理 URL
2. **模型名称** (`model_name`)：如 `gpt-4o`、`gpt-4o-mini`、`deepseek-chat`
3. **API Key 环境变量名**：确认变量名（`OPENAI_API_KEY` / `DF_API_KEY`）。只要变量名，**不要索取、接收或复述密钥本身**。

**跳过条件**：用户已明确提供上述三项信息，或 Pipeline 仅使用非 LLM 算子。

<!-- @if profile==webui -->
**WebUI 部署场景额外提醒**：
- 在 WebUI Serving Manager 中创建 serving（填入 api_url + model_name + api_key）
- 在 WebUI Pipeline 编辑器中，为**每个** LLM 算子分配 serving（不能只设置第一个）
- 已知问题：AST 解析器无法解析 `self.llm_serving` 引用，导致导入的 Pipeline 中所有算子的
  `llm_serving` 参数为空，必须在 WebUI 中手动逐个分配
<!-- @endif -->

### Step 2: 算子选择策略

优先使用已有算子，参考 `context/knowledge_base.md` §八。
若为 core_text 算子，参考 `generating-dataflow-pipeline` skill 的算子选择规则。

### Step 3: 生成代码

使用 `templates/pipeline_template.py` 作为骨架。

**硬性规范 checklist**：
- [ ] `storage` 在 `__init__` 中声明，而非在 `forward()` 里临时创建
- [ ] 每个算子调用传 `storage=self.storage.step()`（每次调用自动递增）
- [ ] 算子成员变量命名带 `_stepN` 后缀（N 为执行顺序）
- [ ] LLM Serving 在 `__init__` 中统一声明
- [ ] `max_workers` 根据 API 能力设置（自建/代理 API 推荐 200+）
- [ ] 包含 `if __name__ == "__main__":` 入口
- [ ] API key 通过环境变量注入，不硬编码

---

## Prompt 创建流程

1. 继承 `PromptABC`（标准）或 `DIYPromptABC`（绕过白名单限制）
2. 加上 `@PROMPT_REGISTRY.register()` 装饰器
3. 实现 `build_prompt(self, ...) -> str` 方法
4. 若算子需限制 Prompt 类型，在算子类上用 `@prompt_restrict(MyPrompt)`
5. 注意 `@prompt_restrict` 必须紧贴类定义上方（参见 Issue #007）

---

## 诊断流程

1. 读取用户的报错信息
2. 在 `diagnostics/known_issues.md` 中匹配已知 Issue
3. 若命中已知 Issue，直接给出根因 + 解决方案
4. 若未命中，结合 `context/knowledge_base.md` 中的架构知识进行分析
5. 给出修复代码示例

**快速匹配表**（无需读文件时的速查）：

| 报错关键词 | 对应 Issue |
|---|---|
| `Unexpected key 'xxx' in operator` | Issue #001（配置参数命名，仅警告非错误）|
| `No object named 'Xxx' found in 'operators' registry` | Issue #002（__init__.py 未注册）|
| `Key Matching Error` / `does not match any output keys` | Issue #003（Pipeline key 不一致）|
| `You must call storage.step() before` | Issue #004（缺少 storage.step()）|
| `DummyStorage` + `AttributeError` / `TypeError` | Issue #005（DummyStorage 不支持 get_keys_from_dataframe）|
| `ModuleNotFoundError` + `dataflow.operators.reasoning.refine` | Issue（LazyLoader 路径，应从父模块 import）|
| `AttributeError: 'NoneType' object has no attribute 'strip'` + `re.split` | Issue #006（re.split 捕获组 None 问题）|
<!-- @if profile==webui -->
| `Failed to process parameter: llm_serving` + `param_value: ''` | **WebUI caveat**（不是 `known_issues.md` 里的编号问题）：Pipeline 从 .py 文件导入后，AST 解析器无法解析 `self.llm_serving` 引用，导致所有算子的 llm_serving 为空 —— 需在 WebUI 中为**每个** LLM 算子手动分配 serving |
<!-- @endif -->

---

## 规范审查流程

对用户提供的代码文件，逐项检查以下规范：

### 算子审查 checklist

```
□ 继承链：OperatorABC → super().__init__() → self.logger 可用
□ 注册：@OPERATOR_REGISTRY.register() 在类定义上方（不是函数上方）
□ run() 参数命名：input_* / output_* / storage
□ run() 返回值：list of output key names
□ storage.read() + storage.write() 都存在
□ LLM 驱动算子：self.llm_serving 命名正确
□ 容错：LLM 响应逐条 try/except，失败有默认值
□ CoT 模型输出：非 CoT 训练目标字段已剥离 <think> 标签
□ get_desc() 存在且支持 zh/en
□ __init__.py TYPE_CHECKING 块已注册
□ @prompt_restrict（如有）紧贴类定义
```

### Pipeline 审查 checklist

```
□ storage 在 __init__ 中声明
□ 所有算子为成员变量（compile() 依赖此机制）
□ forward() 中每次 op.run() 传 storage.step()
□ max_workers 值合理（不要用默认的 10）
□ API key 不硬编码
□ 有 if __name__ == "__main__": 入口
```

---

## 知识库更新感知流程

### 使用 GitHub CLI 感知变更

```bash
# 前提：需要 gh CLI 已认证（gh auth login）
# 查看最近 Issues（可能包含新算子/新功能讨论）
gh issue list --repo OpenDCAI/DataFlow --limit 20 --state open

# 查看最近合并的 PR（新算子通常以 PR 形式合入）
gh pr list --repo OpenDCAI/DataFlow --state merged --limit 20

# 查看某 PR 的具体文件变更
gh pr view <PR_NUMBER> --repo OpenDCAI/DataFlow
```

### 本地变更检测

```bash
# 查看 operators 目录下最近修改的文件
git log --oneline --diff-filter=A -- 'dataflow/operators/**/*.py' | head -20

# 列出所有算子模块 __init__.py 中注册的算子名（用于对比知识库）
python -c "
import sys; sys.path.insert(0, '.')
from dataflow.utils.registry import OPERATOR_REGISTRY
OPERATOR_REGISTRY._get_all()
names = sorted(OPERATOR_REGISTRY.get_obj_map().keys())
for n in names: print(n)
"

# 快速扫描：找出所有已注册但未在 knowledge_base.md 中出现的算子
```

### 判断是否需要更新知识库

当以下任一情况发生时，建议更新知识库：

1. `gh pr list` 发现有新 PR 涉及 `dataflow/operators/` 路径
2. `git log` 发现有新的算子文件（`_filter.py` / `_generator.py` / `_refiner.py` / `_evaluator.py`）
3. 用户反馈某算子不存在于知识库中但实际存在于代码中
4. 算子签名（`__init__` / `run()` 参数）发生了变更

### 更新知识库的步骤

1. 读取新算子文件，提取：类名、`__init__` 参数、`run()` 参数、`get_desc()` 说明
2. 在 `context/knowledge_base.md` §八 对应模块下补充算子条目
3. 在 `context/dev_notes.md` 七、版本变更记录中追加条目
4. 提交说明：`docs: sync knowledge_base with new operators from <PR/commit>`

---

## 重要架构提醒（每次生成代码前隐式检查）

1. **LazyLoader import 路径**：必须从父模块 import，不能直接用子包路径
   ```python
   # ✅ 正确
   from dataflow.operators.reasoning import ReasoningAnswerGenerator
   # ❌ 错误
   from dataflow.operators.reasoning.generate.reasoning_answer_generator import ReasoningAnswerGenerator
   ```

2. **storage.step() 用法**：
   - Pipeline `forward()` 中：`op.run(storage=self.storage.step(), ...)`（每次调用传递）
   - 独立测试脚本中：先 `storage.step()`，再 `op.run(storage=storage, ...)`

3. **re.split() 捕获组**：凡在 `re.split()` pattern 中用 `(...)`，一律改为 `(?:...)`

4. **Serving 生命周期**：不要在算子内手动调用 `serving.cleanup()`，由 Pipeline 管理

---

## 文件索引

| 文件 | 用途 |
|---|---|
| `context/knowledge_base.md` | DataFlow 架构、API、目录结构、算子列表（只读参考） |
| `context/dev_notes.md` | 开发规范、最佳实践（可追加更新）；已知问题指针指向 known_issues.md |
| `diagnostics/known_issues.md` | 结构化 Issue 数据库，供诊断快速匹配 |
| `templates/operator_template.py` | 算子骨架模板 |
| `templates/pipeline_template.py` | Pipeline 骨架模板 |
| `templates/prompt_template.py` | Prompt 骨架模板 |
| `scripts/check_updates.sh` | 检测仓库变更、感知是否需要更新知识库的脚本 |
