#!/usr/bin/env bash
set -euo pipefail

CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/tmux-popups"
GENERATED_CONFIG="$CACHE_DIR/generated.conf"

"$CURRENT_DIR/scripts/generate-config.sh"
tmux source-file "$GENERATED_CONFIG"
