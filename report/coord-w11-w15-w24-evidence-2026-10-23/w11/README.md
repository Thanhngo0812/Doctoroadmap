# W-11 — reproduction of lost authentication return destination

Reviewed product commit: `85397092ed10bffe2db3bda96d2db6a6d2759c48`.
Dedicated worktree: `C:/Users/ngoco/Desktop/Doctoroadmap/tmp/coord-w11-auth-repro-20261023`.
Dedicated branch: `review/w11-auth-repro-20261023`.

This reproduction adds only `src/web/frontend/src/W11AuthReturn.repro.test.tsx`. It does not edit `Auth.tsx` or any other runtime source. HTTP/authentication are mocked, and unexpected requests throw. No PostgreSQL, model, provider, mail, cloud, browser server, or held-out data is used.

Dependencies were installed with `npm.cmd --prefix src/web/frontend ci --ignore-scripts --no-audit --no-fund` (native exit 0).

From the dedicated worktree:

```powershell
npm.cmd --prefix src/web/frontend test -- src/W11AuthReturn.repro.test.tsx --pool=threads --maxWorkers=1 --reporter=default --reporter=junit --outputFile=C:/Users/ngoco/Desktop/Doctoroadmap/tmp/coord-w11-auth-repro-evidence-20261023/auth-return-red.xml
```

Result: **10 tests: 2 passed, 8 failed, 0 errors, 0 skipped; native exit 1**.

- Controls: entering login directly from the invite and completing it returns to the invite; entering registration directly does too.
- Counterexamples: login → registration and registration → login, using either the header or footer switch, both with reduced motion/direct routing and with the application's view-transition branch enabled.
- Every counterexample completes the mocked authentication POST and fails the final destination assertion: expected `/join/disposable-w11-repro-token`, received `/khoa-hoc`.
- The transition variants also assert that `document.startViewTransition` actually ran once. This rules out merely labelling the cases as transition coverage.

Cause: `Auth.tsx` calculates the checked `next` destination, but its `switchTarget` (`/dang-nhap` or `/dang-ky`) omits it. Both the links and the transition callback navigate to that target. The destination therefore falls back to `/khoa-hoc` in the next form.

`result.json` records the exact argv/cwd, source commit, test SHA-256, counts and failed case names. `native-exit.txt` records the child test runner's exit rather than the evidence wrapper's successful exit. The JUnit and log retain assertion details. No green run or product fix is claimed.
