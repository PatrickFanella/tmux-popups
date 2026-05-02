#!/usr/bin/env bash
set -euo pipefail
. "$(dirname "${BASH_SOURCE[0]}")/../lib.sh"

printf 'Command docs for: '
read -r cmd
[[ -z "$cmd" ]] && exit 0
tmp="${TMPDIR:-/tmp}/tmux-docs-popup.$$"
trap 'rm -f "$tmp"' EXIT
if command -v tldr >/dev/null 2>&1 && tldr "$cmd" >"$tmp" 2>/dev/null; then
  less -R "$tmp"
elif man "$cmd" >/dev/null 2>&1; then
  man "$cmd"
else
  printf 'No tldr/man entry for %s\n' "$cmd"
  pause
fi
