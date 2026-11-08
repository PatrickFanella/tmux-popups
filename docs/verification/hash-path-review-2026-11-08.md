# Literal checkout hash review — 2026-11-08

Result: PASS for the focused regression cases below.
Candidate: `1d9910a5defe66534ed297520fa675d5e6277ca1`.

A checkout path containing literal `##` passed validation but failed dispatch
because run-shell format expansion consumed the pair before invoking the script.
The original quoting reproduction failed to create its tool marker. The repair
escapes hashes in the executable path for the direct action's format expansion
and the menu action's additional expansion. The inner popup command stays literal.
Existing rejection of tmux expressions in checkout paths remains unchanged.

The review also found that the previous quoting test changed a legacy Yazi mode
option while running a custom adapter. That adapter defaults to popup by path,
so the supposed window loop still tested popups. The test now writes an explicit
row mode for each case.

All five quoting tests passed with the corrected modes on Dozor (tmux 3.5a,
Bash 5.2.37; 39.641 seconds) and in the private CI-equivalent container (tmux 3.3a,
Bash 5.2.15; 30.458 seconds). The new case uses a checkout named
`plugin # and ## literal`, direct and menu actions, window and popup modes, and
both `always` and `on-success` close policies. Existing apostrophe, backslash,
shell-expression, reload, configurable command and unsupported-format cases pass.
Bash syntax and the project's ShellCheck flags passed.

These attached PTY checks use private tmux servers, disposable homes and substitute
tools. They do not qualify a native terminal, provider or real clipboard backend.
No user checkout, tmux server or configuration was used.
