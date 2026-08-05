#!/usr/bin/env bash
# install.sh — single entry point for every DataFlow-Harness install profile.
#
#   ./install.sh --profile webui          full stack: canvas + backend + MCP
#   ./install.sh --profile harness        backend + MCP, no Node, no frontend
#   ./install.sh --profile skills         standalone agent skills only
#
#   ./install.sh --profile harness --dry-run    show the plan, change nothing
#   ./install.sh --profile webui --check        check prerequisites only
#   ./install.sh --uninstall                    remove what an install created
#   ./install.sh configure-agent --agent claude configure an agent's MCP client
#
# What each profile does and does not install is declared in
# installers/profiles/<id>.json — this script only reads and executes them, so
# there is one flow rather than three copy-pasted ones.

set -euo pipefail

DF_REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DF_REPO_ROOT"

# shellcheck source=installers/config.sh
source "$DF_REPO_ROOT/installers/config.sh"
# shellcheck source=installers/lib/common.sh
source "$DF_REPO_ROOT/installers/lib/common.sh"
# shellcheck source=installers/lib/steps.sh
source "$DF_REPO_ROOT/installers/lib/steps.sh"

usage() {
  cat <<'EOF'
DataFlow-Harness installer

Usage:
  ./install.sh --profile <webui|harness|skills> [options]
  ./install.sh configure-agent --agent <claude|codex|cursor> [--scope project|user]
  ./install.sh --list
  ./install.sh --uninstall

Profiles:
  webui      Visual DAG canvas + backend + MCP + skills. Needs Python and Node.
  harness    Backend + MCP + skills. Needs Python only — never touches Node.
  skills     Standalone agent skills only. Installs no packages and no services.

Options:
  --profile <id>     Which layer to install (required unless --list/--uninstall)
  --check            Verify prerequisites and print the plan; install nothing
  --dry-run          Print every step that would run; change nothing
  --scope <s>        Skills destination:
                       project (default) → ./.claude/skills, inside this repo
                       user              → ~/.claude/skills, every project
  --force            Overwrite skills that already exist
  --uv               Install Python packages with uv (default)
  --pip              Install Python packages with pip instead
  --verbose          Show command output
  --uninstall        Remove only what a previous install recorded
  --list             Show the three profiles side by side
  -h, --help         This message

Installing never writes agent MCP configuration — that is a separate, explicit
command (./install.sh configure-agent --help). Installing writes inside this
repo only, unless you pass --scope user, which installs skills into
~/.claude/skills.
EOF
}

# ---------- argument parsing ------------------------------------------------
DF_PROFILE=""
DF_CHECK_ONLY=0
DF_DRY_RUN=0
DF_FORCE=0
DF_VERBOSE=0
# Project scope by default: installing should not write outside the repo unless
# the user asks for it. --scope user installs into ~/.claude/skills, which makes
# the skills available in every project but does modify their home directory.
DF_SCOPE="project"
DF_DO_UNINSTALL=0
DF_DO_LIST=0

if [[ "${1:-}" == "configure-agent" ]]; then
  shift
  exec "$DF_REPO_ROOT/installers/configure_agent.sh" "$@"
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile)    DF_PROFILE="${2:-}"; shift 2 ;;
    --profile=*)  DF_PROFILE="${1#*=}"; shift ;;
    --check|--check-only) DF_CHECK_ONLY=1; shift ;;
    --dry-run)    DF_DRY_RUN=1; shift ;;
    --force|-f)   DF_FORCE=1; shift ;;
    --uv)         DF_PYTHON_INSTALLER="uv"; shift ;;
    --pip)        DF_PYTHON_INSTALLER="pip"; shift ;;
    --verbose|-v) DF_VERBOSE=1; shift ;;
    --scope)      DF_SCOPE="${2:-}"; shift 2 ;;
    --scope=*)    DF_SCOPE="${1#*=}"; shift ;;
    --uninstall)  DF_DO_UNINSTALL=1; shift ;;
    --list)       DF_DO_LIST=1; shift ;;
    -h|--help)    usage; exit 0 ;;
    *) err "unknown option: $1"; echo; usage >&2; exit 2 ;;
  esac
done

case "$DF_PYTHON_INSTALLER" in
  uv|pip) ;;
  *) err "invalid Python installer: $DF_PYTHON_INSTALLER (use 'uv' or 'pip')"; exit 2 ;;
esac

export DF_REPO_ROOT DF_DRY_RUN DF_FORCE DF_VERBOSE DF_PYTHON DF_PYTHON_INSTALLER

PROFILE_DIR="$DF_REPO_ROOT/installers/profiles"

df_receipt_for_target() {
  # One receipt per skills destination, so uninstalling a project-scope install
  # cannot remove skills a user-scope install put in $HOME.
  local target="$1" slug
  slug=$(printf '%s' "$target" | df_stdin_hash | cut -c1-12)
  printf '%s/%s/receipt-%s' "$DF_REPO_ROOT" "$DF_RECEIPT_DIR" "$slug"
}

# ---------- --list ----------------------------------------------------------
if [[ "$DF_DO_LIST" -eq 1 ]]; then
  header "Available profiles"
  for f in "$PROFILE_DIR"/*.json; do
    id=$(df_json "$f" 'd["id"]')
    label=$(df_json "$f" 'd["label"]')
    desc=$(df_json "$f" 'd["description"]')
    printf '\n%s%s%s — %s\n' "$C_BOLD" "$id" "$C_RESET" "$label"
    printf '  %s\n' "$desc"
    printf '  %sInstalls:%s\n' "$C_GREEN" "$C_RESET"
    df_json "$f" 'd["installs"]' | while IFS= read -r line; do printf '    + %s\n' "$line"; done
    printf '  %sDoes NOT install:%s\n' "$C_YELLOW" "$C_RESET"
    df_json "$f" 'd["does_not_install"]' | while IFS= read -r line; do printf '    - %s\n' "$line"; done
  done
  printf '\nInstall one with: ./install.sh --profile <id>\n'
  exit 0
fi

# ---------- --uninstall -----------------------------------------------------
if [[ "$DF_DO_UNINSTALL" -eq 1 ]]; then
  header "Uninstall"

  shopt -s nullglob
  receipts=("$DF_REPO_ROOT/$DF_RECEIPT_DIR"/receipt-*)
  # Honour a receipt written by an older version of this installer.
  [[ -f "$DF_REPO_ROOT/$DF_RECEIPT_REL" ]] && receipts+=("$DF_REPO_ROOT/$DF_RECEIPT_REL")
  shopt -u nullglob

  if [[ ${#receipts[@]} -eq 0 ]]; then
    info "No install receipt found — nothing recorded to remove."
    info "Nothing was deleted. Skills you installed by hand are left alone."
    exit 0
  fi

  total_removed=0
  total_kept=0
  for receipt in "${receipts[@]}"; do
    header_line=$(head -1 "$receipt")
    info "Receipt $(basename "$receipt") → skills installed into: $header_line"
    receipt_kept=0

    # Line 1 is the skills destination. Each further line is
    # "<absolute-path>\t<hash-at-install>\t<label>". Paths are absolute because a
    # single receipt spans two destinations: the skills directory (which moves
    # with --scope) and this repo, for Cursor assets and AGENTS.md.
    while IFS=$'\t' read -r entry recorded_hash label; do
      [[ -n "$entry" ]] || continue
      [[ "$entry" == "$header_line" ]] && continue

      if [[ "$entry" == /* ]]; then
        dst="$entry"
        name="${label:-$entry}"
      else
        # Legacy receipt: bare ids, resolved against the skills destination.
        dst="$header_line/$entry"
        name="$entry"
      fi

      if [[ ! -e "$dst" ]]; then
        skip "$name (already gone)"
        continue
      fi

      # Refuse to delete anything that changed since we wrote it. Without this,
      # an uninstall silently discards local edits — or worse, removes something
      # the user has since taken over.
      if [[ -z "$recorded_hash" ]]; then
        warn "$name was recorded by an older installer with no checksum — NOT removing"
        warn "  delete it yourself if you are sure: rm -rf '$dst'"
        total_kept=$((total_kept + 1)); receipt_kept=$((receipt_kept + 1))
        continue
      fi
      if [[ "$(df_tree_hash "$dst")" != "$recorded_hash" ]]; then
        warn "$name has changed since it was installed — NOT removing $dst"
        warn "  delete it yourself if you are sure: rm -rf '$dst'"
        total_kept=$((total_kept + 1)); receipt_kept=$((receipt_kept + 1))
        continue
      fi

      if [[ "$DF_DRY_RUN" -eq 1 ]]; then
        plan "rm -rf $dst"
      else
        rm -rf "$dst"
        ok "removed $dst"
      fi
      total_removed=$((total_removed + 1))
    done < "$receipt"

    # Only drop the receipt once everything it records is gone; otherwise the
    # entries we kept would become unremovable orphans.
    if [[ "$DF_DRY_RUN" -eq 0 ]] && [[ "$receipt_kept" -eq 0 ]]; then
      rm -f "$receipt"
      ok "removed $(basename "$receipt")"
    elif [[ "$receipt_kept" -gt 0 ]]; then
      info "keeping $(basename "$receipt") — it still records $receipt_kept item(s) that were not removed"
    fi
  done

  # Prune now-empty directories we created, but never a directory that still
  # holds someone else's files.
  if [[ "$DF_DRY_RUN" -eq 0 ]]; then
    rmdir "$DF_REPO_ROOT/.cursor/skills" 2>/dev/null && ok "removed empty .cursor/skills/"
    rmdir "$DF_REPO_ROOT/.codex/skills" 2>/dev/null && ok "removed empty .codex/skills/"
    rmdir "$DF_REPO_ROOT/.codex" 2>/dev/null
    rmdir "$DF_REPO_ROOT/.claude/skills" 2>/dev/null
  fi

  # Tidy the receipt dir if it is now empty.
  [[ "$DF_DRY_RUN" -eq 0 ]] && rmdir "$DF_REPO_ROOT/$DF_RECEIPT_DIR" 2>/dev/null

  info "Removed $total_removed skill(s); kept $total_kept."
  info "Python/Node packages are left installed — remove those with pip/npm yourself."
  exit 0
fi

# ---------- profile resolution ----------------------------------------------
if [[ -z "$DF_PROFILE" ]]; then
  err "no profile given. Pick one:"
  err "  --profile webui     full canvas + backend + MCP"
  err "  --profile harness   backend + MCP only (no Node)"
  err "  --profile skills    standalone skills only (no packages)"
  err ""
  err "Not sure? Run ./install.sh --list"
  exit 2
fi

MANIFEST="$PROFILE_DIR/$DF_PROFILE.json"
if [[ ! -f "$MANIFEST" ]]; then
  err "unknown profile: $DF_PROFILE"
  err "available: $(cd "$PROFILE_DIR" && ls *.json | sed 's/\.json//' | tr '\n' ' ')"
  exit 2
fi

case "$DF_SCOPE" in
  user)    DF_SKILLS_TARGET="$DF_SKILLS_USER_DIR" ;;
  project) DF_SKILLS_TARGET="$DF_REPO_ROOT/$DF_SKILLS_PROJECT_DIR" ;;
  *) err "invalid --scope: $DF_SCOPE (use 'user' or 'project')"; exit 2 ;;
esac
DF_RECEIPT="$(df_receipt_for_target "$DF_SKILLS_TARGET")"
# Start a fresh receipt for this run: it records what THIS install creates.
# Anything left untouched must not be listed, or uninstall would delete files we
# did not write. A dry run creates nothing at all — the staging dir absorbs
# every write, so the receipt is not touched either.
if [[ "$DF_DRY_RUN" -eq 0 ]]; then
  mkdir -p "$(dirname "$DF_RECEIPT")"
  : > "$DF_RECEIPT.new"
fi
export DF_SKILLS_TARGET DF_RECEIPT

PROFILE_LABEL=$(df_json "$MANIFEST" 'd["label"]')

# ---------- announce --------------------------------------------------------
header "DataFlow-Harness — $PROFILE_LABEL"
df_json "$MANIFEST" 'd["description"]' | fold -s -w 76 | sed 's/^/  /'
echo
printf '  %sWill install:%s\n' "$C_GREEN" "$C_RESET"
df_json "$MANIFEST" 'd["installs"]' | while IFS= read -r l; do printf '    + %s\n' "$l"; done
printf '  %sWill NOT install:%s\n' "$C_YELLOW" "$C_RESET"
df_json "$MANIFEST" 'd["does_not_install"]' | while IFS= read -r l; do printf '    - %s\n' "$l"; done
printf '  %sWrites outside this repo:%s\n' "$C_BOLD" "$C_RESET"
df_json "$MANIFEST" 'd["writes_outside_repo"]' | while IFS= read -r l; do printf '    ! %s\n' "$l"; done
printf '    Skills destination: %s\n' "$DF_SKILLS_TARGET"

if [[ "$DF_DRY_RUN" -eq 1 ]]; then
  printf '\n  %sDRY RUN — nothing will be changed.%s\n' "$C_YELLOW" "$C_RESET"
fi

# ---------- prerequisites ---------------------------------------------------
header "Prerequisites"
PREREQ_FAILED=0
prereq_count=$(df_json "$MANIFEST" 'len(d["prerequisites"])')
for ((i = 0; i < prereq_count; i++)); do
  p_id=$(df_json "$MANIFEST" "d['prerequisites'][$i]['id']")
  p_check=$(df_json "$MANIFEST" "d['prerequisites'][$i]['check']")
  p_min=$(df_json "$MANIFEST" "d['prerequisites'][$i].get('min','')")
  p_reason=$(df_json "$MANIFEST" "d['prerequisites'][$i]['reason']")
  df_check_prereq "$p_id" "$p_check" "$p_min" "$p_reason" || PREREQ_FAILED=$((PREREQ_FAILED + 1))
done

# The skills-only profile installs no packages. Runtime profiles use uv by
# default, while --pip keeps a compatible escape hatch for restricted systems.
if [[ "$DF_PROFILE" != "skills" ]]; then
  if [[ "$DF_PYTHON_INSTALLER" == "uv" ]]; then
    df_check_prereq "uv" "uv --version" "" "install Python packages" \
      || PREREQ_FAILED=$((PREREQ_FAILED + 1))
  else
    df_check_prereq "pip" "$DF_PYTHON -m pip --version" "" "install Python packages" \
      || PREREQ_FAILED=$((PREREQ_FAILED + 1))
  fi
fi

if [[ "$PREREQ_FAILED" -gt 0 ]]; then
  err "$PREREQ_FAILED prerequisite(s) missing — fix them and re-run."
  exit 1
fi

if [[ "$DF_CHECK_ONLY" -eq 1 ]]; then
  header "Plan"
  step_count=$(df_json "$MANIFEST" 'len(d["steps"])')
  for ((i = 0; i < step_count; i++)); do
    s_label=$(df_json "$MANIFEST" "d['steps'][$i]['label']")
    printf '  %d. %s\n' "$((i + 1))" "$s_label"
  done
  echo
  ok "Prerequisites satisfied. Re-run without --check to install."
  exit 0
fi

# ---------- staging ---------------------------------------------------------
DF_STAGING="$(mktemp -d "${TMPDIR:-/tmp}/dataflow-install.XXXXXX")"
export DF_STAGING
cleanup() { rm -rf "$DF_STAGING" "${DF_BOUNDARY_SNAPSHOT_DIR:-}"; }
trap cleanup EXIT

# Fingerprint every path this profile promised not to touch, before any step
# runs. Verified after the last one — see the "Boundary check" section below.
df_snapshot_boundaries "$MANIFEST"

# ---------- run steps -------------------------------------------------------
header "Install"
step_count=$(df_json "$MANIFEST" 'len(d["steps"])')
for ((i = 0; i < step_count; i++)); do
  s_id=$(df_json "$MANIFEST" "d['steps'][$i]['id']")
  s_label=$(df_json "$MANIFEST" "d['steps'][$i]['label']")
  s_run=$(df_json "$MANIFEST" "d['steps'][$i]['run']")
  s_skip=$(df_json "$MANIFEST" "d['steps'][$i].get('skip_if','')")

  printf '\n%s%d/%d%s %s\n' "$C_BOLD" "$((i + 1))" "$step_count" "$C_RESET" "$s_label"

  if [[ -n "$s_skip" ]] && eval "$s_skip" >/dev/null 2>&1; then
    skip "$s_id (already satisfied)"
    continue
  fi

  debug "run: $s_run"
  if ! eval "$s_run"; then
    err "step '$s_id' failed: $s_label"
    err "re-run with --verbose to see the full output"
    exit 1
  fi
done

# ---------- boundary assertions --------------------------------------------
header "Boundary check"
if ! df_verify_boundaries; then
  err "this profile modified something its manifest forbids — a bug in the installer."
  err "nothing is rolled back automatically; inspect the paths listed above."
  exit 1
fi
ok "all ${DF_BOUNDARY_CHECKED:-0} declared boundary path(s) unchanged"

# ---------- verify ----------------------------------------------------------
header "Verify"
VERIFY_FAILED=0
verify_count=$(df_json "$MANIFEST" 'len(d.get("verify",[]))')
for ((i = 0; i < verify_count; i++)); do
  v_label=$(df_json "$MANIFEST" "d['verify'][$i]['label']")
  v_run=$(df_json "$MANIFEST" "d['verify'][$i]['run']")
  if eval "$v_run"; then
    ok "$v_label"
  else
    err "$v_label"
    VERIFY_FAILED=$((VERIFY_FAILED + 1))
  fi
done

if [[ "$VERIFY_FAILED" -gt 0 ]]; then
  err "$VERIFY_FAILED verification(s) failed — the install is incomplete."
  exit 1
fi

# Finalize the receipt. Line 1 is the destination; each further line is
# "<skill-id>\t<hash of what we wrote>".
#
# Only skills THIS run created are in "$DF_RECEIPT.new". Entries from previous
# runs are carried over so their skills stay uninstallable, but a skill we
# merely found already present is deliberately absent — uninstall must not
# delete directories this installer did not write.
if [[ "$DF_DRY_RUN" -eq 0 ]]; then
  if [[ -s "$DF_RECEIPT.new" ]] || [[ -f "$DF_RECEIPT" ]]; then
    tmp_receipt=$(mktemp)
    {
      printf '%s\n' "$DF_SKILLS_TARGET"
      {
        [[ -s "$DF_RECEIPT.new" ]] && cat "$DF_RECEIPT.new"
        # Carry over prior entries, minus any path this run just rewrote — its
        # hash changed, and the new line already records the current state.
        if [[ -f "$DF_RECEIPT" ]]; then
          tail -n +2 "$DF_RECEIPT" | while IFS=$'\t' read -r old_path old_hash old_label; do
            [[ -n "$old_path" ]] || continue
            if ! cut -f1 "$DF_RECEIPT.new" 2>/dev/null | grep -qFx "$old_path"; then
              printf '%s\t%s\t%s\n' "$old_path" "$old_hash" "$old_label"
            fi
          done
        fi
      } | sort -u
    } > "$tmp_receipt"
    mv "$tmp_receipt" "$DF_RECEIPT"
  fi
  rm -f "$DF_RECEIPT.new"
fi

# ---------- next steps ------------------------------------------------------
header "Done — $PROFILE_LABEL"
if [[ "$DF_DRY_RUN" -eq 1 ]]; then
  ok "Dry run complete. Nothing was changed."
else
  ok "Installed. Next:"
fi
df_json "$MANIFEST" 'd["next_steps"]' | while IFS= read -r l; do printf '    %s\n' "$l"; done
echo
