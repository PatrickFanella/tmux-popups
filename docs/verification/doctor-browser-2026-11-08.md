# Doctor input check in a browser terminal

Candidate: `9685cc7486dd8a02f6cd3ddd649d75e6414cb747`.
Observed November 8, 2026 UTC on Dozor, Debian 13, Bash 5.2, tmux 3.5a.
Terminal: ttyd 1.7.7 / xterm.js in Chromium 157, 139 columns by 46 rows.
The outer terminal reports `xterm-256color`; the popup reports `tmux-256color`.

A disposable tmux server used a temporary HOME/XDG tree and registry. A user-owned
wrapper selected `doctor.sh --input-check 30` through a direct F12 popup binding,
then paused after completion so its output could be read. No user installation,
configuration, real clipboard or provider was used.

PASS: type `tmux-popups` through the browser terminal and press Enter. The popup
reported bytes `74 6d 75 78 2d 70 6f 70 75 70 73` and exit status 0. An earlier
10-second check reached its deadline without input, consistent with the bound.
Six isolated doctor regressions also pass, including read-only state snapshots,
invalid registries, overrides, conflicting keys and input timeout behavior.

This is a real browser terminal input result for #19. It does not qualify native
desktop terminal applications, Yazi/OpenCode terminal-query behavior, actual
providers or the complete matrix in #12/#24. The screenshot is retained in the
T3 browser artifacts as `browser-screenshot-localhost-mw7dx3qf-fa449a9a.png`.
