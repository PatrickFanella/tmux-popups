# Diagnose a launcher problem

Run commands from the plugin checkout in the affected attached tmux session.
Start with `scripts/doctor.sh`. Ordinary diagnosis leaves the shared cache,
effective bindings and ownership unchanged. Explicit executable arguments and
shell expressions are omitted from its report.

| Symptom | Check and next action |
| --- | --- |
| A direct key opens another tool | Read the binding plan and `tmux list-keys -N`. The default `skip` policy keeps an existing binding. Change the registry key or choose `warn` or `replace`, then reload the entrypoint. |
| A removed key stays rebound | Reload through `tmux-popups.tmux`. A later user replacement or unbind is protected. Unknown bindings from older versions have no restorable ownership record. |
| A tool is absent from the menu | Check `scripts/list-popups.sh --deps` for enabled state and missing dependency groups. Per-entry options override the profile. `hide-unavailable` omits missing tools; `show-disabled` keeps a disabled menu label. |
| A tool exists but fails immediately | Dependency checks establish executable presence, not configuration, credentials or compatibility. Run the adapter from an attached terminal or set its popup/window close policy to `on-success` to retain output. |
| An edit has no effect | Check the selected registry and provenance in doctor or `--origin-tsv`. A nonempty environment registry takes precedence over the tmux option. Reload through the entrypoint after changing options or rows. |
| A registry fails validation | Use actual tabs and `-` for defaults. Check the reported file and line, executable permissions, JSON arguments and duplicate keys. Even disabled and overridden source rows are validated. The last good cache remains available. |
| Generation says no server is running | Run it inside the target tmux server. Listing can use a private temporary server outside tmux, but generation needs a real target. |
| A window returns to an earlier directory | Reuse returns to the original live process. Use `directory` scope or disable reuse, then close and relaunch. Project actions may change to the Git root while the origin variable retains the invoking directory. |
| Retry uses an old environment | Close and relaunch to pick up server environment changes. Retry keeps the recovery view's environment while revalidating the current executable and original pane/client. |
| Closing a retained failure shows another tmux view | The nonzero status is retained. Press `q` to dismiss tmux's normal run-shell error view. |

## Compare popup and window input

Run this bounded check explicitly in the affected terminal:

```sh
scripts/doctor.sh --input-check 10
```

Type `tmux-popups` and press Enter. Compare the received bytes. Ctrl-C cancels;
the timeout is ten seconds. A successful line check proves that input arrived,
but does not qualify terminal queries or the application's own key handling.

Check focus and record `TERM`, `tmux -V`, the terminal/application versions,
client count, mode and exact keys that failed. Compare the same application in
popup and window mode on a disposable server. Report paste, Enter, Escape,
Ctrl-C, resize and reopen separately. Command mode provides no interactive
terminal. Its background policy connects all three standard streams to `/dev/null`.

## Diagnose Yazi

Enable the Yazi entry before testing; it is optional in the small profile.
The shipped Yazi adapters use window mode by default. Keep that mode while
investigating historical popup terminal-response timeouts. Explicit `popup`
rows take precedence over the legacy Yazi mode option.

`TMUX_POPUPS_YAZI_SAFE` defaults to `on`. The launcher creates a cache config
that disables preview and preload plugins. Set it to `off` only when comparing
your full configuration. Neither safe mode nor the wrapper's warning establishes
that the actual Yazi version works in your terminal. Keep image passthrough and
terminal-query results in the qualification record.

## Diagnose optional providers

Chat requires `ocq` and Node.js, plus a working provider configuration. Its
errors retain the last valid session and return to the prompt. Ctrl-C cancels
an owned request and closes chat. Clipboard failures keep chat open.

OpenCode and other provider-backed tools need their own configuration. A
substitute executable or passing CI does not establish authentication, network
availability or real provider behavior. Keep real-provider checks separate from
launcher and keyboard checks, and omit credentials from reports.
