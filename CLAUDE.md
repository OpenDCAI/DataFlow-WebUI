# DataFlow WebUI — Project Rules

> **Deployment assumption**: this project is a **single-user, local-first** tool.
> Each developer/user runs both backend and frontend on their own machine.
> There is **no authentication, no registration, no multi-tenant concern**.
> Do NOT add login pages, JWT/session infrastructure, or per-user ACL.

## WebUI Change Policy

The previous strict allow-list (only operator-rendering fixes / existing-endpoint
patches) has been **relaxed**. New routes, new sidebar items, new backend
endpoints, and new services are all permitted when they serve the goal of
"completing DataFlow-WebUI as a usable local tool".

### Encouraged work areas

1. **Agent chat experience** — tool-call progress indicators, session
   persistence, multi-session switching, reconnect logic, robust error surfacing.
2. **Prompt management** — both read-only browsing of the built-in
   `PROMPT_REGISTRY` AND first-class support for user-defined prompt templates
   (file-based persistence under `backend/data/prompts/`, CRUD endpoints,
   editor UI, reference from operator config).
3. **JSON Schema management** — container-based service injection, schema
   validation (ajv), monaco/codemirror editor, deep integration with operator
   parameter panels so saved schemas can be chosen for structured LLM outputs.
4. **Operator rendering** — still a priority: new/fixed node components in
   `components/manage/mainFlow/nodes/`, parameter editors, correct display of
   operators that already exist in `OPERATOR_REGISTRY`.
5. **Repo hygiene** — consolidating/deleting duplicate markdown, removing
   stray `* copy` skill directories, fixing obvious code smells (same-name
   route handlers, hard-coded URLs, services bypassing the DI container).

### Still prohibited

- **Authentication / registration / multi-user features.** Single-user local
  tool only.
- **External telemetry / analytics uploads.** No outbound reporting.
- **Breaking changes to `OPERATOR_REGISTRY` / `PROMPT_REGISTRY` semantics** —
  always extend, never redefine, so upstream DataFlow stays compatible.

### Decision rule

Before a change, ask:

1. Does it make DataFlow-WebUI more useful as a single-user local tool? → OK
2. Does it introduce a login page, account system, or remote telemetry? → **NO**
3. Does it silently mutate DataFlow core-registry semantics? → **NO**
4. Everything else → proceed, and keep changes minimal + consistent with
   existing patterns (`core/container.py`, `api/v1/envelope.py`, etc.).
