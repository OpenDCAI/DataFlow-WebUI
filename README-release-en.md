# DataFlow-WebUI (Release)

Quick start for this release package: **[docs/RELEASE-PACKAGE.md](docs/RELEASE-PACKAGE.md)**
(中文与 English 均在同一份文档中).

Python 3.10 is recommended and is the minimum supported version. Choose one
isolated environment before installing:

```bash
# venv
python3.10 -m venv .venv
source .venv/bin/activate       # Windows PowerShell: .venv\Scripts\Activate.ps1

# or conda
conda create -n dataflow python=3.10 -y
conda activate dataflow
```

The release archive already contains the built frontend, so Node.js/npm are not
needed to run it. Install [uv](https://docs.astral.sh/uv/getting-started/installation/)
using your system package manager (Homebrew on macOS, the official installer
on Linux, or PowerShell/winget on Windows), then run:

```bash
cd backend && uv pip install -r requirements.txt && cd ..
./run.sh          # Windows: run.bat
```

If uv is unavailable, use `python -m pip install -r requirements.txt` instead.
The requirements intentionally pin `setuptools<82` (DataFlow still imports
`pkg_resources`) and `mcp<2` (`fastapi-mcp==0.4.0` uses the MCP v1 Server API).

Then open http://localhost:8000/

Note: the server has no authentication, and running a pipeline is arbitrary code
execution. It binds `127.0.0.1` by default — this machine only. To expose it on
your network, opt in with `DATAFLOW_HOST=0.0.0.0 ./run.sh`.
