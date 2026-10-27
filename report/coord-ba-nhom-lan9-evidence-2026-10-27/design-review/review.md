# Independent design review R9 — 2026-10-27

Reviewed `work/w24-figma-evidence` at `bda1366b8d033ce0dcf4660651959293c178f7c8` against main source pin `e52bf4f245e9e6c0454ee83760ea4bf8ad55adff`. Scope: `scripts/test_w10_library_filter_vm.cjs`, `tests/unit/presentation/test_tokens_and_wcag.py`, and `report/w24-w10-w23-phoihop-2026-10-25.md`. Read AGENTS.md, code-review-and-quality skill, W-23 task, and the R8 report/prompt. No product/worker edits, PostgreSQL runs, paid providers, live cache, held-out inputs, links, deletion, push, or Cloud Figma gates.

**Verdict:** accept the D-R8-02 guard improvement. No Critical or Required code finding. W-23 remains incomplete; the report needs the dated corrections below before it can be used as an acceptance record. Correcting this document and retaining the open W-23 work item is sufficient to accept the guard without reopening source/token/branding/math work already accepted.

## Required — D-R9-01: the W-23 table still asserts conclusions without paired evidence

`report/w24-w10-w23-phoihop-2026-10-25.md:45` (also lines 46–54). The candidate replaces the HTML screenshot side with a source filename/anchor; it adds no corresponding captured HTML state, capture URL, crop coordinates, measured font rendering, padding, or target measurements. The self-check row acknowledges folded HTML versus expanded React, then asserts matching 16px padding/font/icons. A source anchor cannot establish those claims. The viewer/menu rows also turn layout differences into accepted decisions without the owner decision requested by W-23.

There is a visible, independently checked counterexample at line 54: `library-here-390-light.png` contains **two** tabs, “Tạo ở đây 2” and “Tạo ở nơi khác 2”; the report says that React/HTML match with **three**, including “Tất cả”. At line 48 the React sample contains superscripts in `x²+y²` and `1+1=2`; this image cannot prove the reported subscript `.msub` alignment. These are report errors, not evidence that the accepted React implementation is broken.

Remedy: add a dated correction retaining the historical assets, explicitly keep W-23 open, withdraw unsupported match/measurement/approval claims, and record unresolved layout decisions. Completion later needs actual matching React/HTML captures with full source SHA, URL, viewport/theme/motion/state/crop, observed deviations and handling, font load/render evidence, and interaction/keyboard/reduced-motion verification. Do not require Cloud Figma.

## Required — D-R9-02: use the actual W-10 capture source SHA

`report/w24-w10-w23-phoihop-2026-10-25.md:50` (all W-10 rows through line 54). These rows label `browser-r7-main` captures as `aaf68eb6795c929169e5212a05093d8d817c76e3`, but `report/w10-r7-evidence/browser-r7-main/runtime.json:7` records capture source **`1fc0f553bec808241388b722fa2c10a1c6ead33d`**, base `http://127.0.0.1:8020`, clean source paths, and scripted providers.

Remedy: label the capture with its actual source SHA and distinguish the later accepted W-10 commit. Independent `git diff --name-only 1fc0f553… aaf68eb… -- src/web/frontend scripts/w10_web_check.cjs scripts/w10_web_runtime.py` is empty, so a documented frontend/harness reuse proof is available. Do not relabel an old run as a new capture or reopen W-10 acceptance.

## Optional — clarify the W-16 warning threshold as a design choice

`report/w24-w10-w23-phoihop-2026-10-25.md:72`. This report presents 70% as a reference rule. The reviewed W-16 task/spec requests three states but does not prescribe this numerical boundary. Reconcile or label the report's threshold as a design choice when updating guidance; neither 70% nor the later React 80% choice should be represented as a newly mandated quota policy. No product blocker follows from this report difference.

## Independent verification

- Scratch copies of both guard files and W-10 HTML have exact byte SHA-256 equality with the pinned candidate blobs and worker files (`resume-verification.json`).
- Baseline through `scripts/w05_run_tests.py`: **64 passed**, native 0, 0 failure/error.
- Independently changed the **actual scratch HTML onclick attributes** from here/elsewhere to button/assistant, then ran the ordinary behavior test `test_w10_library_filters_by_group_independent_of_origin`, not the built-in mutant mode. It failed at the observable title assertion (`visibleHere == []`), **1 failure / 0 errors / native 1**. This closes the R8 wiring coverage gap.
- Restored scratch HTML to SHA-256 `a6d42207d1c4f3915734b9efff6c757442ca6fefead5bec61706b9eddf7c0ecf`; worker bytes stayed unchanged; rerun **64 passed**, native 0. Earlier interrupted-review baseline, inverted/group/scope mutation logs remain untouched.
- All **10 PNG and 3 WEBM** references exist and have identical root/worker bytes. All referenced HTML anchors now exist. All 10 PNGs were visually inspected. W-08/W-09 recorded runtime SHAs match their report labels; W-10 discrepancy is documented above (`evidence-inspection.json`).
- Existing video metadata confirms durations W-08 412.20s, W-09 279.68s, W-10 342.52s. Eight nonblank sampled frames from the claimed intervals were visually inspected; the recording changes viewport/theme and includes gray unused recording area. This is partial content inspection, not continuous playback, exact action-timestamp certification, or a React/HTML motion comparison. Keep the old recordings as historical interaction evidence and provide state/config-specific verified intervals for W-23 completion.
- No new browser product matrix or build was needed for these two test-only code changes. The parent coordinator owns the combined application/browser/build/PG gates. New external spend: **0 USD**.

Correctness improves because the normal behavior test now executes the actual markup handler. Readability/architecture stay within the existing small VM helper, with no dependency change or product code growth. The executed HTML is checked-in local design input, so this change adds no untrusted-input surface. Runtime cost is limited to test subprocesses. No Required finding across these five code-review axes.

The evidence inspection helper's first terminal print hit Windows cp1252 `UnicodeEncodeError` after writing its JSON; rerunning with `-X utf8` succeeded. This reviewer output-encoding issue is not a product/test RED and was not counted as one.
