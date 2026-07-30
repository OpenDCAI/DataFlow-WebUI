# Component boundaries

## Layers

```
┌─────────────────────────────────────────────┐
│ frontend/          Vue 3 + Vite canvas      │  webui profile only
└───────────────┬─────────────────────────────┘
                │ HTTP /api/v1 only
┌───────────────▼─────────────────────────────┐
│ backend/                                    │  webui + harness
│   api/v1/     REST endpoints                │
│   mcp_server  /mcp, SSE, whitelisted tools  │
│   services/   registries, validation, exec  │
└───────────────┬─────────────────────────────┘
                │ imports
┌───────────────▼─────────────────────────────┐
│ open-dataflow  (external package)           │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ skills/canonical/   instructions for agents  │  all three profiles
└─────────────────────────────────────────────┘
```

Dependency direction is one-way: `frontend → backend → open-dataflow`. Skills
depend on nothing at build time; at run time the MCP-aware ones need the backend.

## Rules

**The frontend talks to the backend only over `/api/v1`.** It must not read
operator internals or reach into DataFlow directly. The canvas and an agent both
being able to mutate a pipeline is why a single server-side representation exists.

**MCP tools are a whitelist, not "every route".** `backend/app/mcp_server.py`
names the `operation_id`s it exposes. Adding a route does not expose it; renaming
one silently removes a tool from every agent, which is why
`installers/checks/check_mcp_whitelist.py` cross-checks the two at CI time.

**`/mcp` speaks JSON-RPC, `/api/v1` speaks the `ApiResponse` envelope.** The
exception handlers in `backend/app/api/v1/handlers.py` branch on the path
(`_is_protocol_path`). Wrapping a JSON-RPC error in the envelope makes strict
clients such as Cursor reject the response.

**Skills are generated, never hand-edited outside `skills/canonical/`.** See
[ADR-001](adr-001-source-of-truth.md).

**Profiles declare their own boundaries.** `installers/profiles/<id>.json` lists
`must_not_touch`, and the installer verifies it. `harness` must install with no
Node.js present; `skills` must install no packages at all.

## Configuration ownership

| Kind | Where | Notes |
|---|---|---|
| Install-time paths, ports, package managers | `installers/config.sh` | The one definition; docs and scripts reference it |
| Backend runtime paths | `backend/app/core/config.py` | Registry files, cache, `ops.json` |
| Project agent config | `.mcp.json`, `.cursor/`, `.codex/` | Written by `configure-agent`, default scope |
| User agent config | `~/.codex/config.toml`, `~/.cursor/mcp.json` | Only with `--scope user`, after a diff |
| Credentials | environment variables | Never written to disk by anything here |
| Runtime data | `backend/data/`, `backend/cache_local/` | Gitignored; never deleted by uninstall |

## Security posture

Single-user, local-first, **no authentication** — stated in `CLAUDE.md` and not
an oversight. Consequences worth being explicit about:

- the backend binds `0.0.0.0:8000` by default, exposing the API and MCP endpoint
  to the local network. `DATAFLOW_HOST=127.0.0.1` restricts it
- any process that can reach the port can create and execute pipelines
- pipeline execution runs Python via Ray, so it is arbitrary code execution by
  design
- do not deploy this as a shared service without putting authentication in front
  of it

## Static guards

| Check | Catches |
|---|---|
| `installers/checks/check_mcp_whitelist.py` | Whitelisted MCP tool with no matching route |
| `installers/checks/check_skills.py` | Broken skill links, bad frontmatter, name collisions, malformed directives |
| `installers/generate_agent_assets.py --check` | Generated agent files drifting from canonical |
| `installers/checks/check_profiles.py` | Profile manifest calling an undefined function; profile boundary claims contradicting steps |
| `installers/checks/check_shell.sh` | Shell syntax errors, ShellCheck warnings |

All run without DataFlow installed, so they are fast and always available. See
`.github/workflows/checks.yml`.
