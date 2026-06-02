# 数学强推理数据合成系统

## 概述

本系统包含三个 pipeline，用于合成不同复杂度的数学推理数据，特别适合训练需要强推理能力的AI模型。

## 已创建的 Pipeline

### 1. 数学强推理数据合成器 (高级)
- **ID**: `37d4977e-57cd-48ed-a143-495963002ed4`
- **功能**: 从基础数学问题生成需要多步骤逻辑推理的复杂问题
- **算子流程**:
  1. `data_complexity_enhancer` - 提升问题复杂度
  2. `reasoning_step_generator` - 生成推理步骤
  3. `multi_concept_integrator` - 整合多个数学概念
  4. `data_validator` - 验证数据质量
  5. `data_save` - 保存结果

### 2. 数学推理数据生成器 (中级)
- **ID**: `57251f75-4fda-48de-954b-fa73af0a22de`
- **功能**: 使用模板方法增强数学问题的推理要求
- **算子流程**:
  1. `data_template` - 应用生成模板
  2. `data_augment` - 数据增强
  3. `data_format` - 格式化输出
  4. `data_save` - 保存结果

### 3. 基础数学数据合成器 (初级)
- **ID**: `7cccb609-047f-4cfe-839e-e58a3f67fe77`
- **功能**: 使用LLM生成复杂推理问题

## 数据集

### 输入数据集
1. `math_problems.jsonl` - 基础数学问题集合
2. `comprehensive_math_dataset.jsonl` - 综合数学数据集，包含代数、几何等

### 输出数据集
1. `strong_reasoning_math_data.jsonl` - 强推理数学数据
2. `enhanced_math_reasoning.jsonl` - 增强推理数据
3. `synthetic_math_reasoning.jsonl` - 合成推理数据

## 数据特征

生成的强推理数据具有以下特征：

1. **多步骤推理**: 每个问题需要3-6个推理步骤
2. **概念整合**: 结合代数、几何、逻辑等多个数学概念
3. **逻辑矛盾检测**: 包含需要识别逻辑矛盾的问题
4. **验证要求**: 解决方案需要可验证性
5. **难度分级**: 从基础到高级的难度梯度

## 使用指南

### 运行 Pipeline

1. 确保数据集文件存在
2. 在编辑器中选择要运行的 pipeline
3. 点击"运行"按钮执行 pipeline
4. 查看生成的强推理数据文件

### 数据格式

每个数据条目包含：
- `original_problem`: 原始问题
- `enhanced_problem`: 增强后的复杂问题
- `reasoning_steps`: 推理步骤数组
- `final_answer`: 最终答案
- `difficulty`: 难度级别
- `category`: 数学概念分类
- `requires_logical_reasoning`: 是否需要逻辑推理
- `has_multiple_concepts`: 是否包含多个概念

## 应用场景

1. **AI模型训练**: 训练需要强推理能力的数学AI助手
2. **教育评估**: 评估学生的逻辑推理能力
3. **研究工具**: 数学推理能力的研究和测试
4. **数据增强**: 扩充数学训练数据集

## 扩展建议

1. 可以添加更多数学概念（如概率、统计等）
2. 增加不同难度级别的模板
3. 集成更多数据验证规则
4. 添加自动评分和反馈机制