# Qualification records

Each record names its candidate and environment. A result applies only to the
cases and commit recorded. The final integrated qualification remains tracked in
[issue #24](https://git.subcult.tv/PatrickFanella/tmux-popups/issues/24).

| Evidence | Scope |
| --- | --- |
| [Automated verification](../../tests/README.md) | Syntax, ShellCheck and isolated tmux/PTY regressions. Provider, clipboard and some tool integrations use substitutes. |
| [Read-only doctor](doctor-browser-2026-11-08.md) | Actual attached browser-terminal diagnosis and bounded input check. |
| [Search](search-browser-2026-11-08.md) | Actual fzf selection, no-match cancellation and original context in an attached browser terminal. |
| [Project actions](project-actions-2026-11-08.md) | Real Git/Bash checks, substitutes for editor/coding tools, and actual browser-terminal shell input. |
| [Failure recovery](recovery-browser-2026-11-08.md) | Actual browser-terminal application input, retry, fresh window, close and process/context checks. |
| [Migration](migration-2026-11-08.md) | Isolated manual install, custom script, example registries, reload and saved-revision return. |
| [Final terminal matrix](terminal-matrix-2026-11-08.md) | Real Yazi/OpenCode input in both modes and two actual browser clients on the final code candidate, plus explicit limits. |
| [Chat lifecycle review](chat-review-2026-11-08.md) | Normal dispatcher quit/copy-quit, bounded owned-group cleanup and actual browser retest. |
| [Hash-path review](hash-path-review-2026-11-08.md) | Explicit-mode direct/menu quoting and retained-close regression on both tested tmux versions. |
| [Full code review](full-review-2026-11-08.md) | Capability evidence, repaired findings, local full-suite result and remaining readiness gates. |
| [Actual clipboard paste](paste-browser-2026-11-08.md) | Browser keyboard copy/paste into all six applications in both modes, plus cancellation and exact-byte cleanup evidence. |
| [Phone attempt](phone-2026-11-08.md) | Inconclusive Android emulator attempt after device-control reference errors. |

The browser terminal is Chromium attached through ttyd to an isolated tmux
server. The final matrix and paste follow-up qualify real Yazi/OpenCode UI and
clipboard input for that stated target. Other native terminals, phone input,
real providers, clipboard/image backends and full user configurations remain
unqualified. No record authorizes tags, releases or a change to the user's
installation under issue #25.

See the [release review packet](../release-review-2026-11-08.md) for proposed
notes, migration/rollback links, canonical/mirror ownership and the open approval gate.
