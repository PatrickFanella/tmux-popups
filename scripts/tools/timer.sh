#!/usr/bin/env bash
set -euo pipefail
printf 'Minutes [25]: '
read -r minutes
minutes="${minutes:-25}"
[[ "$minutes" =~ ^[0-9]+$ ]] || { printf 'Invalid minutes.\n'; sleep 1; exit 1; }
seconds=$((minutes * 60))
while (( seconds >= 0 )); do
  clear 2>/dev/null || true
  printf 'Pomodoro\n────────\n\n%02d:%02d remaining\n\nCtrl-c to stop.\n' $((seconds / 60)) $((seconds % 60))
  sleep 1
  seconds=$((seconds - 1))
done
printf '\aDone. Press Enter to close... '
read -r _ || true
