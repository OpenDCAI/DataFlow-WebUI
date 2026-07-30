---
name: unified-bench-dataset-evaluator
description: >-
  UnifiedBenchDatasetEvaluator 算子参考文档。

  使用场景：对 bench 数据集的模型回答进行统一评测。
---

# UnifiedBenchDatasetEvaluator 算子参考

`UnifiedBenchDatasetEvaluator` 支持 6 类评测类型（eval_type），对生成回答进行评分，写入 4 个输出列。

## 1. 导入

```python
from dataflow.operators.core_text import UnifiedBenchDatasetEvaluator
```

## 2. 构造函数

```python
UnifiedBenchDatasetEvaluator(
    eval_type="key2_qa",
    llm_serving=None,
    prompt_template=None,
    eval_result_path=None,
    metric_type=None,
    use_semantic_judge=False,
    system_prompt="You are a helpful assistant specialized in evaluating answer correctness.",
)
```

**重要**：必须显式传 `prompt_template=None`。默认值是 `AnswerJudgePrompt`（类本身），会触发 `TypeError`。

| 参数 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `eval_type` | 否 | `"key2_qa"` | 评测类型 |
| `llm_serving` | 条件必填 | `None` | `use_semantic_judge=True` 时必须提供 |
| `prompt_template` | 否 | `AnswerJudgePrompt` | 传 `None` 使用内置回退 |
| `eval_result_path` | 否 | 自动生成 | 统计结果 JSON 文件路径 |
| `metric_type` | 否 | `None` | 评测指标，不传则自动选择 |
| `use_semantic_judge` | 否 | `False` | 使用 LLM 做语义判断 |
| `system_prompt` | 否 | `"You are a helpful assistant..."` | LLM 系统提示词（`use_semantic_judge=True` 时使用） |

### eval_type 及所需 input_xxx_key

| eval_type | 必传的 input_xxx_key |
|-----------|---------------------|
| `key1_text_score` | `input_text_key` |
| `key2_qa` | `input_question_key`, `input_target_key` |
| `key2_q_ma` | `input_question_key`, `input_targets_key` |
| `key3_q_choices_a` | `input_question_key`, `input_choices_key`, `input_label_key` |
| `key3_q_choices_as` | `input_question_key`, `input_choices_key`, `input_labels_key` |
| `key3_q_a_rejected` | `input_question_key`, `input_better_key`, `input_rejected_key` |

## 3. run() 方法签名

```python
op.run(
    storage=self.storage.step(),
    input_question_key="question",
    input_target_key="golden_answer",
    input_pred_key="generated_ans",
)
# 返回: 列名列表
```

| 参数 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `storage` | 是 | None | Storage 步骤对象 |
| `input_pred_key` | 否 | `"generated_ans"` | 模型生成回答的列名 |
| `input_question_key` | 条件必填 | `None` | 问题列名 |
| `input_target_key` | 条件必填 | `None` | 单标准答案列名 |
| `input_targets_key` | 条件必填 | `None` | 多标准答案列名 |
| `input_choices_key` | 条件必填 | `None` | 选项列名 |
| `input_label_key` | 条件必填 | `None` | 单标准标签列名 |
| `input_labels_key` | 条件必填 | `None` | 多标准标签列名 |
| `input_better_key` | 条件必填 | `None` | 偏好答案列名 |
| `input_rejected_key` | 条件必填 | `None` | 拒绝答案列名 |
| `input_context_key` | 否 | `None` | 可选的上下文列，提供额外信息 |

## 4. 输出列（4列）

- `eval_valid`：评测是否有效的布尔列
- `eval_error`：错误信息列
- `eval_pred`：解析后的预测答案列
- `eval_score`：数值评分列

## 5. 使用示例

```python
from dataflow.operators.core_text import UnifiedBenchDatasetEvaluator
from dataflow.serving import APILLMServing_request
from dataflow.utils.storage import FileStorage

class MyPipeline:
    def __init__(self):
        self.storage = FileStorage(
            first_entry_file_name="./data/bench.jsonl",
            cache_path="./cache",
            file_name_prefix="step",
            cache_type="jsonl"
        )

        self.llm_serving = APILLMServing_request(
            api_url="https://api.openai.com/v1/chat/completions",
            key_name_of_api_key="DF_API_KEY",
            model_name="gpt-4o",
            max_workers=10
        )

        self.evaluator = UnifiedBenchDatasetEvaluator(
            eval_type="key2_qa",
            llm_serving=self.llm_serving,
            prompt_template=None,
            use_semantic_judge=True
        )

    def forward(self):
        self.evaluator.run(
            storage=self.storage.step(),
            input_question_key="question",
            input_target_key="golden_answer",
            input_pred_key="generated_ans"
        )

if __name__ == "__main__":
    pipeline = MyPipeline()
    pipeline.forward()
```

## 6. 重要说明

- `eval_type` 必须与 `BenchAnswerGenerator` 的 `eval_type` 保持一致
- 统计结果保存到 `eval_result_path` 指定的 JSON 文件
- `use_semantic_judge=True` 时必须提供 `llm_serving`

## 5. 运行逻辑

1. 从 storage 读取 DataFrame。
2. 根据 `eval_type` 验证所需的 `input_xxx_key` 列存在。
3. 创建 4 个输出列：`eval_valid`、`eval_error`、`eval_pred`、`eval_score`。
4. 对每行：
   - 从 `input_pred_key` 提取预测答案
   - 根据 `eval_type` 提取标准答案
   - 如果 `use_semantic_judge=True`：调用 LLM 判断正确性
   - 如果 `use_semantic_judge=False`：使用基于规则的比较
   - 解析并评分结果
5. 将结果写入 4 个输出列。
6. 保存统计信息到 `eval_result_path` JSON 文件。
7. 返回列名列表。

## 6. prompt_template 使用

### 重要说明

- 默认值是 `AnswerJudgePrompt`（类，非实例）→ 导致 `TypeError`
- **必须显式传 `prompt_template=None`** 使用内置回退
- 仅在 `use_semantic_judge=True` 时使用

### 推荐用法

```python
# 推荐：传 None
evaluator = UnifiedBenchDatasetEvaluator(
    eval_type="key2_qa",
    llm_serving=llm_serving,
    prompt_template=None,
    use_semantic_judge=True
)
```

### 自定义模板用法

```python
from dataflow.prompts.core_text import AnswerJudgePrompt

# 传入实例以自定义提示
custom_prompt = AnswerJudgePrompt()

evaluator = UnifiedBenchDatasetEvaluator(
    eval_type="key2_qa",
    llm_serving=llm_serving,
    prompt_template=custom_prompt,
    use_semantic_judge=True
)
```

### 传递给 `build_prompt(...)` 的字段

使用自定义 `AnswerJudgePrompt` 实例时，算子会传入：
- `answer`：预测答案
- `reference_answer`：标准答案

LLM 响应必须包含：
```json
{
  "judgement_result": true  // 或 false
}
```
