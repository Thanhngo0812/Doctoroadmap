# Independent W-24 re-review — 2026-10-22

Reviewed `f1ca86dccdf5f7b8e224d325314324050fe415f1` in `tmp/w24-figma-evidence`. **Verdict: Required changes remain; cannot approve the complete local package yet, and W-24 Cloud acceptance remains open.** No Critical security finding. Worker source and evidence were never modified. Runtime uses ordinary copies or reads known local files; HTTP(S) is blocked, with no Cloud/API/model/live/held-out access.

## Verified improvements

- Actual Chromium: 12 W-07/W-14 configurations (390/768/1280 × light/dark), font ready and500ms settling. All six dark configurations now use `rgb(232,237,242)` body text; all W-07 progress fills use the brand blue. No page overflow or visible buttons smaller than44px in this matrix. W-14 spinner loads and renders96×96.
- W-07 visible interactions:8/18(44%) → mark LCx9/18(50%) → undo LAD8/18(44%). Repeating each action does not double count. Module badge and bar agree; accordion toggles both visibility and `aria-expanded`.
- Original verifier in an ordinary copy, with only an external-network block added: baseline4/4, native exit0. Removing actual clipboard write, removing citation scroll, or retaining animated src each produces3/4, native exit1 at the correct Flow2/4/3 assertion. Clipboard now observes the real browser clipboard; scroll now starts offscreen and measures viewport intersection.
- Independent frame mutation: replaced bytes of `Untitled_Artwork_static.png` in the scratch copy with real animated GIF bytes, retaining the static filename. Verifier returns exit1 specifically at `Spinner frame changed over time...`, proving the frame comparison itself catches animation rather than merely checking a filename. Scratch image restored.
- Entire token test file:28 passed, native exit0. This does not prove complete raw/CSS parity; see Required2.
- New report labels Figma prototype links as worker declarations and acknowledges four missing page groups. The new metadata identifies a local mapping rather than an actual Cloud export; that is an improvement, not Cloud provenance.

## Required

1. **OS reduced-motion still renders a broken image.** `design/preview/prototype_flows.html:412` retains `content:url('../assets/spinner_frame0_static.png')`, a nonexistent asset. The manual toggle uses the corrected image, so the happy-path verifier passes; actual `prefers-reduced-motion: reduce` activates this stale CSS replacement. Repro: Chromium context `reducedMotion:'reduce'`, Flow3 → select → start. The `<picture>` source decodes correctly (`naturalWidth=2000`), but computed CSS content points to the missing old file, generates `ERR_FILE_NOT_FOUND`, and renders the broken image/alt text at171×21 instead of the image. See `browser-observations.json` and `prototype-os-reduced-motion.png`. Fix the CSS path or remove the redundant override; verify OS setting as well as manual toggle. NaturalWidth alone cannot validate a CSS replacement image.

2. **Raw/CSS contract remains divergent, and the guard does not compare actual CSS.** `design/tokens/figma_variables_raw_export.json:83,197,230,252` use dark tint alpha0.15 while actual CSS uses0.14. Light `--color-surface-2` is missing despite raw declaring white; `--radius-full` is missing in both modes. Complete37×2 effective-mode comparison yields seven mismatched mode entries. A description saying light surface-2 equals surface is not an implemented alias. `tests/unit/presentation/test_tokens_and_wcag.py:392` hardcodes a subset instead of reading CSS and checking every declared value/mode. The exact guard rejects primary mutation but accepts four independent mutations: dark tint, dark spacing, dark radius, motion-base. More decisively, after changing raw dark brand tint to alpha0.99, the entire28-test file still passes, native exit0. See `token-css-observations.json`, `raw-brand-tint-dark-mutation.log/.xml/-exit.json`. Update the local contract to the existing authoritative CSS and compare all declared mappings/modes with named alias policy if intended; do not lower the token contract to fit this JSON. Correct report's “100% synchronized” claim. The evidence-folder raw JSON remains the older35-variable version while design JSON now has37; either update that copy or explicitly label it historical.

3. **Checklist still overstates scope and misroutes evidence.** `report/w24-kiem-lai-2026-10-22.md:87` calls `screens.html` a landing hero, but that file contains course/roadmap/learning/quiz/upload mockups, not the required public introduction. Row2 points login/register to `w03_auth_screens.html`, whose screens are verification/reset; actual login/register preview is elsewhere. The22-row table still omits original required states: invite course, upload finished/cancel/parse error, empty roadmap library, lecture pending/streaming/fatal/page viewer, six chat states, quiz generation, guest/logged-in/bad invite, course management, usage near/at ceiling, and per-page dark coverage. Keep all original spec11 rows/states and mark missing/unverified explicitly rather than treating generic page presence as full state coverage. This may remain an open completion list when receiving local fixes, but cannot support closing W-24.

## Cloud completion remains unverified

- No independently observed Variables export/receipt; metadata and37 local values are a mapping, not evidence of Cloud collection contents. Plugin still creates16 color+10spacing variables and has not been shown to produce all37 local mappings.
- Node IDs and new Present URLs are worker declarations; this review made no external calls, so neither reachability nor actual four-flow navigation is attested.
- No four prototype videos were supplied in the evidence directory. Screenshots/local browser verification do not substitute for the original Figma video/browse requirements.
- Full original page/state checklist and Cloud parity still need completion. W-23 should not be opened as though the complete Figma source of truth had been accepted.

## Evidence and commands

- `copy-manifest.json`: ordinary copied files with SHA256; no links.
- `native-exits.json`, `unit-token-results.xml`: baseline28 passed and actual native exits.
- `prototype-mutation-results.json` and baseline/three named mutation logs: original verifier's actual baseline and RED outcomes, with external-network-only instrumentation documented.
- `static-png-content-is-animated-exit.json/.log`: real frame-change assertion RED after content mutation; scratch restored.
- `browser-check.cjs`, `browser-observations.json`, `w07-fixed-dark-390.png`, `prototype-os-reduced-motion.png`: twelve configurations, interactions and the OS reduced-motion regression. Both images were opened and visually inspected.
- `token-check.py`, `token-css-observations.json`: all74 mode comparisons and exact-guard counterexamples.
- `raw-brand-tint-dark-mutation-exit.json/.log/.xml`: entire test file stays green with a deliberately wrong raw dark tint; scratch restored.

Re-run from root: `node tmp/coord-w24-review-20261022/browser-check.cjs` and `.venv/Scripts/python.exe tmp/coord-w24-review-20261022/token-check.py`. Verifier command is `node scripts/verify_prototype_flows.cjs` from the scratch root. Its mutable scratch `report/w24-evidence` directory contains the last mutation run; use the named aggregate JSON/logs above as the evidence of each run.

Optional: allow the narrow mobile “Bắt đầu học” button to grow vertically so its three-line label fits. The650px empty diagram placeholder added solely to place the citation offscreen would be better supplied by a test fixture than presented as designed course content.
