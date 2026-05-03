#!/usr/bin/env bash
set -euo pipefail
. "$(dirname "${BASH_SOURCE[0]}")/../lib.sh"

ensure_newsboat_urls() {
  mkdir -p "$HOME/.newsboat"
  if [[ ! -f "$HOME/.newsboat/urls" ]]; then
    cat >"$HOME/.newsboat/urls" <<'EOF'
# Add RSS/Atom feed URLs here, one per line.
# https://hnrss.org/frontpage
# https://www.archlinux.org/feeds/news/
EOF
  fi
}

while true; do
  clear 2>/dev/null || true
  printf 'Info\n────\n\n[w] weather  [n] newsboat  [e] edit feeds  [q] quit\n> '
  read -r action || exit 0
  case "$action" in
    w|weather) curl -fsSL 'https://wttr.in/?0' | less -R ;;
    n|news) ensure_newsboat_urls; require_cmd newsboat; newsboat || pause ;;
    e|edit) ensure_newsboat_urls; "${EDITOR:-nvim}" "$HOME/.newsboat/urls" ;;
    q|quit|/quit|exit|/exit) exit 0 ;;
  esac
done
