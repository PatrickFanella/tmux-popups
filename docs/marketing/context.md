# tmux-popups marketing context

Prepared November 8, 2026 for SUBCULT. Copy is draft. Product baseline:
`d78bf16`; website deployment has not happened. No post is approved or scheduled.

## Product facts and audience

tmux-popups is a small, MIT-licensed tmux toolkit. A TSV registry generates
the quick menu and direct bindings. It is for people who already use tmux and
want nearby tools without maintaining separate menu and key definitions.
This audience is a positioning hypothesis, not interview research.

The first-use path is TPM registration → reload → Prefix+I → Prefix+Enter.
The manual alternative is a canonical Gitea clone and a `run-shell` entrypoint.
Bash and tmux are required; individual adapters have their own dependencies.
Python 3 is required for JSON arguments and retained-exit recovery. No product
account is required for the core toolkit. Provider-backed adapters need their
own configuration. No tagged release is published at the baseline.

Source: <https://git.subcult.tv/PatrickFanella/tmux-popups>.
Intended site: <https://tmux-popups.subcult.tv/> (not yet deployed).
Feedback: <https://git.subcult.tv/PatrickFanella/tmux-popups/issues>.
Studio support: <https://subcult.tv/support>.

The existing alternative is a user's hand-written tmux menu and bindings;
that is a mechanism comparison, not a measured claim about saved time.
The question for an introduction is whether a five-entry default makes the
first menu understandable before people add their own tools.

## Voice and visual rules

Studio source `f69b93c299216425dadb6f5c6117d24c2e36388d` owns Instrument Panel.
The owner selected it and confirmed IBM Plex. The site's exact selection and
font transformations are in [site-brand.json](../site-brand.json).

Use a dotfiles author's voice: “Add a row. Get a popup.” Name registry rows,
bindings, tools and actual paths. Avoid generic productivity claims, blanket
terminal compatibility, a required AI provider, or an invented release number.
Use the graphite/mint/amber tokens, IBM Plex Condensed headings, Sans body and
Mono commands. Label the illustrated menu as an illustration. Terminal styling
belongs to the user.

Voice: `studio/content/VOICE.md`, tmux-popups section. Claims register:
`studio/content/social/Product Claims Register.md`, C-TMUX-01.

## Claims and evidence

| Claim | Evidence at product baseline | Qualification / review trigger |
| --- | --- | --- |
| Menu and direct bindings share one TSV registry | `README.md`, `popups.tsv`, generator and dispatcher | Source-backed; recheck after registry contract changes |
| Five entries enabled; 25 shipped | `popups.tsv` | Small profile only; checked by the site validator |
| Local rows override shipped IDs; new IDs append | `README.md`, `scripts/lib.sh` | Personal files must stay outside the checkout |
| Help, list and doctor report dependency state | Shared resolver and doctor scripts | Local binaries, not credentials or provider qualification |
| Existing prefix keys are skipped by default | Conflict policy in README and reconciler | Not a guarantee about unknown historical bindings |
| MIT licensed source, no build step | `LICENSE`, Bash entrypoint | Optional helpers still have dependencies |

Session switching, provider setup and universal terminal qualification stay
outside these claims. The local website demo proves only browser interaction,
not tmux application behavior. Full runtime tests and browser observations are
recorded separately in [the site review](../verification/site-2026-11-08.md).

## Measurement

Primary action: a reader completes installation and opens the menu. There is
no installation telemetry or website analytics, so no conversion rate or
adoption baseline is available. Use voluntary feedback and reproducible issues;
do not substitute views or clicks for successful use. Review copy after the
first reports of installation friction.
