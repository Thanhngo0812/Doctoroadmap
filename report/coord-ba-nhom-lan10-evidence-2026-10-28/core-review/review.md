# Independent backend review R10 — W17.1

**Verdict: conditionally acceptable for W17.1 backend only.** No Critical or Required implementation finding reproduced. The coordinator must still pass a fresh full PostgreSQL gate on the exact integration commit. This review does not accept React, W17.2/W17.3, or all W17.

Reviewed delivery `9cf405acbbf8838d05a17b4bb7936d171cb5afa5` (`work/w17-admin-users-backend`) against coordinator main `776f1f00b13726fcdc95f12bfd18a2b937bbd153`. Delivery branch base is `530a8c9f5109bac549b224f17ffee727d2767c07`; its three commits are implementation `7722a78b`, expanded tests `8a8a46cb`, and evidence packaging `9cf405ac`. The diff after the tested source commit `8a8a46cb1e7eef2c95daddbe6cc36192b5aeff20` contains no `src`, `scripts`, `tests`, or `pyproject.toml` changes. Broad main-to-delivery differences in unrelated evaluation files arise from the older branch base and are outside this backend review; integration must retain current main.

Read AGENTS.md, code-review-and-quality SKILL.md, round-9 core assignment, W-17 ticket, functional spec sections 3/8/9/10/11, database/auth infrastructure, complete delivered implementation/tests, and the delivery report/evidence. All probes use ordinary copies under this scratch directory. Worker/root product files were not changed.

## Findings

### Optional C-R10-01 — explicitly decide how to recover from zero active admins

Locations: delivered `wayfinder/application/admin.py:48`, `:55`; `wayfinder/infrastructure/admin_store.py:46`; delivery report line 39.

The last role-admin can disable itself: the role stays admin, its sessions are revoked, and the database has zero active admins. A disabled admin also counts in `admin_count`, so an active admin may demote itself while only disabled admins retain the role. The first case is independently reproduced by `test_last_role_admin_demote_rejected_but_disable_is_explicit_gap`; its SQL assertion proves zero `role='admin' AND status='active'` rows after disabling the only admin. This can leave web administration inaccessible until an operator creates another admin or restores access externally.

This is **not a Required W17.1 change**: the specification prohibits demoting the last admin, and the assignment explicitly requires reporting the disable-policy gap without silently inventing a new rule. The worker clearly documents the behavior, does not claim owner approval, and proposes preserving at least one active admin plus a CLI recovery procedure. Recommend that the project owner decide that policy and the recovery procedure before operational use; keep it recorded as open.

## Implementation assessment

- Authorization is in domain policy and application service. All three current admin operations authorize before work; mutations authorize again after the shared admin/account locks. Current account role/status is read rather than trusting an old Actor. New HTTP routes depend on authorization and use existing Origin/CSRF middleware. No membership bypass was added to learning routes.
- Role transitions execute under existing AuthStore.atomic with the shared `admin:users` key. Account ID and normalized-email keys match existing account/login/reset paths. The global key protects count-then-demote across independent runtimes; the email key orders disable against login session creation. Author PG race mutants remove these locks and are assertion-red. SQLite review probes do not prove PG lock behavior.
- Account changes, session revocation and every actual field-change audit insert share one transaction. Independent SQL snapshot tests inject audit/session-delete failure and prove account role/status/quota, sessions and audit all match the pre-call snapshot. No-op patches produce no duplicate events. Enable does not recreate deleted sessions.
- User SQL selects declared public account metadata, course counts and quota counts; no course titles/content are queried. Audit SQL selects only id/time/actor/action/target/IP, excluding meta. HTTP DTOs strip extras at top/item/nested levels; an independent real-app probe and an independent DTO mutant prove this.
- Filters use bound parameters, literal strpos email matching, stable ordering, limits 1..100 and offsets 0..100000. HTTP schema rejects invalid role/status/action/UUID/time bounds and patch fields. Independent injection-shaped email search returns zero matching accounts.
- Null quota override inherits the configured per-user monthly default. The default remains null for demo; this change never enables a global cap. Quota counts reuse the existing Vietnamese month helper and `counts_quota` predicate, with an exclusive next-month bound. Author leap/year/month boundary cases and the independent SQL boundary case exercise this.
- Registration already creates a session and writes last_login_at; successful login advances it. CLI admin creation keeps last_login_at null until login. The independent fake-store test executes the existing AccountService behavior to verify all three semantics.
- No migrations/dependencies/IAM layer were added. The change fits existing policy, service, store, composition and router boundaries. The two correlated aggregates are bounded by the page size and use existing schema; no unbounded private learning records are loaded.

## Independent executable evidence

Standard runner only: `.venv/Scripts/python.exe scripts/w05_run_tests.py`. The scratch runner copy is unchanged; `WAYFINDER_TEST_DATABASE_URL=sqlite+pysqlite:///:memory:` prevents reading .env. A scratch conftest accepts the standard mandatory flag but defines no PG fixtures. No PostgreSQL, browser, SMTP, provider, live cache or heldout-data work was run by this reviewer.

- Final restored suite: **23 passed, 0 failures, 0 errors**, native exit 0, `runs/final-restored.xml`, `runs/final-restored.log`, `runs/final-restored-exit.json`.
- Six independent source mutants: removed revoke; bypassed last-role-admin guard; removed atomic transaction; exposed audit meta; removed user HTTP response model; removed post-lock live-actor recheck. **6/6 caught**, seven failing assertions in total, **0 setup errors**. Each mutant has a dedicated native receipt, log and JUnit; `mutations.json` records original/restored identical SHA256. Byte backups are ordinary files in `runs`.
- The first scratch baseline (`baseline-01`) had 15 failures because raw SQLite fixture IDs used hyphens while SQLAlchemy's non-native UUID binding uses compact hex. This was a reviewer harness defect, corrected only in synthetic seeding. `baseline-02` passed 22 cases. It is not claimed as a product RED or as a valid regression proof. After adding the separate registration semantics probe, final-restored passed 23.

## Source and author evidence audit

- `source-copy-manifest.json` records 261 ordinary source copies and matching SHA256 values. `copy-restore-audit.json` verifies exact final source restoration and no reparse files.
- `author-tested-source-audit.json`: **144/144** source hashes in the author's full-gate receipt match current delivery-worktree bytes. The tested source and handoff source are equivalent; packaging alone follows the source gate.
- Independent `test_delivery_evidence_manifest_and_junit_are_consistent` checks every packaged manifest hash; the full JUnit has 3485 testcases, no failures/errors, matching 3481 passed + 3 skip + 1 xfail. The author reports PG native exit 0; this audit authenticates those local artifacts, not a rerun.
- `author-mutation-audit.json`: **11/11** author mutation XMLs contain assertion failures and zero errors, agreeing with the mutation ledger. Source anchors and named tests correspond to the claimed guards. No author mutation is counted as independent reviewer execution.
- Raw worktree and git-blob hashes differ for some pre-existing CRLF files, explicitly recorded by the author's source identity report. Current worktree hashes match the exact tested native bytes. Packaged evidence normalizes LF/ANSI/trailing whitespace with raw SHA values retained in its manifest; this is disclosed, not silently represented as raw bytes.
- The author's full gate/React/build were run at 8a8a46cb. The source/evidence packaging note preserves its console UnicodeEncodeError and the subsequent manifest verification; it does not pass that packaging command off as a successful test gate. Unrelated modified W06/W14/W15/W25 test exports remain outside the delivery commit.

Artifacts: `summary.json`, `commands.md`, `test_independent_admin.py`, `run-probes.ps1`, `run-mutations.ps1`, `runs/`, `mutations.json`, source/copy/author audit JSONs. The exact main integration PostgreSQL gate remains a coordinator responsibility and acceptance condition.
