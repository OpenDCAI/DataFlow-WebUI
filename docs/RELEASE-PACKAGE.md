# Running a release package

For users who downloaded a `DataFlow-WebUI-<version>.zip` from the releases page
rather than cloning the repository. The frontend is already built, so there is no
Node.js step.

Cloning the repository instead? The release package has no `install.sh` — see
the project README at
<https://github.com/OpenDCAI/DataFlow-WebUI#readme> for the three install
profiles. (An absolute URL on purpose: this file also ships inside the release
zip, where no sibling repository files exist.)

## 中文

### 1. 准备 Python 环境

推荐 Python **3.10**（最低也是 3.10），确保命令行可以直接使用 `python`。

任选一种：

```bash
# 方式 A：venv
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 方式 B：conda
conda create -n dataflow python=3.10
conda activate dataflow
```

### 2. 安装后端依赖

```bash
cd backend
uv pip install -r requirements.txt
cd ..
```

若尚未安装 uv，可参阅项目 README 的各系统安装说明，或使用
`python -m pip install -r requirements.txt` 作为备用方案。依赖已固定
`setuptools<82`（避免 `pkg_resources` 缺失）和 `mcp<2`（避免
`fastapi-mcp==0.4.0` 的 `Server.__init__` 参数不兼容）。

### 3. 启动服务

在**解压后的根目录**运行：

```bash
./run.sh        # Windows: run.bat
```

浏览器打开 http://localhost:8000/

### 4. 连接 Agent（可选）

发布包不含 `install.sh`。如需让 Claude Code / Codex / Cursor 通过 MCP 连接，
在包根目录手动创建 `.mcp.json`：

```json
{
  "mcpServers": {
    "dataflow": { "type": "sse", "url": "http://localhost:8000/mcp" }
  }
}
```

Codex 则在 `~/.codex/config.toml` 追加：

```toml
[mcp_servers.dataflow]
url = "http://localhost:8000/mcp"
enabled = true
tool_timeout_sec = 120
```

## English

### 1. Prepare Python

Python **3.10** recommended and required; make sure `python` is on your `PATH`.

```bash
# Option A: venv
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Option B: conda
conda create -n dataflow python=3.10
conda activate dataflow
```

### 2. Install backend dependencies

```bash
cd backend
uv pip install -r requirements.txt
cd ..
```

If uv is unavailable, use `python -m pip install -r requirements.txt` instead.
The requirements pin `setuptools<82` and `mcp<2` for compatibility with the
bundled DataFlow and `fastapi-mcp==0.4.0` versions.

### 3. Run

From the **release root directory**:

```bash
./run.sh        # Windows: run.bat
```

Open http://localhost:8000/

### 4. Connect an agent (optional)

The release package ships no `install.sh`. Create `.mcp.json` in the package root
by hand:

```json
{
  "mcpServers": {
    "dataflow": { "type": "sse", "url": "http://localhost:8000/mcp" }
  }
}
```

For Codex, append to `~/.codex/config.toml`:

```toml
[mcp_servers.dataflow]
url = "http://localhost:8000/mcp"
enabled = true
tool_timeout_sec = 120
```

## Notes

There is **no authentication**, and running a pipeline executes Python through
Ray — arbitrary code execution by design.

`run.sh` / `run.bat` therefore bind **`127.0.0.1` by default**: reachable from
this machine only. To expose it to your network, opt in explicitly:

```bash
DATAFLOW_HOST=0.0.0.0 ./run.sh          # Windows: set DATAFLOW_HOST=0.0.0.0
DATAFLOW_PORT=9000 ./run.sh             # a different port
```

The scripts print a warning when you bind anything other than localhost. Do not
do it on an untrusted network — anyone who can reach the port can run code.
