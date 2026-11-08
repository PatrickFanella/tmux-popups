# Project action verification

Candidate implementation: `b55ec3d79caabcd89d67ff69996862fff55ef115`.
Observed November 8, 2026 UTC on Dozor, Debian 13.
Real tools: Git 2.47.3 and Bash 5.2.37.

The isolated checks use temporary Git repositories and directories containing
spaces, apostrophes and control bytes. Real Git status from the root and a nested
directory reports the root-relative fixture file. Outside Git, status fails
visibly without initializing a repository. Real Bash keeps the exact invoking
directory in root, nested and non-repository cases.

Editor and coding-tool substitutes check literal arguments, project-root cwd,
notes path precedence, no note creation during discovery, and visible missing
tool errors. Registry dispatch preserves the original invoking directory while
the coding adapter changes cwd to the repository root. A second launch reuses
the same live tool window. The documented tmux notes environment setting also
reaches the selected notes window and opens the configured root-relative file.
No provider or system clipboard is contacted.

PASS: in Chromium 157 / ttyd 1.7.7, open the native Quick Menu and select
`shell here` with menu key `2`. A real Bash window opens in the disposable
`invoking directory with spaces`. Typing a printf command records matching cwd,
original directory, session and pane values. Typing `exit` closes the new window
and returns to the parent. The screenshot is retained as
`browser-screenshot-localhost-mw7iigct-0e6ce128.png` in T3 browser artifacts.
The owned terminal server and browser tab were stopped afterward.

Real OpenCode and editor interaction, provider compatibility and the broader
native-terminal matrix remain unqualified under #12/#24. The phone attempt is separately recorded as
inconclusive in `phone-2026-11-08.md`.
