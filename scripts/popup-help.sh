#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
. "$root/scripts/lib.sh"
local_registry="$(resolve_local_registry)"
policy="$(availability_policy)"

tmux_opt() {
  tmux show-option -gqv "$1" 2>/dev/null || true
}
menu_key="$(tmux_opt @tmux-popups-menu-key)"; menu_key="${menu_key:-Enter}"
reload_key="$(tmux_opt @tmux-popups-reload-key)"; reload_key="${reload_key:-R}"
config_file="$(tmux_opt @tmux-popups-config-file)"; config_file="${config_file:-$HOME/.tmux.conf}"
config_file="$(expand_home_path "$config_file")"

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

  "$root/scripts/list-popups.sh" --state-tsv | while IFS=$'\t' read -r id direct_key menu_key title width height command launch_mode completion enabled deps status; do
    [[ "$direct_key" == "-" || "$enabled" == off ]] && continue
    [[ "$status" == ok || "$policy" == ignore ]] || continue
    printf 'Prefix + %-7s %-18s %-14s deps:%-22s %s\n' "$direct_key" "$title" "$id" "$deps" "$(status_mark "$status")"
  done

  cat <<EOF

Quick Menu keys: Prefix + $menu_key, then key
----------------------------------------------
EOF

  "$root/scripts/list-popups.sh" --state-tsv | while IFS=$'\t' read -r id direct_key menu_key title width height command launch_mode completion enabled deps status; do
    [[ "$menu_key" == "-" || "$enabled" == off ]] && continue
    if [[ "$status" != ok && "$policy" != ignore ]]; then
      [[ "$policy" != hide-unavailable ]] || continue
      menu_key="-"
    fi
    printf '%-7s %-18s %-14s deps:%-22s %s\n' "$menu_key" "$title" "$id" "$deps" "$(status_mark "$status")"
  done

  cat <<EOF
v       vscode here        configurable: @tmux-popups-vscode-command
R       reload tmux        source $config_file
q       exit menu

Optional adapters and disabled rows
-----------------------------------
$("$root/scripts/list-popups.sh" --deps)
Enable an adapter with @tmux-popups-<id>-enabled on, then reload.

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
