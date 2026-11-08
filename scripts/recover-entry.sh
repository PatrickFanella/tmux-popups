#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
. "$root/scripts/lib.sh"
id="${1:?entry id required}"
policy="${2:?close policy required}"
mode="${3:?launch mode required}"
[[ $# == 3 && "$id" =~ ^[a-zA-Z0-9_-]+$ ]] || die 'invalid recovery arguments'
[[ "$policy" == on-success || "$policy" == never ]] || die 'invalid recovery close policy'
[[ "$mode" == popup || "$mode" == window ]] || die 'recovery requires popup or window mode'
# CLI/piped execution retains the application's exit status without prompting.
if [[ ! -t 0 || ! -t 1 || ! -t 2 ]]; then exec "$root/scripts/run-popup.sh" "$id"; fi
require_cmd python3
terminal_state="$(stty -g)"
terminal_group() {
  # Use the TTY on stderr; stdin carries this helper's source, not app input.
  python3 - "$1" <<'PYCODE'
import os
import signal
import sys
signal.signal(signal.SIGTTOU, signal.SIG_IGN)
group = int(sys.argv[1])
try:
    os.tcsetpgrp(2, group or os.getpgrp())
except OSError:
    sys.exit("tmux-popups: recovery terminal is no longer available")
PYCODE
}
child=""
stop_child() {
  if [[ -n "$child" ]]; then
    if kill -0 -- "-$child" 2>/dev/null; then
      kill -TERM -- "-$child" 2>/dev/null || true
      kill -CONT -- "-$child" 2>/dev/null || true
      sleep 0.1
      kill -KILL -- "-$child" 2>/dev/null || true
    fi
    wait "$child" 2>/dev/null || true
    child=""
  fi
}
trap stop_child EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
trap 'exit 129' HUP
while true; do
  # Stop before execution so the child cannot read or exit before receiving
  # the terminal. Only this launch's process group is owned.
  set -m
  (
    kill -STOP "$BASHPID"
    exec "$root/scripts/run-popup.sh" "$id" --recover
  ) &
  child=$!
  while kill -0 "$child" 2>/dev/null; do
    [[ "$(jobs -sp)" != "$child" ]] || break
    sleep 0.01
  done
  set +m
  terminal_group "$child"
  kill -CONT -- "-$child"
  if wait "$child"; then status=0; else status=$?; fi
  terminal_group 0
  stty "$terminal_state"
  stop_child
  [[ "$status" != 130 ]] || exit 130
  if [[ "$policy" == on-success && "$status" == 0 ]]; then exit 0; fi
  printf '\033[0m\033[?25h\ntmux-popups: %s exited with status %s.\n' "$id" "$status"
  if [[ "$mode" == popup ]]; then
    printf '[r] retry  [w] start again in a window  [c/Enter] close > '
  else
    printf '[r] retry  [c/Enter] close > '
  fi
  # Recovery reads input only after the application and its owned group end.
  retry=no
  while IFS= read -rsn1 action; do
    case "$action" in
      r|R) retry=yes; printf '\nRetrying %s...\n' "$id"; break ;;
      w|W)
        [[ "$mode" == popup ]] || continue
        origin_pane && origin_client || exit 1
        environment=()
        for variable in CLIENT SESSION WINDOW PANE DIRECTORY; do
          name="TMUX_POPUPS_$variable"
          environment+=(-e "$name=${!name}")
        done
        executable=${root//\'/\'\\\'\'}
        command="'$executable/scripts/recover-entry.sh' $id $policy window"
        directory=${TMUX_POPUPS_DIRECTORY//#/##}
        tmux new-window -t "$TMUX_POPUPS_SESSION:" -c "$directory" \
          "${environment[@]}" -n "$id" "$command" || exit 1
        exit 0 ;;
      c|C|q|Q|'') exit "$status" ;;
    esac
  done
  [[ "$retry" == yes ]] || exit "$status"
done
