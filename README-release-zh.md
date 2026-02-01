# DataFlow-WebUI (Release)

## 中文 · 快速开始

### 1. 准备 Python 环境
- 推荐 Python **3.10 / 3.11**
- 确保命令行可以直接使用 `python`

你可以任选一种方式：

**方式 A：venv**
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

**方式 B：conda**

```bash
conda create -n dataflow python=3.10
conda activate dataflow
```

### 2. 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
cd ..
```

### 3. 启动服务

在 **解压后的根目录** 直接运行：

```bash
./run.sh
```

Windows：

```bat
run.bat
```

然后在浏览器打开：

```
http://localhost:8000/
```
