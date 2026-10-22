#!/usr/bin/env bash
set -euo pipefail
repo_dir="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="$repo_dir/src:${PYTHONPATH:-}"
exec python3 -m aidesktop "$@"
