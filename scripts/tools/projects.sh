#!/usr/bin/env bash
set -euo pipefail
. "$(dirname "${BASH_SOURCE[0]}")/../lib.sh"
projects_dir="${PROJECTS_DIR:-$HOME/Projects}"
case "$projects_dir" in '~'/*) projects_dir="$HOME/${projects_dir#~/}" ;; esac
exec_yazi_popup "$projects_dir"
