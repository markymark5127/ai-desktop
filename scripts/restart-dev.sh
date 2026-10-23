#!/usr/bin/env bash
# Development helper: ensure a freshly pulled AI Desktop Python process owns
# the GNOME application ID instead of reactivating a hidden older instance.
# Never kills Newelle, other Python processes or processes owned by other users.
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if ! command -v pgrep >/dev/null 2>&1; then
  echo "pgrep is needed to locate your previous AI Desktop process." >&2
  exit 1
fi

# Match only a Python 'aidesktop' module process running as this user.
# Include /usr/bin/python3(.x), python3, and python executable variations.
pattern='^([^[:space:]]*/)?python(3(\.[0-9]+)?)?[[:space:]]+-m[[:space:]]+aidesktop([[:space:]]|$)'
mapfile -t processes < <(pgrep -u "$(id -u)" -f "$pattern" || true)

if (( ${#processes[@]} )); then
  echo "Stopping old AI Desktop instance(s): ${processes[*]}"
  for pid in "${processes[@]}"; do
    [[ "$pid" == "$$" ]] && continue
    kill "$pid" 2>/dev/null || true
  done

  # Wait for the application's session-bus registration to be released,
  # otherwise the new launch can still be forwarded to old Python code.
  for iteration in {1..25}; do
    still_running=false
    for pid in "${processes[@]}"; do
      if kill -0 "$pid" 2>/dev/null; then
        still_running=true
      fi
    done
    if [[ "$still_running" == false ]]; then
      break
    fi
    sleep 0.12
  done

  for pid in "${processes[@]}"; do
    if kill -0 "$pid" 2>/dev/null; then
      echo "AI Desktop process $pid is still running. Close it before retrying." >&2
      exit 1
    fi
  done
fi

exec bash "$repo_dir/scripts/run-dev.sh" "$@"
