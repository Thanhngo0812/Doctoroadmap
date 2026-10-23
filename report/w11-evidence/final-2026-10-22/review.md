# W11 integration review

Read-only review of service/store/routes, composition merge, migration and UI at `a559737`.

## Findings resolved

- Browser/Axe found an invalid `aria-labelledby` on the failed-join branch. A React regression failed before adding the heading ID; it passed afterwards. No reset/email page was reused.
- Initial development fixture created `share_link` through SQLAlchemy metadata. It now asserts the revision and table created by Alembic; W11 has exactly one successor migration after W14.
- Browser harness closed a freshly reopened dialog while its list fetch was running. It now waits for that response before Escape, retaining the zero unexpected failed-request assertion.
- Evidence redaction initially collided with CSP and then contrast analysis. A harness-only same-origin stylesheet now uses text-security; application CSP and foreground/background tokens are unchanged. Full tokens are also redacted from JSON, including Axe node HTML.

## Correctness and security checks

- Preview is the explicit token-based public route; management uses session actor and owner authorization. All `{cid}` routes remain subject to the private-course inventory test, including outsiders with admin role.
- Token is canonical base64url for 32 random bytes; persistent fields contain only SHA-256 digest and six-character tail. Create returns the URL once; list does not contain it. No auth response/request headers are included in browser evidence.
- Join locks link, then course; validates current link, preserves existing membership without another use, checks capacity, inserts membership, increments bounded count and writes audit in one transaction. Revoke never reverses lock order. An audit error rolls back both membership and use.
- Revoking a link does not remove membership. Removal/leave modifies membership only, with immediate next-request authorization. Exact session/progress payloads remain in PostgreSQL and can be read again after rejoin. Owner cannot remove self or leave.
- Member list excludes learner identities for ordinary learners. Preview returns course/owner summary only. No client-provided owner/doc/version is accepted.
- Merge retains W14 `BuildView.upload_id` scoped to actor/course and per-upload `confirmed_at`; no W14 worker/state/schema code was replaced.

## Scope and maintainability

- No new dependency or generic abstraction. Native dialog provides focus containment/Escape/restoration. Existing API helper, CSRF/session, design tokens and theme shell are reused.
- Phase B use cases and live providers are unchanged. The accepted SA55 code received from main is not a web implementation or permission to spend.
- No Critical/Required product issue remains from this review; final gates and browser evidence remain separate executable proof, not inferred from this document.

## Verification boundaries

Mutation ledgers distinguish assertion failures from setup/schema RED. All mutation runs finish and restore exact source bytes before a full gate/server. Basetemp lives under `tmp/`. Browser fixture account/course are created only in a UUID test DB. Whole-repo tests regenerate older evidence JSON; copies are archived under this ticket and originals restored, rather than staged as unrelated changes.

## Final integration and appearance review

The final source is `bf3cb87dbc2a6345f3399a59a640a863c9f9c7d6`, based on main `dee87ccde928100c7e6168a348040d77d197ebfb`.

- Fixed the harness theme matrix to invoke the real React toggle. Mutating only the HTML theme attribute left the logo out of sync; the actual application theme state must drive both. Dispatch while the modal shell is inert is scoped to appearance capture, not a claim of interactive background access.
- The taste inspector initially exited with a missing profile directory. The harness now creates it and requires a parseable report with all three viewport measurements; exit code alone is insufficient.
- Visual review found owner/learner date columns shifted because the owner's action column had no button. A browser assertion failed on the old CSS at 768 px, then passed after reserving the action width consistently at 768/1280 in both themes. The mobile layout retains its separate stacked rules.
- The inspector reports no FAIL and one hero-void warning on a two-person member list. Extra empty canvas is appropriate for real small membership; inventing rows or unrelated modules would distort this screen's task. No product content was fabricated to satisfy that heuristic.
- The report named browser-alignment-red completed successfully because the preparation command failed decoding before inserting the new assertion. It is retained as history and is not counted as a RED. The subsequent browser-alignment-red2 contains the genuine independent geometry assertion failure.

No Critical/Required finding remains from this source review. Full gate and final browser results are recorded separately in the handoff report; this review does not grant acceptance or authorize a merge.

## Accessible transient and denied states

Final source advanced to `b9b5e6817390f8189813707095a04eeac16df95a` after three focused regressions demonstrated missing label targets during loading and on the denied members page. The error heading now has its own ID; loading sections omit the reference until their heading exists. All three tests failed before the fix and passed after it (regions-red.xml / regions-green.xml). The final browser runs on this source. The final full Python gate uses a fresh basetemp and acceptance-* logs. No backend, migration, provider, or Phase B use case changed in this last fix.
