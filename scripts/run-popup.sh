#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
registry="$root/popups.tsv"

id="${1:?popup id required}"

while IFS=$'\t' read -r popup_id direct_key menu_key title width height command; do
  [[ -z "${popup_id:-}" || "$popup_id" == \#* ]] && continue
  [[ "$popup_id" == "$id" ]] || continue

  if [[ "$command" == "-" ]]; then
    exec "${SHELL:-/usr/bin/env bash}"
  fi

  exec "$root/$command"
done <"$registry"

printf 'tmux-popups: unknown popup id: %s\n' "$id" >&2
printf 'Press Enter to close...'
read -r _ || true
exit 1
