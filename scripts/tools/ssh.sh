#!/usr/bin/env bash
set -euo pipefail
. "$(dirname "${BASH_SOURCE[0]}")/../lib.sh"

ssh_config="$HOME/.ssh/config"
[[ -f "$ssh_config" ]] || { printf 'No ~/.ssh/config found.\n'; pause; exit 0; }
require_cmd fzf
host=$(awk 'tolower($1)=="host" { for (i=2; i<=NF; i++) if ($i !~ /[*?]/) print $i }' "$ssh_config" | sort -u | fzf --prompt='ssh › ')
[[ -n "${host:-}" ]] || exit 0
exec ssh "$host"
