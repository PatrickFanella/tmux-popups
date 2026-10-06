#!/usr/bin/env bash
set -euo pipefail

# Ownership belongs to this tmux server, independently of cache/checkouts.
config="${1:?generated config required}"
scratch="$(mktemp -d)"
table="tmux-popups-stage-${scratch##*/}"
locked=no
applying=no
cleanup() {
  local status=$?
  if [[ "$applying" == yes ]]; then
    # Restore only the slots this transition touched, plus its ownership state.
    if ! tmux source-file "$scratch/rollback"; then
      printf 'tmux-popups: binding rollback failed\n' >&2
    fi
  fi
  tmux unbind-key -a -T "$table" 2>/dev/null || true
  rm -rf "$scratch"
  if [[ "$locked" == yes ]]; then tmux wait-for -U tmux-popups-bindings; fi
  return "$status"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

tmux wait-for -L tmux-popups-bindings
locked=yes
# Snapshot the input so overlapping cache writers cannot alter our transaction.
cp "$config" "$scratch/input"
tmux source-file -n "$scratch/input"
# Execute bind commands only in a disposable table. This validates keys and
# commands without running their actions or changing any effective user key.
while IFS= read -r line; do
  if [[ "$line" == 'bind-key "'* ]]; then
    printf 'bind-key -T "%s" %s\n' "$table" "${line#bind-key }"
  elif [[ -n "$line" && "$line" != \#* ]]; then
    printf 'tmux-popups: unexpected generated config command\n' >&2
    exit 1
  fi
done <"$scratch/input" >"$scratch/stage"
tmux source-file "$scratch/stage"

option() { tmux show-option -gqv "$1"; }
q() {
  local value="$1"
  value=${value//\\/\\\\}
  value=${value//\"/\\\"}
  value=${value//\$/\\\$}
  value=${value//$'\n'/\\n}
  value=${value//$'\r'/\\r}
  value=${value//$'\t'/\\t}
  printf '"%s"' "$value"
}
# Newer tmux exposes raw binding fields, including notes, through -F.
# Use a private delimiter so multiline notes remain literal data.
read_modern_table() {
  local name="$1" dump key repeat note command field
  local delimiter="__${table}__"
  local -a fields
  if ! dump="$(tmux list-keys -T "$name" -F "#{key_string}${delimiter}#{key_repeat}${delimiter}#{key_note}${delimiter}#{key_command}${delimiter}" 2>"$scratch/error")"; then
    if [[ "$(cat "$scratch/error")" == "table $name doesn't exist" ]]; then snapshot=(); return; fi
    cat "$scratch/error" >&2
    return 1
  fi
  snapshot=()
  while [[ -n "$dump" ]]; do
    fields=()
    for field in key repeat note command; do
      [[ "$dump" == *"$delimiter"* ]] || return 1
      fields+=("${dump%%"$delimiter"*}")
      dump="${dump#*"$delimiter"}"
    done
    key="$(q "${fields[0]}")"; repeat="${fields[1]}"; note="${fields[2]}"; command="${fields[3]}"
    [[ "$repeat" == 0 || "$repeat" == 1 ]] || return 1
    snapshot["$key"]="bind-key -T prefix -N $(q "$note") $key $command"
    if [[ "$repeat" == 1 ]]; then snapshot["$key"]="bind-key -r -T prefix -N $(q "$note") $key $command"; fi
    dump="${dump#$'\n'}"
  done
}
modern=no
[[ "$(tmux list-commands list-keys)" == *'-F '* ]] && modern=yes
# Default list-keys serializes commands but pads columns and omits notes.
# Normalize its header and capture notes separately, including multiline notes.
# This also works on tmux 3.3a, which has no list-keys -F.
read_table() {
  local name="$1" line repeat key token command note lookup character source_table
  if [[ "$modern" == yes ]]; then read_modern_table "$name"; return; fi
  local pattern='^bind-key[[:space:]]+(-r[[:space:]]+)?-T[[:space:]]+([^[:space:]]+)[[:space:]]+([^[:space:]]+)[[:space:]]+(.*)$'
  tmux list-keys >"$scratch/lines"
  snapshot=()
  while IFS= read -r line; do
    [[ "$line" =~ $pattern ]] || { printf 'tmux-popups: invalid key snapshot\n' >&2; return 1; }
    repeat="${BASH_REMATCH[1]}"; source_table="${BASH_REMATCH[2]}"
    token="${BASH_REMATCH[3]}"; command="${BASH_REMATCH[4]}"
    [[ "$source_table" == "$name" ]] || continue
    # Retain the serialized key as the ownership identity and source argument.
    key="$token"
    lookup=""
    while [[ -n "$token" ]]; do
      character="${token:0:1}"; token="${token:1}"
      if [[ "$character" == "\\" && -n "$token" ]]; then
        character="${token:0:1}"; token="${token:1}"
      fi
      lookup+="$character"
    done
    # A literal semicolon needs escaping at the tmux CLI command boundary.
    [[ "$lookup" == ';' ]] && lookup='\;'
    note="$(tmux list-keys -N -T "$name" -- "$lookup" 2>/dev/null || true; printf '.')"
    note="${note%.}"; note="${note%$'\n'}"
    [[ -z "$note" ]] || note="${note#* }"
    snapshot["$key"]="bind-key ${repeat:+-r }-T prefix -N $(q "$note") $key $command"
  done <"$scratch/lines"
}
declare -A snapshot=() current=() wanted=() previous=() installed=() protected=() touched=()
read_table "$table"
((${#snapshot[@]} > 0)) || { printf 'tmux-popups: no generated bindings\n' >&2; exit 1; }
# Use canonical key names from tmux, so aliases and duplicate slots reconcile.
for key in "${!snapshot[@]}"; do wanted["$key"]="${snapshot[$key]}"; done
read_table prefix
for key in "${!snapshot[@]}"; do current["$key"]="${snapshot[$key]}"; done

: >"$scratch/plan"
: >"$scratch/rollback-state"
count="$(option @tmux-popups-owned-count)"
count="${count:-0}"
[[ "$count" =~ ^[0-9]+$ && ${#count} -le 4 ]] || { printf 'tmux-popups: invalid binding ownership state\n' >&2; exit 1; }
count=$((10#$count))
for ((index=0; index<count; index++)); do
  prefix="@tmux-popups-owned-$index"
  key="$(option "$prefix-key")"
  old="$(option "$prefix-installed")"
  prior="$(option "$prefix-previous")"
  for field in key installed previous; do
    printf 'set-option -g %s %s\n' "$(q "$prefix-$field")" "$(q "$(option "$prefix-$field")")" >>"$scratch/rollback-state"
    printf 'set-option -gu %s\n' "$(q "$prefix-$field")" >>"$scratch/plan"
  done
  [[ -n "$key" ]] || { printf 'tmux-popups: incomplete binding ownership state\n' >&2; exit 1; }
  if [[ -v wanted["$key"] ]]; then
    installed["$key"]="$old"
    previous["$key"]="$prior"
    if [[ "${current[$key]:-}" != "$old" ]]; then protected["$key"]=yes; fi
  elif [[ "${current[$key]:-}" == "$old" ]]; then
    touched["$key"]=yes
    if [[ -n "$prior" ]]; then
      printf '%s\n' "$prior" >>"$scratch/plan"
    else
      printf 'unbind-key -T prefix %s\n' "$key" >>"$scratch/plan"
    fi
  fi
done
index=0
# Sorted canonical names keep ownership state stable across repeated reloads.
printf '%s\n' "${!wanted[@]}" | LC_ALL=C sort >"$scratch/order"
while IFS= read -r key; do
  if [[ ! -v previous["$key"] ]]; then previous["$key"]="${current[$key]:-}"; fi
  if [[ ! -v protected["$key"] ]]; then
    touched["$key"]=yes
    printf '%s\n' "${wanted[$key]}" >>"$scratch/plan"
    installed["$key"]="${wanted[$key]}"
  fi
  prefix="@tmux-popups-owned-$index"
  {
    printf 'set-option -g %s %s\n' "$(q "$prefix-key")" "$(q "$key")"
    printf 'set-option -g %s %s\n' "$(q "$prefix-installed")" "$(q "${installed[$key]}")"
    printf 'set-option -g %s %s\n' "$(q "$prefix-previous")" "$(q "${previous[$key]}")"
  } >>"$scratch/plan"
  if ((index >= count)); then
    for field in key installed previous; do
      printf 'set-option -gu %s\n' "$(q "$prefix-$field")" >>"$scratch/rollback-state"
    done
  fi
  ((index+=1))
done <"$scratch/order"
printf 'set-option -g @tmux-popups-owned-count %s\n' "$index" >>"$scratch/plan"
if tmux show-option -g @tmux-popups-owned-count >"$scratch/count" 2>/dev/null; then
  printf 'set-option -g @tmux-popups-owned-count %s\n' "$(option @tmux-popups-owned-count)" >>"$scratch/rollback-state"
else
  printf 'set-option -gu @tmux-popups-owned-count\n' >>"$scratch/rollback-state"
fi
: >"$scratch/rollback"
for key in "${!touched[@]}"; do
  if [[ -n "${current[$key]:-}" ]]; then
    printf '%s\n' "${current[$key]}" >>"$scratch/rollback"
  else
    printf 'unbind-key -T prefix %s\n' "$key" >>"$scratch/rollback"
  fi
done
cat "$scratch/rollback-state" >>"$scratch/rollback"
tmux source-file -n "$scratch/plan"
tmux source-file -n "$scratch/rollback"
applying=yes
tmux source-file "$scratch/plan"
applying=no
