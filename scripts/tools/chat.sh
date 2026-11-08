#!/usr/bin/env bash
set -u
# shellcheck source=../lib.sh
# shellcheck disable=SC2154
. "$(dirname "${BASH_SOURCE[0]}")/../lib.sh"
reset=""; bold=""; dim=""; red=""; green=""; cyan=""; magenta=""
setup_colors

model="${OCQ_MODEL:-openai/gpt-5.4-mini}"
session_id=""
resp=""
debug_log="${TMUX_POPUPS_CHAT_DEBUG_LOG:-/tmp/tmux-popups-chat-debug.log}"

debug_input() {
  [[ "${TMUX_POPUPS_CHAT_DEBUG:-}" == "1" ]] || return 0
  local label="$1" value="$2" bytes
  bytes="$(printf '%s' "$value" | od -An -tx1 | tr -d '\n' | sed 's/^ *//')"
  printf '%s raw=%q bytes=%s norm=%q\n' "$label" "$value" "$bytes" "$(normalize_input "$value")" >>"$debug_log"
}

if { true </dev/tty; } 2>/dev/null; then
  exec </dev/tty
fi

normalize_input() {
  local value="$1"
  value="${value//$'\r'/}"
  value="${value//$'\e[200~'/}"
  value="${value//$'\e[201~'/}"
  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  printf '%s' "$value"
}

is_quit() {
  case "$(normalize_input "$1")" in
    q|Q|quit|/quit|exit|/exit) return 0 ;;
    *) return 1 ;;
  esac
}

close_popup_and_exit() {
  # Let the launcher's normal exit handling close this view. Explicitly closing
  # our own popup first delivers HUP before the successful exit can complete.
  exit 0
}

# Request files and process ownership live for the entire script, including traps.
require_cmd ocq
require_cmd node
request_dir="$(mktemp -d "${TMPDIR:-/tmp}/tmux-popups-chat.XXXXXXXX")" || exit 1
request_pid=""
stop_request() {
  if [[ -n "$request_pid" ]]; then
    # Stop only this request's group, including descendants of an exited leader.
    if kill -0 -- "-$request_pid" 2>/dev/null; then
      kill -TERM -- "-$request_pid" 2>/dev/null || true
      sleep 0.1
      kill -KILL -- "-$request_pid" 2>/dev/null || true
    fi
    wait "$request_pid" 2>/dev/null || true
    request_pid=""
  fi
}
cleanup() {
  stop_request
  rm -rf -- "$request_dir"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
trap 'exit 129' HUP

ocq_with_spinner() {
  local prompt="$1" status frame frames i
  frames=$'|/-\\'
  i=0
  set -m
  ocq "${args[@]}" "$prompt" >"$request_dir/json" 2>"$request_dir/error" </dev/null &
  request_pid=$!
  set +m
  while kill -0 "$request_pid" 2>/dev/null; do
    frame="${frames:i++%${#frames}:1}"
    printf '\r%s%sThinking%s %s' "$dim" "$cyan" "$reset" "$frame" >&2
    sleep 0.12
  done
  wait "$request_pid"
  status=$?
  stop_request
  printf '\r\033[2K' >&2
  if (( status != 0 )); then
    printf 'ocq failed (status %s)\n' "$status" >&2
    return 1
  fi
  # Parse once. Invalid responses never replace the last valid session/answer.
  if ! node - "$request_dir" <<'JS'
const fs = require('fs');
const dir = process.argv[2];
try {
  const data = JSON.parse(fs.readFileSync(dir + '/json', 'utf8'));
  if (!data || typeof data.sessionID !== 'string' || !data.sessionID.trim() ||
      typeof data.text !== 'string' || !data.text.trim() ||
      data.sessionID.includes('\0') || data.text.includes('\0')) throw Error();
  fs.writeFileSync(dir + '/session', data.sessionID);
  fs.writeFileSync(dir + '/response', data.text);
} catch {
  process.exitCode = 1;
}
JS
  then
    printf 'ocq returned an invalid or empty response; try again.\n' >&2
    return 1
  fi
  session_id="$(cat "$request_dir/session")"
  resp="$(cat "$request_dir/response"; printf '.')"
  resp="${resp%.}"
}

clear 2>/dev/null || true
printf '%s%s%s %s%s%s\n' "$bold" "$magenta" "Quick Chat" "$dim" "· $model" "$reset"
printf '%s/exit or /quit to close · c copies · cq copies+quits · q quits · Ctrl-C cancels the request and closes%s\n' "$dim" "$reset"
rule

while true; do
  printf '%s%sYou%s %s›%s ' "$bold" "$cyan" "$reset" "$dim" "$reset"
  IFS= read -r line || break
  debug_input prompt "$line"
  line="$(normalize_input "$line")"
  [[ -z "$line" ]] && break
  is_quit "$line" && close_popup_and_exit

  args=(--json --model "$model")
  [[ -n "$session_id" ]] && args+=(--session "$session_id")

  if ! ocq_with_spinner "$line"; then
    echo
    continue
  fi

  printf '\n%s%sAssistant%s %s›%s\n' "$bold" "$green" "$reset" "$dim" "$reset"
  printf '%s\n\n' "$resp"
  rule

  printf '%sEnter%s continue  %sc%s copy  %scq%s copy+quit  %sq%s/%sexit%s quit %s›%s ' "$dim" "$reset" "$cyan" "$reset" "$cyan" "$reset" "$cyan" "$reset" "$cyan" "$reset" "$dim" "$reset"
  IFS= read -r key || break
  debug_input action "$key"
  key="$(normalize_input "$key")"
  is_quit "$key" && close_popup_and_exit
  case "$key" in
    c|C|copy)
      if printf '%s' "$resp" | copy_text; then
        printf '%s%sCopied.%s\n' "$green" "$bold" "$reset"
      else
        printf 'Copy failed; response is still available.\n' >&2
      fi
      echo ;;
    cq|CQ|cQ|Cq|copyquit|copy-quit)
      if printf '%s' "$resp" | copy_text; then close_popup_and_exit
      else printf 'Copy failed; chat remains open.\n' >&2; fi ;;
    *) echo ;;
  esac
done
