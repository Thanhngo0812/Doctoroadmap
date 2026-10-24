# W15 independent review, 2026-10-24

Reviewed `work/w15-real-build` at `9b3bd8287e50c095e946eb4301ccc00a5572ca02`. Requested baseline `5936a5d`; root later reported main `a3804cf`. Read-only worker source review using AGENTS.md and code-review-and-quality. No PG suite, actual operator execution, credentials, SMTP, Cloudinary or paid provider calls. Only this scratch directory was written.

**Full operator package: request changes. Prefix through `bf761fe`: source-review approved, subject to root's integration gates. Full W15 remains open.**

## Required W15-R4-1: Windows prepared plans cannot be executed

`src/web/backend/tests/w15_operator_run.py:88` stores `run_dir=str(run_dir.relative_to(ROOT))`. On this Windows host the native path has backslashes. At `:122`, execute passes that exact string to `safe_path`, whose `src/web/backend/wayfinder/domain/file_paths.py:8` explicitly rejects backslashes.

Both committed real-profile dry-run plans contain this value:

- `report/w15-evidence/operator-20261024/doc6-plan-at-ffd070d.json:3`: `tmp\\w15-operator-doc-6-8aac10784169`.
- `report/w15-evidence/operator-20261024/candidate-plan-at-ffd070d.json:3`: `tmp\\w15-operator-candidate-954c6b6ca4e0`.

An exact saved-plan call to the real `safe_path` raises `ValueError('Path escapes its root')` for both. The same paths converted to `/` pass. This happens before profile/DB/provider composition, so a valid human approval cannot make the prepared Windows flow run. The synthetic operator happy-path test writes `.as_posix()` at `src/web/backend/tests/test_operator_w15.py:60`, bypassing prepare and masking the defect.

Minimal remedy: write `.as_posix()` in prepare. Keep safe_path strict. Add a named regression such as `test_prepared_windows_plan_roundtrips_through_execute_path_validation` that consumes the saved prepare output with fake composition/approval; observe it fail before the fix. Do not repair a real plan manually or loosen path validation as the regression test.

Runnable counterexample, no DB or provider:

```powershell
& 'C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe' -B 'C:/Users/ngoco/Desktop/Doctoroadmap/tmp/coord-r4-core-review-20261024/repro_windows_plan.py'
```

Native exit 0 means the script observed the two expected rejection counterexamples and the passing POSIX controls. It is not a successful operator execution.

## Safe milestone split

The source delta from `5936a5d` to `bf761fe` is identical in size/scope to the source delta from root's later `a3804cf` to that prefix: five test/harness files, 458 added lines, no product source changes:

- `test_pipeline_postport_w15.py`: 269 lines, real DocumentPipeline stages with explicit fake generation/embedding, independent PostgreSQL reads, usage deltas, terminal/cancel/lease coverage, and trace-versus-meter accounting.
- `test_internal_dry_run_w15.py`: 89 lines, independent SHA-verified fixture copies, real core dry-run collector, no queue/course/usage/cache SQL side effects and no paid calls.
- `test_doc6_cache_only_w15.py`: 91 lines, real doc6 bytes and default pipeline through HTTP/worker, expected failure at label-roles cache miss, zero provider use, no published graph or success mail.
- `w15_capture.py`: three lines adding source provenance coverage.
- `w15_mutations.py`: six lines adding injection/checkpoint mutations.

`bf761fe` itself adds only the 91-line doc6 cache-miss regression. Earlier source additions are `a888e92` and `4cbd2ac`. None opens a production spend path. Exclude `5ed9ca1` (operator spend feature), `ffd070d` (operator harness) and `9b3bd82` (operator reports) from this milestone until the Required issue is fixed/reviewed. Reports accumulated before the prefix are much larger than the source delta; they remain historical/fake evidence, not a full-W15 completion claim.

No other high-confidence Required finding was found in this prefix. Root must run the agreed focused/full PG gates on the actual integration tree before merging it; this review did not run those gates or mutate worker source.

## Approval, cost and receipt assessment

The added operator feature has no API request-body or WebSettings switch opening spend. The normal adapter remains allow_spend=False. BuildSpendApproval checks full PDF SHA, u-hash, pipeline version and priced model profile, and consumes the reference in the same PostgreSQL atomic boundary before paid construction, including a failed attempt. The outer operator harness also matches approval database to the prepared nonce database.

The approval JSON's `approved_by='project-owner'` is a trusted local operator attestation, not cryptographic proof of the human author's identity. The docs expressly place that trust outside the HTTP interface. Do not describe it as cryptographically unforgeable or a general untrusted-file authorization mechanism.

The guard reserves capacity before dispatch, holds concurrent reservations, retains a timeout/missing-usage upper bound and stops later dispatch. Audit failure keeps an already returned billed response available to the core meter. RealBuildAdapter marks unknown/stopped terminal receipts failed; known usage remains the core meter delta. The independent synthetic SQL export confirms counted_in=build trace typed cost/tokens are zero and the summed build ledger equals the build receipt exactly once. The provider hook is a budget and audit layer, not another billed ledger input.

Isolated in-process fake probes independently exercised exhausted remaining capacity, timeout retention and reported cost greater than the bound; all prevented the next dispatch. These are not actual billing measurements. Abrupt process-kill recovery was not tested here; a persisted consumed reference prevents automatic reuse, but the in-memory guard/event state and final receipt cannot be claimed durable across a killed process from these tests alone. Existing W25 cancellation/late-receipt tests are synthetic controls, not a real provider cancellation demonstration.

Doc6 actual-byte evidence is accurately limited: the upload/worker path stops with SpendNotAllowed and zero calls after reading; no ready/course/success mail proof exists for that book. The bootstrap-then-web-ready flow is only rehearsed with synthetic PDF/providers. The proposed 1 USD bootstrap and 3 USD candidate caps have no owner approval and were not executed. No new approval request is made by this review.

## Evidence checked

`verify_selected_evidence.py` verified ten selected manifest SHA/byte entries, and all 23 current source byte hashes in the recorded full-gate native metadata match the tested `ffd070d` source. Recorded JUnit: scope 76/76, full 2534 passed of 2536 with the pre-existing Cloudinary skip and replay xfail, no failure/error. Recorded mutation JSON has 29 assertion kills, zero setup errors and source-restored flags. Those mutation runs were read, not rerun. Source-native captured HEAD `4038055` for dirty precommit scope/mutations is accurately distinguished from the full gate at `ffd070d` in the report.

Selected synthetic SQL exports independently show trace zeroing/single-count ledger, doc6 cache miss without free-success claim, and both internal dry-runs with collector one/no queue/no provider/all relevant SQL counts zero. Did not scan live cache, held-out sources, or all 1108+ historical receipt files. These checks validate consistency of the selected committed evidence; root's fresh gates determine current integration status.

```powershell
& 'C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe' -B 'C:/Users/ngoco/Desktop/Doctoroadmap/tmp/coord-r4-core-review-20261024/verify_selected_evidence.py'
& 'C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe' -B 'C:/Users/ngoco/Desktop/Doctoroadmap/tmp/coord-r4-core-review-20261024/probe_spend_guard.py'
```

Both returned native exit 0. Provider calls and DB connections by this reviewer: zero. No cleanup, linked assets, fixture changes, or worker source edits.

## Follow-up: embedding pricing unit before any paid run

Root requested an additional primary-source check. See [embedding-pricing-primary-check.md](embedding-pricing-primary-check.md). No character-based undercharge is proven: official Cloud material explicitly supports tokens for gemini-embedding-001 batch usage, whereas the online pricing table only says “count” and the response examples contain both token and billable-character metadata. **Required before paid/profile sign-off:** establish the exact online Vertex SKU unit and metadata mapping for the bound at build_spend.py:56 and actual-cost formula at :103. This is an evidence prerequisite, not a second reproduced functional defect or a blocker for the test-only bf761fe prefix. The ordinary no-spend adapter and the Windows finding's verdict are unchanged.
