# W11 sharing API contract

Approved contract for frontend integration, 2026-10-21. Scope excludes email invitations and member progress summaries.

## Share links

`POST /api/v1/courses/{cid}/share-links` requires an owner session and CSRF. Body:

```json
{"expires_in_days": 7, "max_uses": null}
```

`expires_in_days` defaults to `WebSettings.share_link_default_days`; explicit `null` means no expiry. `max_uses` defaults to `null` (unlimited). The response includes a `link` with `id`, one-time `token`, `url` formed from `WebSettings.public_base_url + "/join/" + token`, `token_tail`, `created_at`, `expires_at`, `max_uses`, `use_count`, and `status`. The raw token is returned only in this creation response and is never stored or logged.

`GET /api/v1/courses/{cid}/share-links` returns `{ "items": [...] }`. Each list item contains `id`, `token_tail`, `created_at`, `expires_at`, `max_uses`, `use_count`, `revoked_at`, and `status`; there is no token or URL.

`DELETE /api/v1/courses/{cid}/share-links/{lid}` revokes an owned link and returns `{ "message": "Đã thu hồi link chia sẻ." }`. Repeated revoke is idempotent. Revocation does not remove current members.

## Join preview and join

Guest `GET /api/v1/join/{token}` returns `{course_id,title,owner:{display_name},module_count,concept_count}`. Invalid, revoked, expired, and exhausted tokens have the same `link_invalid` error code, status, and response body.

Authenticated `POST /api/v1/join/{token}` requires CSRF and returns `{course_id,role,joined_at,already_member}`. A repeat join returns the current role (`owner` remains `owner`) and does not consume use capacity. It still rejects revoked or expired links. A new learner joins atomically with link use-count increment, membership capacity check (200), and audit event.

## Members

`GET /api/v1/courses/{cid}/members` returns a stable top-level object with `role`, `owner`, and `member_count`. Owners additionally receive `members`, containing `{user_id,display_name,joined_at,last_active_at,via}` for every member. Learners do not receive the `members` property or another learner's identity.

`DELETE /api/v1/courses/{cid}/members/{uid}` is owner-only and returns `{ "message": "Đã xoá thành viên." }`. The member loses access on the next request; Phase B data remains. `POST /api/v1/courses/{cid}/leave` removes the current learner and returns `{ "message": "Đã rời khoá học." }`. Owners receive `forbidden` when attempting to leave.

## Errors and privacy

- Private course or unknown link/member IDs: `not_found`.
- Non-owner management/removal: `forbidden`.
- Invalid fields: `validation` with the standard structured envelope.
- Course membership cap: `course_full` (409).
- Owner leave: `forbidden`.
- Link invalidity always uses the same `link_invalid` envelope; do not expose the reason.

All mutating endpoints use the existing session cookie, `get_actor`, Origin and CSRF checks. Link and recovery responses use `Referrer-Policy: no-referrer` and `Cache-Control: no-store`. The generic request logger must not record raw tokens.

## Storage and transaction behavior

Persist only `SHA-256(raw_32_bytes)`, the last six encoded token characters, and link metadata. The URL token is the canonical unpadded base64url encoding of those random bytes; parsing validates that canonical encoding, decodes it, then hashes the bytes for lookup. The full token is returned only on create. `join_by_link` locks the share-link row before the course row, checks token validity, preserves idempotent existing membership, checks capacity, inserts a learner membership, increments `use_count`, and appends the audit event in one transaction. Link revoke locks only the share-link row; it never locks the course, preserving the same lock order and avoiding a reverse-order deadlock. Removing or leaving a course does not delete Phase B rows.

Final W11 schema is created in a UUID-named PostgreSQL database by Alembic revision `w11_0007`, directly after `w14_0006`. The sharing fixture asserts that revision and table; it does not call `metadata.create_all`. The initial checkpoint used local schema scaffolding and was not migration acceptance evidence. See the 2026-10-22 handoff for the final migrated PostgreSQL gate.
