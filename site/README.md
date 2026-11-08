# tmux-popups product site

Static HTML, CSS and a small script for the menu illustration and copy buttons.
No package install, build step, analytics or backend is required. The intended
canonical URL is `https://tmux-popups.subcult.tv`; these files do not deploy it.

Preview from the repository root:

```sh
python3 -m http.server 18785 --bind 127.0.0.1 --directory site
```

Open `/` and `/docs/`. Production nginx serves `404.html` for missing paths.
The browser illustration describes real default entries but executes no tools.
With JavaScript disabled, its shell example, navigation and all documentation
remain readable; inactive demo controls and copy buttons stay disabled or hidden.

## Content sources

| Site content | Owning source |
| --- | --- |
| Install commands, config defaults, modes, conflicts, recovery, reuse | `README.md`, `tmux-popups.tmux`, `scripts/lib.sh`, `scripts/run-popup.sh` |
| Five default entries and 25 shipped rows | `popups.tsv`; checked by `scripts/check-site.py` |
| Daily note path and timer limits | `scripts/tools/notes.sh`, `scripts/tools/timer.sh` |
| Doctor, cache validation and reload | `scripts/doctor.sh`, `scripts/generate-config.sh`, `scripts/apply-config.sh` |
| Update and rollback | `docs/migration.md` |
| Maturity and qualification limits | `docs/release-review-2026-11-08.md`, `docs/verification/README.md` |
| Access terms | `LICENSE` (MIT) |
| Positioning and draft channel copy | `docs/marketing/context.md`, `docs/marketing/packet.md` |

The source baseline for this page is product commit `d78bf16` on November 8,
2026. Update the site when those facts change. No dedicated CONTRIBUTING or
SECURITY document exists at this baseline, so More links to source and testing
instead of inventing destinations.

Anonymous Gitea deep links redirect to login. Reading links therefore use the
public GitHub mirror; Git and contribution links retain canonical Gitea. Issue
submission requires a Gitea account.

## Brand handoff

Studio owns the masters: `subculture-collective/subcult-tv`, revision
`f69b93c299216425dadb6f5c6117d24c2e36388d`, `studio/brands/tmux-popups/`.
The owner selected Instrument Panel, confirmed IBM Plex, then requested this
site. `docs/site-brand.json` is the explicit public selection: unchanged mark
and 1200 × 630 share card, four font subsets and their three OFL texts. Private
reference screenshots and the rest of the pack are excluded.

Named CSS tokens follow the pack: graphite canvas, light text, mint selection
and focus, amber annotation, square bordered panels. The terminal illustration
uses selectable HTML text; it is not a screenshot or runtime qualification.
Marks render at 48px in headers and 32px in footers with 25% clear space. There
is no 16px favicon: the guide requires a separately reviewed simplified drawing.

The WOFF2s derive from IBM Plex Sans Condensed 700, Sans 400/700 and Mono 400.
Their internal names are **Tmux Panel Condensed/Sans/Mono**, respecting the
reserved font name in the OFL. The glyph designs and approved type roles remain
IBM Plex. No fonts or colors are installed into the user's terminal.

To reproduce the exact selected outputs, create an isolated environment with
`fonttools[woff]==4.68.0` and `brotli==1.2.1`, then run:

```sh
python3 scripts/update-site-brand.py /path/to/subcult-tv
```

The checkout must contain the receipt's Studio source bytes. The script checks
all input/output hashes before replacing files, retains OFL names/copyright,
renames modified font families, subsets the recorded Latin/punctuation/arrow
ranges, and refuses unexpected destination drift. A changed source or export
requires a reviewed receipt update, not a blind overwrite.

## Checks and deployment

```sh
python3 scripts/check-site.py
node --check site/app.js
docker build -f deploy/Dockerfile -t tmux-popups-site:local .
```

Both CI workflows run the static check. Check navigation, copy success and
fallback, all five demo rows, keyboard focus, font loading, console/network
errors and page overflow at 360px and 1280px after visual changes.

`deploy/` follows Pult's unprivileged nginx and external `projects` network.
Set `TMUX_POPUPS_SITE_IMAGE` to an immutable image reference and
`TMUX_POPUPS_SITE_REVISION` to its source commit. The supplied HTTP Caddy stanza
matches Pult's origin behind the existing edge; it is not standalone TLS setup.
Do not edit the shared proxy or activate Compose as part of a local preview.
Website deployment needs explicit authorization under Studio's launch workflow.
