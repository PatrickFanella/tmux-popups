# Chat lifecycle review — 2026-11-08

Result: PASS for the controlled cases below.
Candidate: `c1f0f313f0dc4aee28f961931114abc40a81eb57`.

## Reproductions and repair

A dispatcher-launched popup with the original client context returned 129 when
`q` or `cq` closed its own popup before reaching exit 0. A Chromium 157 / ttyd 1.7.7 /
tmux 3.5a session showed the extra run-shell error view. A focused tmux 3.3a test
reproduced that status. Chat now exits normally and lets the launcher close its
presentation, avoiding the self-induced HUP.

A successful provider substitute spawned a child that ignored TERM and then
exited. The original completion path left that owned child alive. The focused
pre-fix regression failed. Completion and interruption now use the same bounded
request-group cleanup, including KILL after the TERM grace period.

Ten chat tests passed on Dozor (5.200 seconds) and in a private CI-equivalent
container with Bash 5.2.15, tmux 3.3a, Python 3.11.2 and Node 24 (5.012 seconds).
The tests cover exact response bytes, session continuation, provider/copy errors,
normal dispatcher popup quit/copy-quit, stubborn descendants and cancellation.
Bash syntax and the project's ShellCheck flags passed.

## Browser retest

The committed repair ran on a private tmux server with isolated HOME, XDG paths
and TMPDIR. Provider and clipboard programs were substitutes, without credentials
or external requests.

- Prefix + F8 opened chat. Typing `q` and Enter returned to the original Bash
  pane, with no run-shell failure view.
- Reopening accepted `browser lifecycle repair` and displayed `Browser reply`.
  Typing `cq` and Enter copied the exact response to the owned fixture file and
  returned directly to Bash. Its file modification time followed this run.
- The request directory was removed, and only the original Bash pane remained.
  The browser tab, ttyd process and private tmux server were stopped afterward.

T3 screenshot after copy-and-quit: `browser-screenshot-localhost-mw7m989h-6fca50d3.png`.
Real provider and system clipboard qualification remain separate in #12/#24.
