# W-07 Browser Harness Review

## Scope

Read-only review of `scripts/w07_web_check.cjs`, `scripts/w07_web_runtime.py`, and the final browser/runtime artifacts. I did not run the harness. The final browser run is pinned to source commit `8f7fd4e`; results below are from the parent-run artifacts.

## Verdict

No blocking issue found in the runtime isolation or console/error classification.

## Evidence reviewed

- [runtime.json](runtime.json) records browser exit code 0, migration head `w06_0005`, and removal of the UUID-named disposable database. An independent PostgreSQL connection found two learner A progress rows, no learner B rows, and no persisted rollback write.
- [browser-audit.json](browser-audit.json) records six real API screenshots and twelve separately labeled mock-only empty/loading/error screenshots. The mock states are marked `acceptance: false`.
- The real browser path used fake mail/media adapters and recorded zero model calls and zero cost. Runtime provider entry points are patched to fail if invoked.
- The browser audit contains 19 raw console errors. All are retained and narrowly classified: two unauthenticated `/me` 401s during registration, one intercepted rollback PUT 500, four intercepted progress GET 500s for mock error screenshots, and twelve CSP messages during Axe probes. For the HTTP errors, classification requires matching stage, method/path, and status in the API response log; the rollback case additionally asserts the exact PUT path and exactly one occurrence.
- The six Axe Google Fonts XHR failures are retained as raw probe requests and only classified as expected for `/css2`, `xhr`, `csp`, during an `axe:*` stage. The audit reports zero genuine console errors, page errors, other failed requests, unexpected external requests, or font failures. Axe reported zero violations and zero incomplete checks at each viewport/theme. Independent SVG contrast checks recorded minimum ratios of 5.637 in light mode and 7.349 in dark mode.
- Learner state and progress artifacts contain synthetic IDs and progress data, not cookies or CSRF/session tokens. Runtime logs do not serialize the database URL or provider credentials.
- The taste inspector reports one non-blocking `unused-canvas` warning at 1280px: content stops 189px short of the right edge while starting 40px from the sidebar. It reports no findings at 768px or 390px. This is a visual review note, not an Axe or browser assertion failure.
- The mobile account control is labeled “Tài khoản” and the harness uses its full accessible name.

The rollback 500 is intentionally injected in the browser; it is not evidence of a real server 500. Its lack of a database write is checked separately by the real progress GET and independent PostgreSQL audit.
