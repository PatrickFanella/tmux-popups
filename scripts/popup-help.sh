#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
local_registry="${TMUX_POPUPS_LOCAL_REGISTRY:-${XDG_CONFIG_HOME:-$HOME/.config}/tmux-popups/popups.local.tsv}"

tmux_opt() {
  tmux show-option -gqv "$1" 2>/dev/null || true
}
menu_key="$(tmux_opt @tmux-popups-menu-key)"; menu_key="${menu_key:-Enter}"
reload_key="$(tmux_opt @tmux-popups-reload-key)"; reload_key="${reload_key:-R}"
config_file="$(tmux_opt @tmux-popups-config-file)"; config_file="${config_file:-$HOME/.tmux.conf}"
case "$config_file" in '~'/*) config_file="$HOME/${config_file#~/}" ;; esac

status_mark() {
  case "$1" in
    ok) printf 'ok' ;;
    missing:*) printf '%s' "$1" ;;
    *) printf '%s' "$1" ;;
  esac
}

{
  cat <<EOF
tmux-popups
===========

Popups
------
Bindings are generated from the merged registry:

- Default: $root/popups.tsv
- Local:   $local_registry

Local rows override default rows with the same id. Reload tmux to regenerate.

Direct binds
------------
Prefix + $menu_key       Quick Menu (configurable: @tmux-popups-menu-key)
Prefix + $reload_key        reload tmux config (configurable: @tmux-popups-reload-key)

EOF

  "$root/scripts/list-popups.sh" --deps-tsv | while IFS=$'\t' read -r id direct_key menu_key title width height command deps status; do
    [[ "$direct_key" == "-" ]] && continue
    printf 'Prefix + %-7s %-18s %-14s deps:%-22s %s\n' "$direct_key" "$title" "$id" "$deps" "$(status_mark "$status")"
  done

  cat <<EOF

Quick Menu keys: Prefix + $menu_key, then key
----------------------------------------------
EOF

  "$root/scripts/list-popups.sh" --deps-tsv | while IFS=$'\t' read -r id direct_key menu_key title width height command deps status; do
    [[ "$menu_key" == "-" ]] && continue
    printf '%-7s %-18s %-14s deps:%-22s %s\n' "$menu_key" "$title" "$id" "$deps" "$(status_mark "$status")"
  done

  cat <<EOF
v       vscode here        configurable: @tmux-popups-vscode-command
R       reload tmux        source $config_file
q       exit menu

Helpers
-------
$root/scripts/list-popups.sh --pretty
$root/scripts/list-popups.sh --deps
$root/scripts/doctor.sh

Options
-------
@tmux-popups-menu-key
@tmux-popups-reload-key
@tmux-popups-config-file
@tmux-popups-default-width
@tmux-popups-default-height
@tmux-popups-local-registry
@tmux-popups-enable-vscode
@tmux-popups-vscode-command

Files
-----
Plugin: $root
Default registry: $root/popups.tsv
Local registry: $local_registry
Optional examples: $root/examples/popups.optional.tsv
Generated config: \\${XDG_CACHE_HOME:-\\$HOME/.cache}/tmux-popups/generated.conf
EOF
} | if command -v less >/dev/null 2>&1; then less -R; else cat; fi
