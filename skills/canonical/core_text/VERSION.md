# Reference alignment

These operator references are static snapshots of DataFlow's API. They drift when
upstream changes, so the version they were written against is recorded here
rather than left implicit.

| | |
| --- | --- |
| Upstream | [OpenDCAI/DataFlow](https://github.com/OpenDCAI/DataFlow) |
| Aligned to | `main` at **v1.0.10** |
| Last synced | 2026-04-03 |

## What this means in practice

**With MCP** (the `webui` and `harness` profiles), `get_operator_detail_by_name`
is authoritative — it reports the operators actually installed. If it disagrees
with a file here, this reference is stale; trust MCP.

**Without MCP** (the `skills` profile) these files are the only operator
reference available. If your installed DataFlow is newer than v1.0.10, verify a
signature before relying on it:

```python
import inspect
from dataflow.operators.core_text import PromptedGenerator
print(inspect.signature(PromptedGenerator.__init__))
print(inspect.signature(PromptedGenerator.run))
```

## Updating after an upstream release

1. Diff the upstream operator modules against the affected `SKILL.md` files.
2. Update the signature, execution-logic and mandatory-rule sections.
3. Refresh that operator's `bad.md` example if a failure mode changed.
4. Update the table above.

There is no automated signature check against an installed registry yet. Adding
one — sampling operators through MCP or `inspect.signature` in CI — is the right
way to stop this file becoming a promise nobody verifies.
