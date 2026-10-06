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

if [[ -r /dev/tty ]]; then
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
  if [[ -n "${TMUX:-}" ]]; then
    tmux display-popup -C 2>/dev/null || true
  fi
  exit 0
}

# These belong to this launch, including while a request is running.
request_dir=""
request_pid=""
cleanup_request() {
  if [[ -n "$request_pid" ]]; then
    kill -TERM -- "-$request_pid" 2>/dev/null || true
    sleep 0.05
    kill -KILL -- "-$request_pid" 2>/dev/null || true
    wait "$request_pid" 2>/dev/null || true
    request_pid=""
  fi
  [[ -z "$request_dir" ]] || rm -rf -- "$request_dir"
  request_dir=""
}
trap cleanup_request EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
trap 'exit 129' HUP

request_error() {
  printf '%s%s%s%s\n\n' "$red" "$bold" "$1" "$reset" >&2
}

ocq_with_spinner() {
  local prompt="$1" status frame frames i
  request_dir="$(mktemp -d)" || { request_error "Cannot create request files."; return 1; }
  frames=$'|/-\\'
  i=0

  # A new process group lets interruption stop this request and its children.
  setsid ocq "${args[@]}" "$prompt" >"$request_dir/json" 2>"$request_dir/error" </dev/null &
  request_pid=$!
  while kill -0 "$request_pid" 2>/dev/null; do
    frame="${frames:i++%${#frames}:1}"
    printf '\r%s%sThinking%s %s' "$dim" "$cyan" "$reset" "$frame" >&2
    sleep 0.12
  done
  wait "$request_pid"
  status=$?
  # Also stop children left behind by a provider that has already exited.
  printf '\r\033[2K' >&2
  if (( status != 0 )); then
    request_error "ocq failed (exit $status). Try again."
    cleanup_request
    return 1
  fi

  # Validate once. NUL separators preserve newlines and arbitrary response text.
  if ! node -e '
    const fs = require("fs");
    try {
      const data = JSON.parse(fs.readFileSync(process.argv[1], "utf8"));
      if (!data || typeof data.sessionID !== "string" || !data.sessionID.trim() ||
          typeof data.text !== "string" || !data.text.trim() ||
          data.sessionID.includes("\u0000") || data.text.includes("\u0000")) throw Error();
      process.stdout.write(data.sessionID + "\u0000" + data.text + "\u0000");
    } catch (_) { process.exitCode = 1; }
  ' "$request_dir/json" >"$request_dir/validated" 2>/dev/null; then
    request_error "Invalid or empty ocq response. Try again."
    cleanup_request
    return 1
  fi
  {
    IFS= read -r -d '' session_id
    IFS= read -r -d '' resp
  } <"$request_dir/validated"
  cleanup_request
}

for dependency in ocq node setsid; do
  if ! command -v "$dependency" >/dev/null 2>&1; then
    request_error "Required chat dependency missing: $dependency."
    exit 1
  fi
done

clear 2>/dev/null || true
printf '%s%s%s %s%s%s\n' "$bold" "$magenta" "Quick Chat" "$dim" "· $model" "$reset"
printf '%s/exit or /quit to close · c copies · cq copies+quits · q quits · Ctrl-C cancels%s\n' "$dim" "$reset"
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
        request_error "Copy failed. Response is still available above."
      fi
      echo ;;
    cq|CQ|cQ|Cq|copyquit|copy-quit)
      if printf '%s' "$resp" | copy_text; then
        close_popup_and_exit
      else
        request_error "Copy failed. Response is still available above."
      fi ;;
    *) echo ;;
  esac
done
