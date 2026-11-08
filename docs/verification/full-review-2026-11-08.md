# Final code and behavior review — 2026-11-08

Verdict: the implemented launcher passes its 134-test local gate and the recorded
browser-terminal checks after focused repairs. Hosted head checks and the native
terminal/device qualification limits still block a release-ready verdict.

## Scope and triage

Reviewed code candidate: `94294cf89513c4023cc304a36849fc8f801f1995`.
The review traced the registry, generator, binding reconciler, dispatcher, context
helpers, dependency/executable resolvers, recovery, window reuse, search and tool
adapters. It also checked README/examples, both CI workflows and the regression
harness. This is a shell/CLI project with no React or web-product frontend.
No React performance or web accessibility review applies to the product.

The review covered correctness, lifecycle ownership, quoting, compatibility and
documentation consistency. It did not audit third-party application source or
claim a comprehensive security assessment.

## Capability evidence

| Capability | Implementation and verification |
| --- | --- |
| Registry compatibility and external scripts | `list-popups.sh`, `parse-arguments.py` and execution helpers; registry/user-script tests cover seven through thirteen columns, precedence, literal argv and preserved user files. |
| Validation and cache publication | `generate-config.sh`; invalid-source, alias/collision and overlapping-writer regressions preserve complete last-good output. |
| Binding conflicts and reload ownership | `apply-config.sh`; binding/conflict tests cover skip/warn/replace, user replacements/unbinds, previous notes and rollback. |
| Invoking context and modes | `run-popup.sh` and origin helpers; direct/menu/search tests preserve literal paths and explicit clients, sessions and panes across popup/window/command actions. |
| Failure recovery | `recover-entry.sh`; tests cover foreground input, raw-terminal restoration, retry, fresh-window context, status and owned-group cancellation. Browser controls and the older-shell interrupt repair have separate evidence. |
| Window reuse | `reuse-window.sh`; live pane membership, exact-directory scopes, concurrent launches, independent sessions and exited panes are checked. Real Yazi was reused from two browser clients. |
| Discovery and diagnosis | `search-popups.sh`, `doctor.sh`, `popup-help.sh`; selection, cancellation, no-match, native fallback, read-only cache/binding comparisons and bounded input checks are covered. |
| Tools and project examples | Timer, clipboard, chat and project-action regressions cover their repaired failure paths. Real Git/Bash/Yazi/OpenCode received the narrower checks named in the matrix. Other optional tool/provider integrations remain unqualified. |

## Findings and disposition

| Finding | Reproduction and focused repair |
| --- | --- |
| P2: stale reuse marker selects a window after its tool pane moves away | #55 / PR #54. The new moved-pane test failed before the membership guard and passes after it. User windows and the moved process remain untouched. |
| P2: normal chat quit reports HUP/status 129 | #56 / PR #58. Actual browser q/cq and a dispatcher-launched popup regression reproduce it. Normal exit now closes the view without self-induced HUP. |
| P2: completed chat request leaves a TERM-resistant owned child alive | #56 / PR #58. A successful provider substitute leaves a child before the repair. Shared bounded group cleanup resolves it. |
| P2: literal checkout hash pairs disappear during generated action expansion | #57 / PR #59. Literal hash paths fail dispatch before escaping the executable at its format boundaries. Corrected explicit-mode tests cover direct/menu popup/window and retained-close paths. |
| P2: older command shell masks recovery Ctrl-C status | PR #52 follow-up. Wrapper tracing proved exit 130 while tmux reported 2. `exec` removes the intermediate shell; all 14 recovery cases pass on both tested tmux/Bash versions. |
| Test gap: nominal window quoting cases still used popup mode | PR #59 writes explicit row modes for the custom adapter; the legacy Yazi option does not select its mode. |
| Test race: marker creation precedes contents | PR #52 follow-up. One full run read an empty marker after `exists()` passed. Three fixture checks now wait for the complete expected contents. |

No additional confirmed defect remains in these reviewed implementation paths.
That conclusion does not qualify the untested environments in the matrix or
replace hosted checks on the actual PR heads.

## Verification and limits

`scripts/check.sh` passed syntax, the project's ShellCheck flags and all 134 tests
in 335.624 seconds on the named candidate. The preceding chat stack passed 133
tests in 316.745 seconds. Focused recovery, chat and quoting checks also passed in
a private CI-equivalent Node 24/Bash 5.2.15/tmux 3.3a/Python 3.11.2 container.

The [terminal matrix](terminal-matrix-2026-11-08.md) records actual application
input, two real clients, cleanup, exact versions and the discarded harness runs.
The [phone attempt](phone-2026-11-08.md) remains inconclusive. The owner's original
native terminal and OS paste path remain unavailable; optional providers and
clipboard/image backends were not exercised against real services.

All browser tabs, ttyd processes and private tmux servers started for the UI
checks were stopped. Temporary binaries and the private verification image were
used only for isolated checks. No production process, user's tmux server,
installation, tag, release or mirror configuration was changed.

## Hosted candidate evidence

[Run 20398, job 37862](https://git.subcult.tv/PatrickFanella/tmux-popups/actions/runs/20398/jobs/37862)
passed on candidate `94294cf89513c4023cc304a36849fc8f801f1995`: 134 tests in
142.459 seconds, with the optional real-fzf check skipped because fzf is absent
from that runner. Dozor's full run includes real fzf and passes all 134 tests.

PR #54's earlier hosted run had one window-exit wait time out. Its dispatcher and
mode test match the later successful 133/134-test heads. Eight isolated,
instrumented repetitions on that earlier head passed (91.229 seconds). The
cause remains unreproduced. Pane/dead-status/signal/frame diagnostics were added in
`15612a2` without weakening the expected exit-23 assertion. The instrumented local
mode case passes (14.812 seconds); the new head still must pass hosted CI. This is a test reliability limit, not evidence of a repaired
application defect.
