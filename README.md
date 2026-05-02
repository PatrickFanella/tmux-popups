# tmux-popups

Small tmux popup toolkit with a TSV registry, generated bindings, and shell tools.

The default registry is intentionally dependency-light: tmux + shell, with graceful fallback if `less` is missing. Extra popups that need tools like `ocq`, `opencode`, `task`, `fzf`, `yazi`, or `lazygit` live in `examples/popups.optional.tsv` as copy/paste examples.

## Features

- `Prefix+d` quick menu generated from `popups.tsv`
- Direct bindings generated from the same registry
- One source of truth: `popups.tsv`
- No build step; Bash scripts plus tmux
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
git clone https://github.com/PatrickFanella/tmux-popups.git ~/.config/tmux/plugins/tmux-popups
```

```tmux
run-shell "$HOME/.config/tmux/plugins/tmux-popups/tmux-popups.tmux"
```

Reload tmux:

```sh
tmux source-file ~/.tmux.conf
```

## Default bindings

These defaults avoid non-core app dependencies.

| Key | Popup |
| --- | --- |
| `Prefix+d` | Quick menu |
| `Prefix+C-h` | Popup help |
| `Prefix+C-t` | Shell |
| `Prefix+C-b` | tmux key list |
| `Prefix+C-S-r` | reload tmux config |

The quick menu also includes the timer popup.

## Session management

`tmux-popups` does not bind a session picker by default. For session switching, use [`tmux-sessionx`](https://github.com/omerxx/tmux-sessionx) beside this plugin.

Example TPM config:

```tmux
set -g @plugin 'omerxx/tmux-sessionx'
set -g @sessionx-bind 'j'
set -g @sessionx-prefix 'on'
set -g @sessionx-window-height '80%'
set -g @sessionx-window-width '60%'
```

Then `Prefix+j` opens sessionx.

If you prefer tmux's built-in session picker instead, copy the `sessions` row from `examples/popups.optional.tsv` into `popups.tsv`.

## Add, create, or edit popups

### 1. Understand the registry

Edit `popups.tsv`:

```tsv
id	direct_key	menu_key	title	width	height	command
```

Columns:

| Column | Meaning |
| --- | --- |
| `id` | Unique popup id used by `scripts/run-popup.sh` |
| `direct_key` | Direct tmux binding after prefix, or `-` for none |
| `menu_key` | Key in `Prefix+d` quick menu, or `-` for none |
| `title` | Popup title |
| `width` | tmux popup width, e.g. `80%` |
| `height` | tmux popup height, e.g. `80%` |
| `command` | Plugin-relative script path, or `-` for an interactive shell |

Use tabs between columns. Use `-` for blank/disabled fields.

### 2. Add a shell-only popup

Add this row to `popups.tsv`:

```tsv
scratch	C-s	s	scratch shell	80%	80%	-
```

Reload tmux:

```sh
tmux source-file ~/.tmux.conf
```

Now use:

- `Prefix+C-s` for the direct popup
- `Prefix+d`, then `s` from the quick menu

### 3. Create a new popup script

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

Add a row to `popups.tsv`:

```tsv
hello	-	h	hello	75%	75%	scripts/tools/hello.sh
```

Reload tmux:

```sh
tmux source-file ~/.tmux.conf
```

Open it with `Prefix+d`, then `h`.

### 4. Edit an existing popup

Change its row in `popups.tsv`, then reload tmux.

Example: make the shell popup larger:

```tsv
shell	C-t	Enter	shell	90%	85%	-
```

Reload:

```sh
tmux source-file ~/.tmux.conf
```

### 5. Add optional dependency popups

Optional popups are included as examples in:

```text
examples/popups.optional.tsv
```

Copy rows you want into `popups.tsv`, install the matching tool, then reload tmux.

Example: tmux native sessions does not need extra dependencies, but is optional because `tmux-sessionx` is recommended for session management:

```tsv
sessions	C-j	j	sessions	80%	80%	scripts/tools/sessions.sh
```

Example: quick chat needs [`ocq`](https://github.com/PatrickFanella/ocq):

```tsv
chat	C-g	g	quick chat	80%	80%	scripts/tools/chat.sh
```

Example: yazi file manager needs `yazi`:

```tsv
yazi	C-r	r	yazi	80%	80%	scripts/tools/yazi.sh
```

Reload after copying examples:

```sh
tmux source-file ~/.tmux.conf
```

### 6. Validate generated config

Run:

```sh
scripts/generate-config.sh
tmux source-file -n ~/.cache/tmux-popups/generated.conf
```

If tmux reports no errors, reload normally:

```sh
tmux source-file ~/.tmux.conf
```

## Optional tools

Rows in `examples/popups.optional.tsv` can use:

- `tmux choose-tree` for native tmux session switching
- [`ocq`](https://github.com/PatrickFanella/ocq) for quick OpenCode chat
- `opencode`
- `task` / Taskwarrior
- `nvim`, `vim`, `vi`, or `$EDITOR`
- `tldr`, `man`
- `khal`, `cal`
- `python3`
- `fzf`
- `cliphist`, `wl-copy`, `wl-paste`
- `newsboat`, `curl`
- `journalctl`, `tail`, `watch`
- `glow`, `bat`
- `lazygit`, `yazi`, `ferrosonic`

## How it works

```text
popups.tsv
  -> scripts/generate-config.sh
  -> ~/.cache/tmux-popups/generated.conf
  -> tmux source-file
```

`scripts/run-popup.sh <id>` reads `popups.tsv` and executes the matching command inside `display-popup`.

## Files

- `popups.tsv`: default popup registry and source of truth
- `examples/popups.optional.tsv`: optional popup rows with extra dependencies
- `tmux-popups.tmux`: TPM/manual entrypoint
- `scripts/generate-config.sh`: generates tmux bindings
- `scripts/run-popup.sh`: dispatches popup ids to tool scripts
- `scripts/lib.sh`: shared shell helpers
- `scripts/tools/*.sh`: popup tool implementations

## License

MIT
