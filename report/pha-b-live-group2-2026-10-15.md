# Phase B live acceptance — Group 2 — 2026-10-15

- Approved cap: $0.50; worst-case preflight reserve: $0.235802.
- Recorded usage ledger total: $0.025931; provider calls were recorded under `artifacts/phase_b/recordings/acceptance-group2/`.
- One failed document call has missing provider token metadata; its configured document-call upper bound is $0.006500.
- Pinned graph versions: doc-1 v37, nhap-mon-ml v37, naive-bayes v37, doc-6 v8, xstk-ch3-1 v46, doc-4 v12.

| Kind | Document | Concept | Status | Cost USD | Grounded citations |
|---|---|---|---|---:|---:|
| lecture | doc-1 | Tập hợp | fallback | 0.001527 | 4 |
| lecture | doc-1 | Phần tử | fallback | 0.001876 | 4 |
| assistant | doc-1 | Tập hợp | answered | 0.000699 | 1 |
| document | doc-1 | Tập hợp | failed | 0.001558 | 0 |
| lecture | nhap-mon-ml | Dữ liệu | fallback | 0.001319 | 4 |
| lecture | nhap-mon-ml | Mô hình sinh | fallback | 0.001179 | 4 |
| assistant | nhap-mon-ml | Dữ liệu | answered | 0.000566 | 1 |
| document | nhap-mon-ml | Dữ liệu | failed | 0.001935 | 0 |
| lecture | naive-bayes | Supervised learning | fallback | 0.000828 | 2 |
| lecture | naive-bayes | Real time Prediction | fallback | 0.001033 | 4 |
| assistant | naive-bayes | Supervised learning | insufficient_context | 0.000413 | 0 |
| document | naive-bayes | Supervised learning | failed | 0.001279 | 0 |
| lecture | doc-6 | CSDL | fallback | 0.000846 | 4 |
| lecture | doc-6 | Mô hình dữ liệu quan hệ | fallback | 0.001038 | 4 |
| assistant | doc-6 | CSDL | insufficient_context | 0.000341 | 0 |
| document | doc-6 | CSDL | failed | 0.001053 | 0 |
| lecture | xstk-ch3-1 | Tổng thể | fallback | 0.001283 | 4 |
| lecture | xstk-ch3-1 | Tỉ lệ tổng thể | fallback | 0.001929 | 4 |
| assistant | xstk-ch3-1 | Tổng thể | answered | 0.000552 | 1 |
| document | xstk-ch3-1 | Tổng thể | failed | 0.001337 | 0 |
| lecture | doc-4 | Hình thái ý thức xã hội | fallback | 0.001276 | 4 |
| lecture | doc-4 | Nguồn gốc nhận thức của triết học | fallback | 0.001289 | 4 |
| assistant | doc-4 | Hình thái ý thức xã hội | answered | 0.000772 | 3 |
| document | doc-4 | Hình thái ý thức xã hội | failed | 0.000006 | 0 |

## Replay checks


The full outputs, usage rows, preflight reservation, and replay status checks are in `tmp/phaseb-live-group2.json`.
