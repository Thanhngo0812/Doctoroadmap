# Self-review — W-17.1

Source reviewed/tested: `8a8a46cb1e7eef2c95daddbe6cc36192b5aeff20`, based on main `530a8c9f5109bac549b224f17ffee727d2767c07`.

- Correctness: three routes match the assigned milestone. Partial PATCH preserves omitted values; null quota inherits settings. Vietnam month bounds and counts match existing quota with independently constructed fixture rows. No global cap is enabled.
- Security: role/status policy plus live account recheck; admin changes serialize under a PostgreSQL advisory transaction lock. Account/email locks overlap login/password reset. Account changes, session deletion and audit share one repository transaction. HTTP CSRF/Origin use the existing middleware. Admin-only routes are recursively enumerated; an unguarded probe is detected.
- Privacy: repository selects a fixed user/audit projection, not learning payloads or audit.meta. Actual DTOs drop injected extras recursively. Private chat/document/quiz markers persisted in PostgreSQL never appear in admin output. Admin without membership receives not_found across the course route inventory.
- Architecture/simplicity: application/domain/ports import no FastAPI, SQLAlchemy or other infrastructure frameworks. Existing account/session/audit tables and password/session machinery are reused. One new specialized repository inherits AuthStore transaction handling; no migration, IAM, ledger copy, mail queue or transport change. Queries are parameterized and page size/offset bounded; course/build counts use existing tables/indexes without one Python query per user.
- Verification: 48 W17 PostgreSQL/HTTP cases; 11 deliberately broken guards caught by assertions with zero setup errors. Mutation files restored byte-for-byte. Full runner: 3481 pass, 3 skip, 1 existing SA66 xfail. Skip details retained in JUnit/summary; no W17 skip. React/build native results recorded separately after PG, at the same source HEAD.

No required implementation finding remains within W-17.1. This is a self-review, not coordinator acceptance and not completion of the whole W-17 ticket.

Policy gap retained for owner decision: disabling the last admin is allowed by the assigned status transition; disabled accounts still count as role=admin for the demotion guard. The spec only prohibits last-admin demotion. Preserving one active admin plus a recovery procedure is proposed in the report, not silently introduced as policy.

Optional W12 operational note is documented only: a post-commit verification callback failure may make HTTP report failure after verification committed; listing invitations repairs attachment. No W12 code changed here.
