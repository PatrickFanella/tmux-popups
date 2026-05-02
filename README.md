# tmux-popups

Small tmux popup toolkit with a TSV registry, generated bindings, and shell tools.

## Features

- `Prefix+d` quick menu generated from `popups.tsv`
- Direct bindings for common popups like chat, yazi, lazygit, notes, keys, and sessions
- Popup tools for tasks, notes, docs/man pages, calendar, calculator, SSH hosts, clipboard, weather/news, timer, logs, watch, and markdown preview
- No build step; POSIX-ish Bash scripts plus tmux
- Generated config stored at `${XDG_CACHE_HOME:-$HOME/.cache}/tmux-popups/generated.conf`

## Install with TPM

Add to `~/.tmux.conf`:

```tmux
set -g @plugin 'patrickfanella/tmux-popups'
```

Reload tmux, then press TPM install key (`prefix + I`).

## Install manually

Clone somewhere, then run the plugin script from your tmux config:

```sh
git clone https://github.com/patrickfanella/tmux-popups.git ~/.config/tmux/plugins/tmux-popups
```

```tmux
run-shell "$HOME/.config/tmux/plugins/tmux-popups/tmux-popups.tmux"
```

Reload tmux:

```sh
tmux source-file ~/.tmux.conf
```

## Default bindings

Direct bindings:

| Key | Popup |
| --- | --- |
| `Prefix+d` | Quick menu |
| `Prefix+C-h` | Popup help |
| `Prefix+C-g` | Quick chat (`ocq`) |
| `Prefix+C-o` | `opencode` |
| `Prefix+C-t` | Shell |
| `Prefix+C-n` | Daily note |
| `Prefix+C-y` | `lazygit` |
| `Prefix+C-r` | `yazi` |
| `Prefix+C-f` | `ferrosonic` |
| `Prefix+C-j` | tmux sessions |
| `Prefix+C-b` | tmux key list |
| `Prefix+C-z` | edit `~/.zshrc` |
| `Prefix+C-S-r` | reload tmux config |

The quick menu includes additional tools: tasks, docs, calendar, calculator, SSH, clipboard, weather/news, timer, logs, watch, markdown preview, config edit, home/projects/downloads, VS Code, and reload.

## Optional tools

Popups degrade where possible, but these tools unlock more entries:

- `ocq` for quick chat
- `opencode`
- `task` / Taskwarrior
- `nvim` or `$EDITOR`
- `tldr`, `man`
- `khal`, `cal`
- `fzf`
- `cliphist`, `wl-copy`, `wl-paste`
- `newsboat`, `curl`
- `glow`, `bat`
- `lazygit`, `yazi`, `ferrosonic`

## Add or change a popup

Edit `popups.tsv`:

```tsv
id	direct_key	menu_key	title	width	height	command
```

Use `-` for no direct key, no menu key, or no command. Commands are paths relative to the plugin root.

Reload tmux after edits:

```sh
tmux source-file ~/.tmux.conf
```

## Files

- `popups.tsv`: source of truth for popup id, keys, title, size, command
- `tmux-popups.tmux`: TPM/manual entrypoint
- `scripts/generate-config.sh`: generates tmux bindings
- `scripts/run-popup.sh`: dispatches popup ids to tool scripts
- `scripts/lib.sh`: shared shell helpers
- `scripts/tools/*.sh`: popup tool implementations
