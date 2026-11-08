# tmux-popups introduction packet

Draft for SUBCULT, November 8, 2026. Based on [context](context.md). No channel
publication, spend or schedule is authorized by this packet. Site links below
are intended destinations and must respond before a post is approved.

## Product brief and page copy

**Tools up. Context stays.**

A quick menu for your tmux tools. Open a shell, jot a note, start a timer.
One TSV registry generates the menu and your direct bindings. Start with help,
shell, daily notes, timer and tmux keys; enable more tools when you need them.

Keep personal rows outside the checkout. A matching ID overrides the shipped
entry, and a new ID adds one. The launcher uses Bash and tmux; optional helpers
have their own dependencies. Source is MIT licensed, with no tagged release yet.

Primary action: install with TPM at <https://tmux-popups.subcult.tv/#install>.
Secondary action: <https://tmux-popups.subcult.tv/docs/>.
Feedback: <https://git.subcult.tv/PatrickFanella/tmux-popups/issues>.

**Short description:** A small tmux popup toolkit. One TSV registry for your
quick menu and direct bindings, with local overrides and dependency checks.

**Directory description:** tmux-popups opens shell, notes, timer and optional
tools from a generated tmux menu. Add or override TSV rows outside the checkout,
choose popup/window/command mode, and inspect dependencies with help or doctor.
Requires Bash and tmux. MIT licensed source.

**Page title:** tmux-popups — a quick menu for your tmux tools.

**Meta description:** Shell, notes, timer and your own tools, a shortcut away.
A small tmux popup toolkit with one TSV registry for the quick menu and direct
bindings.

## FAQ

- **What does it do?** Generates a quick menu and direct tmux bindings from a TSV registry.
- **Who is it for?** People already using tmux who want to keep nearby tool definitions in one place.
- **What does it cost?** The source is MIT licensed. You supply tmux, Bash and each adapter's dependencies.
- **How do I start?** Register it with TPM, reload, install with Prefix+I, then open Prefix+Enter.
- **What are the limits?** Optional apps need their own setup. Local dependency checks do not qualify every terminal or provider. Session switching stays with other tools.
- **Where do I get help?** Start with the site troubleshooting section or open a reproducible Gitea issue.

## Short introduction drafts

**Version A — mechanism:**

Add a row. Get a popup. tmux-popups generates your quick menu and direct
bindings from the same TSV registry. Start with shell, notes, timer, help and
tmux keys; keep your own rows outside the plugin checkout. Bash + tmux, MIT
licensed source. <https://tmux-popups.subcult.tv/>

**Version B — first use:**

Prefix+Enter: a shell, today's note, a timer, help and your tmux keys.
That's the small default in tmux-popups. The menu and direct bindings come
from one TSV registry; your local file adds or overrides tools. Requires
Bash and tmux. <https://tmux-popups.subcult.tv/>

Editorial choice: A explains the mechanism for a new reader; B depends more
on already understanding tmux prefixes. Both avoid time-saving measurements
and compatibility promises. Neither is a release announcement.

## Site release note draft

tmux-popups has a small Instrument Panel website with install instructions,
the default keys, local registry examples and recovery documentation. The
browser menu is an illustration; it doesn't execute tmux commands. Source
and issue links point to canonical Gitea, with the GitHub mirror kept for TPM.
Publish this note only after the site is deployed and checked.

## Demo brief

Record a real tmux session with synthetic paths and no credentials. Use the
small profile and note the tmux/terminal versions. Open Prefix+Enter, choose
shell, exit, open the menu again, then show the same shell row in the registry.
Caption the keys and the distinction between a row and its generated binding.
Show daily notes only in a temporary notes directory. Do not use a provider
adapter as the default demonstration.

Keep the real capture separate from the site's labeled illustration. Approved
identity assets are in Studio; crops and the final post need their own review.
Suggested alt text: “A tmux quick menu opens a shell over a pane; the matching
shell registry row defines its direct key, menu key and dimensions.”

## 30-day outline after publication approval

Owner: SUBCULT. No start date is scheduled; the window begins with an approved
site introduction. No paid spend or automated outreach is planned.

| Window | Work | Evidence and next decision |
| --- | --- | --- |
| Week 1 | Check the public install journey and approve one real demo | Fix failed steps before sharing |
| Week 2 | Publish one approved introduction in an appropriate channel | Retain post link and distinct installation questions |
| Week 3 | Improve docs for reproducible questions; adapt the demo if useful | Recheck changed commands; do not infer adoption from views |
| Week 4 | Review issue themes and time spent answering them | Continue only with a concrete useful next message |

Before publication, check the live destinations, current product claims,
media rights/crops/captions, and a named person to answer replies. No account
analytics or conversion baseline is currently available.
