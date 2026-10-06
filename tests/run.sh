#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
for tool in python3 tmux timeout; do
  command -v "$tool" >/dev/null || { printf 'Required test tool missing: %s\n' "$tool" >&2; exit 1; }
done
timeout --signal=TERM --kill-after=5s 90s python3 "$root/tests/test_launcher.py" "$@"
if (($# == 0)); then
  timeout --signal=TERM --kill-after=5s 90s python3 "$root/tests/test_quoting.py" QuotingTests
fi
