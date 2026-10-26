# Independent R7 design review — 2026-10-26

Approve the D-R6-01 / W10 HTML design source milestone at 26e4a9adc66410679b616b76dff9d5f1522a0d0a (base b3c4426). The implementation corrects the rejected filter behavior. Accept the source with a dated coordinator correction to its submitted report and retained independent browser regression guard. Do not accept W23, including the report's claimed W08/W09 partial acceptance, on the evidence supplied.

Scope: unmerged 0b5993e and 26e4a9a, principally design/preview/w10_quiz_screens.html, tests/unit/presentation/test_tokens_and_wcag.py, and report/evidence claims. Read AGENTS.md, code-review-and-quality, browser-testing-with-devtools, W10, W23, R6 decision/instructions, and Pha B2 section 4. No product, worker, Git, React, provider, paid, external network, Cloud Figma, shared-data, or held-out changes. All mutations used this review's scratch copies. No PostgreSQL suite was run; the parent owns the integrated gate.

## Findings

Required D-R7-01 — correct W23 provenance and withdraw unsupported acceptance. report/w24-w10-w23-phoihop-2026-10-25.md:40-47 calls each pair a perfect match and accepts W08/W09 partially, but:

- Line 42 labels coord-ba-nhom-lan5-evidence-2026-10-25/design-browser/w08-ready-390.png as React. Its archived producer design-browser.cjs navigates to file preview design/preview/w08_lecture_screens.html and captures #section-lecture-ready. It is a 366px-wide element crop at a 390px viewport, not a React capture; that producer takes screenshots only in the no-preference motion case. This row cannot prove reduced-motion mascot behavior.
- I inspected the actual line-40 React PNG. It shows the algebra roadmap and an assistant panel, not a completed cardiology lecture or P_coronary. The paired HTML PNG is a long multi-state cardiology preview. Line 41's React PNG shows the assistant overlay on a module lesson, not the named source-viewer state.
- The genuine R6 React images are pinned by archived browser/runtime.json to 7a99fbd17621b6429dec08869e07a7e4d178f97f. I checked git diff --name-only between that SHA and HEAD for src/web/frontend: empty, native 0. Historical reuse is possible; source staleness is not the reason for rejection. The table still needs matching actual states, crop/viewport information, differences and disposition, keyboard/effects/reduced-motion observations, and appropriately linked video. Its current perfect-match wording is unsupported.

Disposition agreed with parent: add a dated coordinator correction at the top, preserve the submission below, withdraw these acceptance/perfect-match claims, identify the static image correctly, and assign actual paired W08/W09/W10 review and interaction/video evidence to the next design job. W23 stays open for real W10 and the remaining acceptance criteria. This does not reopen accepted W08/W09 functionality, W22/W24, math, or Cloud Figma.

Required D-R7-02 — the authored guard is not a behavior test. test_tokens_and_wcag.py:1054-1112 checks strings, fixture attributes, and hardcoded local booleans. The newly named falsifiable test never invokes filterLibrary. In my isolated copy, the full 64 tests pass both before and after changing the actual filter comparison cardGroup === group to cardGroup !== group. The inverted source displays the wrong records. Therefore report lines 27-30 and 69 must not claim these tests protect actual filter behavior.

The independent browser guard now fills that verification gap for this source acceptance. Retain browser-probe.cjs and its results; assign upgrading the authored regression to the next design slice. Its observable record assertions reject both the exact historical origin filter and the inverted new condition. This is a verification/report finding, not evidence that the shipped corrected filter is wrong.

No Critical issues. No optional style findings.

## Source behavior verified

The real pinned worker HTML was run directly in Chromium 156.0.8078.4 at 390, 768, 1280 × light/dark × default/reduced motion, 12 configurations. The initial copied source SHA equals worker SHA a6d42207d1c4f3915734b9efff6c757442ca6fefead5bec61706b9eddf7c0ecf; the final worker remains clean.

Named assertions in browser-probe.cjs:

- inspectFilters: keyboard Enter on each tab produces independently specified visible document titles. Here includes assistant-created-in-A and button-created-in-A; elsewhere includes button-created-in-roadmap-about-A and assistant-created-in-module-2. All restores four records. Origin is preserved separately. The prototype consumes canonical group; it need not reconstruct core home_scope/node intersection logic.
- Scope boundary: five selections enables create with no warning; six disables it and shows scope_too_large; returning to five restores it. This is preview UI evidence, not backend/provider enforcement evidence.
- No horizontal overflow, visible interactive target smaller than 44px, or page error across all 12 configurations.
- Three formula nodes per configuration expose one MathML tree each, no nested KaTeX; real accessibility snapshots contain math. Subscripts are physically smaller and lower than their base. Strict CSS source guards also pass in the 64-test suite. Reduced-motion skeleton animation names are none.
- Exact old filterLibrary(origin,...) plus historical button/assistant tab arguments transplanted onto crossed current fixtures fails both tab title assertions. The new comparison inverted to !== also fails both. The controls leave All intact, ruling out a generic empty-list/setup error.

Run from the repository: node tmp/coord-r7-design-review-20261026/browser-probe.cjs C:/Users/ngoco/Desktop/Doctoroadmap/tmp/w24-figma-evidence/design/preview/w10_quiz_screens.html

The optional source path lets the same guard reject a future faulty worker file. Control variants remain under this review scratch directory.

## Limits and other axes

External HTTP(S) requests were aborted. Every configuration has one classified resource console error from the blocked Google Fonts import. There are zero page errors; do not report a clean console or successful Be Vietnam Pro loading. CDP CSS.getPlatformFontsForNode reports Segoe UI, with no declared loaded font faces. document.fonts.check returning true in the main observations is not evidence that the requested face exists. Screenshots use fallback fonts and cannot establish exact Be Vietnam Pro metrics.

I visually inspected the new 390px library and quiz captures: wrapping, distinct selected tab, readable subscript placement and button targets match the measurements. The prototype intentionally displays separate static lifecycle sections; this review does not treat inert submit/download/source buttons as production functionality or reopen accepted milestones. Its fixture filter is simple, local and bounded; no new dependency, trust-boundary, security, architectural, or performance regression was found in the two code files.

Artifacts include summary.json, source-manifest.json, native-records.json, browser-probe.json, native browser result, baseline and mutation JUnit/logs, w23-provenance.json, and font CDP results. No worker source was changed. Initial generic exec helper failed to launch; all actual review runs used Node child_process with inherited environment and completed native 0.
