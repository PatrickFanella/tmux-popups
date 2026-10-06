#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
. "$root/scripts/lib.sh"
default_registry="$root/popups.tsv"
local_registry="$(resolve_local_registry)"

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

# Validate every source row, even one replaced by a later same-ID override.
# Buffer the result so a failure never emits a usable partial registry.
merged_tsv() (
  local registries=("$default_registry") records source line id direct menu title width height command key slot canonical
  local -a order=()
  local -A rows=() locations=() shortcuts=() target_keys=()
  [[ -r "$local_registry" ]] && registries+=("$local_registry")
  records="$(awk -F '\t' '
    /^[[:space:]]*$/ || /^[[:space:]]*#/ { next }
    $0 == "id\tdirect_key\tmenu_key\ttitle\twidth\theight\tcommand" { next }
    {
      if (NF != 7) {
        printf "%s:%d: expected 7 TSV fields, got %d\n", FILENAME, FNR, NF > "/dev/stderr"
        bad = 1; next
      }
      for (i = 1; i <= 7; i++) if ($i == "") {
        printf "%s:%d: empty required field %d\n", FILENAME, FNR, i > "/dev/stderr"
        bad = 1
      }
      print FILENAME "\t" FNR "\t" $0
    }
    END { if (bad) exit 1 }
  ' "${registries[@]}")" || return 1
  # Retain every source key, even if a later row replaces its popup ID.
  # Each probe prints the target's canonical identity before an alias can
  # replace that binding. One source-file call validates the complete batch.
  local probe table input marker binding error validated
  local -a inputs=()
  local -A key_locations=() identities=()
  probe="$(mktemp "${TMPDIR:-/tmp}/tmux-popups-keys.XXXXXXXX")"
  table="tmux-popups-keys-${probe##*/}"
  # shellcheck disable=SC2329 # Invoked by the EXIT trap in this subshell.
  cleanup_keys() {
    tmux unbind-key -a -T "$table" 2>/dev/null || true
    rm -f -- "$probe" "$probe.error"
  }
  trap cleanup_keys EXIT
  trap 'exit 130' INT
  trap 'exit 143' TERM
  # Some target versions omit a one-key table from list-keys output.
  printf 'bind-key -T "%s" F1 display-message anchor\n' "$table" >"$probe"
  printf 'bind-key -T "%s" F2 display-message anchor\n' "$table" >>"$probe"
  queue_key() {
    local input="$1" location="$2" quoted
    [[ -v key_locations["$input"] ]] && return
    key_locations["$input"]="$location"
    inputs+=("$input")
    quoted="${input//\\/\\\\}"
    quoted="${quoted//\"/\\\"}"
    quoted="${quoted//\$/\\\$}"
    printf 'bind-key -T "%s" "%s" display-message probe%d\nlist-keys -T "%s"\n' \
      "$table" "$quoted" "${#inputs[@]}" "$table" >>"$probe"
  }
  while IFS=$'\t' read -r source line id direct menu title width height command; do
    [[ -n "$source" ]] || continue
    slot="$source:$line"
    [[ "$id" =~ ^[a-zA-Z0-9_-]+$ ]] || die "$slot: unsupported popup id: $id"
    case "$title" in
      *'#{'*|*'#('*|*$'\r'*) die "$slot: unsupported tmux format or line break in title" ;;
    esac
    for key in direct menu; do
      valid_key "${!key}" || die "$slot: invalid key for popup $id $key shortcut: ${!key}"
      [[ "${!key}" == "-" ]] || queue_key "${!key}" "$slot: popup $id $key shortcut"
    done
    for key in "$width" "$height"; do
      valid_dimension "$key" || die "$slot: invalid dimension: $key"
    done
    [[ "$command" == "-" || ( -f "$root/$command" && -x "$root/$command" ) ]] || die "$slot: executable target not found or not executable: $command"
    [[ -v rows["$id"] ]] || order+=("$id")
    rows["$id"]="$id"$'\t'"$direct"$'\t'"$menu"$'\t'"$title"$'\t'"$width"$'\t'"$height"$'\t'"$command"
    locations["$id"]="$slot"
  done <<<"$records"
  local menu_key reload_key enable_vscode
  menu_key="$(tmux show-option -gqv @tmux-popups-menu-key 2>/dev/null || true)"
  reload_key="$(tmux show-option -gqv @tmux-popups-reload-key 2>/dev/null || true)"
  enable_vscode="$(tmux show-option -gqv @tmux-popups-enable-vscode 2>/dev/null || true)"
  menu_key="${menu_key:-Enter}"; reload_key="${reload_key:-R}"
  valid_key "$menu_key" && [[ "$menu_key" != "-" ]] || die "invalid menu key: unknown key $menu_key"
  valid_key "$reload_key" && [[ "$reload_key" != "-" ]] || die "invalid reload key: unknown key $reload_key"
  queue_key "$menu_key" 'built-in quick menu'
  queue_key "$reload_key" 'built-in reload'
  queue_key R 'built-in menu reload'
  queue_key q 'built-in Exit'
  [[ "$enable_vscode" == off ]] || queue_key v 'built-in vscode'
  validated=yes
  binding="$(tmux source-file "$probe" 2>"$probe.error")" || validated=no
  # Canonical key names occupy the fourth whitespace field, including Space
  # for a literal space. Unique probe markers retain each alias's identity.
  while IFS=$'\t' read -r marker canonical; do
    [[ -n "$marker" ]] && identities["$marker"]="$canonical"
  done < <(awk '$NF ~ /^probe[0-9]+$/ {print $NF "\t" $4}' <<<"$binding")
  marker=0
  for input in "${inputs[@]}"; do
    ((marker+=1))
    [[ -v identities["probe$marker"] ]] || {
      error="$(cat "$probe.error")"
      die "${key_locations[$input]}: invalid key $input on target tmux: ${error:-no canonical key returned}"
    }
    target_keys["$input"]="${identities[probe$marker]}"
  done
  [[ "$validated" == yes ]] || die "target tmux key validation failed: $(cat "$probe.error")"
  target_key() { canonical_key "${target_keys[$1]}"; }
  target_key "$menu_key"
  shortcuts["direct:$canonical"]='built-in quick menu'
  target_key "$reload_key"
  slot="direct:$canonical"
  [[ ! -v shortcuts["$slot"] ]] || die "duplicate direct shortcut: $reload_key conflicts with ${shortcuts[$slot]}"
  shortcuts["$slot"]='built-in reload'
  target_key R; shortcuts["menu:$canonical"]='built-in reload'
  target_key q; shortcuts["menu:$canonical"]='built-in Exit'
  if [[ "$enable_vscode" != off ]]; then
    target_key v; shortcuts["menu:$canonical"]='built-in vscode'
  fi
  for id in "${order[@]}"; do
    IFS=$'\t' read -r id direct menu title width height command <<<"${rows[$id]}"
    for key in direct menu; do
      [[ "${!key}" == "-" ]] && continue
      target_key "${!key}"
      slot="$key:$canonical"
      [[ ! -v shortcuts["$slot"] ]] || die "${locations[$id]}: popup $id: duplicate $key shortcut ${!key} after target tmux key normalization conflicts with ${shortcuts[$slot]}"
      shortcuts["$slot"]="${locations[$id]} ($id)"
    done
  done
  for id in "${order[@]}"; do printf '%s\n' "${rows[$id]}"; done
)

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
