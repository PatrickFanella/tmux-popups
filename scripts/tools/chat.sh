#!/usr/bin/env bash
set -u
# shellcheck source=../lib.sh
# shellcheck disable=SC2154
. "$(dirname "${BASH_SOURCE[0]}")/../lib.sh"
setup_colors

model="${OCQ_MODEL:-openai/gpt-5.4-mini}"
session_id=""
resp=""

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

clear 2>/dev/null || true
printf '%s%s%s %s%s%s\n' "$bold" "$magenta" "Quick Chat" "$dim" "· $model" "$reset"
printf '%s/exit or /quit to close · c copies last reply · q quits%s\n' "$dim" "$reset"
rule

while true; do
  printf '%s%sYou%s %s›%s ' "$bold" "$cyan" "$reset" "$dim" "$reset"
  read -r line || break
  [[ -z "$line" || "$line" == "/exit" || "$line" == "/quit" ]] && break

  args=(--json --model "$model")
  [[ -n "$session_id" ]] && args+=(--session "$session_id")

  if ! json=$(ocq "${args[@]}" "$line"); then
    printf '%s%socq failed%s\n' "$red" "$bold" "$reset" >&2
    echo
    continue
  fi

  session_id=$(printf '%s' "$json" | json_field sessionID)
  resp=$(printf '%s' "$json" | json_field text)

  printf '\n%s%sAssistant%s %s›%s\n' "$bold" "$green" "$reset" "$dim" "$reset"
  printf '%s\n\n' "$resp"
  rule

  printf '%sEnter%s continue  %sc%s copy  %sq%s quit %s›%s ' "$dim" "$reset" "$cyan" "$reset" "$cyan" "$reset" "$dim" "$reset"
  read -r key || break
  case "$key" in
    c|C|copy) printf '%s' "$resp" | copy_text && printf '%s%sCopied.%s\n' "$green" "$bold" "$reset"; echo ;;
    q|Q|quit|/quit|exit|/exit) break ;;
    *) echo ;;
  esac
done
