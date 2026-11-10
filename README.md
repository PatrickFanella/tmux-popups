# tmux-popups

<a href="https://tmux-popups.subcult.tv/">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/brand/lockup.svg">
    <img src="docs/brand/lockup-light.svg" alt="tmux-popups. Instrument Panel wordmark beside a popup over a terminal pane." height="80">
  </picture>
</a>

**Tools up. Context stays.**

tmux-popups is a tmux plugin that opens your terminal tools in popups or windows from one quick menu. You list tools in a tab-separated registry; the plugin builds the menu and direct key bindings from it, checks whether each tool is installed, and leaves your own bindings alone unless you tell it otherwise. It is plain Bash with optional Python 3 helpers and has no build step.

[Website](https://tmux-popups.subcult.tv/) · [Docs](https://tmux-popups.subcult.tv/docs/) · [Support SUBCULT](https://subcult.tv/support)

A [SUBCULT](https://subcult.tv) project.

![tmux-popups demo](assets/demo.gif)

## Features

- `Prefix+Enter` quick menu and direct bindings generated from the same registry rows.
- Default registry `popups.tsv`, plus a local registry (`~/.config/tmux-popups/popups.local.tsv`) that overrides or adds rows.
- Three launch modes: popup, window or command (foreground or background).
- Dependency checks: missing tools show as disabled menu labels, and dispatch checks again before launch.
- Your own scripts with exact arguments (JSON array, no shell expansion), or an explicit shell expression when you want one.
- Conflict handling for keys you already use, and restoration of your previous bindings when a plugin key is removed.
- Optional retained view after a tool fails, with retry, and optional reuse of a tool window per session or directory.
- Optional searchable launcher (`fzf`, with a tmux menu fallback) and project-aware actions.
- `scripts/doctor.sh` diagnostics and `scripts/list-popups.sh` listings.

## Install with TPM

Add to `~/.tmux.conf` or your sourced tmux config:

```tmux
set -g @plugin 'subculture-collective/tmux-popups'
```

Reload tmux, then press the TPM install key (`prefix + I`).

## Install manually

```sh
git clone https://github.com/subculture-collective/tmux-popups.git ~/.config/tmux/plugins/tmux-popups
```

Source the plugin entrypoint from your tmux config:

```tmux
run-shell "$HOME/.config/tmux/plugins/tmux-popups/tmux-popups.tmux"
```

Then reload tmux with `tmux source-file ~/.tmux.conf`.

To work on the plugin while TPM still manages it, clone it elsewhere and symlink the checkout to `~/.config/tmux/plugins/tmux-popups`; keep the `@plugin` line in your config.

## Default bindings

The default profile enables help, shell, daily notes, timer and tmux keys. The other shipped tools stay in the registry, off, and show with their status in help and `scripts/list-popups.sh --deps`.

| Key | Action |
| --- | --- |
| `Prefix+Enter` | Quick menu |
| `Prefix+C-h` | Help, dependency status and optional tools |
| `Prefix+T` | Shell |
| Menu `N` | Daily note |
| Menu `P` | Timer |
| `Prefix+C-b` | tmux keys |
| `Prefix+R` | Reload tmux config |

Turn a shipped tool on or off without editing its row:

```tmux
set -g @tmux-popups-lazygit-enabled 'on'
set -g @tmux-popups-chat-enabled 'off'
```

To enable every shipped row, launch tools even when dependencies are missing, and take over existing keys:

```tmux
set -g @tmux-popups-profile 'full'
set -g @tmux-popups-availability 'ignore'
set -g @tmux-popups-conflicts 'replace'
```

Session switching is left to [tmux-sessionx](https://github.com/omerxx/tmux-sessionx). For tmux's built-in picker, copy the `sessions` row from `examples/popups.optional.tsv`.

## Plugin options

Set these before the plugin loads, then reload through `tmux-popups.tmux`.

| Option | Default | Meaning |
| --- | --- | --- |
| `@tmux-popups-menu-key` | `Enter` | Key that opens the quick menu |
| `@tmux-popups-reload-key` | `R` | Key that reloads the tmux config |
| `@tmux-popups-config-file` | `~/.tmux.conf` | Config file the reload key sources |
| `@tmux-popups-default-width` | `80%` | Width for rows that use `-` |
| `@tmux-popups-default-height` | `80%` | Height for rows that use `-` |
| `@tmux-popups-local-registry` | `~/.config/tmux-popups/popups.local.tsv` | Local registry path |
| `@tmux-popups-user-script-directory` | `~/.config/tmux-popups/scripts` | Where `user` rows look for scripts |
| `@tmux-popups-profile` | `small` | `small` or `full` |
| `@tmux-popups-availability` | `show-disabled` | `show-disabled`, `hide-unavailable` or `ignore` |
| `@tmux-popups-conflicts` | `skip` | `skip`, `warn` or `replace` for keys you already bound |
| `@tmux-popups-yazi-mode` | `window` | `popup` or `window` for the Yazi tools |
| `@tmux-popups-enable-vscode` | `on` | Menu entry `v` that runs the vscode command in the pane's directory |
| `@tmux-popups-vscode-command` | `code .` | Command for that entry |
| `@tmux-popups-<id>-enabled` | from profile | `on` or `off` per row |
| `@tmux-popups-<id>-close` | `always` | `always`, `on-success` or `never` |
| `@tmux-popups-<id>-reuse` | `off` | `off`, `session` or `directory` (window mode only) |

`TMUX_POPUPS_LOCAL_REGISTRY` and `TMUX_POPUPS_USER_SCRIPT_DIRECTORY` in the environment take precedence over the matching options. Paths accept a leading `~/`.

## Registry format

Rows are tab-separated. Blank lines and lines starting with `#` are ignored. Use `-` for a default value.

```tsv
id	direct_key	menu_key	title	width	height	command	mode	completion	enabled	deps	kind	arguments
```

| Column | Meaning |
| --- | --- |
| `id` | Unique ID used by `scripts/run-popup.sh` |
| `direct_key` | Direct binding after the prefix, or `-` |
| `menu_key` | Key in the quick menu, or `-` |
| `title` | Popup title |
| `width`, `height` | Popup size such as `80%` or a cell count, or `-` for the default |
| `command` | Executable path interpreted by `kind`, or `-` for an interactive shell |
| `mode` | `popup`, `window` or `command` |
| `completion` | `foreground` or `background` (background is for command mode only) |
| `enabled` | `on` or `off` |
| `deps` | `auto`, `-`, or space-separated commands with `|` alternatives, such as `python3 fzf|sk` |
| `kind` | `plugin` (relative to the plugin), `absolute`, `user` (relative to the user-script directory) or `shell` |
| `arguments` | JSON array of strings, or `-` |

Rows may stop after any column from the seventh on; missing columns take their defaults. `auto` dependency checks apply to the shipped tool scripts; declare dependencies for your own scripts. Each JSON argument is passed as exactly one argument, with no expansion of `~`, variables or globs; JSON arguments need Python 3. Only the `shell` kind runs the command through `${SHELL:-bash} -c`.

Popup mode closes with the tool. Window mode opens a window in the invoking session. Command mode runs the executable through `run-shell` without a terminal; use it for tools that do not read input. Every mode starts in the invoking directory.

Examples, with real tabs between fields:

```tsv
personal	X	x	Personal script	80%	80%	record user's argv	popup	foreground	on	-	user	["two words", "it's literal", ""]
external	-	-	External script	80%	80%	/home/me/my scripts/task	command	foreground	on	-	absolute	["--project", "project with spaces"]
expression	-	-	Explicit shell	80%	80%	printf hello | cat	command	foreground	on	-	shell	-
```

## Local override registry

The plugin merges `popups.tsv` with your local registry. A local row with the same `id` replaces the default row in place; new IDs are added at the end. Keep the shipped `popups.tsv` unchanged so updates apply cleanly.

```tsv
chat	C-a	a	quick chat	-	-	scripts/tools/chat.sh
scratch	C-s	s	scratch shell	80%	80%	-
```

## Create a popup script

Keep personal scripts outside the plugin checkout:

```sh
mkdir -p "${XDG_CONFIG_HOME:-$HOME/.config}/tmux-popups/scripts"
cat > "${XDG_CONFIG_HOME:-$HOME/.config}/tmux-popups/scripts/hello.sh" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
printf 'Hello from tmux-popups.\n\nPress Enter to close... '
read -r _ || true
SH
chmod +x "${XDG_CONFIG_HOME:-$HOME/.config}/tmux-popups/scripts/hello.sh"
```

Add this row to your local registry:

```tsv
hello	F8	8	hello	75%	75%	hello.sh	popup	foreground	on	-	user	-
```

Reload through the plugin entrypoint, then press `Prefix+F8` or choose `8` from `Prefix+Enter`.

## Optional examples

- `examples/popups.optional.tsv`: extra rows, including tmux's session picker and a searchable launcher (`Prefix+M-Space`, menu `/`). The launcher uses `fzf` when installed and a tmux menu otherwise.
- `examples/popups.project.tsv`: project actions for Git status, a shell, project notes (`NOTES.md` at the Git root by default, or `TMUX_POPUPS_PROJECT_NOTES`) and a coding tool.

Copy the rows you want into your local registry, install the tools they need, and reload.

## Invoking context

Bindings and menu actions export the origin of each launch: `TMUX_POPUPS_CLIENT`, `TMUX_POPUPS_SESSION`, `TMUX_POPUPS_WINDOW`, `TMUX_POPUPS_PANE` and `TMUX_POPUPS_DIRECTORY`. The IDs refer to where you pressed the key, even when the tool runs in a new window. Your scripts can read them, or source `scripts/lib.sh` and call `close_origin_popup`. If the origin no longer exists, these helpers report an error instead of acting on another client.

## Failures, retry and window reuse

With `@tmux-popups-<id>-close` set to `on-success` or `never`, the view stays open after the tool exits and shows its exit status. Press `r` to run it again, `c` or Enter to close, or `w` in a popup to run it again in a new window. This needs Python 3.

With `@tmux-popups-<id>-reuse` set to `session` or `directory`, a window-mode tool returns to its live window instead of opening a new one.

## Keys you already use

The plugin records each prefix key it binds and the binding it replaced. With the default `skip` policy, an existing binding is kept and the conflict is reported. When you change or remove a plugin key, the previous binding comes back, but only if the plugin's binding is still in place. Your own later rebinds or unbinds are never overwritten.

Preview what a reload would do:

```sh
scripts/apply-config.sh --explain "${XDG_CACHE_HOME:-$HOME/.cache}/tmux-popups/generated.conf"
```

Always reload through `tmux-popups.tmux`. Sourcing `generated.conf` directly skips conflict handling and restoration.

## Listing and diagnostics

```sh
scripts/list-popups.sh --pretty
scripts/list-popups.sh --deps      # with dependency status
scripts/doctor.sh                  # tmux, TPM, registries, options, dependencies and conflicts
scripts/doctor.sh --input-check 10 # report the bytes and TERM a popup receives
```

`doctor.sh` validates a generated config in a temporary directory and does not change your bindings or cache. Warnings are informational; failures exit nonzero. See [troubleshooting](docs/troubleshooting.md) and [migration and recovery](docs/migration.md).

## Optional tools

The shipped rows use these when you turn them on: `lazygit`, `yazi`, `ferrosonic`, `task` (Taskwarrior), `nvim`/`vim`/`vi` or `$EDITOR`, `tldr`, `man`, `less`, `khal` or `cal`, `python3`, `ssh`, `fzf`, `cliphist`, `wl-copy`, `wl-paste`, `newsboat`, `curl`, `journalctl`, `tail`, `watch`, `glow`, `bat`, `opencode`, and `ocq` with Node.js for quick chat.

| Variable | Used by | Default |
| --- | --- | --- |
| `NOTES_DIR` | `notes` | `~/Notes/daily` |
| `PROJECTS_DIR` | `projects` | `~/Projects` |
| `TMUX_POPUPS_YAZI_SAFE` | Yazi tools | `on` (disables preview plugins, which break inside tmux popups) |

Yazi opens in a window by default because it can time out on terminal queries inside `display-popup`.

## How it works

```text
popups.tsv + optional local registry
  -> scripts/list-popups.sh --tsv
  -> scripts/generate-config.sh
  -> ~/.cache/tmux-popups/generated.conf
  -> scripts/apply-config.sh
  -> reconciled tmux prefix bindings
```

Generation validates the new bindings on the running tmux server in temporary key tables and replaces the cache only when they pass. `scripts/run-popup.sh <id>` dispatches a row; bindings call it with `--launch`.

## Project layout

```txt
tmux-popups.tmux      TPM and manual entrypoint
popups.tsv            default registry
examples/             optional and project rows
scripts/              generator, applier, dispatcher, doctor, listings and helpers
scripts/tools/        the shipped tool scripts
tests/                isolated regression tests
site/                 product website
```

## Contributing

Report bugs and request features in [GitHub issues](https://github.com/subculture-collective/tmux-popups/issues). Open pull requests on GitHub against `main`.

CI runs Bash syntax checks, ShellCheck, the isolated regression suite and the website checks on every pull request. Run the same checks locally with Git, Python 3, ShellCheck, tmux and GNU `timeout` installed:

```sh
scripts/check.sh
python3 scripts/check-site.py
```

`tests/run.sh` runs only the regression suite. [tests/README.md](tests/README.md) explains the fixtures.

## License

MIT. See [LICENSE](LICENSE).
