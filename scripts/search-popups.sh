#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
. "$root/scripts/lib.sh"

# This child runs inside a popup. The parent waits for it to close before
# dispatching the selected entry, so a second popup never replaces the picker.
if [[ "${1:-}" == --pick ]]; then
  [[ $# == 3 ]] || die 'usage: search-popups.sh --pick CHOICES SELECTION'
  exec fzf --delimiter=$'\t' --with-nth=2.. --no-multi --layout=reverse \
    --prompt='Popup> ' --header='Title | shortcuts | mode | availability' <"$2" >"$3"
fi
(($# == 0)) || die 'search-popups.sh takes no arguments; launch it through a command-mode registry entry'
origin_pane
origin_client
policy="$(availability_policy)"
rows="$("$root/scripts/list-popups.sh" --execution-tsv)"
choices=""
while IFS=$'\t' read -r id direct menu title width height command mode completion enabled deps status kind arguments; do
  [[ "$enabled" == on ]] || continue
  [[ "$kind:$command" != plugin:scripts/search-popups.sh ]] || continue
  [[ "$status" == ok || "$policy" != hide-unavailable ]] || continue
  choices+="$id"$'\t'"$title"$'\t'"prefix:$direct/menu:$menu"$'\t'"$mode"$'\t'"$status"$'\n'
done <<<"$rows"
if [[ -z "$choices" ]]; then
  tmux display-message -c "$TMUX_POPUPS_CLIENT" 'tmux-popups: no enabled launcher entries'
  exit 0
fi
shell_word() {
  local value="$1"
  value=${value//\'/\'\\\'\'}
  printf "'%s'" "$value"
}
tmux_word() {
  local value="$1"
  value=${value//\\/\\\\}; value=${value//\"/\\\"}; value=${value//\$/\\\$}
  value=${value//$'\n'/\\n}; value=${value//$'\r'/\\r}; value=${value//$'\t'/\\t}
  printf '"%s"' "$value"
}
if ! command -v fzf >/dev/null 2>&1; then
  # Literal origin data passes through display-menu and run-shell formatting.
  # Escape hashes for both layers; shell/tmux quoting preserves other bytes.
  menu_items=()
  while IFS=$'\t' read -r id direct menu title width height command mode completion enabled deps status kind arguments; do
    [[ "$enabled" == on ]] || continue
    [[ "$kind:$command" != plugin:scripts/search-popups.sh ]] || continue
    [[ "$status" == ok || "$policy" != hide-unavailable ]] || continue
    if [[ "$status" != ok && "$policy" != ignore ]]; then
      menu_items+=("-$title [$status]" "" "")
      continue
    fi
    action=""
    for value in "$root/scripts/run-popup.sh" "$id" --launch "$TMUX_POPUPS_CLIENT" \
      "$TMUX_POPUPS_SESSION" "$TMUX_POPUPS_WINDOW" "$TMUX_POPUPS_PANE" "$TMUX_POPUPS_DIRECTORY"; do
      action+="$(shell_word "$value") "
    done
    action=${action//#/####}
    [[ "$menu" != - ]] || menu=""
    menu_items+=("$title [$mode]" "$menu" "run-shell $(tmux_word "$action")")
  done <<<"$rows"
  menu_items+=(Exit q "")
  exec tmux display-menu -c "$TMUX_POPUPS_CLIENT" -t "$TMUX_POPUPS_PANE" \
    -T ' Quick Menu (fzf unavailable) ' -x C -y C "${menu_items[@]}"
fi

scratch="$(mktemp -d "${TMPDIR:-/tmp}/tmux-popups-search.XXXXXXXX")"
cleanup() { rm -rf -- "$scratch"; }
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
printf '%s' "$choices" >"$scratch/choices"
picker="$(shell_word "$root/scripts/search-popups.sh") --pick $(shell_word "$scratch/choices") $(shell_word "$scratch/selection")"
# display-popup performs one format expansion on its shell command.
picker=${picker//#/##}
status=0
tmux display-popup -c "$TMUX_POPUPS_CLIENT" -t "$TMUX_POPUPS_PANE" \
  -T ' Search popups ' -w 90% -h 80% -E "$picker" || status=$?
case "$status" in
  0) ;;
  1|130) exit 0 ;;
  *) die "search picker failed (status $status)" ;;
esac
selection="$(cat "$scratch/selection" 2>/dev/null || true)"
[[ -n "$selection" ]] || exit 0
[[ "$selection" != *$'\n'* ]] || die 'search picker returned multiple selections'
id="${selection%%$'\t'*}"
[[ "$id" =~ ^[a-zA-Z0-9_-]+$ ]] || die 'search picker returned an invalid entry'
# A substitute or unusual fzf configuration must not dispatch an unlisted ID.
awk -F '\t' -v wanted="$id" '$1 == wanted {found=1} END {exit !found}' "$scratch/choices" || die 'search picker returned an unlisted entry'
cleanup
trap - EXIT
exec "$root/scripts/run-popup.sh" "$id" --launch "$TMUX_POPUPS_CLIENT" \
  "$TMUX_POPUPS_SESSION" "$TMUX_POPUPS_WINDOW" "$TMUX_POPUPS_PANE" "$TMUX_POPUPS_DIRECTORY"
