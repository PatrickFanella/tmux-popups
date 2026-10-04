#!/usr/bin/env bash
set -euo pipefail
. "$(dirname "${BASH_SOURCE[0]}")/../lib.sh"
projects_dir="${PROJECTS_DIR:-$HOME/Projects}"
projects_dir="$(expand_home_path "$projects_dir")"
exec_yazi_popup "$projects_dir"
