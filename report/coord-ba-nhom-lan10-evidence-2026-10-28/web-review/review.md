# Independent web review — R10, 2026-10-28

W04 `f52466dc092edb1bffa7bb4fe030d5482c4d5836`: approve subject to the coordinator's exact final integrated gates/browser acceptance. No Critical or Required finding in this delivery.

W12 `af2993a57ae4d9c023e0b77a5d6b699399753427`: request changes for WEB-R10-01. Its author suite passes but misses a reproducible request-ordering regression.

## Required — WEB-R10-01 (P2): older GET overwrites successful invitation creation

At `src/web/frontend/src/Invitations.tsx:19`, the list effect applies `setItems(value)` without invalidating reads that started before a successful mutation. The form remains enabled while that list is loading. The send callback at lines 35–36 correctly adds the POST response items, but the earlier GET can subsequently replace them with its old snapshot.

Reproduction against the actual `EmailInvitations` component in an ordinary scratch source copy:

1. Hold the first `GET /api/v1/courses/course/invitations`, whose snapshot is `{items:[]}`.
2. Fill “Email người nhận” with `new@example.invalid`, then click “Gửi lời mời”.
3. Resolve POST with one canonical public invitation. The success notice appears.
4. Release the earlier empty GET. The UI now says “Chưa có lời mời đang chờ.” The newly created email and its cancel button are absent despite the successful POST.

The independent test `review regression: a list response started before POST cannot erase the newly created invitation` fails on the missing rendered email: **1 assertion failure, 0 setup errors** in `w12-independent-final.xml`. The three controls pass. In particular the normal GET-then-POST control sends exactly 50 distinct addresses once, renders the POST response email with an enabled cancel button, and does not show an empty list. This establishes an ordering defect rather than a bad DTO or rendering fixture.

Required action for the web owner: ignore superseded list responses or serialize reads and writes, settle loading correctly, and add the interleaving regression. No reviewer product fix has been applied. The coordinator has been notified to hold W12.

## W04 correctness and security

The account page reuses the real PATCH `/me`, POST `/me/password`, and POST `/auth/logout-all` contracts. Name validation trims and checks 1–60 code points; password fields use the current W02 UI rules, with common-password rejection on the backend. Field envelopes, invalid-current-password feedback, busy states, confirmation, route cleanup and password clearing are exercised by the existing component suite.

Independent probes execute actual `AuthProvider` callbacks. A stale successful refresh and a delayed profile PATCH from A cannot replace B's rendered email or the CSRF token observed on a later real `apiFetch` call. A queued logout-all transition for A cannot clear a later B session. These are independent observable assertions, not checks of an assigned guard flag. The 10 author account cases plus 3 independent cases pass: `w04-focused-rerun.xml`, native exit 0, **13 passed**.

Removing the refresh epoch condition in the scratch `Auth.tsx` kills the independent identity test: **1 assertion failure, 0 setup errors**. The original bytes are restored with matching SHA-256 `83b129bbb2580cbe564e694e671f0a24f5f57d6917df9b2e33c2ce1c9a5767a3`; restored independent suite **3 passed**, native 0. See `w04-refresh-epoch-mutant.restoration.json` and `w04-restored-green.xml`.

## W12 contract, security and coverage

The six API calls match the accepted backend; accept/decline use public invitation IDs and no raw-token membership endpoint. The client validates 50 inputs before deduplication, then posts normalized unique emails. UI failures cover unverified email, rate limiting, validation, and full courses. The membership flow refreshes actual courses after acceptance and states the W11 privacy disclosure. The unverified inbox independent probe verifies both the absence of accept controls and the absence of an inbox request.

Fragment processing removes `#invitation=...`, carries boolean context through form switching, and makes no invitation/token API request. The independent AuthPage test asserts the actual resulting route and records every fetch; its sole request is `/api/v1/me`. Disabling fragment removal produces **1 assertion failure, 0 setup errors**. SHA-256 after exact restoration is `594edbb3004c54cc3a2537cce687bea3b6a1f04c90e9fc9f3c0f3c6db16c493b`. Restored controls pass. The copied author invitations suite independently passes **13 cases**, native 0 (`w12-focused-rerun.xml`), while WEB-R10-01 remains RED.

## Provenance and integration

Pinned coordinator main is `776f1f00b13726fcdc95f12bfd18a2b937bbd153`. W04's merge base is `4c69322c9ee23f65902a2ab4f42b519c5e4ca828`; W12's is `530a8c9f5109bac549b224f17ffee727d2767c07`. W12 does not include W04. Neither submitted delivery includes the newer pinned main, so author gates do not replace the coordinator's final integrated gates.

Manifest audit checks the scoped web/scripts source files and every ticket evidence entry: W04 **590 source / 189 evidence**, W12 **591 source / 352 evidence**, **0 mismatches**. Unrelated core source entries and paths excluded conservatively by the source allowlist are recorded explicitly; this is not a claim to revalidate the entire repository manifest. `git diff` confirms no `src`/`scripts` changes between W04's tested source `bc4349fd7369af467f7064bf88794a118800d529` and its tip, or between W12's tested merge source `079020110a975e6da211a7a36a1981082bc87fe6` and its tip. Full hash results are in the two provenance JSON files.

The author JUnit artifacts support their reported counts: W04 Python 3,407 passed plus 4 skipped/xfail, React 239 passed; W12 Python 3,433 passed plus 4 skipped/xfail, React 243 passed; no failures/errors in those author final suites. Author mutation artifacts contain assertion failures with no setup errors. These are audited author artifacts, not independent reviewer PG runs.

The coordinator's preliminary combined candidate `44de063abedcc588da116ecbb8454e50d1e63806` was inspected read-only. Its `Auth.tsx` preserves W04's provider/epoch/profile/logout-all code, and adds W12's intended AuthPage fragment/state changes. Diffs and native receipts are in `topology-and-combined-auth.json`. The coordinator subsequently chose to exclude W12 pending repair; this review does not accept the preliminary combined candidate.

## Boundaries and evidence

Applied the local `code-review-and-quality` instructions and root AGENTS.md against the R9 assignment, W04/W12 tickets, functional/design specs, accepted backend code and worker reports. Inspected existing author mobile screenshots for account and invitation states; they are not new reviewer browser captures. No extra visual finding is claimed from this limited inspection.

All probes/mutations ran in `tmp/coord-r10-web-review-20261028` ordinary frontend/dependency copies. Initial copied-author runs encountered missing `rehype-katex` in the coordinator root's installed dependencies; those setup-error logs remain as historical attempts, and ordinary copies of missing worker dependency directories enabled the final passing reruns. No package install/network call was used. Commands, native exit codes, source hashes, JUnit, logs, mutation originals and restoration receipts remain in scratch. `copy-and-restoration-final.json` verifies that the copied product source files exactly match their worker originals after restoration.

No worker/root/feature code, database, worktree or existing artifact was edited or removed. No full Python/PostgreSQL gate or own browser runtime was run, no learner/held-out cache or real `.env` values were read, and no paid/provider/SMTP call was made. Cost 0 USD. Final acceptance remains conditional on the coordinator's exact final source and integrated gates/browser checks.
