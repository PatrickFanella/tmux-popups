#!/usr/bin/env bash
set -euo pipefail
# Called only after the dispatcher has resolved/validated the invoking context.
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
. "$root/scripts/lib.sh"
id="${1:?entry id required}"
policy="${2:?reuse scope required}"
title="${3:?window title required}"
launch_command="${4:?launch command required}"
[[ "$id" =~ ^[a-zA-Z0-9_-]+$ ]] || die 'invalid reuse entry id'
[[ "$policy" == session || "$policy" == directory ]] || die 'invalid reuse scope'
origin_pane
origin_client
# Store an exact ASCII representation so option output escaping cannot change
# comparisons for tabs, carriage returns, newlines or literal backslashes.
directory="$(printf '%s' "$TMUX_POPUPS_DIRECTORY" | od -An -tx1 | tr -d ' \n')"
lock="tmux-popups-reuse-$TMUX_POPUPS_SESSION-$id"
locked=no
cleanup() {
  if [[ "$locked" == yes ]]; then tmux wait-for -U "$lock"; fi
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
tmux wait-for -L "$lock"
locked=yes
# Recheck after waiting. A vanished origin must not target a different client.
origin_pane
origin_client
while IFS= read -r window; do
  [[ "$(tmux show-option -w -t "$window" -qv @tmux-popups-entry)" == "$id" ]] || continue
  [[ "$(tmux show-option -w -t "$window" -qv @tmux-popups-reuse)" == "$policy" ]] || continue
  if [[ "$policy" == directory ]]; then
    [[ "$(tmux show-option -w -t "$window" -qv @tmux-popups-directory)" == "$directory" ]] || continue
  fi
  pane="$(tmux show-option -w -t "$window" -qv @tmux-popups-tool-pane 2>/dev/null || true)"
  if [[ -n "$pane" && "$(tmux display-message -p -t "$pane" '#{window_id} #{pane_dead}' 2>/dev/null || true)" == "$window 0" ]]; then
    tmux select-window -t "$window"
    exit 0
  fi
  # Keep exited remain-on-exit panes and any user-added panes for inspection.
  # They no longer represent a live reusable tool.
  tmux set-window-option -u -t "$window" @tmux-popups-entry \
    \; set-window-option -u -t "$window" @tmux-popups-reuse \
    \; set-window-option -u -t "$window" @tmux-popups-directory \
    \; set-window-option -u -t "$window" @tmux-popups-tool-pane 2>/dev/null || true
done < <(tmux list-windows -t "$TMUX_POPUPS_SESSION" -F '#{window_id}')
launch_environment=()
for variable in CLIENT SESSION WINDOW PANE DIRECTORY; do
  name="TMUX_POPUPS_$variable"
  launch_environment+=(-e "$name=${!name}")
done
launch_directory=${TMUX_POPUPS_DIRECTORY//#/##}
created="$(tmux new-window -P -F '#{window_id} #{pane_id}' -t "$TMUX_POPUPS_SESSION:" \
  -c "$launch_directory" "${launch_environment[@]}" -n "$title" "$launch_command")"
read -r window pane <<<"$created"
# Fast successful tools may close before tagging. No window remains to reuse.
if ! tmux list-windows -t "$TMUX_POPUPS_SESSION" -F '#{window_id}' | grep -Fxq -- "$window"; then exit 0; fi
if ! tmux set-window-option -t "$window" @tmux-popups-reuse "$policy" \
  \; set-window-option -t "$window" @tmux-popups-directory "$directory" \
  \; set-window-option -t "$window" @tmux-popups-tool-pane "$pane" \
  \; set-window-option -t "$window" @tmux-popups-entry "$id" 2>/dev/null; then
  if tmux list-windows -t "$TMUX_POPUPS_SESSION" -F '#{window_id}' | grep -Fxq -- "$window"; then
    die "could not mark reusable window $window"
  fi
fi
