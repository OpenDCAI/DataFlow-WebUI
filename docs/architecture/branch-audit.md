# Branch audit

Audited 2026-07-29 against `main` at `b64f2b9` (v1.0.0).

## Method

Ahead/behind counts alone are misleading here: most branches were merged by
squash or rebase, so they still show commits "ahead" of `main` whose changes are
already in it. This audit uses `git cherry origin/main origin/<branch>`, which
compares patch content and marks commits already upstream with `-`.

Reproduce:

```bash
git cherry -v origin/main origin/<branch>     # '-' = already in main, '+' = not
```

## Summary

Of 19 non-`main` remote branches: **16 can be archived and deleted**, and
**3 carry 2 groups of undecided work** — `fix/pipeline-compile-check-and-webui-ux`
(1 commit), plus `prompt_para_info` and `frontend`, which hold overlapping
prompt-parameter work and must be resolved together.

**`frontend` must not be deleted.** It looks archivable by commit count but
carries `c8da97f` (349 insertions across 8 frontend files) that is not in `main`.

## Branches with no unmerged work — safe to archive and delete

Seven are strict ancestors of `main` (ahead = 0):

| Branch | Behind `main` |
|---|---|
| `backend` | 118 |
| `dev` | 22 |
| `registry2container` | 191 |
| `rename_core_path` | 221 |
| `feature/val_disable` | 119 |
| `260226reload_op` | 16 |
| `yuanshu-dev` | 13 |

Ten more show commits "ahead" but `git cherry` reports every one already applied
in `main`:

| Branch | Unique commit | Verdict |
|---|---|---|
| `skills-agent` | `c6fbcfe` fix(api): keep /mcp responses as raw JSON-RPC | Already in `main` via `3b08491` (PR #84) |
| `260227bug` | `b67f299` remove redundant import | equivalent in `main` |
| `260228bug` | `d9a9c9b` revise df-extension logic | equivalent in `main` |
| `20260201` | `a1cbb60` README clarity | equivalent in `main` |
| `auto_release` | `c7725bd` auto release action | equivalent in `main` |
| `backend-task-download` | `0caa560` fix download url + task registry init | equivalent in `main` |
| `cors` | `86076e5` CORS support | equivalent in `main` |
| `error_handle` | `60cb979` response envelope | equivalent in `main` |
| `pipeline_init_check` | `e59891e` pipeline registry init check | equivalent in `main` |

That is 16 branches: 7 strict ancestors plus these 9. `frontend` is **not**
among them — see below.

### Correction to the earlier plan

The cleanup plan recorded `skills-agent` as holding one commit needing review and
cherry-pick (item P0-04). It does not. `main` obtained the same fix through
`3b08491`, and `git diff origin/main origin/skills-agent -- backend/app/api/v1/handlers.py`
is empty. Relative to `main`, `skills-agent` is a **net regression** of ~762 lines:
it lacks `LICENSE`, `backend/app/services/pipeline_compile_check.py`, the ray
executor improvements, and the pipeline auto-layout fix. Do not merge it. P0-04
is closed as "already applied".

## Branches with genuinely unmerged work

### `fix/pipeline-compile-check-and-webui-ux` — 1 commit

- Forked from `89c1c04` (2026-07-07); 5 behind, 1 ahead
- `29a4a06` "Harden pipeline render and compile check (code review fixes)"
- Touches `backend/app/services/pipeline_compile_check.py`,
  `frontend/src/hooks/dataflow/usePipelineOperation.js`,
  `frontend/src/views/manage/dataflow/index.vue` (19 insertions, 18 deletions)
- These are follow-up review fixes on top of PR #83, which was merged
- **Action:** review and cherry-pick as its own PR, or record why it was rejected

### `prompt_para_info` — 5 commits

- Forked from `1402dba` (2026-02-06); 22 behind, 6 ahead (5 unmerged)
- `977d4a7` add `param` + `description` to prompt_registry
- `7ba3094` param processing for prompt_template
- `09698d6` pipeline api update, empty string → None
- `5ab7151` input_keys processing
- `30e652d` move pipeline whitelist into core settings
- Touches `backend/app/api/v1/endpoints/`, `backend/app/core/`
- The only branch carrying a substantial unmerged **feature**. It has drifted
  5 months and overlaps the prompt-parameter work since released
- **Action:** needs an owner decision — rebase and finish, or close. Do not
  delete without one.

### `frontend` — 1 of 2 commits unmerged

- 23 behind, 4 ahead; `git cherry` marks one commit unmerged
- `c8da97f` "Update promptInfo and var_keyword" — **349 insertions, 21
  deletions across 8 files**: `axios/api.js`, `axios/model.js`, the operator
  node component, a new `valueInput/kvInput.vue`, `stores/dataflow.js`
- `b268bbb` "Update title and ico" is already equivalent in `main`
- This is substantial frontend work for prompt parameters and key-value inputs,
  overlapping `prompt_para_info`'s backend side of the same feature
- **Action:** resolve together with `prompt_para_info`. **Do not delete this
  branch** — counting only "commits ahead" makes it look disposable, and it is
  not.

## Recommended sequence

1. Tag before deleting anything, so nothing becomes unreachable:
   ```bash
   for b in backend dev registry2container rename_core_path feature/val_disable \
            260226reload_op yuanshu-dev skills-agent 260227bug 260228bug \
            20260201 auto_release backend-task-download cors error_handle \
            pipeline_init_check; do
     git tag "archive/$b/2026-07-29" "origin/$b"
   done
   git push origin --tags
   ```
2. Delete those 16 remote branches. The list above is exhaustive and
   deliberately excludes `frontend`, `prompt_para_info` and
   `fix/pipeline-compile-check-and-webui-ux`.
3. Open a PR for `29a4a06` from `fix/pipeline-compile-check-and-webui-ux`.
4. Assign one owner and a decision date to the prompt-parameter feature as a
   whole: `prompt_para_info` (backend, 5 commits) **and** `frontend`'s
   `c8da97f` (frontend, 349 insertions). They are two halves of one change and
   reviewing either alone will look incomplete. If no owner materializes,
   archive-tag both and delete — but that is a deliberate decision to drop a
   feature, not routine cleanup.
5. Protect `main`: require PRs, require the `checks` workflow, forbid direct
   pushes, protect release tags.

Deleting a branch that has an `archive/*` tag loses nothing — the commits stay
reachable through the tag.
