#!/usr/bin/env bash
set -euo pipefail
. "$(dirname "${BASH_SOURCE[0]}")/../lib.sh"
origin_pane
origin_client
# A client name is a tty path, but quote it as tmux command data anyway.
client=${TMUX_POPUPS_CLIENT//\\/\\\\}
client=${client//\"/\\\"}
exec tmux choose-tree -Zw -t "$TMUX_POPUPS_PANE" "switch-client -c \"$client\" -t '%%'"
