#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
for tool in python3 tmux timeout; do
  command -v "$tool" >/dev/null || { printf 'Required test tool missing: %s\n' "$tool" >&2; exit 1; }
done
exec timeout --signal=TERM --kill-after=5s 240s python3 "$root/tests/run_tests.py" "$@"
