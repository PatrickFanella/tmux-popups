#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"
files=(tmux-popups.tmux scripts/*.sh scripts/tools/*.sh tests/*.sh)
for file in "${files[@]}"; do
  bash -n "$file"
done
shellcheck -x -e SC1091,SC2034,SC2086 "${files[@]}"
tests/run.sh
