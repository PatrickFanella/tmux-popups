#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
id="${1:?popup id required}"

row="$(
  "$root/scripts/list-popups.sh" --tsv |
    awk -F '\t' -v wanted="$id" '
      $1 == wanted { print; found = 1; exit }
      END { exit found ? 0 : 1 }
    '
)" || row=""

if [[ -n "$row" ]]; then
  IFS=$'\t' read -r _popup_id _direct_key _menu_key _title _width _height command <<<"$row"

  if [[ "$command" == "-" ]]; then
    if [[ -n "${SHELL:-}" ]]; then
      exec "$SHELL"
    fi
    exec /usr/bin/env bash
  fi

  exec "$root/$command"
fi

printf 'tmux-popups: unknown popup id: %s\n' "$id" >&2
printf 'Press Enter to close...'
read -r _ || true
exit 1
