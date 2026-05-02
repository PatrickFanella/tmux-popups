#!/usr/bin/env bash

TMUX_POPUPS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

has_tty() { [[ -t 1 && "${NO_COLOR:-}" == "" ]]; }

setup_colors() {
  if has_tty; then
    reset=$'\033[0m'; bold=$'\033[1m'; dim=$'\033[2m'
    red=$'\033[31m'; green=$'\033[32m'; cyan=$'\033[36m'; magenta=$'\033[35m'
  else
    reset=""; bold=""; dim=""; red=""; green=""; cyan=""; magenta=""
  fi
}

pause() {
  printf '\nPress Enter to continue... '
  read -r _ || true
}

die() {
  printf 'error: %s\n' "$*" >&2
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "$1 not found"
}

maybe_exec_cmd() {
  local cmd="$1"
  shift
  if command -v "$cmd" >/dev/null 2>&1; then
    exec "$cmd" "$@"
  fi
  printf '%s not found\n' "$cmd"
  pause
  exit 127
}

open_editor() {
  exec "${EDITOR:-nvim}" "$@"
}

copy_text() {
  if command -v wl-copy >/dev/null 2>&1; then
    wl-copy
  elif command -v wlcopy >/dev/null 2>&1; then
    wlcopy
  elif command -v xclip >/dev/null 2>&1; then
    xclip -selection clipboard
  else
    printf 'No clipboard tool found: install wl-copy, wlcopy, or xclip.\n' >&2
    return 1
  fi
}

rule() {
  setup_colors
  printf '%s%s%s\n' "$dim" "────────────────────────────────────────" "$reset"
}
