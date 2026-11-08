#!/usr/bin/env bash
set -euo pipefail
. "$(dirname "${BASH_SOURCE[0]}")/../lib.sh"
action="${1:?usage: project-action.sh git|shell|notes|code [arguments]}"
shift
case "$action" in git|shell|notes|code) ;; *) die "unknown project action: $action" ;; esac
directory="${TMUX_POPUPS_DIRECTORY:-$PWD}"
cd -- "$directory" || die "invoking directory is unavailable: $directory"
if [[ "$action" == shell ]]; then
  shell="$(shell_command)" || die "no usable shell: ${SHELL:-bash}"
  exec "$shell" "$@"
fi
# Keep the Git output terminator separate from literal directory bytes. Non-Git
# directories (and installations without Git) use the invoking directory.
if project="$(git rev-parse --show-toplevel 2>/dev/null && printf '.')"; then
  project="${project%.}"
  project="${project%$'\n'}"
else
  project="$directory"
fi
cd -- "$project" || die "project directory is unavailable: $project"
case "$action" in
  git)
    require_cmd git
    exec git status --short --branch "$@" ;;
  notes)
    (($# <= 1)) || die 'notes accepts one optional file path'
    note="${1:-${TMUX_POPUPS_PROJECT_NOTES:-NOTES.md}}"
    note="$(expand_home_path "$note"; printf '.')"; note="${note%.}"
    [[ "$note" == /* ]] || note="$PWD/$note"
    editor="$(editor_command)" || die "no usable editor: ${EDITOR:-nvim|vim|vi}"
    parent="${note%/*}"
    mkdir -p -- "${parent:-/}"
    exec "$editor" "$note" ;;
  code)
    tool="${1-opencode}"
    if (($#)); then shift; fi
    [[ -n "$tool" ]] || die 'coding tool command is empty'
    maybe_exec_cmd "$tool" "$@" ;;
esac
