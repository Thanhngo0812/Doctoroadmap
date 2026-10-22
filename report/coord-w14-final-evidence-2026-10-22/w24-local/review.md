# Independent W-24 review — 78fb774

Reviewed `78fb774df4e4960cff80e3257d98af79f08aad17` against the previously reviewed `f1ca86d`. Worker source/evidence were never edited; worker Git status remained clean. Focused tests used ordinary byte copies under `tmp/coord-w24-review-78fb774`, without links, deletion, models, SMTP, external HTTP, held-out data or shared phase-B cache.

**Verdict: approve the local code fixes for the two previously reproduced defects; request documentation changes before accepting the complete78fb774 package. W-24 remains open for missing design states, genuine Cloud Variables and four prototype videos.** No Critical security finding. There is no reason to re-open the old broken-asset or74-value mismatch findings: they are now verified fixed.

## Local code evidence

1. **OS reduced-motion fixed.** Actual Chromium OS setting `reducedMotion:'reduce'` now loads the real static image, including its CSS replacement. `naturalWidth=2000`, rendered64×64, zero failed requests, and equal rendered buffers350ms apart. Screenshot was opened and visually inspected. Original four-flow verifier in the copied project returns4/4, native exit0. Reintroducing the former nonexistent CSS asset returns3/4, native exit1 specifically at the OS failed-asset assertion. Manual/clipboard/scroll logic from the previously verified version is unchanged.
2. **Full raw/CSS parity fixed.** Independent comparison of37 variables across two effective modes gives74/74, zero mismatches. The evidence-directory raw file equals the design raw file byte for byte. Added root values for surface-2 and radius-full are additive and agree with the existing design values; four tint alphas now match0.14.
3. **The raw guard now catches the earlier counterexamples.** Focused file32 tests passed, native exit0. Four separate on-disk scratch mutations—dark brand tint0.99, dark space-4=999, dark radius-lg=999, motion-base=999ms—each make the actual named raw/CSS test fail with native exit1. The scratch JSON and HTML were restored; worker originals were never touched.

## Required before receiving the whole package

1. **Correct the remaining false-positive checklist rows in `report/w24-kiem-lai-2026-10-22.md`.** At line144, “Tham gia: link hỏng/hết hạn” is checked using `w03_auth_screens.html#screen-token-invalid`; that exact screen discusses one-use email verification24h/password reset60min, not a broken course invitation. Mark missing or reference an actual invitation-error design. At line126, the row “nút huỷ” only establishes a button exists; the original spec requires the cancelled state. `btn-cancel-pipeline` occurs once with no handler and no cancelled screen. Keep button existence separate and mark the cancelled state missing. The dark-mode row substitutes roadmap/upload/auth/course/profile for the spec's explicit minimum roadmap/learning/chat/quiz; retain the required learning/chat/quiz rows and mark absent or unverified evidence. These are documentation corrections, not a request to implement new product behavior in this patch.
2. **Keep local contract, plugin capabilities and observed Cloud state distinct.** At report line161, the statement that37-variable JSON is generated/synchronized directly with plugin canvas code is too strong: the unchanged plugin defines16 colors and10 spacing variables, not the37 local mappings. The local JSON metadata names collection `VariableCollectionId:45:1`, which is a declared mapping rather than a verified receipt. Parent coordinator has now independently read the actual Cloud file and reported one empty `WayFinder Tokens` collection `VariableCollectionId:45:2`, Light-only (`45:0`), zero variables. This review did not perform that Cloud call; cite the parent's saved tool receipt in the acceptance report. The worker report should record that observed gap and avoid treating lack of a REST token as proof Variables exist. The appropriate path is an actual file/plugin Variables inspection/export, not requiring Enterprise solely to demonstrate existing canvas data.

The existing report appropriately keeps W-22/W-24/W-23 open and now lists most missing states explicitly. Keep that improvement; no need to make every missing state before receiving an accurately scoped local-fix package. However, the checked items above still need correction before the package can be accepted as written.

## Safe merge scope

The local code changes in `design/preview/prototype_flows.html`, `design/tokens/tokens.css`, both raw-contract JSON copies, `scripts/verify_prototype_flows.cjs`, and `tests/unit/presentation/test_tokens_and_wcag.py` are supported by focused GREEN/RED evidence and may be received as local fixes once reporting is accurate. **Do not describe the whole78fb774 package or W-24 as accepted; recommend a worker follow-up documentation commit followed by review of that exact resulting SHA.** No cherry-pick, branch edits, commit or merge was performed by this reviewer. Whole-repository integration gates remain the coordinator's separate responsibility.

## Cloud identifiers and absent proof

- File key `UVhhlZnqdpV0JDcAHwJczo`.
- Current worker report contains no new verified node/export receipt and no prototype video files. Its raw metadata collection45:1 is not a Cloud observation.
- The preceding worker report declared start nodes401:1200,405:2100,410:3500,415:4200. Those are historical self-declarations, not verified node IDs; root should enumerate actual pages/nodes and save the real receipt.
- Coordinator's just-observed empty collection prevents accepting a complete Cloud Variables library. Four flows and screen/state parity still need actual browser/Figma evidence even if local mockups and tests pass.

## Evidence

- `copy-manifest.json`: ordinary copies with SHA256.
- `unit-token-results.log/.xml`, `unit-native-exit.json`:32 passed, exit0.
- `token-css-observations.json`, four `*-mutation.log/.xml`:74/74 actual values and four failing mutation runs with exact command/exit.
- `prototype-mutation-results.json`, `baseline.log`, `os-css-path-broken.log`:4/4 GREEN and targeted OS asset mutation RED. HTTP(S) was fulfilled locally as empty200 CSS for deterministic offline fonts; application assertions and local asset behavior were unchanged.
- `browser-check.cjs`, `browser-observations.json`, `prototype-os-reduced-fixed.png`: real Chromium image decode/render/frozen state and a visually inspected screenshot. Native browser command exit0.
- `checklist-observations.json`: exact referenced auth-invalid copy and absent cancellation handler.

Optional: prototype spinner remains the pre-existing64px rather than the spec's96px in-card size; the dedicated W-14 preview already uses96px. This does not invalidate the now-fixed OS image regression but remains part of full design conformance. Also consider rejecting duplicate raw variable names/properties in the parity helper, so37 entries cannot conceal omission through duplication.
