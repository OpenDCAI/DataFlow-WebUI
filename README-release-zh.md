# DataFlow-WebUI (Release)

本发布包的完整快速开始（中英双语）：**[docs/RELEASE-PACKAGE.md](docs/RELEASE-PACKAGE.md)**

Python 推荐 3.10，最低要求也是 3.10。请先选择一种隔离环境：

```bash
# venv
python3.10 -m venv .venv
source .venv/bin/activate       # Windows PowerShell：.venv\Scripts\Activate.ps1

# 或 conda
conda create -n dataflow python=3.10 -y
conda activate dataflow
```

发布包已经包含构建好的前端，运行发布包不需要 Node.js/npm。请先按系统
说明安装 [uv](https://docs.astral.sh/uv/getting-started/installation/)，然后执行：

```bash
cd backend && uv pip install -r requirements.txt && cd ..
./run.sh          # Windows: run.bat
```

如果无法使用 uv，可改用 `python -m pip install -r requirements.txt`。依赖
固定了 `setuptools<82`（DataFlow 仍使用 `pkg_resources`）和 `mcp<2`
（`fastapi-mcp==0.4.0` 使用 MCP v1 的 Server API）。

然后浏览器打开 http://localhost:8000/

注意：服务不带任何认证，且执行 pipeline 等同于任意代码执行。默认只监听 `127.0.0.1`（仅本机）。
如需局域网访问，需显式指定 `DATAFLOW_HOST=0.0.0.0 ./run.sh`。
