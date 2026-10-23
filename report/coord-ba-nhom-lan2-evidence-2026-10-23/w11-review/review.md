# Independent W-11 review — 2026-10-23

Pinned worker commit: `253874bbd83e4224477542928b4a3ef9344db93a` in `tmp/w11-share-links`.
Previous reviewed commit: `85397092ed10bffe2db3bda96d2db6a6d2759c48`.

**Verdict: approve the W-11 auth-return correction. No Critical or Required finding remains.** The original eight failing form-switch cases now pass independently. Coordinator integration gates and any later main contracts remain separate work; this review does not merge or push anything.

## Product review

- `Auth.tsx` preserves the already sanitized `next` in one `switchTarget`, reused by the header link, footer link, and view-transition callback. It does not forward raw `requestedNext`. No-next navigation keeps the existing destination. The existing rejection of external schemes, protocol-relative URLs, backslashes and whitespace is unchanged.
- The other Auth markup edit reuses CourseShell's SVG theme icon and retains the accessible button label. No style token, typeface, palette, motion preference or CSS rule is weakened.
- The worker imported the original ten-case reproduction with only Testing Library type-option compatibility adjustments and a regression comment; original assertions remain. Twelve unsafe-next cases are additional coverage.
- The W-11 service/store/API and migration did not change relative to the previous review. Previously reviewed transaction, max-use/capacity, revoke/membership, token storage, immediate authorization and private-data retention controls remain intact. W-15 and SA22 changes in the diff were received from main and are not attributed to this auth patch.

## Independent executable check

Only two files were copied as ordinary bytes from the pinned worker into the existing isolated review worktree `tmp/coord-w11-auth-repro-20261023`: the patched `Auth.tsx` and the expanded worker test, named `W11AuthReturn.worker-recheck.test.tsx` locally. The worker worktree was not changed. The original independent ten-case test remains present and was run alongside the worker's twenty-two cases.

Result: **32 passed, 0 failed, 0 errors, 0 skipped; native exit 0**. This covers the original 8 header/footer × login/register × transition counterexamples, direct controls, plus the 12 unsafe-next cases. HTTP/auth are mocked and unexpected requests throw. No PostgreSQL, browser runtime, model, mail or provider was invoked.

Exact cwd/argv and counts are in `focused-result.json`; source hashes are in `focused-inputs.json`. `auth-return-independent-green.xml` and `.log` preserve the independent result. The original RED remains at `tmp/coord-w11-auth-repro-evidence-20261023`: 8 failures and 2 controls passed against unchanged product `85397092`.

## Read-only evidence verification

- Both source manifests: **639/639 SHA-256 hashes each match** the pinned worker source. Final evidence manifest: **318/318 hashes match**.
- Source/test/script/design deltas between tested `2c5166b`, browser-tested `33f9c25`, and handoff `253874bb` are empty. Main bases `865974a` and `1d193735` are ancestors. Documentation receipt timing and the owner's baseline freeze are explicitly recorded by the worker.
- Saved final/latest JUnit: **2,292 Python passed / 1 live Cloudinary skip**, and **143 React passed** in each run. Saved native exits for Python, React, build and browser are 0. These are verified worker results, not full gates rerun by this reviewer.
- All **8 backend mutations** fail via one assertion each, with 0 errors, native 1, and source hashes restored to the current worker bytes. Removing the next sanitizer fails **12 selected assertions**; the 10 unselected tests are reported as filtered skips for that mutation only. Its source is restored and all 143 React tests run without skips in the full suite.
- Saved browser audit: **48 screenshots, 16 Axe audits at 1280 px, 113 HTTP records, 8 auth-return scenarios**, no violations/incomplete checks/unexpected console/page/request errors. Four normal-motion scenarios observe one forwarded native transition call; four reduced-motion scenarios observe none. Harness checks exact invite return, authentication, join and subsequent course GET for every combination.
- Saved SQL evidence verifies auth-return link use count 8, one remaining owner, the primary link use count 1, retained Phase B data and required audit event types. Harness uses separate UUID PostgreSQL and fake/no external providers, and records cleanup. This reviewer did not query PostgreSQL or start that runtime.
- Viewed final auth registration at 390 px dark and auth login at 1280 px light; the small SVG replacement fits the existing design and labels remain clear. Axe scope is accurately separated from the 390/768/1280 screenshot matrix.

## Optional

The pre-existing browser harness console whitelist still accepts a text-only 401 match without route/stage scoping. Narrowing it to the expected identity bootstrap request would improve later diagnostics, but it is not a blocker for this patch and does not invalidate the auth-return assertions.

Full machine-readable checks are saved in `evidence-verification.json`. No worker file, shared-main file, held-out input, global learner cache, skill or model configuration was modified. No commit, merge or push was performed in this review round.
