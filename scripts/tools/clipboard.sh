#!/usr/bin/env bash
set -euo pipefail
. "$(dirname "${BASH_SOURCE[0]}")/../lib.sh"

require_cmd cliphist
require_cmd fzf
require_cmd wl-copy
if ! cliphist list | grep -q .; then
  printf 'No cliphist entries yet.\n\nStart capture with:\n  wl-paste --watch cliphist store\n'
  pause
  exit 0
fi
item=$(cliphist list | fzf --prompt='clipboard › ' --preview='printf "%s" {} | cliphist decode 2>/dev/null | head -200')
[[ -n "${item:-}" ]] || exit 0
printf '%s' "$item" | cliphist decode | wl-copy
printf 'Copied selected history item.\n'
sleep 1
