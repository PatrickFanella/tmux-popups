# tmux-popups

Small tmux popup toolkit with a TSV registry, generated bindings, shared shell helpers, dependency checks, and optional local overrides.

![tmux-popups demo](assets/demo.gif)

## Features

- `Prefix+Enter` quick menu generated from registry rows
- Direct bindings generated from the same rows
- Default registry: `popups.tsv`
- Local override registry: `~/.config/tmux-popups/popups.local.tsv`
- Dependency status in help and CLI output
- Doctor script for common tmux/TPM/config problems
- Bash-only implementation; no build step
- Generated config stored at `${XDG_CACHE_HOME:-$HOME/.cache}/tmux-popups/generated.conf`

## Install with TPM

Add to `~/.tmux.conf` or your sourced tmux config:

```tmux
set -g @plugin 'PatrickFanella/tmux-popups'
```

Reload tmux, then press TPM install key (`prefix + I`).

## Install manually

```sh
git clone https://github.com/PatrickFanella/tmux-popups.git ~/.config/tmux/plugins/tmux-popups
```

Then source the plugin entrypoint:

```tmux
run-shell "$HOME/.config/tmux/plugins/tmux-popups/tmux-popups.tmux"
```

Reload tmux:

```sh
tmux source-file ~/.tmux.conf
```

## Local development with TPM

Useful when hacking on the plugin but still letting TPM manage load/update keys.

```sh
git clone https://github.com/PatrickFanella/tmux-popups.git ~/Projects/tools/tmux-popups
mkdir -p ~/.config/tmux/plugins
ln -sfn ~/Projects/tools/tmux-popups ~/.config/tmux/plugins/tmux-popups
```

Keep TPM registration in tmux config:

```tmux
set -g @plugin 'PatrickFanella/tmux-popups'
```

TPM will see `tmux-popups`; the symlink points it at your working tree.

## Default bindings

The default registry includes the full popup set. Some rows need optional tools; dependency status is visible in `Prefix+C-h` and `scripts/list-popups.sh --deps`.

| Key | Popup |
| --- | --- |
| `Prefix+Enter` | Quick menu |
| `Prefix+C-h` | Popup help + dependency status |
| `Prefix+O` | quick chat via [`ocq`](https://github.com/PatrickFanella/ocq) |
| Menu `o` | opencode |
| `Prefix+T` | shell |
| Menu `N` | daily note |
| `Prefix+g` | lazygit |
| `Prefix+Y` | yazi |
| `Prefix+F` | ferrosonic |
| `Prefix+C-b` | tmux key list |
| `Prefix+Z` | dotfiles picker |
| `Prefix+R` | reload tmux config |

Session switching is intentionally left to [`tmux-sessionx`](https://github.com/omerxx/tmux-sessionx). Example:

```tmux
set -g @plugin 'omerxx/tmux-sessionx'
set -g @sessionx-bind 'j'
set -g @sessionx-prefix 'on'
set -g @sessionx-window-height '80%'
set -g @sessionx-window-width '60%'
```

Then `Prefix+j` opens sessionx. If you prefer tmux's built-in picker, copy the `sessions` row from `examples/popups.optional.tsv`.

## Plugin options

Set these before the plugin loads:

```tmux
set -g @tmux-popups-menu-key 'Enter'
set -g @tmux-popups-reload-key 'R'
set -g @tmux-popups-config-file '~/.tmux.conf'
set -g @tmux-popups-default-width '80%'
set -g @tmux-popups-default-height '80%'
set -g @tmux-popups-local-registry '~/.config/tmux-popups/popups.local.tsv'
set -g @tmux-popups-enable-vscode 'on'
set -g @tmux-popups-vscode-command 'code .'
set -g @tmux-popups-yazi-mode 'window'
```

`@tmux-popups-config-file` is the tmux config file reloaded by the `R` reload binding and the Quick Menu "reload tmux" entry. Defaults to `~/.tmux.conf`. Set this if your config lives elsewhere, for example:

```tmux
set -g @tmux-popups-config-file '~/.config/tmux/tmux.conf'
```

Use `-` in a row's width or height to inherit the default width/height options.

## Registry format

Rows are tab-separated:

```tsv
id	direct_key	menu_key	title	width	height	command
```

| Column | Meaning |
| --- | --- |
| `id` | Unique popup id used by `scripts/run-popup.sh` |
| `direct_key` | Direct tmux binding after prefix, or `-` for none |
| `menu_key` | Key in quick menu, or `-` for none |
| `title` | Popup title |
| `width` | tmux popup width, e.g. `80%`, or `-` for default |
| `height` | tmux popup height, e.g. `80%`, or `-` for default |
| `command` | Plugin-relative script path, or `-` for an interactive shell |

Blank lines and lines beginning with `#` are ignored.

## Local override registry

Default path:

```text
~/.config/tmux-popups/popups.local.tsv
```

The plugin merges:

```text
popups.tsv
  + popups.local.tsv
  -> generated bindings
```

If a local row has the same `id` as a default row, the local row overrides it while keeping the original order. New local ids are appended.

Example local override: move chat to another key and use default popup size:

```tsv
chat	C-a	a	quick chat	-	-	scripts/tools/chat.sh
```

Example local-only scratch shell:

```tsv
scratch	C-s	s	scratch shell	80%	80%	-
```

Reload tmux after edits:

```sh
tmux source-file ~/.tmux.conf
```

## Create a popup script

Create `scripts/tools/hello.sh`:

```sh
#!/usr/bin/env bash
set -euo pipefail

printf 'Hello from tmux-popups.\n\nPress Enter to close... '
read -r _ || true
```

Make it executable:

```sh
chmod +x scripts/tools/hello.sh
```

Add a row to `popups.tsv` or your local registry:

```tsv
hello	-	h	hello	75%	75%	scripts/tools/hello.sh
```

Reload tmux and open it with `Prefix+Enter`, then `h`.

## Optional examples

Extra rows live in:

```text
examples/popups.optional.tsv
```

Copy rows into your local registry or `popups.tsv`, install matching tools, then reload tmux.

Examples:

```tsv
sessions	C-j	j	sessions	80%	80%	scripts/tools/sessions.sh
chat	O	g	quick chat	80%	80%	scripts/tools/chat.sh
yazi	Y	r	yazi	80%	80%	scripts/tools/yazi.sh
```

`chat` needs [`ocq`](https://github.com/PatrickFanella/ocq).

## List and dependency helpers

```sh
scripts/list-popups.sh --pretty
scripts/list-popups.sh --deps
scripts/list-popups.sh --tsv
scripts/list-popups.sh --deps-tsv
```

`Prefix+C-h` shows the same dependency status inside tmux.

Dependency groups can contain alternatives, e.g. `glow|bat|less` means one of those commands is enough.

## Doctor

Run:

```sh
scripts/doctor.sh
```

It checks:

- tmux availability/version
- plugin root
- default/local registries
- TPM path and local plugin entry
- TPM registration in tmux config
- generated config creation
- `tmux source-file -n` validation
- per-popup dependency status

Warnings are informational. Failures exit nonzero.

## Validate generated config

```sh
scripts/generate-config.sh
tmux source-file -n ~/.cache/tmux-popups/generated.conf
tmux source-file ~/.tmux.conf
```

## CI

GitHub Actions runs:

- `bash -n` on plugin scripts
- ShellCheck
- config generation smoke test

## Optional tools used by default/extra rows

- [`ocq`](https://github.com/PatrickFanella/ocq) for quick OpenCode chat
- `opencode`
- `task` / Taskwarrior
- `nvim`, `vim`, `vi`, or `$EDITOR`
- `tldr`, `man`, `less`
- `khal`, `cal`
- `python3`
- `ssh`, `fzf`
- `cliphist`, `wl-copy`, `wl-paste`
- `newsboat`, `curl`
- `journalctl`, `tail`, `watch`
- `glow`, `bat`
- `lazygit`, `yazi`, `ferrosonic`

## Environment variables

Some tool scripts respect environment variables:

| Variable | Script | Default |
| --- | --- | --- |
| `NOTES_DIR` | `notes` popup | `~/Notes/daily` |
| `PROJECTS_DIR` | `projects` popup | `~/Projects` |
| `TMUX_POPUPS_YAZI_SAFE` | yazi launcher | `on` |

Yazi rows open in a normal tmux window by default. Yazi can report a terminal
response timeout inside `display-popup`, so window mode is the safer default.

Yazi still runs in safe mode by default. tmux popups do not reliably support
image-preview passthrough, so the launcher disables Yazi preview/preload plugins
via a generated cache config. Set `TMUX_POPUPS_YAZI_SAFE=off` before launch to
use your full Yazi config and accept the tmux risk.

To force popup mode:

```tmux
set -g @tmux-popups-yazi-mode 'popup'
```

Warning: popup mode may trigger Yazi terminal response timeouts; tmux-popups
shows a warning before launching Yazi in popup mode.

## How it works

```text
popups.tsv + optional local registry
  -> scripts/list-popups.sh --tsv
  -> scripts/generate-config.sh
  -> ~/.cache/tmux-popups/generated.conf
  -> tmux source-file
```

`scripts/run-popup.sh <id>` reads the merged registry and executes the matching command inside `display-popup`.

## Files

- `popups.tsv`: default popup registry
- `~/.config/tmux-popups/popups.local.tsv`: optional local overrides
- `examples/popups.optional.tsv`: optional popup row examples
- `tmux-popups.tmux`: TPM/manual entrypoint
- `scripts/list-popups.sh`: merged registry and dependency listing
- `scripts/generate-config.sh`: generates tmux bindings
- `scripts/run-popup.sh`: dispatches popup ids to tool scripts
- `scripts/doctor.sh`: diagnostics
- `scripts/popup-help.sh`: help popup
- `scripts/lib.sh`: shared shell helpers
- `scripts/tools/*.sh`: popup tool implementations

## License

MIT
