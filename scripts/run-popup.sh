#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
id="${1:?popup id required}"
. "$root/scripts/lib.sh"
if [[ "${2:-}" == --launch ]]; then
  [[ $# == 7 ]] || die "launch requires client, session, window, pane and directory"
  export TMUX_POPUPS_CLIENT="$3" TMUX_POPUPS_SESSION="$4"
  export TMUX_POPUPS_WINDOW="$5" TMUX_POPUPS_PANE="$6" TMUX_POPUPS_DIRECTORY="$7"
  origin_pane
  origin_client
else
  # CLI callers may supply the contract; TMUX_PANE never identifies a client.
  if [[ -z "${TMUX_POPUPS_PANE:-}" && -n "${TMUX_PANE:-}" ]]; then
    export TMUX_POPUPS_PANE="$TMUX_PANE"
    TMUX_POPUPS_SESSION="$(tmux display-message -p -t "$TMUX_PANE" '#{session_id}')"
    TMUX_POPUPS_WINDOW="$(tmux display-message -p -t "$TMUX_PANE" '#{window_id}')"
    export TMUX_POPUPS_SESSION TMUX_POPUPS_WINDOW
  fi
  export TMUX_POPUPS_DIRECTORY="${TMUX_POPUPS_DIRECTORY:-$PWD}"
fi
cd -- "$TMUX_POPUPS_DIRECTORY" || die "origin directory is unavailable: $TMUX_POPUPS_DIRECTORY"
rows="$("$root/scripts/list-popups.sh" --state-tsv)"

row="$(
  awk -F '\t' -v wanted="$id" '
      $1 == wanted { print; found = 1 }
      END { exit found ? 0 : 1 }
    ' <<<"$rows"
)" || row=""

if [[ -n "$row" ]]; then
  IFS=$'\t' read -r _popup_id _direct_key _menu_key _title _width _height command mode completion enabled deps status <<<"$row"

  [[ "$enabled" == on ]] || die "popup $id is disabled; set @tmux-popups-$id-enabled on and reload"
  policy="$(availability_policy)"
  if [[ "$status" != ok && "$policy" != ignore ]]; then
    message="tmux-popups: $id unavailable ($status); see scripts/list-popups.sh --deps"
    if [[ "${2:-}" == --launch ]]; then tmux display-message -c "$TMUX_POPUPS_CLIENT" "$message"; fi
    printf '%s\n' "$message" >&2
    exit 127
  fi

  if [[ "$mode" == command ]]; then
    if [[ "$completion" == background ]]; then
      # No terminal input/output and no completion status after launch.
      "$root/$command" </dev/null >/dev/null 2>&1 &
      exit 0
    fi
    exec "$root/$command"
  fi

  if [[ "${2:-}" == --launch ]]; then
    launch_environment=()
    for variable in CLIENT SESSION WINDOW PANE DIRECTORY; do
      name="TMUX_POPUPS_$variable"
      launch_environment+=(-e "$name=${!name}")
    done
    # Quote the executable for the one shell boundary in tmux's launch command.
    executable=${root//\'/\'\\\'\'}
    launch_command="'$executable/scripts/run-popup.sh' $id"
    # tmux treats -c/-d as formats, so protect literal hashes in path data.
    launch_directory=${TMUX_POPUPS_DIRECTORY//#/##}
    case "$mode" in
      window)
        exec tmux new-window -t "$TMUX_POPUPS_SESSION:" -c "$launch_directory" \
          "${launch_environment[@]}" -n "$_title" "$launch_command" ;;
    esac
    case "$command" in
      scripts/tools/yazi.sh|scripts/tools/home.sh|scripts/tools/projects.sh|scripts/tools/downloads.sh)
        tmux display-message -c "$TMUX_POPUPS_CLIENT" 'tmux-popups: warning: yazi popup mode may trigger terminal response timeout' ;;
    esac
    [[ "$_width" == - ]] && _width="$(tmux show-option -gqv @tmux-popups-default-width)"
    [[ "$_height" == - ]] && _height="$(tmux show-option -gqv @tmux-popups-default-height)"
    exec tmux display-popup -c "$TMUX_POPUPS_CLIENT" -t "$TMUX_POPUPS_PANE" \
      -d "$launch_directory" "${launch_environment[@]}" -T " $_title " \
      -w "${_width:-80%}" -h "${_height:-80%}" -E "$launch_command"
  fi

  if [[ "$command" == "-" ]]; then
    shell="$(shell_command)" || die "no usable shell: ${SHELL:-bash}"
    exec "$shell"
  fi

  exec "$root/$command"
fi

printf 'tmux-popups: unknown popup id: %s\n' "$id" >&2
printf 'Press Enter to close...'
read -r _ || true
exit 1
