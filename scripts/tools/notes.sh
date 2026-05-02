#!/usr/bin/env bash
set -euo pipefail
. "$(dirname "${BASH_SOURCE[0]}")/../lib.sh"

notes_dir="${NOTES_DIR:-$HOME/Notes/daily}"
today="$(date +%F)"
note="$notes_dir/$today.md"
mkdir -p "$notes_dir"
if [[ ! -f "$note" ]]; then
  cat >"$note" <<EOF
# $today

## Scratch

## Log

EOF
fi
open_editor "$note"
