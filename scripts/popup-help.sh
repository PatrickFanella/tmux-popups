#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
registry="$root/popups.tsv"

{
  cat <<'EOF'
Tmux popups
===========

Persistence
-----------
Popups open named tmux sessions via popup-session.sh.
Reopening a popup reattaches to its existing popup-* session if still alive.
If the tool exits, its popup session ends and next open starts fresh.

Direct binds
------------
Prefix + d       Quick Menu
Prefix + C-S-r   reload ~/.config/tmux/tmux.conf

EOF

  while IFS=$'\t' read -r id direct_key menu_key title width height command; do
    [[ -z "${id:-}" || "$id" == \#* || "$direct_key" == "-" ]] && continue
    printf 'Prefix + %-7s %-18s popup-%s\n' "$direct_key" "$title" "$id"
  done <"$registry"

  cat <<'EOF'

Quick Menu keys: Prefix + d, then key
--------------------------------------
EOF

  while IFS=$'\t' read -r id direct_key menu_key title width height command; do
    [[ -z "${id:-}" || "$id" == \#* || "$menu_key" == "-" ]] && continue
    printf '%-7s %-18s popup-%-14s %s\n' "$menu_key" "$title" "$id" "$command"
  done <"$registry"

  cat <<'EOF'
v       vscode here        code-insiders .
R       reload tmux        source ~/.config/tmux/tmux.conf
q       exit menu

Files
-----
Plugin: ~/.config/tmux/plugins/tmux-popups
Registry: popups.tsv
Generated config: ~/.cache/tmux-popups/generated.conf
EOF
} | less -R
