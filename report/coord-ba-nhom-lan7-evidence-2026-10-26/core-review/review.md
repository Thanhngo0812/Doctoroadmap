# R7 independent backend review — W-16

Verdict: **approve the backend milestone**, with no concrete blocker found at pinned HEAD `d1bf42b274c8015fcfdc09b861f5f9a7edfecadb`. Root owns the separate final PostgreSQL gate and acceptance/merge decision. This does **not** close whole W-16: the React usage page and fixed limit banners remain assigned to web after W-10.

## Scope and controls

Reviewed the three product/test changes against base `b3c4426666dd868040ea0bc52e6485f5af6e1ac4`: `learning_usage.py`, `build_store.py`, and `test_usage_w16.py`. Read AGENTS.md, code-review-and-quality skill, W-16 task, round-six assignment, web spec §8, Pha B2 §8 and existing W-14 behavior. Inspected unchanged API response models, owner/auth flow, typed ledger query, build confirmation/retry/reuse, and core DailySpendGuard context.

No product/Git edits, DB sessions, provider/ADC/SMTP/Cloudinary calls, paid work, external network calls, push, deletion, links, or worktree cleanup. All reviewer files stay in this scratch directory. Worker source hashes before and after are identical. Shared retained evidence output already dirty in the worker checkout was left untouched.

## Findings

No Required/Critical findings. The implementation fixes the observed overcounts with narrow changes and reuses the intended ledger port. No schema, core generation/cache/retry rules, public API shape, price or ceiling changes were introduced.

- Correctness: personal totals use assistant/document across courses for the authenticated actor; shared totals use lecture/quiz_gen/quiz_verify globally. Raw trace rows marked counted_in=build are excluded. Failed measured usage remains part of spend. Day filtering is lower-inclusive and upper-exclusive; exact lower and upper edges, midnight 17:00 UTC, year/month rollover, and leap day were checked.
- Build counts: the real quota SELECT remains count(*) over counts_quota, owner and original queued_at, now bounded to both month edges. A fixture with two counted attempts and synthetic spend 81.34 returns 2, not its dollar sum. Failed positive-cost counts; a reused zero-cost uncounted row and another actor's build do not count. Existing W-14 reuse/retry semantics remain unchanged. max=null/default/account override and remaining=0 were checked.
- Security/API: SQL predicates remain parameterized and scoped before reading rows. The real HTTP response model removes injected top-level and nested usd/cost fields; shared_content_today exposes only limited, monthly view only used/max/resets_at. Query learner_id cannot select another owner. Actual authorization uses unchanged get_actor; the worker native PG tests include guest/disabled/cross-owner assertions.
- Readability/architecture/performance: the diff is small, keeps quota ownership in the existing repository, uses the canonical usage_rows port and existing DTO, adds no dependencies or unnecessary abstraction, and avoids an unfiltered whole-ledger read. The port supplies the indexed owner/day or purpose/day predicates. Calendar upper filtering of ledger rows stays in the projection because the existing port takes since, not until.

## Independent execution

All Python tests ran through scripts/w05_run_tests.py with a fresh scratch basetemp. No PostgreSQL fixture was requested. The offline adapter executes the real production PostgreSQL query-builder predicates on isolated SQLite fixture rows, stripping only PostgreSQL bind-cast syntax and normalizing timestamp values to UTC for SQLite comparison. The production quota SQL executes directly against a separate in-memory table. The FastAPI route and Pydantic response model execute through ASGI TestClient with an actor override. The adapter is not claimed as an actual PG execution.

| Runnable assertion | Evidence |
|---|---|
| test_exact_day_bounds_and_reset ×3 | Exact start/reset edges, previous-day rejection via real repository predicate, 16:59→17:00 reset, leap/year/month transitions |
| test_actor_purpose_course_trace_and_failure_aggregation | Personal 0.5 vs other learner 0.8, two courses, global shared threshold, measured failed usage, trace/build/unrelated-purpose exclusions |
| test_real_quota_sql_counts_exact_month_not_dollars ×6 | Count 2 vs spend 81.34, both month edges, demo null/3/account override, reuse/other-actor exclusions |
| test_actual_http_response_model_removes_private_nested_keys | Real HTTP JSON, recursive money-key scan, monthly public fields, cache-control no-store |
| test_repository_rejects_naive_since | Timezone boundary guard |

Baseline and final restoration checks: **12 passed, 0 failures, 0 errors**. See baseline3.xml and final.xml; native output and exact commands are retained beside them. Two earlier scratch adapter failures are preserved (harness-attempt1 and baseline2); they are harness portability errors, not product RED evidence.

Seven mutants applied only to in-memory source copies were each rejected by the same runnable assertions:

| Mutant | Observed assertion failures |
|---|---:|
| Remove counted_in=build exclusion | 1 |
| Make day upper edge inclusive | 3 |
| Remove personal owner filter | 1 |
| Scope shared usage to current actor | 1 |
| Remove month upper bound | 6 |
| Remove month lower bound | 6 |
| Omit HTTP response_model | 1 |

Every mutation has native .log/.xml and command/exit JSON. All mutant XML files have zero error tags; failures are observable ratios, booleans, counts or leaked JSON keys, not assigned marker flags. Source before/after SHA checks establish that no worker file was changed.

## Supplied evidence and provenance

Verified **115/115** manifest file hashes and byte lengths with zero mismatches. Native full JUnit records **2731 tests, 0 errors/failures, 2 expected skip/xfail = 2729 passed**, including all 13 W-16 cases. React JUnit records **203 passed**; build native log and exit JSON show **exit 0**. The full gate's recorded source SHA values match current pinned files. There are no product/scripts/pyproject changes between tested code commit `7f98cf7` and final `d1bf42b`; the later commit adds report/evidence only.

The native RED run is baseline b3c4426: **7 assertion failures / 6 passes / 0 setup errors**. Its test SHA predates the documented extra assertion added after a surviving shared-owner mutant; final focused/full evidence records the strengthened test SHA. The initial setup error and first surviving mutation were retained and correctly distinguished in the report. usage-1 fixture metadata labels synthetic ledger data, 0 provider calls and no real-spend claim. Unknown historical W-15 cost is not relabeled as zero.

See summary.json, evidence-verification.json, source-before.json and source-after.json for machine-readable evidence.
