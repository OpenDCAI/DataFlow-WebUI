# DataFlow WebUI — Project Rules

## WebUI Change Policy (MANDATORY)

All modifications to `backend/app/` and `frontend/src/` MUST comply with this policy.

### Allowed Changes ONLY

1. **Operator Rendering Support (Frontend)** — Add or fix rendering for DataFlow operators not yet properly displayed in the WebUI pipeline canvas.
   - New/fixed node components in `components/manage/mainFlow/nodes/`
   - Fix parameter rendering in operator config panels
   - Add missing operator-specific UI elements (param editors, display widgets)
   - Fix display bugs for operators that exist in DataFlow but show incorrectly

   Verification: operator exists in `OPERATOR_REGISTRY` (`GET /api/v1/operators/`) but WebUI renders it incorrectly.

2. **Operator API Support (Backend)** — Add or fix API endpoints that serve existing DataFlow operator/pipeline/serving/dataset data.
   - Missing CRUD endpoint for an existing resource type
   - Fix serialization of operator parameters
   - Fix edge cases in existing endpoints (null handling, pagination)
   - Add query params or filters to existing list endpoints

### Prohibited Changes

- **NO** new analytical pages or dashboards (e.g., taxonomy analytics, custom reports)
- **NO** new backend endpoints for derived/computed data (e.g., `/api/v1/taxonomy/analytics`, `/api/v1/custom-stats`)
- **NO** new sidebar navigation items (`navList` in `manage/index.vue`)
- **NO** new routes in `router/Manage/index.js`
- **NO** new `views/manage/*/index.vue` pages
- **NO** new services/registries in `core/container.py`
- **NO** new config paths in `core/config.py`
- **NO** feature-level functionality not tied to making existing operators render in the UI

### Decision Rule

Before any frontend/backend change, check:
1. Does it make an existing DataFlow operator render correctly in the WebUI? → Allowed
2. Does it fix a bug in an existing API endpoint? → Allowed
3. Does it add missing CRUD for an existing resource type? → Allowed
4. Anything else → **PROHIBITED** — ask user to explicitly override

If the user requests a prohibited change, explain the policy and ask for explicit override confirmation.
