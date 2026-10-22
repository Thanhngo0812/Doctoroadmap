# W14 React integration review

Read-only adversarial review of `Builds.tsx`, `builds-api.ts`, `Courses.tsx`, `courses-api.ts`, `Roadmap.tsx`, and build route wiring on 2026-10-22. No tests, browser, backend, or server were run for this review. The implementation is still being edited, so findings below describe the files at review time.

## Required follow-ups

1. **Upload navigation does not abort the upload request.** `UploadPage` stores the quota request in `uploadController.current` (lines 29–40), but `submit` creates a different local controller (line 55) and never stores it. The unmount cleanup therefore aborts only the quota request. If the user navigates elsewhere while upload is pending, a late successful response still calls `navigate(...)` (line 60) and can take over the new page. Store the active upload controller in the ref and clear it when that request finishes, or otherwise invalidate the completion on unmount. The current `Builds.test.tsx` does not cover unmount while uploading.

2. **Joined courses must not enter the owner upload/build screen.** `resumePath` in `courses-api.ts` currently sends every non-ready course with a build to `/ban-dung/...`, regardless of `course.role`. The W14 build detail GET is correctly actor-upload scoped; a joined learner has `upload_id: null`, and `get_build` returns 404 without an upload owned by that learner. `Roadmap.tsx` already handles non-ready courses using membership-authorized course status and a refresh button, and redirects only owners to the build screen. Make `resumePath` follow that same owner-only rule so joined learners land on the course page/status refresh instead of the 404 build screen. This also keeps owner-only title/confirmation controls out of the member flow.

## Items verified in the current source

- Build route changes abort the prior fetch and clear `action` before loading new IDs. The stale-action state issue is fixed in the current file (`Builds.tsx` lines 105–110).
- Running cancellation now shows a pending message and hides the cancel button while `cancel_requested` is true (`Builds.tsx` lines 222–223).
- The page loads course, build, and optional actor-scoped upload data; it validates returned build/course/upload IDs before using them. Polls and actions use `AbortSignal`, and polling checks the expected build and course IDs.
- Confirmation is keyed to the upload’s `confirmed_at`, not only the shared build status. This correctly permits an unconfirmed second upload to set its own course title when the shared build is already running or succeeded.
- Cancel/retry controls follow server `can_cancel`/`can_retry`, and the API also enforces requester ownership. Error display maps known codes to user messages and does not render `BuildView.error.message`, avoiding disclosure of internal worker details.
- The build tests cover initial confirmation, a same-file upload confirmed while the shared build is running, polling cadence/control visibility, retry, success, and cancel. They do not currently cover route changes during an action or upload, delayed stale responses, or joined-member build navigation.

## Reported to root/frontend

The missing upload abort and joined-course navigation behavior were sent to root and frontend for the active fix pass. No product files were changed here.

## Root disposition after the review

- The upload now owns its AbortController and checks its aborted state before navigation; `aborts an in-flight upload when leaving the upload screen` is a named runnable regression.
- `resumePath` and the roadmap redirect enter build details only for owners. The shared-build card regression asserts that a joined learner's link remains `/khoa-hoc/:cid`; the membership-gated course screen offers a status refresh. The upload/build API's original ownership boundary remains intact.
- Pending cancellation disables duplicate cancellation, and route changes reset the action state. No broader W-11 permissions were added for W-14.
- Browser review identified the intrinsic-width file picker and a long status heading on 390px. Both were fixed without hiding overflow, truncating the user's course title, changing tokens, or relaxing the inspector. Status is now the short heading and the full course title is a separate paragraph.

The final local React suite has 103 passing tests. Real browser and final-main evidence have separate scopes in the root report; this read-only review alone does not claim either.
