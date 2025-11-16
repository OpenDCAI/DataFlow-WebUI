# 算子管理 API 使用指南

本文档介绍从 DataFlow-Agent 迁移过来的算子管理功能的使用方法。

## 📋 功能概述

新增了以下算子管理 API：

1. **算子详细信息查询** - 获取算子的参数、描述等详细信息
2. **算子源码查看** - 查看算子的 Python 源码实现
3. **Prompt 模板源码** - 查看算子使用的 Prompt 模板
4. **AI 智能推荐（RAG）** - 基于自然语言描述推荐相关算子
5. **缓存管理** - 刷新算子信息缓存

---

## 🚀 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量

如果要使用 RAG 功能，需要配置 API Key：

```bash
export DF_API_KEY="your-openai-api-key"
```

### 3. 启动服务器

```bash
make dev
# 或者
uvicorn app.main:app --reload --port 8000 --reload-dir app --host=0.0.0.0
```

### 4. 访问 API 文档

打开浏览器访问：http://localhost:8000/docs

---

## 📚 API 接口详解

### 1. 获取算子列表（简化版）

**已有功能，保持不变**

```http
GET /api/v1/operators/
```

返回所有算子的基本信息（名称、类型、描述）。

**示例响应：**
```json
{
  "code": 200,
  "message": "OK",
  "data": [
    {
      "name": "text_cleaner",
      "type": {"level_1": "text", "level_2": "preprocess"},
      "description": "清洗文本数据",
      "allowed_prompts": ["BasicPrompt", "AdvancedPrompt"]
    }
  ]
}
```

---

### 2. 获取算子详细信息

**新增功能**

```http
GET /api/v1/operators/details?category=text2sql
```

**参数：**
- `category`（可选）：算子类别，如 `text2sql`, `rag` 等。为空则返回所有算子

**示例响应：**
```json
{
  "code": 200,
  "message": "OK",
  "data": [
    {
      "node": 1,
      "name": "nl_to_sql",
      "description": "将自然语言转换为SQL查询",
      "parameter": {
        "init": [
          {"name": "model", "default": "gpt-4", "kind": "POSITIONAL_OR_KEYWORD"}
        ],
        "run": [
          {"name": "text", "default": null, "kind": "POSITIONAL_OR_KEYWORD"}
        ]
      },
      "required": "",
      "depends_on": [],
      "mode": ""
    }
  ]
}
```

**按类别查询：**
```http
GET /api/v1/operators/details/text2sql
```

---

### 3. 获取算子源码

**新增功能**

```http
GET /api/v1/operators/source/{operator_name}
```

**示例：**
```http
GET /api/v1/operators/source/text_cleaner
```

**响应：**
```json
{
  "code": 200,
  "message": "OK",
  "data": {
    "operator_name": "text_cleaner",
    "source_code": "class TextCleaner(BaseOperator):\n    def run(self, text):\n        ..."
  }
}
```

---

### 4. 获取 Prompt 模板源码

**新增功能**

```http
GET /api/v1/operators/prompt-source/{operator_name}
```

**示例：**
```http
GET /api/v1/operators/prompt-source/text_cleaner
```

**响应：**
```json
{
  "code": 200,
  "message": "OK",
  "data": {
    "operator_name": "text_cleaner",
    "prompt_sources": {
      "BasicPrompt": "class BasicPrompt:\n    ...",
      "AdvancedPrompt": "class AdvancedPrompt:\n    ..."
    }
  }
}
```

---

### 5. AI 智能推荐算子（RAG）⭐

**新增功能 - 核心亮点**

```http
POST /api/v1/operators/recommend
```

**请求体：**
```json
{
  "query": "我想清洗文本数据，去除HTML标签",
  "category": null,
  "top_k": 5
}
```

**参数：**
- `query`：自然语言描述（支持单个字符串或字符串数组）
- `category`（可选）：限定算子类别
- `top_k`（可选）：返回前 k 个结果，默认 5

**单个查询示例响应：**
```json
{
  "code": 200,
  "message": "OK",
  "data": {
    "query": "我想清洗文本数据，去除HTML标签",
    "results": [
      "html_remover",
      "text_cleaner",
      "html_stripper",
      "clean_html",
      "remove_tags"
    ]
  }
}
```

**批量查询：**
```json
{
  "query": ["清洗数据", "生成SQL", "文本分类"],
  "top_k": 3
}
```

**批量查询响应：**
```json
{
  "code": 200,
  "message": "OK",
  "data": {
    "query": ["清洗数据", "生成SQL", "文本分类"],
    "results": [
      ["text_cleaner", "data_cleaner", "preprocess"],
      ["nl_to_sql", "text2sql", "sql_generator"],
      ["text_classifier", "classify", "categorizer"]
    ]
  }
}
```

**⚠️ 注意事项：**
- 需要配置环境变量 `DF_API_KEY`
- 第一次调用会比较慢（生成向量索引），后续会使用缓存
- 向量索引存储在 `backend/data/operator_resources/` 目录

---

### 6. 刷新算子缓存

**新增功能**

```http
POST /api/v1/operators/refresh-cache
```

重新扫描 `OPERATOR_REGISTRY` 并生成 `ops.json` 缓存文件。

**响应：**
```json
{
  "code": 200,
  "message": "OK",
  "data": {
    "message": "Cache refreshed successfully",
    "total_operators": 150
  }
}
```

---

## 🧪 测试示例

### 使用 curl 测试

```bash
# 1. 获取所有算子
curl http://localhost:8000/api/v1/operators/

# 2. 获取 text2sql 类别的详细信息
curl http://localhost:8000/api/v1/operators/details/text2sql

# 3. 获取算子源码
curl http://localhost:8000/api/v1/operators/source/text_cleaner

# 4. AI 推荐算子
curl -X POST http://localhost:8000/api/v1/operators/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "query": "我想将自然语言转换为SQL",
    "top_k": 5
  }'

# 5. 刷新缓存
curl -X POST http://localhost:8000/api/v1/operators/refresh-cache
```

### 使用 Python 测试

```python
import httpx

base_url = "http://localhost:8000/api/v1/operators"

# AI 推荐算子
response = httpx.post(
    f"{base_url}/recommend",
    json={
        "query": "我想清洗文本数据",
        "category": "text",
        "top_k": 5
    }
)
print(response.json())
```

---

## 📁 文件结构

```
backend/
├── app/
│   ├── api/v1/endpoints/
│   │   └── operators.py          # ✅ 新增/扩展的 API 接口
│   ├── schemas/
│   │   └── operator.py            # ✅ 扩展的数据模型
│   ├── services/
│   │   ├── operator_registry.py   # 已有的算子注册服务
│   │   └── operator_tools_service.py  # ✅ 新增的算子工具服务
│   └── core/
│       └── config.py              # ✅ 添加了 DATA_DIR 配置
├── data/
│   └── operator_resources/        # 算子缓存目录（自动创建）
│       ├── ops.json               # 算子信息缓存
│       ├── faiss_all.index        # FAISS 向量索引
│       └── faiss_all.index.meta   # 索引元数据
├── requirements.txt               # ✅ 添加了新依赖
└── OPERATOR_API_GUIDE.md          # ✅ 本文档
```

---

## 🔧 故障排除

### 1. RAG 功能报错：API Key 未配置

**错误：**
```
401 Unauthorized: 必须提供 OpenAI API-Key
```

**解决：**
```bash
export DF_API_KEY="your-api-key"
```

### 2. 找不到算子

**错误：**
```
404 Not Found: 未找到算子 'xxx'
```

**解决：**
- 检查算子名称是否正确
- 运行刷新缓存接口：`POST /api/v1/operators/refresh-cache`

### 3. FAISS 索引构建失败

**错误：**
```
Failed to build FAISS index
```

**解决：**
- 检查是否安装了 `faiss-cpu`
- 删除旧的索引文件：`rm -rf backend/data/operator_resources/faiss_*.index*`
- 重新调用 RAG 接口

---

## 🎯 前端集成示例

```javascript
// Vue 3 组合式 API
import { useGlobal } from "@/hooks/general/useGlobal";
const { $api } = useGlobal();

// 1. AI 推荐算子
async function recommendOperators(userInput) {
  const response = await $api.operators.recommend_operators({
    query: userInput,
    top_k: 5
  });
  return response.data.results;
}

// 2. 获取算子详情
async function getOperatorDetails(category) {
  const response = await $api.operators.get_operators_by_category(category);
  return response.data;
}

// 3. 查看源码
async function viewOperatorSource(operatorName) {
  const response = await $api.operators.get_operator_source(operatorName);
  console.log(response.data.source_code);
}
```

---

## 📊 性能说明

| 功能 | 首次调用 | 后续调用 | 说明 |
|------|---------|---------|------|
| 获取算子列表 | ~50ms | ~50ms | 读取缓存 |
| 获取详细信息 | ~100ms | ~100ms | 生成 ops.json |
| 获取源码 | ~10ms | ~10ms | 直接获取 |
| RAG 推荐 | ~5s | ~500ms | 首次需生成向量 |

---

## 🔮 未来扩展

- [ ] 支持更多 Embedding 模型
- [ ] 算子使用统计和推荐优化
- [ ] 算子版本管理
- [ ] 算子依赖关系可视化

---

## 📞 问题反馈

如有问题请在项目 Issue 中反馈。
