# W14 React backend contract review

Reviewed W14 upload/build routes, `BuildService`, course cards, PostgreSQL store, W25 cancellation tests, and the W14 acceptance ticket on 2026-10-22. No provider, mail, or Cloudinary network call was made.

## UI contract

- `POST /api/v1/uploads` is multipart with `file` and `rights_confirmed`; success is an `upload-1` object containing top-level `upload_id` and nested `build`.
- `POST /api/v1/uploads/{upload_id}/build` accepts `{}` or `{"title":"..."}` and returns a `build-1` view. The optional title is 1–120 characters and is saved once at confirmation, before indexing.
- Poll `GET /api/v1/builds/{build_id}?course_id={course_id}`. Pass `course_id` on every poll: one account can have multiple courses sharing a reused build, and omitting it selects an arbitrary matching upload context.
- `POST /api/v1/builds/{build_id}/cancel?course_id={course_id}` and `/retry` use the same course context and require the authenticated session plus CSRF. Render controls from `can_cancel` / `can_retry`, while treating server responses as authoritative.
- `GET /api/v1/me/usage` returns `builds_used`, `build_monthly_max`, and `builds_remaining`.
- Error body is `{error:{code,message,retry_after,ref}}`; relevant codes include `file_invalid`, `file_too_large`, `file_encrypted`, `too_many_pages`, `quota_exceeded`, `confirmation_expired`, `conflict`, `forbidden`, and `not_found`.

## Resume field and access scope

Course cards originally exposed `build_id` and `course_id` but not the upload identifier required by the only confirmation route. That prevented the UI from resuming an `awaiting_confirmation` course after navigating away. The W14 worktree now adds nullable `upload_id` to `BuildView`; owner cards and owner-scoped GET polling resolve the upload by `(actor, build, course)`. Learner cards receive `null`, and a nonmember's build poll remains 404. This avoids exposing another account's upload ID when a shared build has distinct uploads/courses.

An HTTP/PostgreSQL test covers two same-owner courses reusing one build, verifies the distinct upload IDs in their cards and polls, then verifies outsider 404 and learner `upload_id: null`. The test failed before the implementation with `KeyError: 'upload_id'` and passes after it.

The shared build status does not say whether a particular upload has been confirmed. `UploadView` now also returns nullable `confirmed_at` from that actor-owned upload. This lets the UI distinguish a second unconfirmed course from the already-queued shared build and submit its own title. A second HTTP/PostgreSQL regression confirms the second upload after the first queues the shared build, checks its course title and timestamp, verifies repeat confirmation does not overwrite either, and asserts there is still one quota use and no worker attempt. It failed before implementation with `KeyError: 'confirmed_at'` and passes after it.

## State and permission behavior

- Upload is not confirmation: no worker claim occurs before the explicit confirm POST.
- Reuse is keyed by document digest and pipeline version. A second upload gets its own course/title context while sharing the build. Reusing a succeeded build creates a ready course without a new build or quota charge.
- `can_cancel` and `can_retry` are derived from the original build requester and current state. Service operations independently enforce that requester check. Cancel while running sets `cancel_requested`; the page should keep polling until terminal status.
- Retry is available only for failed retryable builds. It uses a new lease/receipt and preserves quota accounting.
- Upload/build/quota and course-list reads set `Cache-Control: no-store`. Upload size and PDF validation happen server-side; client MIME/extension checks are only an early UI hint.

## Verification

W05 runner, UUID-named PostgreSQL DB, isolated fixture, fake media/mail/build runner, and provider-network guards:

- RED: `report/w14-react-evidence/card-red2.xml` (missing resume ID assertion); `confirm-red2.xml` (missing upload confirmation timestamp).
- GREEN: `report/w14-react-evidence/build-contract2.xml` (resume ID, independent per-upload confirmation/title, reuse, and W25 commit-order regressions): 18 passed, 0 failures/errors.

Root regenerated OpenAPI after both `BuildView.upload_id` and `UploadView.confirmed_at` were added (commits `4c13841`, `261523e`). No full gate or browser run was performed as part of this backend review; root's later runs are recorded separately.
