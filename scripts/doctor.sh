#!/usr/bin/env bash
set -u

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cache_dir="${XDG_CACHE_HOME:-$HOME/.cache}/tmux-popups"
generated="$cache_dir/generated.conf"
local_registry="${TMUX_POPUPS_LOCAL_REGISTRY:-${XDG_CONFIG_HOME:-$HOME/.config}/tmux-popups/popups.local.tsv}"
failures=0
warnings=0

ok() { printf 'ok      %s\n' "$*"; }
warn() { printf 'warning %s\n' "$*"; warnings=$((warnings + 1)); }
fail() { printf 'fail    %s\n' "$*"; failures=$((failures + 1)); }

printf 'tmux-popups doctor\n'
printf '==================\n\n'

if command -v tmux >/dev/null 2>&1; then
  ok "tmux found: $(tmux -V 2>/dev/null || printf unknown)"
else
  fail 'tmux not found'
fi

if [[ -n "${TMUX:-}" ]]; then
  ok 'running inside tmux'
else
  warn 'not running inside tmux; tmux option checks may be limited'
fi

if [[ -d "$root" ]]; then
  ok "plugin root: $root"
else
  fail "plugin root missing: $root"
fi
if [[ -f "$root/popups.tsv" ]]; then
  ok 'default registry exists'
else
  fail 'popups.tsv missing'
fi
if [[ -f "$local_registry" ]]; then
  ok "local registry exists: $local_registry"
else
  warn "local registry not found: $local_registry"
fi

tpm_path="$(tmux show-environment -g TMUX_PLUGIN_MANAGER_PATH 2>/dev/null | sed 's/^TMUX_PLUGIN_MANAGER_PATH=//' || true)"
if [[ -z "$tpm_path" ]]; then
  tpm_path="${TMUX_PLUGIN_MANAGER_PATH:-${XDG_CONFIG_HOME:-$HOME/.config}/tmux/plugins}"
fi
if [[ -d "$tpm_path" ]]; then
  ok "TPM path: $tpm_path"
  if [[ -e "$tpm_path/tmux-popups" ]]; then
    ok "TPM entry exists: $tpm_path/tmux-popups"
  else
    warn "TPM entry missing: $tpm_path/tmux-popups"
  fi
else
  warn "TPM path not found: $tpm_path"
fi

if grep -R "PatrickFanella/tmux-popups\|patrickfanella/tmux-popups" \
  "$HOME/.tmux.conf" "$HOME/.config/tmux"/*.conf >/dev/null 2>&1; then
  ok 'TPM plugin registration found in tmux config'
else
  warn "TPM plugin registration not found; add: set -g @plugin 'PatrickFanella/tmux-popups'"
fi

if "$root/scripts/list-popups.sh" --tsv >/dev/null 2>&1; then
  ok 'merged registry parses'
else
  fail 'merged registry failed to parse'
fi

if "$root/scripts/generate-config.sh" >/dev/null 2>&1; then
  ok "generated config: $generated"
else
  fail 'config generation failed'
fi

if [[ -f "$generated" ]]; then
  if tmux source-file -n "$generated" >/dev/null 2>&1; then
    ok 'generated config validates with tmux'
  else
    fail 'generated config failed tmux validation'
  fi
else
  fail "generated config missing: $generated"
fi

printf '\nDependencies\n------------\n'
"$root/scripts/list-popups.sh" --deps || fail 'dependency listing failed'

printf '\nSummary\n-------\n'
printf 'failures: %s\nwarnings: %s\n' "$failures" "$warnings"
if ((failures > 0)); then
  exit 1
fi
exit 0
