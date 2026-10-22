# Browser run history

All runs use a dedicated test configuration and UUID PostgreSQL database, fake providers and a real browser. Earlier failed runs remain evidence of development/debugging; only a complete green run is local workflow evidence. None is final acceptance on an approved main.

| Run | Observed result and action |
|---|---|
| 1–2 | Upload overflow at390: native file input's intrinsic width368 extended to x422. Fixed sizing, then introduced the genuine keyboard-accessible Vietnamese file chooser. Run2 preserves element measurements. |
| 3 | Harness-only test-control GET matched the SPA fallback and returned HTML. Ordered gated test-control routes ahead of the fallback. No product route bypass was added. |
| 4 | Harness expected an edited name to be persisted before the explicit confirmation. Corrected it to assert the server's filename-derived name before confirmation and the chosen name after POST. |
| 5 | Manifest-copy preparation exceeded the initial30s wait; teardown's15s join also expired and left a disposable DB. Added bounded240s worker waits with state diagnostics, teardown cancellation between fake stages, and cleanup that still closes/drops its UUID resources after errors. |
| 6 | Generic touch-target check measured the deliberately clipped native input rather than its visible label. Check the visible44px chooser and independently prove Tab reaches the native input and shows a focus outline. |
| 7 | Reading status matched both a heading and descriptive waiting text. Use exact heading locators. |
| 8 | Real390px long course name caused a three-line h1 and a taste FAIL. Fix the product: short status h1 plus full wrapping course name. Preserve the failed inspector output in run8/review-round1. |
| 9 | Heading fix passed taste (0FAIL/1WARN), but the generic30s completion wait expired during the remaining manifest copy/remap. Use a bounded worker-specific wait and keep normal UI/request timeouts. All worker wait branches now report state/errors. |
| 10 | Docker was stopped on resuming work, so PostgreSQL was unavailable. No UI assertion ran. Started Docker Desktop and only `db-test`; reran against a new UUID database. |
| 11 | All workflow branches completed and Axe had0 violations/0 incomplete. The audit rejected an Axe font probe because this Chromium reported its blocked-request reason as `csp`, while the classifier recognized only `net::ERR_BLOCKED_BY_CSP`. Preserve both the raw console event and failed request. Accept those two exact CSP reasons only for the Axe stage, Google Fonts `/css2`, and XHR/fetch; keep the independent one-warning/one-blocked-request count assertion. No CSP policy or application error assertion was relaxed. |

Each final cleanup records `temporaryDatabaseRemoved` in runtime.json. Test controls and the synthetic actor password are harness-only; no production secrets, cookies or headers are written to reports. Input files under fixtures/ are regenerated from approved development data and excluded from Git. Static taste snapshots are explicitly design-only and do not replace the workflow HTTP evidence.
