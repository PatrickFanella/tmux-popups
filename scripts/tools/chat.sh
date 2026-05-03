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

json_field() {
  local field="$1"
  node -e '
    const field = process.argv[1]
    let input = ""
    process.stdin.setEncoding("utf8")
    process.stdin.on("data", chunk => input += chunk)
    process.stdin.on("end", () => {
      const data = JSON.parse(input)
      process.stdout.write(data[field] || "")
    })
  ' "$field"
}

ocq_with_spinner() {
  local prompt="$1" json_file err_file pid status frame frames i
  json_file="$(mktemp)"
  err_file="$(mktemp)"
  trap 'rm -f "$json_file" "$err_file"' EXIT INT TERM
  frames=$'|/-\\'
  i=0

  ocq "${args[@]}" "$prompt" >"$json_file" 2>"$err_file" </dev/null &
  pid=$!

  while kill -0 "$pid" 2>/dev/null; do
    frame="${frames:i++%${#frames}:1}"
    printf '\r%s%sThinking%s %s' "$dim" "$cyan" "$reset" "$frame" >&2
    sleep 0.12
  done

  wait "$pid"
  status=$?
  printf '\r\033[2K' >&2

  if (( status != 0 )); then
    [[ -s "$err_file" ]] && cat "$err_file" >&2
    rm -f "$json_file" "$err_file"
    return "$status"
  fi

  cat "$json_file"
  rm -f "$json_file" "$err_file"
}

clear 2>/dev/null || true
printf '%s%s%s %s%s%s\n' "$bold" "$magenta" "Quick Chat" "$dim" "· $model" "$reset"
printf '%s/exit or /quit to close · c copies · cq copies+quits · q quits%s\n' "$dim" "$reset"
rule

while true; do
  printf '%s%sYou%s %s›%s ' "$bold" "$cyan" "$reset" "$dim" "$reset"
  read -r line || break
  debug_input prompt "$line"
  line="$(normalize_input "$line")"
  [[ -z "$line" ]] && break
  is_quit "$line" && close_popup_and_exit

  args=(--json --model "$model")
  [[ -n "$session_id" ]] && args+=(--session "$session_id")

  if ! json=$(ocq_with_spinner "$line"); then
    printf '%s%socq failed%s\n' "$red" "$bold" "$reset" >&2
    echo
    continue
  fi

  session_id=$(printf '%s' "$json" | json_field sessionID)
  resp=$(printf '%s' "$json" | json_field text)

  printf '\n%s%sAssistant%s %s›%s\n' "$bold" "$green" "$reset" "$dim" "$reset"
  printf '%s\n\n' "$resp"
  rule

  printf '%sEnter%s continue  %sc%s copy  %scq%s copy+quit  %sq%s/%sexit%s quit %s›%s ' "$dim" "$reset" "$cyan" "$reset" "$cyan" "$reset" "$cyan" "$reset" "$cyan" "$reset" "$dim" "$reset"
  IFS= read -r key || break
  debug_input action "$key"
  key="$(normalize_input "$key")"
  is_quit "$key" && close_popup_and_exit
  case "$key" in
    c|C|copy) printf '%s' "$resp" | copy_text && printf '%s%sCopied.%s\n' "$green" "$bold" "$reset"; echo ;;
    cq|CQ|cQ|Cq|copyquit|copy-quit) printf '%s' "$resp" | copy_text && close_popup_and_exit ;;
    *) echo ;;
  esac
done
