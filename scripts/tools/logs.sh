#!/usr/bin/env bash
set -euo pipefail
printf 'Logs\n────\n\n[o] opencode service  [f] file tail  [j] journal unit\n> '
read -r action
case "$action" in
  o|opencode) exec journalctl --user -u opencode -f ;;
  f|file) printf 'Log file: '; read -r file; [[ -n "$file" ]] || exit 0; file="${file/#\~/$HOME}"; exec tail -f "$file" ;;
  j|journal) printf 'User unit name: '; read -r unit; [[ -n "$unit" ]] || exit 0; exec journalctl --user -u "$unit" -f ;;
esac
