#!/usr/bin/env bash
set -euo pipefail
. "$(dirname "${BASH_SOURCE[0]}")/../lib.sh"

require_cmd cliphist
require_cmd fzf
require_cmd wl-copy

# Materialize the complete history once. Early picker exits cannot break the
# producer, and a failed producer must never be reported as empty history.
work_dir="$(mktemp -d "${TMPDIR:-/tmp}/tmux-popups-clipboard.XXXXXXXX")"
trap 'rm -rf -- "$work_dir"' EXIT
trap 'exit 130' INT
trap 'exit 143' TERM HUP
if ! cliphist list > "$work_dir/history"; then
  die 'could not read cliphist history'
fi
if [[ ! -s "$work_dir/history" ]]; then
  printf 'No cliphist entries yet.\n\nStart capture with:\n  wl-paste --watch cliphist store\n'
  pause
  exit 0
fi
if item=$(fzf --prompt='clipboard › ' --preview='printf "%s" {} | cliphist decode 2>/dev/null | head -200' < "$work_dir/history"); then
  [[ -n "$item" ]] || exit 0
else
  status=$?
  case "$status" in
    1|130) exit 0 ;;
    *) die "clipboard picker failed (status $status)" ;;
  esac
fi
# Decode fully before writing the clipboard; files preserve binary bytes and
# trailing newlines and avoid copying a partial item when decoding fails.
if ! printf '%s' "$item" | cliphist decode > "$work_dir/decoded"; then
  die 'could not decode selected cliphist item'
fi
wl-copy < "$work_dir/decoded"
printf 'Copied selected history item.\n'
sleep 1
