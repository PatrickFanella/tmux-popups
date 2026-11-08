# Search in a browser terminal

Candidate: `783f6b071787fbbfe7a7ce5fcb3122e8f1fc4516`.
Observed November 8, 2026 UTC on Dozor, Debian 13, tmux 3.5a.
Terminal: ttyd 1.7.7 / xterm.js in Chromium 157, 139 columns by 46 rows.
Picker: the installed fzf reports `0.60 (devel)`.

The disposable tmux server used temporary HOME/XDG directories and a local
command-mode search row bound to F11. A second local row ran a harmless probe
that recorded its cwd and the five invoking-context environment values.

PASS: open search with Prefix+F11. The picker showed titles, direct/menu keys,
launch modes and availability. Type `Browser probe`, wait for its sole match
(`1/6`), then press Enter. The picker closed and the probe recorded the exact
original client, session, window, pane, directory and cwd. No owned search
temporary directory remained.

PASS: a query with no matches showed `0/6`; Enter returned to the parent without
a launch. A separate Ctrl-C cancellation also returned without modifying the
probe artifact or leaving an owned search temporary directory.

The selection screenshot is retained as
`browser-screenshot-localhost-mw7ei17v-ce23bb5c.png` in T3 browser artifacts.
Native-menu fallback and unusual literal directories are covered by the attached
regression fixtures. This result does not qualify Yazi/OpenCode, real providers,
native desktop terminals or the final #12/#24 matrix.
