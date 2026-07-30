# DataFlow-WebUI (Release)

本发布包的完整快速开始（中英双语）：**[docs/RELEASE-PACKAGE.md](docs/RELEASE-PACKAGE.md)**

简版 — 在本目录下执行：

```bash
cd backend && pip install -r requirements.txt && cd ..
./run.sh          # Windows: run.bat
```

然后浏览器打开 http://localhost:8000/

注意：服务不带任何认证，且执行 pipeline 等同于任意代码执行。默认只监听 `127.0.0.1`（仅本机）。
如需局域网访问，需显式指定 `DATAFLOW_HOST=0.0.0.0 ./run.sh`。
