# DataFlow-WebUI (Release)

Quick start for this release package: **[docs/RELEASE-PACKAGE.md](docs/RELEASE-PACKAGE.md)**
(中文与 English 均在同一份文档中).

Short version — from this directory:

```bash
cd backend && pip install -r requirements.txt && cd ..
./run.sh          # Windows: run.bat
```

Then open http://localhost:8000/

Note: the server has no authentication, and running a pipeline is arbitrary code
execution. It binds `127.0.0.1` by default — this machine only. To expose it on
your network, opt in with `DATAFLOW_HOST=0.0.0.0 ./run.sh`.
