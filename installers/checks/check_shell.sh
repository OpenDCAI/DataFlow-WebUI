#!/usr/bin/env bash
# check_shell.sh — syntax + lint every shell script in the repo (plan P2-04).
#
#   bash -n     always runs; catches syntax errors.
#   the linter  runs when available. CI installs it; locally it may be absent,
#               in which case we say so rather than pretend the check passed.
#
# (A comment line whose first word is the linter's own name is parsed as a
#  directive and fails with SC1072/SC1073, so that word is avoided at line start.)
#
# Use --require-shellcheck (CI does) to make a missing shellcheck a failure.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT" || exit 1

REQUIRE_SHELLCHECK=0
[[ "${1:-}" == "--require-shellcheck" ]] && REQUIRE_SHELLCHECK=1

if [[ -t 1 ]]; then
  C_GREEN=$'\033[32m'; C_RED=$'\033[31m'; C_YELLOW=$'\033[33m'; C_RESET=$'\033[0m'
else
  C_GREEN=""; C_RED=""; C_YELLOW=""; C_RESET=""
fi

# Collected into a plain array rather than with `mapfile`, which does not exist
# in bash 3.2 — the version macOS still ships, and one this repo must run on.
SCRIPTS=()
while IFS= read -r line; do
  [[ -n "$line" ]] && SCRIPTS+=("$line")
done < <(
  {
    find . -name "*.sh" -not -path "./frontend/node_modules/*" -not -path "./.git/*"
    # Extensionless executables with a shell shebang (install.sh has an
    # extension, but a future entry point may not).
    find . -maxdepth 2 -type f -perm -u+x -not -name "*.sh" -not -path "./.git/*" \
      -not -path "./frontend/node_modules/*" -print0 2>/dev/null |
      xargs -0 -I{} sh -c 'head -1 "{}" | grep -q "^#!.*sh" && echo "{}"' 2>/dev/null
  } | sort -u
)

if [[ ${#SCRIPTS[@]} -eq 0 ]]; then
  echo "[shell-check] no shell scripts found — that is suspicious"
  exit 1
fi

FAILED=0

echo "[shell-check] bash -n on ${#SCRIPTS[@]} script(s)"
for f in "${SCRIPTS[@]}"; do
  if ! out=$(bash -n "$f" 2>&1); then
    printf '  %sFAIL%s %s\n' "$C_RED" "$C_RESET" "$f"
    printf '%s\n' "$out" | sed 's/^/       /'
    FAILED=$((FAILED + 1))
  fi
done

if command -v shellcheck >/dev/null 2>&1; then
  echo "[shell-check] shellcheck ($(shellcheck --version | awk '/version:/{print $2}'))"
  for f in "${SCRIPTS[@]}"; do
    # SC1091: sourced files are resolved at runtime via computed paths.
    # SC2154: variables come from sourced config/lib files.
    if ! out=$(shellcheck -e SC1091,SC2154 -S warning "$f" 2>&1); then
      printf '  %sFAIL%s %s\n' "$C_RED" "$C_RESET" "$f"
      printf '%s\n' "$out" | sed 's/^/       /'
      FAILED=$((FAILED + 1))
    fi
  done
elif [[ "$REQUIRE_SHELLCHECK" -eq 1 ]]; then
  printf '[shell-check] %sFAIL%s shellcheck not installed but --require-shellcheck was given\n' \
    "$C_RED" "$C_RESET"
  exit 1
else
  printf '[shell-check] %sSKIPPED%s shellcheck not installed — syntax checked only.\n' \
    "$C_YELLOW" "$C_RESET"
  printf '             install it (brew install shellcheck) for the full lint.\n'
fi

if [[ "$FAILED" -gt 0 ]]; then
  printf '[shell-check] %s%d check(s) failed%s\n' "$C_RED" "$FAILED" "$C_RESET"
  exit 1
fi

printf '[shell-check] %sOK%s — %d script(s) clean\n' "$C_GREEN" "$C_RESET" "${#SCRIPTS[@]}"
