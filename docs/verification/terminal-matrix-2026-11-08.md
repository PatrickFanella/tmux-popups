# Terminal qualification matrix — 2026-11-08

Verdict: the recorded browser-terminal and actual clipboard-paste cases pass.
Qualification applies to this stated target; other native terminals and the
phone remain unqualified. See the follow-up paste matrix below.

## Candidate and environment

The final code candidate is `94294cf89513c4023cc304a36849fc8f801f1995`.
`scripts/check.sh` passed Bash syntax, ShellCheck and all 134 tests in 335.624
seconds on Dozor. The harness bound remains 360 seconds. Hosted results must
qualify each PR's current head before merge.

The actual browser terminal used Chromium 157, ttyd 1.7.7, tmux 3.5a and Bash
5.2.37 on Dozor. Client TERM was `xterm-256color`; application TERM was
`tmux-256color`. The client resized from 139 columns by 46 rows to 103 by 37 and
back. Two browser connections supplied two actual attached clients to one private
session. HOME, XDG paths, working files and the tmux socket belonged to the test.

Official temporary binaries reported Yazi 26.9.1 (`8dd895c`, 2026-09-01) and
OpenCode 1.19.5. No system installation or provider account was used. Downloads
matched the SHA-256 digests published with the upstream release assets:

| Asset | Published and observed SHA-256 |
| --- | --- |
| [Yazi v26.9.1, x86_64 Linux musl ZIP](https://github.com/sxyazi/yazi/releases/tag/v26.9.1) | `9b9c39decccf8cb0ff53a7d637d38f8a79d93bbd0099f4ea9c619ef6bb392f5d` |
| [OpenCode v1.19.5, Linux x64 tar.gz](https://github.com/anomalyco/opencode/releases/tag/v1.19.5) | `588310a336fa3b9df36b3f0225b26f679d453efaad0cf3d66c3651ef3ec1647a` |

OpenCode used the official binary directly, isolated configuration, disabled
updates/sharing/default plugins/external skills/LSP downloads, and no submitted
provider prompt. Yazi used the launcher's default safe configuration. Image
preview and full user configurations were not qualified.

## Final-candidate browser checks

| Application or behavior | Presentation | Outcome and exact interaction |
| --- | --- | --- |
| Real Yazi | Window | PASS: Prefix + F6, type `alpha` in Filter, Enter confirms, Escape clears, q exits. |
| Real Yazi | Popup | PASS: Prefix + F7, type `beta` in Filter, Enter confirms, Escape clears, q exits. |
| Real OpenCode | Window | PASS: Prefix + F8, type an unsubmitted draft, resize, Ctrl-C clears it, `/exit` + Enter closes the application. |
| Real OpenCode | Popup | PASS: Prefix + F9, type an unsubmitted draft, Ctrl-C clears it, another Ctrl-C closes the application. |
| Real Yazi reuse | Window, two clients | PASS: both clients see the session's selected window. After returning to the original pane, the second client launches the same entry and reuses the exact tool PID and two-pane set. q closes it. |
| Working directory | All of these launches | PASS: the isolated invoking directory contains spaces; both application interfaces show that directory. |
| Cleanup | After final run | PASS: only the original Bash pane remains; no process uses either downloaded application executable. Both tabs and the owned ttyd/private tmux server were stopped. |

T3 screenshots: `browser-screenshot-localhost-mw7mjsdi-30b4aed9.png` shows Yazi
filter input; `browser-screenshot-localhost-mw7mmkrd-a56274f8.png` shows the real
OpenCode popup draft. One scripted sub-run advanced before the previous popup
closed; its OpenCode results were discarded. The retest waited for each actual
application prompt and asserted the expected state before sending further input.

## Other recorded checks and revisions

| Evidence | Candidate and scope |
| --- | --- |
| [Earlier real-tool investigation](#earlier-real-tool-investigation) | `1b10392d72445387f227c352cf5d9f895f9761d1`, before the review repairs. |
| [Failure recovery](recovery-browser-2026-11-08.md) | Browser input, retry, fresh-window context and close at `528ae83e0bc18154236636134d82b0b6bb2eb8a1`; CI interrupt repair at `b3bb4f6588a5d02eb1720b909a4664b903ddbceb`. |
| [Chat lifecycle](chat-review-2026-11-08.md) | Browser q/cq retest and exact controlled copy bytes at `c1f0f313f0dc4aee28f961931114abc40a81eb57`; no real provider or system clipboard. |
| [Hash paths](hash-path-review-2026-11-08.md) | Direct/menu, popup/window and retained-close quoting at `1d9910a5defe66534ed297520fa675d5e6277ca1`. |
| [Search](search-browser-2026-11-08.md) | Actual fzf selection/cancellation and original-context checks on its named candidate. |
| [Migration](migration-2026-11-08.md) | Isolated manual clone, personal script, both example registries, generation/reload and saved-revision return. |
| [Automated verification](../../tests/README.md) | Final candidate includes direct/menu/search, two-client context, reload ownership, disabled/missing tools, custom registries, concurrent reuse and repeated launch/close regressions. |

### Earlier real-tool investigation

On the earlier candidate, real Yazi filter typing worked in both modes and a
window handled resize. OpenCode accepted draft input, opened the command palette,
selected Themes with Enter, dismissed it with Escape, and exited without a model
request. Brief stale cells after resize disappeared on a full redraw; no crash
was observed. An initial test wrapper supplied an unsupported `--standalone`
flag; that harness failure was discarded after inspecting its retained pane.

The native menu launched the calculator, which accepted `2**10` and displayed
1024. Its popup appeared only on the invoking browser client. Native menu `/`
opened real fzf, `yazi window` narrowed the list to 1/11, and Enter opened Yazi
after the picker closed. A Bash popup accepted a command and exit. Chat with
controlled provider/clipboard programs accepted input and copied exact bytes,
but exposed the status-129 quit defect later repaired and retested above.

## Limits and remaining gates

| Environment or capability | Outcome |
| --- | --- |
| Owner's original native terminal and historical failure interaction | NOT TESTED: terminal identity, version, configuration and original reproducer are unavailable in this session. The general remembered input failure remains unreproduced there. |
| Android phone emulator | INCONCLUSIVE: [the recorded attempt](phone-2026-11-08.md) stopped after two device-control reference failures. The owned emulator and forwarding process were stopped. |
| Browser clipboard paste | PASS: actual keyboard copy/paste into Bash, chat, calculator, Yazi, OpenCode and fzf in both modes; see [paste evidence](paste-browser-2026-11-08.md). A different native terminal remains untested. |
| Real ocq/provider authentication, requests and continuation | NOT TESTED: optional and unqualified. No credentials or paid/provider calls were used. |
| Real system clipboard, image previews and full Yazi user configuration | NOT TESTED: optional integrations require their own environment evidence. |
| Integrated runtime main | INTEGRATED at `6030555b528e9660bbbda876133c5f2238aa1961`; implementation matches the qualified candidate. Each runtime PR merged after its current head passed hosted checks. |
| Tag, release or user installation update | NOT AUTHORIZED: publication requires the separate release decision in #25. |

Do not treat this matrix as evidence for every terminal or provider. The browser
target is qualified by local/hosted regressions, real applications, two clients
and the [actual clipboard follow-up](paste-browser-2026-11-08.md). No tag, release
or user installation change was made; #25 keeps its separate approval gate.

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
case passed (14.812 seconds). [Run 20407, job 37895](https://git.subcult.tv/PatrickFanella/tmux-popups/actions/runs/20407/jobs/37895)
then passed on that head: 131 tests in 101.788 seconds, with optional real fzf
skipped. PR #54 merged after this green rerun. The one-off remains a test
reliability limit, not evidence of a repaired application defect.

## Integrated runtime revision

PRs #54, #58 and #59 merged after their current heads passed hosted checks.
Runtime main `6030555b528e9660bbbda876133c5f2238aa1961` has byte-identical
`scripts`, `popups.tsv`, `examples` and CI workflows to candidate
`94294cf89513c4023cc304a36849fc8f801f1995`. The only difference before this packet
is the added mode-test timeout diagnostics. This packet includes those diagnostics;
its own head remains subject to the normal full hosted gate before merge.

## Tracker dependency gate

Gitea refused to close implementation-complete #15 while #12 remained open:
`cannot close this issue or pull request because it still has open dependencies`.
#19 also depends on #12, #20 on #19, and #23 on those feature issues. Their
acceptance checkboxes and evidence are recorded, but they remain open under the
existing dependency graph. No dependency was removed or bypassed.

The browser terminal is a real qualified target for the recorded cases. The
paste gap was subsequently resolved by actual clipboard copy/paste in all six
applications and both modes, as recorded in [the follow-up](paste-browser-2026-11-08.md).
The dependency graph can resolve in order once that evidence PR passes and merges.
The original native terminal remains unverified; it is not a new permission
requirement imposed by this review. Phone control remains inconclusive.

## Completed paste follow-up

See [actual browser clipboard paste](paste-browser-2026-11-08.md) for twelve
application/mode paste cases, cancellation, exact bytes and cleanup on runtime
`6030555b528e9660bbbda876133c5f2238aa1961`. This closes the earlier paste evidence
gap for the qualified browser target.

## Runtime-main hosted result

[Run 20412, job 37904](https://git.subcult.tv/PatrickFanella/tmux-popups/actions/runs/20412/jobs/37904)
passed on runtime main `6030555b528e9660bbbda876133c5f2238aa1961`: 134 tests in
319.033 seconds, with only optional real fzf skipped. The local full run includes
fzf. This runtime includes the mode-timeout diagnostics as well as the reviewed
implementation fixes.
