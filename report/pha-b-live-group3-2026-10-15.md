# Group 3: six pinned-module quiz smoke runs — 2026-10-15

Authorized live acceptance run using Gemini 3.1 Flash-Lite, generation cap 1200 and verifier cap 400. Before each document, its current dry-run estimate plus the usage ledger was checked against the $0.50 group cap; every model call also used a concurrent reservation guard. The 19–23 evaluation holdouts were not read.

Status: **stopped**; measured live ledger **$0.175942**; replay spend **$0.00**; group limit **$0.50**.

| Document | Graph | Module | Preflight upper estimate | Actual USD | Items | Model calls (gen/verify) | Result | Submission | ms |
|---|---:|---|---:|---:|---:|---:|---|---|---:|
| doc-1 | v37 | module_001 | $0.064161 | $0.043611 | 8/8 | 16/0 | ready | {'correct_count': 1, 'question_count': 8} | 13278 |
| nhap-mon-ml | v37 | module_001 | $0.051586 | $0.032608 | 1/7 | 14/0 | ready | None | 8358 |
| naive-bayes | v37 | module_001 | $0.050011 | $0.029543 | 0/7 | 14/0 | failed | None | 9464 |
| doc-6 | v8 | module_001 | $0.049887 | $0.028622 | 0/7 | 14/0 | failed | None | 8120 |
| xstk-ch3-1 | v46 | module_001 | $0.067461 | $0.041558 | 7/8 | 15/0 | ready | {'correct_count': 1, 'question_count': 7} | 7839 |

Every returned quiz and `item_ready` event was checked for answer/explanation fields. For quizzes with at least two items, the saved private answer key selected one correct and one incorrect response; the public submission and same-owner history were checked. The replay phase used fresh in-memory storage and the captured `quiz_gen.json` / `quiz_verify.json` sessions, with zero provider spend.

Replay completed for 0/5 documents; any incomplete replay, budget block, or transport failure is recorded in the JSON plan. Recordings: `artifacts\phase_b\recordings\acceptance-group3`. Store: `artifacts\phase_b\acceptance-group3.json`. Detailed per-doc estimates, measured usage, budget events, and replay status: [`tmp/phaseb-live-group3.json`](../tmp/phaseb-live-group3.json).
