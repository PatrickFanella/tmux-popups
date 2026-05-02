#!/usr/bin/env bash
set -euo pipefail
. "$(dirname "${BASH_SOURCE[0]}")/../lib.sh"

taskrc="$HOME/.taskrc"
taskdata="$HOME/.local/share/task"
mkdir -p "$taskdata"
if [[ ! -f "$taskrc" ]]; then
  cat >"$taskrc" <<EOF
data.location=$taskdata
confirmation=no
verbose=blank,header,footnote,label,new-id,affected,edit,special,project,sync,unwait
EOF
fi

while true; do
  clear 2>/dev/null || true
  printf 'Taskwarrior\n────────────\n\n'
  task next || true
  printf '\n[a] add  [d] done  [m] modify  [p] projects  [e] edit taskrc  [q] quit\n> '
  read -r action || exit 0
  case "$action" in
    a|add) printf 'Task: '; read -r text || continue; [[ -n "$text" ]] && task add "$text"; pause ;;
    d|done) printf 'ID(s) done: '; read -r ids || continue; [[ -n "$ids" ]] && task $ids done; pause ;;
    m|mod|modify) printf 'ID: '; read -r id || continue; [[ -z "$id" ]] && continue; printf 'Modification: '; read -r mod || continue; [[ -n "$mod" ]] && task "$id" modify $mod; pause ;;
    p|projects) task projects | less -R ;;
    e|edit) "${EDITOR:-nvim}" "$taskrc" ;;
    q|quit|/quit|exit|/exit) exit 0 ;;
  esac
done
