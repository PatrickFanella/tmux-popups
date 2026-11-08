# Migration command verification — 2026-11-08

Result: PASS for the documented manual and customization paths below.
Code candidate: `0e34c7273cadce29a9e4dbed84e44cf41c2f0eb0`.
Environment: Dozor, tmux 3.5a, Bash 5.2.37, Python 3.13 and Git 2.47.3.

A disposable HOME/XDG tree and private tmux socket contained the entire check.
The canonical manual clone succeeded at main `f60f80de1bbd3d3ba36c508bf70854674d3b1733`.
The isolated clone then fetched the candidate from this local checkout to test
the complete dependent implementation.

The README's personal-script shell commands created an executable outside the
plugin checkout. Its thirteen-column `hello` row validated and CLI dispatch
received Enter and printed the expected greeting. Doctor left cache bytes and
prefix bindings unchanged. Generation, explanation and entrypoint reload passed.
Both `examples/popups.optional.tsv` and `examples/popups.project.tsv` validated
and generated successfully as the selected local registry.

The full/ignore/replace migration options enabled all merged rows and reloaded.
The manual backup/fetch/detached-update/saved-revision-return commands completed.
The final revision matched the candidate, and personal script and registry bytes
matched the pre-update values. The private server and temporary tree were removed.
Twenty local Markdown links in the edited documentation resolved.

Live repository inspection found canonical Gitea ownership
`PatrickFanella/tmux-popups`, default branch `main`, with `mirror=false`.
Its push mirror targets `github.com/PatrickFanella/tmux-popups.git`, syncs on
commit and reported no last error. GitHub HEAD matched the canonical clone SHA
above. No mirror settings, tags, releases or user installation were changed.

The TPM install/update key sequence was documented but not driven against a real
user TPM installation. Provider and native-terminal qualification remain separate
in issues #12 and #24. The existing code candidate passed all 130 regressions in
306.837 seconds; this documentation-only change does not add runtime code.
