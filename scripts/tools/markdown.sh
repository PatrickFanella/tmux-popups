#!/usr/bin/env bash
set -euo pipefail
. "$(dirname "${BASH_SOURCE[0]}")/../lib.sh"
require_cmd fzf
file=$(find "${1:-.}" -type f \( -name '*.md' -o -name '*.markdown' \) 2>/dev/null | fzf --prompt='markdown › ')
[[ -n "${file:-}" ]] || exit 0
if command -v glow >/dev/null 2>&1; then exec glow -p "$file"; fi
if command -v bat >/dev/null 2>&1; then exec bat --paging=always "$file"; fi
exec less "$file"
