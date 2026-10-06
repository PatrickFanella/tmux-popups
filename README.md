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

The small default enables help, shell, daily notes, timer and tmux keys. Optional
adapters remain in the registry and appear with their enabled/dependency status
in help and `scripts/list-popups.sh --deps`.

| Key | Action |
| --- | --- |
| `Prefix+Enter` | Quick menu |
| `Prefix+C-h` | Help, dependency status and optional adapter discovery |
| `Prefix+T` | Shell |
| Menu `N` | Daily note |
| Menu `P` | Timer |
| `Prefix+C-b` | tmux keys |
| `Prefix+R` | Reload tmux config |

To retain the previous full menu and direct keys, set these before loading:

```tmux
set -g @tmux-popups-profile 'full'
set -g @tmux-popups-availability 'ignore'
```

`full` enables every shipped row. `ignore` retains the previous behavior of
launching adapters even when their dependencies are missing. Leave availability
at its default to show unavailable tools as disabled menu labels instead.
Local rows and per-entry options still take precedence over the profile.

Enable an optional adapter without copying or deleting its row:

```tmux
set -g @tmux-popups-lazygit-enabled 'on'
set -g @tmux-popups-chat-enabled 'off'
```

Reload through the plugin entrypoint after changing settings. An `off` row has
no direct or menu binding and cannot be dispatched by ID. It remains listed for
discovery. Existing seven-, eight- and nine-column local rows default to enabled,
including local overrides of optional shipped rows.

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
set -g @tmux-popups-profile 'small'
set -g @tmux-popups-availability 'show-disabled'
```

`@tmux-popups-config-file` is the tmux config file reloaded by the reload binding (`@tmux-popups-reload-key`, default `R`) and the Quick Menu "reload tmux" entry. Defaults to `~/.tmux.conf`. Set this if your config lives elsewhere, for example:

```tmux
set -g @tmux-popups-config-file '~/.config/tmux/tmux.conf'
```

Config paths, local registry paths and `PROJECTS_DIR` accept a literal `~/`
prefix or bare `~`. They expand to the home directory once. Absolute and
ordinary relative paths stay as supplied; variable expressions and command
substitutions in these settings are treated as text.

Generation, dispatch, help and doctor select the same local registry. A nonempty
`TMUX_POPUPS_LOCAL_REGISTRY` environment value takes precedence over
`@tmux-popups-local-registry`, followed by the optional XDG config default.
An explicitly selected registry must be a readable file; a missing optional
default is allowed. Set the environment value when running a CLI helper against
a particular registry.

Use `-` in a row's width or height to inherit the default width/height options.

## Registry format

Rows are tab-separated:

```tsv
id	direct_key	menu_key	title	width	height	command	mode	completion	enabled	deps
```

| Column | Meaning |
| --- | --- |
| `id` | Unique popup id used by `scripts/run-popup.sh` |
| `direct_key` | Direct tmux binding after prefix, or `-` for none |
| `menu_key` | Key in quick menu, or `-` for none |
| `title` | Popup title |
| `width` | tmux popup width, e.g. `80%`, or `-` for default |
| `height` | tmux popup height, e.g. `80%`, or `-` for default |
| `command` | Executable path interpreted by `kind`, or `-` for the legacy interactive shell |
| `mode` | Optional `popup`, `window`, `command`, or `-` for compatibility defaults |
| `completion` | Optional `foreground`, `background`, or `-` for foreground |
| `enabled` | Optional `on` or `off`; old rows default to `on` |
| `deps` | Optional `auto`, `-`, or space-separated command groups with `|` alternatives |
| `kind` | Optional `plugin`, `absolute`, `user`, `shell`, or `-` for `plugin` |
| `arguments` | Optional JSON array of strings, or `-` for no arguments |

Blank lines and lines beginning with `#` are ignored. Seven-column rows remain
valid. Eight-column rows add mode; nine-column rows add completion. Ten columns
add enabled; eleven add dependency metadata. Twelve add execution kind; thirteen
add explicit arguments. Supplied
fields must be nonempty, so use `-` for a default. `--tsv` emits nine columns
with resolved mode and completion; `--deps-tsv` appends dependencies and status.
`--state-tsv` emits those nine columns followed by enabled, dependencies and
status. `--execution-tsv` appends kind and arguments to `--state-tsv`.
The existing output layouts remain unchanged. All listing modes retain disabled
and unavailable rows.

`auto` checks the effective shipped adapter path, never the entry ID. Renaming
an adapter entry keeps its dependency checks; replacing its command changes
them. Unknown custom executables have no inferred external requirements. Their
file must still exist and be executable. Declare requirements explicitly when
needed, for example `python3 fzf|sk`, or use `-` to bypass external checks. This
metadata does not evaluate shell expressions or change command arguments.

### User scripts and arguments

`plugin` resolves an executable relative to the plugin checkout. `absolute`
requires an absolute executable path and expands a literal `~/` prefix once.
`user` resolves a relative executable beneath the user-script directory. These
kinds require a regular executable file, including for disabled rows, and check
it again at dispatch. Paths are single fields; do not add shell quotes around
them. Spaces and apostrophes are part of the filename. Relative paths are joined
to their selected directory; `..` is allowed, so this is not a sandbox.

The user-script directory defaults to
`${XDG_CONFIG_HOME:-$HOME/.config}/tmux-popups/scripts`. A nonempty
`TMUX_POPUPS_USER_SCRIPT_DIRECTORY` environment value overrides
`@tmux-popups-user-script-directory`, which overrides that default. The selected
directory must be absolute after literal home expansion. The plugin never
creates, updates or removes user scripts or the local registry. Keep these files
outside the plugin checkout and `${XDG_CACHE_HOME:-$HOME/.cache}/tmux-popups`,
which contains generated data. Reload after changing the registry or options.

```tmux
set -g @tmux-popups-user-script-directory '~/my scripts'
```

For example, these rows use actual tabs between fields:

```tsv
personal	X	x	Personal script	80%	80%	record user's argv	popup	foreground	on	-	user	["two words", "it's literal", ""]
external	-	-	External script	80%	80%	/home/me/my scripts/task	command	foreground	on	-	absolute	["--project", "project with spaces"]
expression	-	-	Explicit shell	80%	80%	printf hello | cat	command	foreground	on	-	shell	-
```

JSON arguments require Python 3. Each string is exactly one argument, including
empty strings, spaces, apostrophes and JSON-escaped tabs or newlines. NUL and
surrogate code points are rejected. Arguments never expand `~`, variables,
globs or command substitutions. Keep the array on one physical TSV line.
Missing Python or malformed arguments fail validation before cache publication.
Old rows with no arguments do not gain a Python dependency.

`shell` explicitly opts into `${SHELL:-bash} -c` and treats `command` as a shell
expression. It requires `arguments` to be `-`; put any shell syntax in the
expression itself. Shell expressions are evaluated only during execution.
`auto` infers dependencies only for `plugin` adapters. Other kinds have no
inferred requirements; declare their dependencies explicitly. The legacy
`command` value `-` with kind `plugin` still opens an interactive shell and
accepts no arguments. Existing modes, completion policies, invoking context,
enabled controls and registry precedence apply to all execution kinds.

Availability policies apply to enabled rows:

- `show-disabled`, the default, omits unavailable direct bindings and shows a
  disabled menu label with `missing:<commands>`.
- `hide-unavailable` omits unavailable direct and menu bindings. Help and CLI
  dependency output still show the reason.
- `ignore` launches without a dependency preflight, for explicit compatibility
  or user-managed environments.

Dispatch rechecks availability, so a removed dependency cannot launch silently
from a stale menu. It reports the missing group to the origin client and stderr
and returns 127. Dependency checks establish presence, not provider credentials,
configuration or terminal compatibility. `khal` also needs a successful
`--version`, matching its adapter's fallback to `cal`.

The editor resolver honors a nonempty `EDITOR` as one executable name or path.
Otherwise it chooses the first available `nvim`, `vim`, then `vi`. The shell
resolver honors a nonempty `SHELL`, otherwise it uses `bash`. An explicit missing
editor or shell is reported as unavailable rather than replaced by another
command. Execution and dependency checks use these same resolvers.

Legacy rows and rows with mode `-` default to popup. The four shipped adapters
`yazi.sh`, `home.sh`, `projects.sh` and `downloads.sh` under `scripts/tools/` default
to window and honor `@tmux-popups-yazi-mode`, which accepts popup or window.
This compatibility rule follows the executable path, including renamed entries.
A legacy local override pointing at another adapter defaults to popup. Add an
explicit mode to keep a different launch policy. Explicit modes take precedence
over the legacy option, even for Yazi adapters. Entry IDs never choose a mode.

Popup uses the row dimensions, inherits configured dimensions for `-`, and
closes when the adapter exits through `display-popup -E`. Window creates a
window in the origin session, uses the session's dimensions and normal tmux
`remain-on-exit` behavior. Width and height remain validated in every mode but
only affect popup. Both run the adapter in the invoking directory.

Command runs the executable directly without a popup or window, in the invoking
directory with the same origin variables. Foreground is the default. The tmux
`run-shell` action waits for completion and displays output through tmux; it does
not provide an interactive terminal. A nonzero exit produces tmux's normal run-shell diagnostic view, dismissed with
`q`. A CLI call returns the adapter's exit code.
Background starts the adapter with stdin, stdout and stderr connected to
`/dev/null`, then returns success after starting it. It neither waits nor reports
the later exit status. The adapter owns any durable output it needs. Background
is valid only for command mode; command mode requires an executable, not `-`.
No shell expression or arguments are evaluated from the command column.

Choose an adapter that does not require terminal input for command entries.
`run-popup.sh <id>` executes adapters directly for CLI callers. `--launch` is the
binding/menu entrypoint that creates popup or window presentation. Command
completion policy applies to both entrypoints.
CLI calls without a running tmux server validate registry keys using a private,
temporary server, then remove that server and its socket before dispatch.

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
shows a warning before launching a Yazi adapter in popup mode.

## How it works

```text
popups.tsv + optional local registry
  -> scripts/list-popups.sh --tsv
  -> scripts/generate-config.sh
  -> ~/.cache/tmux-popups/generated.conf
  -> scripts/apply-config.sh
  -> reconciled tmux prefix bindings
```

`scripts/run-popup.sh <id>` reads the merged registry and executes the matching adapter. Bindings and menu actions use `--launch` to apply its presentation mode.

## Files

- `popups.tsv`: default popup registry
- `~/.config/tmux-popups/popups.local.tsv`: optional local overrides
- `examples/popups.optional.tsv`: optional popup row examples
- `tmux-popups.tmux`: TPM/manual entrypoint
- `scripts/list-popups.sh`: merged registry and dependency listing
- `scripts/generate-config.sh`: generates tmux bindings
- `scripts/apply-config.sh`: validates and reconciles binding ownership
- `scripts/run-popup.sh`: dispatches popup ids to tool scripts
- `scripts/doctor.sh`: diagnostics
- `scripts/popup-help.sh`: help popup
- `scripts/lib.sh`: shared shell helpers
- `scripts/tools/*.sh`: popup tool implementations

## License

MIT

## Verification

Run `scripts/check.sh` for syntax, ShellCheck and isolated launcher regressions.
See [the verification guide](tests/README.md) for required tools, fixture isolation
and the separate real-terminal release gates.

### Binding restoration on reload

The plugin saves each effective prefix binding and its prior binding on the tmux
server. Changing or removing a direct, menu or reload key restores the prior
binding, including its note and repeat flag. If the key had no prior binding,
it is unbound. Restoration only happens when the current binding still matches
what the plugin installed. Other key tables are untouched.

A user replacement or explicit unbind stays in effect across repeated reloads,
even while that plugin key remains configured. Removing the key from the plugin
configuration ends its ownership record. Configuring it again later starts a
new record. New keys retain the existing overwrite behavior; conflict policy
is tracked in #18. Bindings from versions that did not record ownership cannot
be safely identified or restored automatically.

Reload through `tmux-popups.tmux` so generation and reconciliation both run.
The reconciler validates new bindings in a temporary key table before changing
prefix keys, serializes reloads on the server, and rolls back touched keys and
ownership state if applying the transition fails.


### Registry validation and cache publication

Every non-comment registry row must have seven through eleven nonempty TSV fields.
IDs accept letters, digits, underscores and hyphens. Keys accept a single
printable character or a named tmux key with C-, M- or S- modifiers. Use `-`
to disable a shortcut. Dimensions accept cell counts from 1 through 2147483647, 1% through
100%, or `-` for the configured default. Commands must name an existing
executable plugin-relative file, or `-` for the shell. Optional tool availability
is checked separately, so a wrapper can be valid while its tool is not installed.
Disabled rows still undergo full validation, including metadata and shortcuts. Titles cannot contain tmux formats or carriage returns.

Errors identify the registry file and line, and listing emits no partial TSV.
All source rows are checked, including rows replaced by an intentional same-ID
override. Shortcuts are checked on the final merged rows. Duplicate direct or
menu shortcuts and collisions with the built-in menu, reload, Exit and enabled
vscode shortcuts fail generation. Direct and menu keys use separate namespaces.
Listing checks every source key against the selected tmux server before merging.
Target-normalized collisions identify both source rows or the built-in slot.

Generation requires a running target tmux server. Listing can use a private
temporary server when called outside tmux. Generation writes
an owned temporary file beside `generated.conf`, parses it on that server, and validates bindings
in disposable key tables without changing effective keys or ownership. Only a
successful validation replaces the cache with an atomic rename. Failure leaves
the last valid cache intact and removes owned temporary files and tables.
Overlapping writers use separate files and tables; the last successful rename
wins. Readers see a complete previous or new config. A failed writer cannot
replace a successful writer's config. Binding application remains the separate
server-serialized transaction described above.

The configurable vscode menu command runs through `run-shell` with a shell-quoted
pane directory, including on tmux 3.3a. It retains shell command semantics.

### Invoking context

Direct bindings and menu actions capture the invoking context when tmux dispatches
an entry. Both popup and window launches export `TMUX_POPUPS_CLIENT`,
`TMUX_POPUPS_SESSION`, `TMUX_POPUPS_WINDOW`, `TMUX_POPUPS_PANE` and
`TMUX_POPUPS_DIRECTORY`. The IDs refer to the origin, even when an adapter runs
in a newly created window. The directory remains literal data, including spaces
and shell expressions. Popup launches target the origin client and pane; new
windows target the origin session explicitly.

Local scripts may read these variables or source `scripts/lib.sh` and call
`close_origin_popup`. The optional sessions adapter targets the origin pane and
switches only the invoking client. If an origin vanishes, these helpers report
an error and cancel the action. They never fall back to an unrelated client.
Exiting an adapter still exits normally. `run-popup.sh <id>` also accepts the
contract through its environment. Without it, the CLI uses `TMUX_PANE` for pane,
session and window IDs and `$PWD` for the directory, leaving the client unset.
Client actions then cancel. Calls outside tmux can still run ordinary adapters.
This contract applies to popup, window and command launch modes.
