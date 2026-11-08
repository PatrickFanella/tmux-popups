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
| [Phone attempt](phone-2026-11-08.md) | Inconclusive Android emulator attempt after device-control reference errors. |

The browser terminal is Chromium attached through ttyd to an isolated tmux
server. It supplies actual keyboard/rendering evidence for those cases. It does
not establish behavior in the owner's original native terminal, a real Yazi or
OpenCode session, or a real provider. Those integrations remain optional and
unqualified until their own evidence is recorded. No record authorizes tags,
releases or a change to the user's installation under issue #25.
