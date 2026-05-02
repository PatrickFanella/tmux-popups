#!/usr/bin/env bash
set -euo pipefail
. "$(dirname "${BASH_SOURCE[0]}")/../lib.sh"

clear 2>/dev/null || true
if command -v khal >/dev/null 2>&1 && khal --version >/dev/null 2>&1; then
  khal calendar || true
  printf '\nAgenda:\n'
  khal agenda today 30d || true
else
  if command -v khal >/dev/null 2>&1; then
    printf 'khal is installed but not runnable; using cal fallback.\n'
    printf 'Try: python3 -m pip install --user khal\n\n'
  else
    printf 'khal not found in PATH; using cal fallback.\n\n'
  fi
  cal -3
fi
pause
