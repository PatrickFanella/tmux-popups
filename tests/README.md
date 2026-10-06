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

Quoting checks execute direct and menu actions in windows and attached popups from a checkout with spaces, apostrophes and shell metacharacters. They also exercise reload paths and the configurable editor command. Unsupported entry IDs and tmux format expressions or line breaks in plugin/config/registry paths and titles fail before generation. Attached clients use synthetic PTYs and do not qualify actual terminals for #12 or #24.
