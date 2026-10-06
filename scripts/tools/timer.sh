#!/usr/bin/env bash
set -euo pipefail

# Limit timers to one day and validate before Bash arithmetic can overflow.
max_minutes=1440
sleep_pid=""
cleanup() {
  if [[ -n "$sleep_pid" ]]; then
    kill "$sleep_pid" 2>/dev/null || true
    wait "$sleep_pid" 2>/dev/null || true
    sleep_pid=""
  fi
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM HUP

printf 'Minutes [25] (1-%s): ' "$max_minutes"
read -r minutes || exit 0
minutes="${minutes:-25}"
if [[ ! "$minutes" =~ ^[0-9]+$ ]]; then
  printf 'Invalid minutes: enter a whole number from 1 to %s.\n' "$max_minutes" >&2
  exit 1
fi
# Strip leading zeroes before the length check; 08 and 09 are decimal values.
minutes="${minutes#"${minutes%%[!0]*}"}"
minutes="${minutes:-0}"
if (( ${#minutes} > 4 )) || (( 10#$minutes < 1 || 10#$minutes > max_minutes )); then
  printf 'Unsupported minutes: enter a whole number from 1 to %s.\n' "$max_minutes" >&2
  exit 1
fi
seconds=$((10#$minutes * 60))
while (( seconds > 0 )); do
  clear 2>/dev/null || true
  printf 'Pomodoro\n────────\n\n%02d:%02d remaining\n\nCtrl-c to stop.\n' $((seconds / 60)) $((seconds % 60))
  sleep 1 &
  sleep_pid=$!
  wait "$sleep_pid"
  sleep_pid=""
  seconds=$((seconds - 1))
done
printf '\aDone. Press Enter to close... '
read -r _ || true
