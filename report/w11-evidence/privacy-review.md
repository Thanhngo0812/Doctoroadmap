# W-11 privacy review

**Scope:** Read-only review of the frozen W-11 service, API, and UI in `tmp/w11-share-links`. No service, browser, database, migration, or test command was run for this review.

## Findings

No blocking token-storage, route-authentication, CSRF, or sensitive-response issue found in the reviewed source.

- `SharingService` generates a 32-byte random bearer token, persists its SHA-256 digest and six-character tail, and returns the full token/URL only from create. List responses contain neither token nor URL. Audit metadata records link IDs and join source, not token material. See `src/web/backend/wayfinder/application/sharing.py` and `infrastructure/sharing_schema.py`.
- Share-link create/list/revoke and member-management routes require `get_actor`; the service enforces owner/member permissions. Mutations pass through the global Origin and CSRF guard. Authenticated join requires CSRF; the public preview is read-only. The learner members response omits the member identity list. See `api/auth.py`, `api/app.py`, and `api/sharing.py`.
- Link previews expose the intended course title, owner display name, and published course counts, without member identities. Invalid, revoked, expired, and exhausted links share the same `link_invalid` response. Join locking and membership/capacity updates are transactional in the service/store.
- Link creation and join/auth-return documents receive `Cache-Control: no-store` and `Referrer-Policy: no-referrer`. The HTML also has a no-referrer meta policy. Uvicorn access records containing `/join/` are replaced with a fixed path after up to three URL-decoding passes, including tokens nested in the `next` query parameter. The UI keeps the one-time create result in component state, clears it when the dialog closes, and does not persist it to browser storage. Auth return and successful join use replacement navigation.

## Remaining acceptance work

- **Guest shell follow-up:** The read-only reviewer found an empty authenticated account menu on the public preview. Root subsequently fixed the shell to show a guest login action preserving the invite instead. The root's focused test observed RED on the old menu and GREEN after the fix (`guest-shell-red.xml`, `guest-shell-green.xml`); real-browser verification remains pending.
- **Browser/privacy evidence:** A real-browser review is still needed to verify the guest preview, auth return, successful join, and invalid-link screens, and confirm no unexpected token-bearing requests or console output. Keep raw token values out of screenshots, videos, logs, and report artifacts; inspect only redacted URLs or the permitted six-character tail.
- **PostgreSQL migration:** W-11 migration `w11_0007` is not present in the migration directory in this worktree. It must be added and applied to a UUID-named disposable PostgreSQL database before claiming schema/migration acceptance. The W-11 metadata scaffold is not migration evidence; do not use `create_all` as a substitute.
- **Deployment logging boundary:** The source filter covers Uvicorn access logs. Any reverse proxy or hosting access logs must also avoid storing raw `/join/{token}` request targets before deployment.

## Evidence limits

This is a source review only. The existing privacy/API tests were inspected but not run here; no claim is made about browser behavior, live PostgreSQL concurrency, or migration application.
