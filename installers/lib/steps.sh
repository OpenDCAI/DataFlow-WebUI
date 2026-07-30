#!/usr/bin/env bash
# steps.sh — the df_* functions a profile manifest may name in `run:`,
# `skip_if:` and `verify:`. Sourced by install.sh after common.sh.
#
# Each function must be idempotent: re-running an install leaves the same state.
# Each must honour DF_DRY_RUN by printing what it would do and changing nothing.

# ---------- python ----------------------------------------------------------
df_pip_install() {
  if [[ "${DF_DRY_RUN:-0}" -eq 1 ]]; then
    plan "pip install $*"
    return 0
  fi
  local quiet="-q"
  [[ "${DF_VERBOSE:-0}" -eq 1 ]] && quiet=""
  # shellcheck disable=SC2086
  "$DF_PYTHON" -m pip install $quiet "$@"
}

df_init_dataflow_core() {
  local core_dir="$DF_REPO_ROOT/backend/data/dataflow_core"
  if [[ "${DF_DRY_RUN:-0}" -eq 1 ]]; then
    plan "mkdir -p $core_dir && (cd \"\$_\" && $DF_PYTHON -m dataflow init)"
    return 0
  fi
  mkdir -p "$core_dir"
  ( cd "$core_dir" && "$DF_PYTHON" -m dataflow init ) || {
    warn "dataflow init returned non-zero; the directory exists but may be incomplete"
    return 0
  }
}

df_dataflow_core_ready() {
  local core_dir="$DF_REPO_ROOT/backend/data/dataflow_core"
  [[ -d "$core_dir" ]] && [[ -n "$(ls -A "$core_dir" 2>/dev/null)" ]]
}

# ---------- frontend --------------------------------------------------------
df_build_frontend() {
  local fe="$DF_REPO_ROOT/frontend"
  if [[ ! -f "$fe/package.json" ]]; then
    err "frontend/package.json not found"
    return 1
  fi
  if [[ "${DF_DRY_RUN:-0}" -eq 1 ]]; then
    plan "cd frontend && $DF_NODE_PM install && $DF_NODE_PM run build"
    return 0
  fi
  # Package manager is pinned in installers/config.sh so the docs, the release
  # script and this installer cannot disagree (plan item P1-06).
  ( cd "$fe" && $DF_NODE_PM_INSTALL_CMD ) || return 1
  ( cd "$fe" && $DF_NODE_PM run build ) || return 1
}

# ---------- skills ----------------------------------------------------------
df_skill_ids_for_layers() {
  # df_skill_ids_for_layers <layer>... — ids from the manifest matching layers
  "$DF_PYTHON" -c '
import json, sys
manifest = json.load(open(sys.argv[1], encoding="utf-8"))
layers = set(sys.argv[2:])
for s in manifest["skills"]:
    if s["layer"] in layers:
        print(s["id"])
' "$DF_REPO_ROOT/installers/skills.manifest.json" "$@"
}

df_receipt_add() {
  # df_receipt_add <absolute-path> <label>
  #
  # Records an ABSOLUTE path plus the hash of what we just wrote. Absolute
  # because a receipt mixes two destinations — the skills directory (which moves
  # with --scope) and this repo (Cursor assets, AGENTS.md). Bare ids were
  # ambiguous: uninstall resolved them all against the skills directory, so
  # agent assets reported "already gone" and were orphaned when the receipt was
  # then deleted.
  printf '%s\t%s\t%s\n' "$1" "$(df_tree_hash "$1")" "$2" >> "$DF_RECEIPT.new"
}

df_receipt_lookup() {
  # df_receipt_lookup <absolute-path> — the hash recorded for it, if any.
  [[ -f "$DF_RECEIPT" ]] || return 0
  awk -F'\t' -v p="$1" '$1 == p { print $2; exit }' "$DF_RECEIPT"
}

df_managed_ids() {
  # Every skill id this repo ships. Anything else found in a skills directory
  # belongs to the user and is never touched.
  "$DF_PYTHON" -c '
import json, sys
m = json.load(open(sys.argv[1], encoding="utf-8"))
for s in m["skills"]:
    print(s["id"])
' "$DF_REPO_ROOT/installers/skills.manifest.json"
}

df_install_one_asset() {
  # df_install_one_asset <src> <dst> <label>
  #
  # Copy one managed file or directory, but never clobber something we cannot
  # prove we wrote. Provenance is the recorded hash from a previous install; if
  # the destination differs from both that hash and the incoming content, it has
  # been edited or hand-authored, so it is kept.
  local src="$1" dst="$2" label="$3"

  if [[ ! -e "$dst" ]]; then
    mkdir -p "$(dirname "$dst")"
    cp -R "$src" "$dst"
    df_receipt_add "$dst" "$label"
    ok "$label"
    return 0
  fi

  # Already identical: nothing to do, and not ours to record.
  if diff -rq "$src" "$dst" >/dev/null 2>&1; then
    skip "$label (already current)"
    return 0
  fi

  if [[ "${DF_FORCE:-0}" -eq 1 ]]; then
    rm -rf "$dst"
    mkdir -p "$(dirname "$dst")"
    cp -R "$src" "$dst"
    df_receipt_add "$dst" "$label"
    ok "$label (overwritten, --force)"
    return 0
  fi

  # Do we have a receipt proving we wrote the current contents? If so this is
  # our own stale output and refreshing it loses nothing.
  local recorded=""
  recorded=$(df_receipt_lookup "$dst")
  if [[ -n "$recorded" ]] && [[ "$recorded" == "$(df_tree_hash "$dst")" ]]; then
    rm -rf "$dst"
    mkdir -p "$(dirname "$dst")"
    cp -R "$src" "$dst"
    df_receipt_add "$dst" "$label"
    ok "$label (refreshed)"
    return 0
  fi

  # Two ways to land here, and the user needs to know which: we never wrote this
  # path, or we wrote it and it has since been edited. Either way we keep it —
  # the point is to never silently discard someone's work.
  if [[ -n "$recorded" ]]; then
    warn "$label has local changes since it was installed — leaving it alone"
  else
    warn "$label exists and was not created by this installer — leaving it alone"
  fi
  warn "  re-run with --force to replace it with the version this repo ships"
  DF_ASSETS_KEPT=$((${DF_ASSETS_KEPT:-0} + 1))
  return 0
}

df_install_agent_assets() {
  # Place the agent assets that only ever live in the repo: Cursor skill
  # packages and rules, and AGENTS.md for Codex. Unlike Claude skills these have
  # no user-level location, so --scope does not apply to them.
  #
  # Everything is installed entry by entry. An earlier version replaced
  # .cursor/skills/ wholesale, which deleted skills the user had written
  # themselves; a directory is never removed as a unit here.
  local staged="$DF_STAGING"

  if [[ "${DF_DRY_RUN:-0}" -eq 1 ]]; then
    plan "install into $DF_REPO_ROOT:"
    while IFS= read -r id; do
      [[ -n "$id" ]] && plan "    .cursor/skills/$id/ and .codex/skills/$id/"
    done < <(df_managed_ids)
    plan "    .cursor/rules/<skill>.mdc (generated rules only)"
    plan "    AGENTS.md"
    plan "  existing files not created by this installer are kept"
    return 0
  fi

  if [[ ! -d "$staged/.cursor/skills" ]]; then
    err "staged .cursor/skills missing — generator did not run for cursor"
    return 1
  fi
  if [[ ! -d "$staged/.codex/skills" ]]; then
    err "staged .codex/skills missing — generator did not run for codex"
    return 1
  fi

  # Cursor and Codex each read their own copy: same canonical source, rendered
  # with different agent contexts.
  for agent_dir in .cursor/skills .codex/skills; do
    [[ -d "$staged/$agent_dir" ]] || continue
    mkdir -p "$DF_REPO_ROOT/$agent_dir"
    while IFS= read -r id; do
      [[ -n "$id" ]] || continue
      [[ -d "$staged/$agent_dir/$id" ]] || continue
      df_install_one_asset "$staged/$agent_dir/$id" \
                           "$DF_REPO_ROOT/$agent_dir/$id" \
                           "$agent_dir/$id"
    done < <(df_managed_ids)
  done

  if [[ -d "$staged/.cursor/rules" ]]; then
    mkdir -p "$DF_REPO_ROOT/.cursor/rules"
    # Only rules we generate; hand-written rules in the repo are never touched,
    # and a generated name the user has taken over is kept.
    for f in "$staged/.cursor/rules"/*.mdc; do
      [[ -f "$f" ]] || continue
      local base
      base=$(basename "$f")
      df_install_one_asset "$f" "$DF_REPO_ROOT/.cursor/rules/$base" ".cursor/rules/$base"
    done

    # Remove rules retired by the reorganization. They may still be present in
    # a clone that predates their removal, where they would sit alongside the
    # new per-skill rules as a second, stale copy of the same guidance.
    while IFS= read -r stale; do
      [[ -n "$stale" ]] || continue
      if [[ -f "$DF_REPO_ROOT/.cursor/rules/$stale" ]]; then
        rm -f "$DF_REPO_ROOT/.cursor/rules/$stale"
        ok "removed retired rule .cursor/rules/$stale"
      fi
    done < <("$DF_PYTHON" -c '
import json, sys
m = json.load(open(sys.argv[1], encoding="utf-8"))
for name in m.get("retired_cursor_rules", []):
    print(name)
' "$DF_REPO_ROOT/installers/skills.manifest.json")
  fi

  if [[ -f "$staged/AGENTS.md" ]]; then
    # AGENTS.md is a plausible thing for a user to have written themselves, so
    # it gets the same provenance check as everything else.
    df_install_one_asset "$staged/AGENTS.md" "$DF_REPO_ROOT/AGENTS.md" "AGENTS.md"
  else
    err "staged AGENTS.md missing — generator did not run for codex"
    return 1
  fi
}

df_verify_agent_assets() {
  if [[ "${DF_DRY_RUN:-0}" -eq 1 ]]; then
    plan "verify: AGENTS.md plus every managed skill under .cursor/ and .codex/"
    return 0
  fi
  local missing=0

  if [[ ! -f "$DF_REPO_ROOT/AGENTS.md" ]]; then
    err "AGENTS.md missing (Codex has no instructions)"
    missing=1
  fi

  # Check each managed skill, not just that the directory exists. An empty or
  # partially-copied directory satisfies a directory test while leaving the
  # Codex routing table pointing at files that are not there.
  local agent_dir id
  for agent_dir in .cursor/skills .codex/skills; do
    if [[ ! -d "$DF_REPO_ROOT/$agent_dir" ]]; then
      err "$agent_dir/ missing"
      missing=1
      continue
    fi
    while IFS= read -r id; do
      [[ -n "$id" ]] || continue
      if [[ ! -r "$DF_REPO_ROOT/$agent_dir/$id/SKILL.md" ]]; then
        err "$agent_dir/$id/SKILL.md missing or unreadable"
        missing=1
      fi
    done < <(df_managed_ids)
  done

  # Every routed skill needs its Cursor rule.
  while IFS= read -r id; do
    [[ -n "$id" ]] || continue
    [[ "$id" == "core_text" ]] && continue   # reference package: no rule
    if [[ ! -r "$DF_REPO_ROOT/.cursor/rules/$id.mdc" ]]; then
      err ".cursor/rules/$id.mdc missing or unreadable"
      missing=1
    fi
  done < <(df_managed_ids)

  # AGENTS.md must point at paths that exist, or its routing is a dead end.
  local referenced
  while IFS= read -r referenced; do
    [[ -n "$referenced" ]] || continue
    if [[ ! -e "$DF_REPO_ROOT/$referenced" ]]; then
      err "AGENTS.md routes to '$referenced', which does not exist"
      missing=1
    fi
  done < <(grep -oE '\.codex/skills/[A-Za-z0-9_-]+/SKILL\.md' "$DF_REPO_ROOT/AGENTS.md" 2>/dev/null | sort -u)

  [[ "$missing" -eq 0 ]] || return 1
}

df_install_skills() {
  # df_install_skills <layer>... — copy staged skills into $DF_SKILLS_TARGET
  local ids
  ids=$(df_skill_ids_for_layers "$@") || return 1
  [[ -n "$ids" ]] || { warn "no skills matched layers: $*"; return 0; }

  local staged_root="$DF_STAGING/.claude/skills"
  if [[ "${DF_DRY_RUN:-0}" -eq 1 ]]; then
    plan "install into $DF_SKILLS_TARGET:"
    while IFS= read -r id; do
      plan "    $id/"
    done <<< "$ids"
    return 0
  fi

  mkdir -p "$DF_SKILLS_TARGET"
  local installed=0
  while IFS= read -r id; do
    local src="$staged_root/$id" dst="$DF_SKILLS_TARGET/$id"
    if [[ ! -d "$src" ]]; then
      err "staged skill missing: $id (generator did not produce it)"
      return 1
    fi
    if [[ -e "$dst" ]] && [[ "${DF_FORCE:-0}" -eq 0 ]]; then
      if diff -rq "$src" "$dst" >/dev/null 2>&1; then
        # Identical, but we did NOT create it. Do not record it: --uninstall
        # must never delete a directory this run did not install, even when the
        # contents happen to match what we ship. A previous install of the same
        # profile left its own receipt entry, which still stands.
        skip "$id (already present and identical — left as is, not recorded)"
        continue
      fi
      # Content differs. Refresh it only if a receipt proves we wrote what is
      # currently there — being inside the repo is not proof of ownership, since
      # a user may keep their own skills in a project-scoped directory too.
      local recorded=""
      recorded=$(df_receipt_lookup "$dst")
      if [[ -n "$recorded" ]] && [[ "$recorded" == "$(df_tree_hash "$dst")" ]]; then
        debug "$id: refreshing our own previous output"
      else
        if [[ -n "$recorded" ]]; then
          warn "$id has local changes since it was installed — leaving it alone"
        else
          warn "$id exists at $dst and was not created by this installer — leaving it alone"
        fi
        warn "  re-run with --force to replace it with the version this repo ships"
        continue
      fi
    fi
    rm -rf "$dst"
    cp -R "$src" "$dst"
    # Record provenance: the id plus a fingerprint of exactly what we wrote.
    # --uninstall re-computes it and refuses to delete anything that changed,
    # so local edits after install are never silently discarded.
    df_receipt_add "$dst" "$id"
    ok "$id → $dst"
    installed=$((installed + 1))
  done <<< "$ids"
  debug "installed $installed skill(s)"
}

# ---------- verification ----------------------------------------------------
df_verify_backend_import() {
  if [[ "${DF_DRY_RUN:-0}" -eq 1 ]]; then
    plan "verify: import app.main"
    return 0
  fi
  ( cd "$DF_REPO_ROOT/backend" && "$DF_PYTHON" -c 'import app.main' 2>&1 | tail -5 )
  local rc=${PIPESTATUS[0]}
  if [[ $rc -ne 0 ]]; then
    err "backend failed to import — dependencies may be incomplete"
    return 1
  fi
}

df_verify_frontend_dist() {
  if [[ "${DF_DRY_RUN:-0}" -eq 1 ]]; then
    plan "verify: frontend/dist/index.html exists"
    return 0
  fi
  [[ -f "$DF_REPO_ROOT/frontend/dist/index.html" ]] || {
    err "frontend/dist/index.html missing — the canvas will not load"
    return 1
  }
}

df_verify_mcp_whitelist() {
  if [[ "${DF_DRY_RUN:-0}" -eq 1 ]]; then
    plan "verify: MCP tool whitelist is non-empty"
    return 0
  fi
  "$DF_PYTHON" "$DF_REPO_ROOT/installers/checks/check_mcp_whitelist.py"
}

df_verify_skills() {
  if [[ "${DF_DRY_RUN:-0}" -eq 1 ]]; then
    plan "verify: each installed skill has a readable SKILL.md"
    return 0
  fi
  # One rule for every skill: a readable top-level SKILL.md. Reference packages
  # such as core_text satisfy it with a SKILL.md describing what they document,
  # so there is no directory-name special case here — a name-based exemption
  # hides exactly the "installed but has no entry point" breakage we want caught.
  local missing=0 count=0
  for dir in "$DF_SKILLS_TARGET"/*/; do
    [[ -d "$dir" ]] || continue
    local name
    name=$(basename "$dir")
    if [[ ! -r "$dir/SKILL.md" ]]; then
      err "$name: SKILL.md missing or unreadable at $dir"
      missing=$((missing + 1))
    else
      count=$((count + 1))
    fi
  done
  [[ "$missing" -eq 0 ]] || return 1
  ok "$count skill(s) verified in $DF_SKILLS_TARGET"
}
