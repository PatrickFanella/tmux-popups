# Failure recovery qualification — 2026-11-08

Result: PASS for the controlled terminal cases below. This does not qualify a real Yazi, OpenCode or provider session.

Candidate: `528ae83e0bc18154236636134d82b0b6bb2eb8a1`.
Environment: Dozor, tmux 3.5a, Bash 5.2.37, Python 3.13, Chromium 157 through ttyd 1.7.7. The browser attached to a private tmux server with an isolated HOME and a foreground Python input fixture. The fixture entry used popup mode and `@tmux-popups-recover-close on-success`.

## Browser checks

1. Prefix + F8 opened the popup. Typing `literal r w c` reached the application unchanged. The fixture exited 23; its output, numeric status and retry/window/close controls remained visible.
2. Pressing `r` started a second process. Its input reached the application, and a second exit 23 remained readable.
3. Pressing `w` closed the popup and started a third process in a fresh window named `recover`. Typing `ok` returned 0, closed that window and returned to the original Bash window.
4. A fourth popup exited 23. Pressing `c` closed recovery and retained status 23 in tmux's run-shell error view. Pressing `q` returned to the original pane, as documented.
5. Fixture records confirmed distinct process IDs and byte-for-byte identical original client, session, window, pane, directory and working directory on the initial launch, retry and window fallback. The directory contained spaces. All four application processes had exited; only the original window remained.

Screenshots saved by T3 Code:

- Readable exit 23 and controls: `browser-screenshot-localhost-mw7jls8t-da9ba027.png`.
- Fresh window waiting for application input: `browser-screenshot-localhost-mw7jm8by-9caf462a.png`.

The browser tab, ttyd process and private tmux server were stopped after the check. No user tmux server or configuration was used.

## Automated checks

`PYTHONPATH=tests python3 -m unittest -v test_recovery test_doctor`: 20 tests passed. Recovery coverage includes success, failure, missing targets, retry, retained success, terminal input, fresh-window context, raw terminal restoration, external termination, Ctrl-C, owned child cleanup, vanished origins and compatibility without Python.

`scripts/check.sh`: syntax checks, ShellCheck and all 130 tests passed in 306.837 seconds. The runner timeout is 360 seconds.

Phone qualification remains inconclusive; see [the recorded emulator attempt](phone-2026-11-08.md). No additional phone attempt was made for this change.
