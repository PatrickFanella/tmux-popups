#!/usr/bin/env bash
set -euo pipefail
if command -v less >/dev/null 2>&1; then
  tmux list-keys | less
else
  tmux list-keys
  printf '\nPress Enter to close... '
  read -r _ || true
fi
