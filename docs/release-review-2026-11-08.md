# Review the launcher candidate before publication

Status: prepared for review, with qualification and authorization gates still open.
Code candidate: `94294cf89513c4023cc304a36849fc8f801f1995`.
No tag, release or user installation update is authorized by this packet.

## Proposed release notes

- Validate registry rows before atomically publishing generated bindings. Preserve
  the last good cache and report the source file and line for failures.
- Keep user scripts and explicit argv outside the plugin checkout. Retain legacy
  row layouts, shared registry selection and literal invoking context.
- Provide a small dependency-aware default menu, optional full-menu compatibility,
  enabled/availability controls and skip/warn/replace binding conflicts.
- Reconcile owned bindings on reload while preserving later user replacements and
  explicit unbinds. Add read-only effective diagnosis and bounded input checks.
- Add optional search, reusable windows and project Git/shell/notes/coding actions.
- Add opt-in retained exit views with retry and fresh-window fallback. Repair
  timer input, clipboard selection and chat response/cancellation failures.
- Fix the review findings for moved panes, chat normal exit/owned descendants and
  literal checkout hashes, with focused regressions.

## Evidence for the review

The [full review](verification/full-review-2026-11-08.md) links each capability to
implementation/tests and records repaired findings. The [terminal matrix](verification/terminal-matrix-2026-11-08.md)
names exact candidate/tool versions and pass/inconclusive/not-tested outcomes.
The candidate passed all 134 local checks. Each PR must still pass hosted CI on
its current head and merge cleanly before its work is complete.

Read [migration and rollback](migration.md) before updating. The guide includes
full-menu compatibility, registry/script storage, conflict policy, entrypoint
reload and return to a saved revision. Its isolated command checks are recorded
in [migration verification](verification/migration-2026-11-08.md).

## Ownership and destination

Live inspection on 2026-11-08 confirmed canonical Gitea ownership
`PatrickFanella/tmux-popups`, branch `main`, with `mirror=false`. The configured
push mirror targets `github.com/PatrickFanella/tmux-popups.git`, syncs on commit
and reported no last error. At that observation, GitHub HEAD and canonical main
both equalled `f60f80de1bbd3d3ba36c508bf70854674d3b1733`.

The README's manual installation uses canonical Gitea. TPM's
`PatrickFanella/tmux-popups` shorthand uses the GitHub mirror. No destination,
mirror settings or publication behavior was changed. Recheck both branch heads
and mirror health for an actually approved publication revision.

## Remaining release gates

1. Recheck the resulting exact main revision and hosted evidence for any proposed
   publication. Runtime changes reached `6030555b528e9660bbbda876133c5f2238aa1961`
   after green head checks and clean merges. Its scripts, registry, examples and
   CI workflows match the qualified candidate. The packet itself follows the
   same green-head check before its authorized merge.
2. Complete #12/#24 evidence in the owner's original native terminal, including
   the historical failing interaction and OS paste path. Keep real providers and
   clipboard/image backends optional and unqualified until separately tested.
3. Resolve the phone qualification gap if that environment is required. The
   attempted emulator check stopped on device-control errors, as recorded.
4. Obtain explicit approval under #25 for a concrete revision and destination
   before creating tags/releases or changing the user's installation. Record
   actual publication and live installation evidence only after it occurs.

This packet prepares the review material. It does not close #12, #24 or #25, and
passing CI or merging this document does not grant release approval.
