#!/usr/bin/env bash
# common.sh — shared helpers for install.sh and configure_agent.sh.
#
# Sourced, never executed. Every df_* function used by a profile manifest's
# `run:` / `skip_if:` field is defined here, so a manifest can only ever call a
# reviewed function rather than arbitrary shell.

# ---------- output ----------------------------------------------------------
if [[ -t 1 ]]; then
  C_GREEN=$'\033[32m'; C_YELLOW=$'\033[33m'; C_RED=$'\033[31m'
  C_BLUE=$'\033[34m'; C_DIM=$'\033[2m'; C_BOLD=$'\033[1m'; C_RESET=$'\033[0m'
else
  C_GREEN=""; C_YELLOW=""; C_RED=""; C_BLUE=""; C_DIM=""; C_BOLD=""; C_RESET=""
fi

DF_TAG="${DF_TAG:-install}"

info()  { printf '%s[%s]%s %s\n'            "$C_BLUE" "$DF_TAG" "$C_RESET" "$*"; }
ok()    { printf '%s[%s]%s %sOK%s      %s\n'  "$C_BLUE" "$DF_TAG" "$C_RESET" "$C_GREEN"  "$C_RESET" "$*"; }
skip()  { printf '%s[%s]%s %sSKIP%s    %s\n'  "$C_BLUE" "$DF_TAG" "$C_RESET" "$C_DIM"    "$C_RESET" "$*"; }
warn()  { printf '%s[%s]%s %sWARN%s    %s\n'  "$C_BLUE" "$DF_TAG" "$C_RESET" "$C_YELLOW" "$C_RESET" "$*" >&2; }
err()   { printf '%s[%s]%s %sERROR%s   %s\n'  "$C_BLUE" "$DF_TAG" "$C_RESET" "$C_RED"    "$C_RESET" "$*" >&2; }
plan()  { printf '%s[%s]%s %sPLAN%s    %s\n'  "$C_BLUE" "$DF_TAG" "$C_RESET" "$C_YELLOW" "$C_RESET" "$*"; }
header(){ printf '\n%s── %s ──%s\n' "$C_BOLD" "$*" "$C_RESET"; }
debug() { [[ "${DF_VERBOSE:-0}" -eq 1 ]] && printf '%s[%s] %s%s\n' "$C_DIM" "$DF_TAG" "$*" "$C_RESET" || true; }

# ---------- json ------------------------------------------------------------
# jq is not assumed present (it is not on a stock macOS or slim Linux image),
# so manifest reads go through python3, which every profile already needs.
df_json() {
  # df_json <file> <python-expression-on-`d`>
  local file="$1" expr="$2"
  python3 -c '
import json, sys
with open(sys.argv[1], encoding="utf-8") as fh:
    d = json.load(fh)
out = eval(sys.argv[2], {"d": d, "json": json})
if isinstance(out, (list, tuple)):
    for item in out:
        print(item)
elif out is not None:
    print(out)
' "$file" "$expr"
}

# ---------- prerequisite checks --------------------------------------------
df_version_ge() {
  # df_version_ge <have> <want> — numeric dotted compare, no external tools
  python3 -c '
import sys
def parse(v):
    out = []
    for part in v.strip().lstrip("v").split("."):
        num = ""
        for ch in part:
            if ch.isdigit():
                num += ch
            else:
                break
        out.append(int(num) if num else 0)
    return out
have, want = parse(sys.argv[1]), parse(sys.argv[2])
have += [0] * (len(want) - len(have))
sys.exit(0 if have >= want[: len(have)] else 1)
' "$1" "$2"
}

df_check_prereq() {
  # df_check_prereq <id> <check-cmd> <min-version-or-empty> <reason>
  local id="$1" check="$2" min="$3" reason="$4" out=""
  if ! out=$(eval "$check" 2>&1 | head -1); then
    err "$id not found — needed to $reason"
    case "$id" in
      python) err "  install Python 3.10+ from https://python.org" ;;
      node)   err "  install Node.js 20+ (recommended: nvm install 20)" ;;
      npm)    err "  npm ships with Node.js — reinstall Node" ;;
      pip)    err "  run: python3 -m ensurepip --upgrade" ;;
    esac
    return 1
  fi
  # Take the FIRST version-like token. Naively stripping non-digits would
  # splice unrelated numbers together ("pip 21.2.4 ... (python 3.9)" became
  # "21.2.43.9"), which then compares as a bogusly high version.
  local ver
  ver=$(printf '%s\n' "$out" | grep -Eo '[0-9]+(\.[0-9]+)+' | head -1)
  [[ -n "$ver" ]] || ver=$(printf '%s\n' "$out" | grep -Eo '[0-9]+' | head -1)
  if [[ -n "$min" ]]; then
    if ! df_version_ge "$ver" "$min"; then
      err "$id $ver found, but $min+ is required (needed to $reason)"
      return 1
    fi
  fi
  ok "$id ${ver:-present}"
  return 0
}

# ---------- guard: profile boundaries --------------------------------------
df_expand_boundary_path() {
  # Map a manifest `must_not_touch` entry to an absolute path.
  local p="$1"
  # SC2088: the "~/" below is a literal prefix arriving from the manifest, not a
  # tilde we expect the shell to expand — expanding it is exactly what this
  # function does. The directive has to precede the whole `case`, not a branch.
  # shellcheck disable=SC2088
  case "$p" in
    "~/"*)       printf '%s/%s' "$HOME" "${p#\~/}" ;;
    /*)          printf '%s' "$p" ;;
    node_modules) printf '%s/frontend/node_modules' "$DF_REPO_ROOT" ;;
    *)           printf '%s/%s' "$DF_REPO_ROOT" "${p%/}" ;;
  esac
}

df_boundary_fingerprint() {
  # A single string capturing the state of a file or directory tree: every
  # path plus its content hash. Comparing before/after detects additions,
  # deletions and modifications anywhere underneath.
  local target="$1"
  if [[ -f "$target" ]]; then
    printf 'f:%s\n' "$(df_file_hash "$target")"
  elif [[ -d "$target" ]]; then
    # -print0/-exec keeps filenames with spaces intact. Sorted for stability.
    find "$target" -type f \
      -not -path "*/__pycache__/*" -not -name "*.pyc" -print0 2>/dev/null |
      LC_ALL=C sort -z |
      while IFS= read -r -d '' f; do
        printf '%s:%s\n' "${f#"$target"}" "$(df_file_hash "$f")"
      done
  else
    printf 'absent\n'
  fi
}

df_snapshot_boundaries() {
  # df_snapshot_boundaries <manifest> — record the pre-install state of every
  # path the profile promised not to touch. Written to files under $DF_STAGING
  # because this runs in a subshell-heavy context and arrays would not survive.
  local manifest="$1"
  DF_BOUNDARY_SNAPSHOT_DIR="$(mktemp -d "${TMPDIR:-/tmp}/df-boundary.XXXXXX")"
  export DF_BOUNDARY_SNAPSHOT_DIR
  local i=0
  while IFS= read -r entry; do
    [[ -n "$entry" ]] || continue
    local abs
    abs="$(df_expand_boundary_path "$entry")"
    printf '%s\n' "$entry" > "$DF_BOUNDARY_SNAPSHOT_DIR/$i.name"
    printf '%s\n' "$abs"   > "$DF_BOUNDARY_SNAPSHOT_DIR/$i.path"
    df_boundary_fingerprint "$abs" > "$DF_BOUNDARY_SNAPSHOT_DIR/$i.before"
    i=$((i + 1))
  done < <(df_json "$manifest" 'd.get("must_not_touch",[])')
  debug "snapshotted $i boundary path(s)"
}

df_verify_boundaries() {
  # Compare each snapshotted path against its current state. Any difference is
  # a profile violating its own manifest.
  local violations=0 checked=0
  [[ -d "${DF_BOUNDARY_SNAPSHOT_DIR:-}" ]] || { warn "no boundary snapshot taken"; return 0; }
  for before in "$DF_BOUNDARY_SNAPSHOT_DIR"/*.before; do
    [[ -f "$before" ]] || continue
    local idx entry abs
    idx="$(basename "$before" .before)"
    entry="$(<"$DF_BOUNDARY_SNAPSHOT_DIR/$idx.name")"
    abs="$(<"$DF_BOUNDARY_SNAPSHOT_DIR/$idx.path")"
    checked=$((checked + 1))
    if ! df_boundary_fingerprint "$abs" | diff -q "$before" - >/dev/null 2>&1; then
      err "profile boundary violated: '$entry' changed during install ($abs)"
      if [[ "${DF_VERBOSE:-0}" -eq 1 ]]; then
        df_boundary_fingerprint "$abs" | diff "$before" - | head -20 | sed 's/^/       /' >&2
      else
        err "  re-run with --verbose to see what changed"
      fi
      violations=$((violations + 1))
    fi
  done
  debug "verified $checked boundary path(s)"
  [[ "$violations" -eq 0 ]] || return 1
  # Read by install.sh to report how many paths it verified.
  # shellcheck disable=SC2034
  DF_BOUNDARY_CHECKED="$checked"
  return 0
}

df_file_hash() {
  [[ -f "$1" ]] || { printf 'absent'; return 0; }
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | awk '{print $1}'
  elif command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
  else
    wc -c < "$1" | tr -d ' '
  fi
}

df_stdin_hash() {
  # Hash whatever is piped in. Used to condense a directory fingerprint into
  # one receipt-sized token.
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 | awk '{print $1}'
  elif command -v sha256sum >/dev/null 2>&1; then
    sha256sum | awk '{print $1}'
  else
    wc -c | tr -d ' '
  fi
}

df_tree_hash() {
  # A single hash representing the full contents of a file or directory tree.
  df_boundary_fingerprint "$1" | df_stdin_hash
}
