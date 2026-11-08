#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
. "$root/scripts/lib.sh"

input_check() {
  local seconds="${1:-10}" sample
  [[ "$seconds" =~ ^[0-9]{1,2}$ ]] || die 'input-check seconds must be from 1 to 30'
  seconds=$((10#$seconds))
  ((seconds >= 1 && seconds <= 30)) || die 'input-check seconds must be from 1 to 30'
  [[ -t 0 && -t 1 ]] || die 'input-check requires an attached terminal; run it in the affected popup or window'
  printf 'Input check: TERM=%s; tmux=%s; timeout=%ss\n' "${TERM:-unset}" "$(tmux -V 2>/dev/null || printf unavailable)" "$seconds"
  printf 'Type tmux-popups and press Enter. Ctrl-C cancels.\n'
  if IFS= read -r -t "$seconds" sample; then
    printf 'Received bytes: '
    printf '%s' "$sample" | od -An -tx1 | tr -d '\n'
    printf '\nInput received. Compare popup and window mode if the application still refuses input.\n'
  else
    printf 'No complete line before the deadline. Check client focus, TERM and application terminal queries.\n' >&2
    return 1
  fi
}
case "${1:-}" in
  --input-check)
    (($# <= 2)) || die 'usage: doctor.sh --input-check [1-30 seconds]'
    input_check "${2:-10}"
    exit ;;
  --help|-h)
    printf 'Usage: scripts/doctor.sh [--input-check [1-30 seconds]]\nOrdinary diagnosis does not apply bindings or replace the shared cache.\n'
    exit ;;
  '') (($# == 0)) || die 'unexpected empty argument' ;;
  *) die 'usage: doctor.sh [--input-check [1-30 seconds]]' ;;
esac

scratch="$(mktemp -d "${TMPDIR:-/tmp}/tmux-popups-doctor.XXXXXXXX")"
trap 'rm -rf -- "$scratch"' EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
failures=0
warnings=0
ok() { printf 'ok      %s\n' "$*"; }
warn() { printf 'warning %s\n' "$*"; warnings=$((warnings + 1)); }
fail() { printf 'fail    %s\n' "$*"; failures=$((failures + 1)); }
setting() {
  local key="$1" fallback="$2" value provenance=default
  value="$(tmux show-option -gqv "$key" 2>/dev/null || true)"
  if [[ -n "$value" ]]; then provenance="tmux option $key"; else value="$fallback"; fi
  [[ "$key" != @tmux-popups-config-file ]] || value="$(expand_home_path "$value")"
  printf '%s = %s [%s]\n' "$key" "$value" "$provenance"
}

printf 'tmux-popups doctor\n==================\n'
if command -v tmux >/dev/null 2>&1; then ok "tmux: $(tmux -V)"; else fail 'tmux not found'; fi
inside=no
[[ -z "${TMUX:-}" ]] || inside=yes
printf 'TERM=%s; inside tmux=%s\n' "${TERM:-unset}" "$inside"
if tmux list-sessions >/dev/null 2>&1; then
  printf 'attached clients: %s\n' "$(tmux list-clients -F '#{client_name}' | wc -l | tr -d ' ')"
else
  warn 'no running tmux server; run doctor inside the affected tmux session'
fi
printf 'plugin root: %s\nshared cache: %s\n' "$root" "${XDG_CACHE_HOME:-$HOME/.cache}/tmux-popups/generated.conf"

printf '\nEffective settings\n------------------\n'
setting @tmux-popups-menu-key Enter
setting @tmux-popups-reload-key R
setting @tmux-popups-config-file "$HOME/.tmux.conf"
setting @tmux-popups-default-width 80%
setting @tmux-popups-default-height 80%
setting @tmux-popups-profile small
setting @tmux-popups-availability show-disabled
setting @tmux-popups-conflicts skip
setting @tmux-popups-enable-vscode on
# Report executable configuration, without printing an arbitrary shell expression.
printf 'vscode command: %s\n' "$(if [[ -n "$(tmux show-option -gqv @tmux-popups-vscode-command 2>/dev/null || true)" ]]; then printf 'explicit tmux option (expression omitted)'; else printf 'default: code .'; fi)"
if local_registry="$(resolve_local_registry)"; then
  registry_source='default XDG path'
  if [[ -n "${TMUX_POPUPS_LOCAL_REGISTRY:-}" ]]; then registry_source='environment TMUX_POPUPS_LOCAL_REGISTRY'
  elif [[ -n "$(tmux show-option -gqv @tmux-popups-local-registry 2>/dev/null || true)" ]]; then registry_source='tmux option @tmux-popups-local-registry'; fi
  printf 'local registry = %s [%s]\n' "$local_registry" "$registry_source"
else
  fail 'local registry selection failed'
fi
if directory="$(resolve_user_script_directory)"; then
  directory_source='default XDG path'
  if [[ -n "${TMUX_POPUPS_USER_SCRIPT_DIRECTORY:-}" ]]; then directory_source='environment TMUX_POPUPS_USER_SCRIPT_DIRECTORY'
  elif [[ -n "$(tmux show-option -gqv @tmux-popups-user-script-directory 2>/dev/null || true)" ]]; then directory_source='tmux option @tmux-popups-user-script-directory'; fi
  printf 'user script directory = %s [%s]\n' "$directory" "$directory_source"
else
  fail 'user script directory selection failed'
fi

printf '\nTPM registration\n----------------\n'
tpm_path="$(tmux show-environment -g TMUX_PLUGIN_MANAGER_PATH 2>/dev/null || true)"
if [[ "$tpm_path" == TMUX_PLUGIN_MANAGER_PATH=* ]]; then tpm_path="${tpm_path#*=}"
else tpm_path="${TMUX_PLUGIN_MANAGER_PATH:-${XDG_CONFIG_HOME:-$HOME/.config}/tmux/plugins}"; fi
if [[ -d "$tpm_path" ]]; then
  ok "TPM path: $tpm_path"
  if [[ -e "$tpm_path/tmux-popups" ]]; then ok "TPM entry exists: $tpm_path/tmux-popups"
  else warn "TPM entry missing: $tpm_path/tmux-popups"; fi
else
  warn "TPM path not found: $tpm_path"
fi
if grep -R 'PatrickFanella/tmux-popups\|patrickfanella/tmux-popups' \
  "$HOME/.tmux.conf" "$HOME/.config/tmux"/*.conf >/dev/null 2>&1; then
  ok 'TPM plugin registration found'
else
  warn "TPM plugin registration not found; add: set -g @plugin 'PatrickFanella/tmux-popups'"
fi

printf '\nEffective entries\n-----------------\n'
if rows="$("$root/scripts/list-popups.sh" --origin-tsv)"; then
  ok 'shared registry validation passed'
  while IFS=$'\t' read -r id direct menu title width height command mode completion enabled deps status kind arguments source; do
    resolve_execution "$command" "$kind" "$arguments" "$source"
    executable="${execution_argv[0]:-interactive shell}"
    [[ "$kind" != shell ]] || executable='explicit shell expression (not executed)'
    close="$(entry_close_policy "$id" "$mode")"
    enabled_source="$source"
    if [[ -n "$(tmux show-option -gqv "@tmux-popups-$id-enabled" 2>/dev/null || true)" ]]; then
      enabled_source="tmux option @tmux-popups-$id-enabled"
    elif [[ "$source" == "$root/popups.tsv:"* && "$(tmux show-option -gqv @tmux-popups-profile 2>/dev/null || true)" == full ]]; then
      enabled_source='full profile'
    fi
    printf '%s: %s; mode=%s/%s; close=%s; enabled=%s [%s]; deps=%s (%s); executable=%s; source=%s\n' \
      "$id" "$title" "$mode" "$completion" "$close" "$enabled" "$enabled_source" "$deps" "$status" "$executable" "$source"
  done <<<"$rows"
else
  fail 'merged registry failed shared validation; fix the file/line error above'
fi

printf '\nBinding plan\n------------\n'
if "$root/scripts/generate-config.sh" --output "$scratch/generated.conf"; then
  ok 'generated configuration validates in temporary output'
  if ! "$root/scripts/apply-config.sh" --explain "$scratch/generated.conf"; then fail 'binding explanation failed'; fi
  cache="${XDG_CACHE_HOME:-$HOME/.cache}/tmux-popups/generated.conf"
  if [[ ! -f "$cache" ]]; then
    warn 'shared cache is absent; load tmux-popups.tmux to install bindings'
  elif ! cmp -s "$cache" "$scratch/generated.conf"; then
    warn 'shared cache differs from current settings; reload through tmux-popups.tmux'
  fi
else
  fail 'temporary generation failed; shared cache and effective bindings are unchanged'
fi
printf '\nInput troubleshooting\n---------------------\n'
printf 'Run scripts/doctor.sh --input-check in the affected terminal. Compare popup and window mode, terminal/tmux/application versions, TERM, typing/paste, resize and Ctrl-C.\n'
printf 'Yazi defaults to window mode; keep its safe preview configuration while investigating terminal response timeouts. Optional providers require separate qualification.\n'
printf '\nSummary\n-------\nfailures: %s\nwarnings: %s\n' "$failures" "$warnings"
((failures == 0))
