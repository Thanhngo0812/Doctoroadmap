# Independent W08 review, source 89122f6

Read-only verification is in `summary.json`: 1007 source files, 1007 Git blob mappings, 587 evidence files, 13 counterexamples and final JUnit/browser counts all match. No PG, full test suite, browser server, provider or model was run by this reviewer. The existing worker worktree remains clean.

Two reproducible UI findings:

1. `src/web/frontend/src/Learning.tsx:88-90,127,162-176,199`: marking concept B through the sidebar updates `data.progress`, but the prerequisite and next-up labels in the current lesson read the original `lecture` snapshot. The `Lesson` receives only the selected node's `learned` flag. Mark B learned while A remains open: B's checkbox and module summary become learned, while B's prerequisite/next-up label still says not learned. Both successful saves and optimistic rollback need consistent labels.
2. `src/web/frontend/src/Learning.tsx:82`: the streaming answer filter matches only an unindented `### Tu kiem tra` without a colon. The reviewed core splitter at `src/doc2roadmap/application/phase_b/lecture3.py:73-95` accepts 2-4 hashes, leading whitespace and a trailing colon. Pure calls to the actual splitter confirmed all five headings listed in `summary.json` parse the same body/question/answer. With a valid `##`, `####`, indented heading or colon, the stream visibly reveals the answer before final then folds it at final. Preserve raw body when final `self_check` is null, but use compatible heading handling during streaming.

The helper `Learning.review-repro.test.tsx` retains the author's 10 original cases as controls and adds 7 cases: two stale badges and five core-accepted heading forms. It is prepared, not executed here. Expected on 89122f6: 6 new failures and 11 passes. That expectation is a source-based inference until run, not an asserted test result.

After the coordinator's current full gate finishes, ordinary-copy this helper to `src/web/frontend/src/Learning.review-repro.test.tsx` in the isolated coordinator worktree. Do not copy it into the worker worktree. From that isolated worktree run:

```powershell
npm.cmd --prefix src/web/frontend test -- src/Learning.review-repro.test.tsx --pool=threads --maxWorkers=1 --reporter=default --reporter=junit --outputFile=C:/Users/ngoco/Desktop/Doctoroadmap/tmp/coord-w08-focused-review-20261023/repro.xml
```

Use a subprocess wrapper to capture exact cwd, HEAD, argv, native exit and output to `repro.log`, alongside this helper's SHA in `focused-inputs.json`. No production changes were made to prepare it.
