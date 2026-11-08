# Migrate and recover a tmux-popups installation

Use the [registry reference](../README.md#registry-format) for field details and
[troubleshooting](troubleshooting.md) for diagnosis. Keep personal registries and
scripts outside the plugin checkout and generated cache.

## Save the current revision

For the manual installation path in the README, run these commands in one shell:

```sh
plugin="$HOME/.config/tmux/plugins/tmux-popups"
local_registry="${XDG_CONFIG_HOME:-$HOME/.config}/tmux-popups/popups.local.tsv"
saved="${XDG_STATE_HOME:-$HOME/.local/state}/tmux-popups/update-$(date +%Y%m%d-%H%M%S)"
git -C "$plugin" status --short
mkdir -p "$saved"
git -C "$plugin" rev-parse HEAD > "$saved/revision"
if [ -f "$local_registry" ]; then
	cp "$local_registry" "$saved/popups.local.tsv"
fi
printf 'Recovery files: %s\n' "$saved"
```

If `git status --short` lists changes, save or commit those changes before
updating. Do not reset or clean the checkout to get past an update failure.
For a different installation or an explicitly selected registry, adjust the
first two assignments to those existing paths before running the commands.
Save a copy of your tmux configuration before editing its options.

## Retain the previous full menu

The default profile enables help, shell, daily notes, timer and tmux keys.
To retain the previous full menu and prefix-key replacement behavior, put these
options before the plugin load in your tmux configuration:

```tmux
set -g @tmux-popups-profile 'full'
set -g @tmux-popups-availability 'ignore'
set -g @tmux-popups-conflicts 'replace'
```

`ignore` skips dependency preflight. To keep missing tools visible as disabled
menu labels, use `show-disabled` instead. To preserve keys already claimed by
your configuration, use the default conflict policy `skip`.

Seven-column rows remain valid. Add only the fields you need, in order: mode,
completion, enabled, dependencies, kind, then JSON arguments. Use `-` for defaults;
an empty field is invalid. An old local row defaults to enabled even when it
overrides an optional shipped row. A per-entry enabled option takes precedence
over the row and profile.

A local row replaces the shipped row with the same ID while retaining its
position. New IDs append. A nonempty `TMUX_POPUPS_LOCAL_REGISTRY` selects the
registry before the tmux option, then the optional XDG default. Explicitly
selected missing files are errors. These rules also apply to CLI listing,
help, doctor and dispatch.

## Add personal tools

Follow [Create a popup script](../README.md#create-a-popup-script) to create
`hello.sh` in the user-script directory and add its thirteen-column row to your
local registry. Use actual tabs. Use a `user` or `absolute` executable kind for
personal files; executable paths are literal fields and need no shell quotes.
Only `shell` opts into expression evaluation. JSON arguments require Python 3.

Copy selected rows from [optional tools](../examples/popups.optional.tsv) or
[project actions](../examples/popups.project.tsv). Avoid copying both sets of
rows with the same shortcuts. Validation reports collisions before replacing
the last good cache. Disabled rows still require valid metadata and executables.
A missing external dependency can remain listed, with its availability reason.

Choose `popup` for an interactive popup, `window` for a normal tmux window, or
`command` for an action that needs no terminal input. Background completion is
valid only for command mode. The legacy Yazi adapters default to window mode;
explicit row modes take precedence over `@tmux-popups-yazi-mode`.

Per-entry `@tmux-popups-<id>-close` defaults to `always`. Use `on-success` to
retain failures, or `never` to retain every exit in popup or window mode. These
policies require Python 3. Retry starts another process with the original
invoking context. Popup recovery can start another process in a window.

Per-entry `@tmux-popups-<id>-reuse` defaults to `off`. Use `session` or `directory`
only for window entries. Directory scope matches the exact invoking directory,
including for project actions that later change to the Git root. A reused
process keeps its original environment. See [context](../README.md#invoking-context)
for the five exported origin variables.

## Update and reload

For a clean manual checkout, fetch and select canonical Gitea main:

```sh
git -C "$plugin" fetch origin main
git -C "$plugin" switch --detach origin/main
```

For a TPM-managed checkout, use TPM's update key (`Prefix+U`) and select
`tmux-popups`. TPM's `PatrickFanella/tmux-popups` shorthand uses the GitHub push
mirror. Canonical changes and pull requests live on Gitea. Do not change your
origin merely to run the validation commands below.

From an attached pane, source your configured tmux config if its options changed,
then diagnose and reload through the plugin entrypoint:

```sh
"$plugin/scripts/doctor.sh"
"$plugin/tmux-popups.tmux"
```

Read conflicts in the doctor output. `skip` leaves existing keys in place.
`warn` reports and replaces a newly claimed key. `replace` replaces it silently.
All policies protect a later user replacement or explicit unbind of an owned key.
Change the conflicting key or deliberately select a policy, then reload again.
Do not source `generated.conf` directly.

Reload restores a prior binding when the current binding still matches the
plugin's owned binding. Versions that did not record ownership cannot restore
unknown prior keys. Reapply your tmux configuration or start an isolated test
server when assessing an older installation's binding history.

## Return to the saved revision

In the same shell, use the saved revision and reload that entrypoint:

```sh
git -C "$plugin" switch --detach "$(cat "$saved/revision")"
"$plugin/tmux-popups.tmux"
```

If you also changed the local registry, compare it with
`$saved/popups.local.tsv` and restore the compatible rows you need before reloading.
New fields and options may be unsupported by an older revision. Restore your
previous tmux options as well. The plugin does not replace personal script or
registry files during an update or rollback. Existing tool processes keep their
old environment until closed and relaunched.

## Validate before relying on an update

From the candidate checkout, run `scripts/check.sh` with the tools listed in
[the verification guide](../tests/README.md). Validate the selected registry with
`scripts/list-popups.sh --origin-tsv`. Run doctor inside the affected tmux server.
Test direct, menu and search launch paths that you use, including normal exit,
cancellation and reload. Record your terminal, tmux and application versions
when comparing popup and window behavior.

CI and controlled terminal fixtures do not qualify real provider requests or
all native terminal applications. See [qualification records](verification/README.md).
Tags, releases and changes to a user's installation require the separate release
review in [issue #25](https://git.subcult.tv/PatrickFanella/tmux-popups/issues/25).
