#!/usr/bin/env bash
set -euo pipefail
. "$(dirname "${BASH_SOURCE[0]}")/../lib.sh"

files=(
  "$HOME/.zshrc"
  "$HOME/.zprofile"
  "$HOME/.zshenv"
  "$HOME/.config/tmux/tmux.local.conf"
  "$HOME/.config/tmux/tmux.conf"
  "$HOME/.config/git/config"
  "$HOME/.config/opencode/AGENTS.md"
)

existing=()
for file in "${files[@]}"; do
  [[ -e "$file" ]] && existing+=("$file")
done

if command -v fzf >/dev/null 2>&1; then
  selected="$(printf '%s\n' "${existing[@]}" | fzf --prompt='dotfiles> ' --height=100% --border --reverse)"
else
  printf 'Dotfiles:\n\n'
  select selected in "${existing[@]}"; do
    [[ -n "${selected:-}" ]] && break
  done
fi

[[ -n "${selected:-}" ]] || exit 0
open_editor "$selected"
