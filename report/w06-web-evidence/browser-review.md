# W-06 browser review

Reviewed `scripts/w06_web_check.cjs`, `scripts/w06_web_runtime.py`, `acceptance-summary.json`, `browser-audit.json`, and `runtime.json` at the final W-06 worktree state.

## Findings

- The browser flow used the actual HTTP app and disposable PostgreSQL: UI registration, six sample-course reads, two joins (one by Enter), a repeated forged-body join, reload persistence, real detail/roadmap reads, resume navigation, and outsider 404 checks. The runtime independently confirmed two learner memberships, idempotent duplicate join, six sample owners, zero Phase B writes, and disposable database removal.
- The runtime uses `FakeMailer` and `MemoryMediaStore`, and patches SMTP, Cloudinary construction, Gemini/embedding URL calls, Vertex credentials, and Google auth lookup to raise if invoked. The recorded model call count and cost are zero. No provider call is present in the browser evidence.
- The browser artifacts contain no session/CSRF token, cookie, database URL, or password. The fixed password in the checker is test-only; `learner-state.json` is checked to exclude token/cookie fields. Runtime JSON contains disposable fixture IDs and counts, not credentials.
- Six real screenshots cover 390, 768, and 1280 pixels in light and dark themes. Twelve extra empty/loading/error images are explicitly marked intercepted mock states with `acceptance: false`.
- Axe reports zero violations and zero incomplete checks in all six real viewport/theme combinations. The separate icon contrast check records 18.161:1 in light theme and 14.685:1 in dark theme. Responsive overflow, 44x44 targets, reduced motion, and visible keyboard focus assertions passed.
- The 17 raw console errors are all narrowly classified and retained: one expected unauthenticated `/me` response, four deliberate intercepted 500s, and twelve Axe CSP probe warnings. Each of the six blocked Google CSS2 XHR probes matches its Axe-stage request record. There are zero unclassified console errors, page errors, failed requests, or unexpected external origins; the production CSP was not changed.
- The aggregate gate reports 2,105 Python passes, one skip, and 77 React passes. The one taste-inspector warning says only two of six blocks start above the 1280px fold; it is retained as a design note and does not contradict the browser or accessibility assertions.

No required blocker found in the reviewed harness or evidence. This review verifies the recorded artifacts and harness design; it does not independently rerun the services or tests.
