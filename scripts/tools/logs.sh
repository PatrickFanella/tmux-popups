#!/usr/bin/env bash
set -euo pipefail
printf 'Logs\n────\n\n[s] follow service  [f] tail file\n> '
read -r action
case "$action" in
  s|service) printf 'User unit name: '; read -r unit; [[ -n "$unit" ]] || exit 0; exec journalctl --user -u "$unit" -f ;;
  f|file) printf 'Log file: '; read -r file; [[ -n "$file" ]] || exit 0; file="${file/#\~/$HOME}"; exec tail -f "$file" ;;
esac
