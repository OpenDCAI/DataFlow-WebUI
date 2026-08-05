# DataFlow-Harness Backend

FastAPI service that hosts the REST API, the MCP server, the operator registry
and pipeline validation/execution.

**Most people should not install from here.** Use the repo-root installer, which
also handles the DataFlow framework, the core data directory and skills:

```bash
./install.sh --profile harness    # backend + MCP, no frontend
./install.sh --profile webui      # the above plus the canvas
```

See [docs/profiles/harness.md](../docs/profiles/harness.md).

## Direct installation

Only if you are working on the backend itself and want nothing else touched.

```bash
uv pip install -r requirements.txt
```

If uv is unavailable, use `python -m pip install -r requirements.txt`. Keep
Python 3.10+ active in a venv or conda environment. The requirements pin
`setuptools<82` because DataFlow still imports `pkg_resources`, and `mcp<2`
because `fastapi-mcp==0.4.0` is not compatible with MCP 2's keyword-only
`Server` constructor.

`requirements.txt` includes `open-dataflow`. Python 3.10+ is required.
`open-dataflow==1.0.10` and `fastapi-mcp==0.4.0` are pinned because the backend
depends on their runtime CLI and MCP APIs. Do not replace them with an
unverified editable DataFlow checkout.

## Run

```bash
make dev

# equivalently:
uvicorn app.main:app --reload --port 8000 --reload-dir app --host=0.0.0.0
```

| | |
|---|---|
| API | `http://localhost:8000/api/v1/...` |
| Interactive docs | `http://localhost:8000/docs` |
| MCP (SSE) | `http://localhost:8000/mcp` |

Without a frontend build, startup logs a warning about a missing UI index and no
canvas is served. That is expected for the `harness` profile.

There is **no authentication**, and the default host `0.0.0.0` exposes the API to
your local network. Use `--host=127.0.0.1` to restrict it.

## Tests

```bash
uv pip install -r requirements-dev.txt
pytest -q
```

## Layout

```
app/
  main.py             app factory, CORS, static mount, startup cache refresh
  mcp_server.py       mounts /mcp; whitelists which operation_ids become tools
  api/v1/
    endpoints/        REST routes (operators, pipelines, tasks, datasets, ...)
    handlers.py       exception handlers; /mcp stays raw JSON-RPC, /api/v1 is enveloped
    envelope.py       ApiResponse shape
  core/
    config.py         runtime paths, registry locations, preset whitelist
    container.py      DI container; services are reached through it
  services/           registries, validation, compile check, ray execution
```

Two invariants worth knowing before changing things:

**MCP tools are an explicit whitelist.** `mcp_server.py` lists `operation_id`
values. Adding a route does not expose it as a tool; renaming one removes a tool
silently. `python3 installers/checks/check_mcp_whitelist.py` cross-checks them.

**`/mcp` must not be wrapped in `ApiResponse`.** MCP speaks JSON-RPC 2.0;
enveloping its errors makes strict clients (Cursor) reject them with a schema
error. `handlers.py` branches on the path via `_is_protocol_path`.

Repo-wide change policy lives in [`../CLAUDE.md`](../CLAUDE.md).
