#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
default_registry="$root/popups.tsv"
local_registry_default="${XDG_CONFIG_HOME:-$HOME/.config}/tmux-popups/popups.local.tsv"
local_registry="${TMUX_POPUPS_LOCAL_REGISTRY:-$local_registry_default}"

usage() {
  cat <<'EOF'
Usage: scripts/list-popups.sh [--tsv|--pretty|--deps|--deps-tsv]

Merges popups.tsv with an optional local registry. Later rows with the same id
override earlier rows. Blank lines and # comments are ignored.
EOF
}

deps_for_id() {
  case "$1" in
    help) printf 'tmux less|cat' ;;
    chat) printf 'ocq node' ;;
    opencode) printf 'opencode' ;;
    shell) printf 'shell' ;;
    tasks) printf 'task' ;;
    notes) printf 'editor' ;;
    docs) printf 'tldr|man less|cat' ;;
    calendar) printf 'khal|cal' ;;
    calc) printf 'python3' ;;
    ssh) printf 'ssh fzf' ;;
    clipboard) printf 'cliphist fzf wl-copy' ;;
    info) printf 'curl newsboat' ;;
    timer) printf 'shell' ;;
    logs) printf 'journalctl tail' ;;
    watch) printf 'watch' ;;
    markdown) printf 'fzf glow|bat|less' ;;
    lazygit) printf 'lazygit' ;;
    yazi|home|projects|downloads) printf 'yazi' ;;
    ferrosonic) printf 'ferrosonic' ;;
    keys) printf 'tmux less|cat' ;;
    zshrc|tmux-local) printf 'editor' ;;
    sessions) printf 'tmux' ;;
    *) printf '-' ;;
  esac
}

have_one() {
  local group="$1" item
  IFS='|' read -r -a items <<<"$group"
  for item in "${items[@]}"; do
    case "$item" in
      shell) [[ -n "${SHELL:-}" ]] && return 0 ;;
      editor)
        if [[ -n "${EDITOR:-}" ]] || command -v nvim >/dev/null 2>&1 || command -v vim >/dev/null 2>&1 || command -v vi >/dev/null 2>&1; then
          return 0
        fi
        ;;
      cat) command -v cat >/dev/null 2>&1 && return 0 ;;
      *) command -v "$item" >/dev/null 2>&1 && return 0 ;;
    esac
  done
  return 1
}

deps_status() {
  local deps="$1" dep missing=()
  [[ -z "$deps" || "$deps" == "-" ]] && { printf 'ok'; return; }
  for dep in $deps; do
    if ! have_one "$dep"; then
      missing+=("$dep")
    fi
  done
  if ((${#missing[@]} == 0)); then
    printf 'ok'
  else
    printf 'missing:%s' "$(IFS=,; printf '%s' "${missing[*]}")"
  fi
}

merged_tsv() {
  awk -F '\t' '
    BEGIN { OFS = FS }
    /^[[:space:]]*$/ || /^[[:space:]]*#/ { next }
    NF < 7 { next }
    $1 == "id" { next }
    {
      id = $1
      row[id] = $0
      if (!(id in seen)) {
        order[++count] = id
        seen[id] = 1
      }
    }
    END {
      for (i = 1; i <= count; i++) {
        id = order[i]
        if (row[id] != "") print row[id]
      }
    }
  ' "$default_registry" "$local_registry" 2>/dev/null
}

mode="${1:---pretty}"
case "$mode" in
  --help|-h) usage ;;
  --tsv) merged_tsv ;;
  --pretty)
    printf '%-14s %-9s %-7s %-18s %-9s %-9s %s\n' id direct menu title width height command
    merged_tsv | while IFS=$'\t' read -r id direct_key menu_key title width height command; do
      printf '%-14s %-9s %-7s %-18s %-9s %-9s %s\n' "$id" "$direct_key" "$menu_key" "$title" "$width" "$height" "$command"
    done
    ;;
  --deps|--deps-tsv)
    merged_tsv | while IFS=$'\t' read -r id direct_key menu_key title width height command; do
      deps="$(deps_for_id "$id")"
      status="$(deps_status "$deps")"
      if [[ "$mode" == "--deps-tsv" ]]; then
        printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$id" "$direct_key" "$menu_key" "$title" "$width" "$height" "$command" "$deps" "$status"
      else
        printf '%-14s %-18s %-24s %s\n' "$id" "$title" "$deps" "$status"
      fi
    done
    ;;
  *) usage >&2; exit 2 ;;
esac
