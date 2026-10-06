# Launcher verification

Run `scripts/check.sh` from the repository checkout. It runs Bash syntax,
ShellCheck with the existing project exclusions, and `tests/run.sh`. The test
command requires Python 3, tmux and GNU timeout. It has a 90-second bound.

Each test starts a separate tmux server on a private socket, creates a disposable
home and XDG directories, and removes its clients and server before deleting
those files. It uses substitute programs for Yazi and calculator input. No
provider request or system clipboard write belongs in these fixtures.

The checks cover registry overrides, generated configuration parsing, repeated
loads, a real reload binding, direct and menu action execution, attached-terminal
popup input, unknown entries and tool failure status. The terminal fixtures use a
100-column, 40-row pseudoterminal so the complete default menu fits. They wait for
rendered fixture prompts before sending input.

Gitea Actions uses `.gitea/workflows/ci.yml`; the GitHub publishing copy runs the
same command. Hosted results qualify the exact commit that ran. These controlled
terminal checks do not complete the real-terminal, multiple-client and optional
integration qualification in issue #24, or authorize a release under #25.

Known defect regressions are added with their focused repairs. The October 4
baseline reproduction of issue #4 failed because a literal `~/config/tmux.conf`
reload path expanded to `$HOME/~/config/tmux.conf`. Three additional tests now
cover reload and registry paths plus literal project arguments, including bare
home, spaces, absolute/relative paths and unevaluated shell expressions.

Registry-selection regressions also cover fresh dispatch after generation,
command overrides, environment precedence, help output and explicit missing-file
failures. These cases failed before the shared selection helper was added.

Quoting checks execute direct and menu actions in windows and attached popups from a checkout with spaces, apostrophes and shell metacharacters, including a literal backslash before a semicolon. They also exercise reload paths and the configurable editor command. Unsupported entry IDs and tmux format expressions or line breaks in plugin/config/registry paths and titles fail before generation. Attached clients use synthetic PTYs and do not qualify actual terminals for #12 or #24.

Timer checks use controlled sleep programs to verify decimal input, the empty
25-minute default, the supported 1 to 1440-minute range, zero/invalid/overflow
rejection, exactly 60 sleeps for a one-minute timer, and owned-child cleanup.
An attached tmux popup accepts 09 and Ctrl-C cancels its owned sleep. This
pseudoterminal evidence does not qualify actual terminal applications for #12
or #24.

Clipboard checks use empty, small and 100,000-row histories, producer failures,
picker cancellation/failure and failed decoding. A clipboard substitute checks
exact selected bytes, including NUL, non-UTF-8 bytes and trailing newlines,
without touching the system clipboard. Owned temporary files are checked after
each run. Real cliphist/Wayland checks remain separate environment evidence.

Binding checks use isolated tmux servers to change, disable and remove entry,
menu and reload keys. They compare effective bindings and ownership over repeated
reloads, restore repeat flags and multiline notes, preserve user replacements
and explicit unbinds, and leave root/custom tables unchanged. Alias collisions,
invalid-key rejection, partial-apply rollback and checkout/cache changes are
covered. Special paths and note text must not execute injection markers.

Registry checks reject short/extra rows, every empty field, invalid IDs, keys
and dimensions, missing or nonexecutable targets, and duplicate shortcuts.
Same-ID overrides keep their order and all source rows retain validation.
Generation failures preserve the last-good config and effective bindings and
ownership. Controlled overlapping writers prove complete publication and that
a failed writer cannot replace another writer's valid cache. Tests use only
owned HOME/XDG files and private tmux sockets. The editor regression checks a
pane directory containing spaces, apostrophes, a backslash-semicolon and shell
expressions on tmux 3.3a and newer.
