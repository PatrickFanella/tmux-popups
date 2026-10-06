# Launcher verification

Run `scripts/check.sh` from the repository checkout. It runs Bash syntax,
ShellCheck with the existing project exclusions, and `tests/run.sh`. The test
command requires Python 3, tmux and GNU timeout. It has a 240-second bound.

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

Mode checks load seven-column legacy rows and eight/nine-column extensions,
then dispatch popup, window and foreground/background command entries through
bindings and menu selections. They check popup dimensions, session-sized windows,
exit 23 handling, CLI status propagation, background return before completion,
local overrides and the legacy Yazi adapter-path defaults. Command fixtures
also preserve literal newline/tab directories and the origin contract on two
clients. Invalid extensions preserve the last-good config and bindings.
The longer suite deadline accommodates these added PTY cases; each operation
and completion wait retains its own shorter bound.

Availability checks cover the small default and full-menu compatibility, disabled
row discovery, per-entry option overrides, prior binding restoration and user
replacement preservation on reload. Missing and alternative dependencies change
both direct bindings and menu labels; stale dispatch reports a missing group to
the origin client. Same-ID command replacements, renamed adapters and a custom
executable prove dependency checks follow the effective command. A fixture with
only vi executes daily notes, while missing explicit EDITOR/SHELL values remain
unavailable. An unrunnable khal uses the cal fallback. Invalid enabled/dependency
metadata, including disabled rows and empty explicit enabled options, preserves
the last-good config and bindings. Existing regressions select full/ignore to
continue exercising the pre-existing complete binding configuration.

User-script checks execute outside scripts whose paths contain spaces and
apostrophes through CLI, direct bindings and menu actions in popup, window and
foreground/background command modes. They compare exact argument values,
including empty strings and escaped line breaks, exercise directory and registry
precedence, reject malformed JSON and missing/nonexecutable targets, and replace
a disposable plugin installation before reloading. User script and registry
bytes must survive that replacement. Legacy output layouts and seven/eight/nine/
eleven-column rows retain their behavior. These synthetic PTY checks leave the
actual terminal/tool/provider gates in #12/#24 and owner release gate in #25 open.
