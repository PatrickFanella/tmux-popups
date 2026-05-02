#!/usr/bin/env bash
set -euo pipefail
printf 'Watch command: '
read -r cmd
[[ -n "$cmd" ]] || exit 0
printf 'Interval seconds [2]: '
read -r interval
interval="${interval:-2}"
[[ "$interval" =~ ^[0-9]+([.][0-9]+)?$ ]] || { printf 'Invalid interval.\n'; sleep 1; exit 1; }
exec watch -n "$interval" "$cmd"
