# Actual browser clipboard paste — 2026-11-08

Result: PASS for the browser terminal target and application cases below.
Runtime revision: `6030555b528e9660bbbda876133c5f2238aa1961`.
The fixture used packet checkout `42bf116`; its scripts, registry, examples and CI
workflows match that runtime revision and the qualified code candidate `94294cf`.
No implementation code changed for this check.

## Method and environment

Chromium 157 opened two owned pages in the isolated browser profile: a static
source/target textarea fixture and ttyd 1.7.7 attached to a private tmux 3.5a server.
Known text was copied with Control+A and Control+C. Control+V into the second
textarea verified the expected clipboard value before each terminal paste. The
terminal textarea was focused explicitly, then Control+Shift+V performed actual
clipboard paste. These results do not rely on the preview tool's text-insertion
operation as evidence of paste.

The application environment used Bash 5.2.37, Node 22.23.4, Python 3.13,
fzf 0.60 (devel), Yazi 26.9.1 and OpenCode 1.19.5. Client TERM was
`xterm-256color`; application TERM was `tmux-256color`. HOME/XDG/TMPDIR, the
invoking `project with spaces` directory, scripts and socket were disposable.
Official Yazi/OpenCode downloads matched the digests in the terminal matrix.
Yazi used safe mode; OpenCode disabled updates/sharing/default plugins/external
skills/LSP downloads and submitted no provider prompt. Chat provider and response
copy commands were substitutes; no real provider request was made.

## Application matrix

Each row passed in both popup and window mode: twelve clipboard cases in total.

| Application | Pasted data and observed result |
| --- | --- |
| Bash | A known printf command created an owned marker containing exact `shell-paste-ok` bytes, then exited normally. |
| Chat adapter | `tmux-popups paste fixture` rendered at the input prompt and reached the provider substitute as exactly those 25 bytes. The controlled reply displayed; q exited normally. |
| Python calculator | Pasted `7*6`, pressed Enter and observed 42. `/exit` returned to the original pane. |
| Real Yazi | Pasted `alpha` into Filter. Enter confirmed the filter, Escape cleared it, and q exited. The window filter also survived resize to 103x37 and restoration. |
| Real OpenCode | The pasted draft rendered exactly. Control+C cleared it. `/exit` + Enter closed the interface without submitting a model request. |
| Real fzf | The pasted `alpha` query narrowed the choices. Enter wrote exactly `alpha` plus its newline to the owned selection file, then closed the view. |

Additional actual-terminal checks passed: Bash Control+C cancelled an unsubmitted
line; fzf Escape cancelled a window picker; fzf Control+C closed a popup picker;
calculator Control+C closed both modes; and Control+C cancelled an owned slow
chat request in both modes. The slow provider PID was stopped and its request
directory removed. Expected nonzero popup cancellation views were dismissed with
q. Earlier matrix records also cover real typing, menu/search selection,
OpenCode command-menu Escape, repeated reopen and two-client exact-PID reuse.

Screenshots saved by T3:

- Yazi window paste/filter: `browser-screenshot-localhost-mw7o8jxz-570d8bb3.png`.
- Yazi popup paste/filter: `browser-screenshot-localhost-mw7o8lwk-b9463192.png`.
- OpenCode window pasted draft: `browser-screenshot-localhost-mw7o8v0n-033b825a.png`.
- OpenCode popup pasted draft: `browser-screenshot-localhost-mw7o90at-5911c24f.png`.

## Harness corrections and cleanup

An initial Control+V/read-builtin sub-run was discarded. The final terminal
checks use the client's Control+Shift+V binding at normal application inputs.
A fixed Bash prompt expectation was also corrected: normal window shells use the
system prompt while the fixture's parent shell uses `bash-5.2$`. Neither harness
condition is recorded as an application failure or a passed case.

After the successful checks, only the original Bash pane remained. No process
used the downloaded application executables, and no chat request directory
remained. Both browser tabs and the owned ttyd, tmux and HTTP fixture processes
were stopped. The evidence concerns this browser clipboard route. It does not
qualify a different native terminal, real cliphist/Wayland backend, provider,
phone, image preview or full user configuration.

Together with the final local/hosted regressions and the earlier actual-terminal
matrix, this completes the recorded input qualification for the stated browser
target. The remembered historical failure was not reproduced there; its original
terminal/configuration is unverified. No dependency or release approval gate was
removed to reach this result.

## Runtime-main hosted result

[Run 20412, job 37904](https://git.subcult.tv/PatrickFanella/tmux-popups/actions/runs/20412/jobs/37904)
passed on runtime main `6030555b528e9660bbbda876133c5f2238aa1961`: 134 tests in
319.033 seconds, with only optional real fzf skipped. The local full run includes
fzf. This runtime includes the mode-timeout diagnostics as well as the reviewed
implementation fixes.
