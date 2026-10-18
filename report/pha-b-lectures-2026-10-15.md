# Phase B lecture and document offline audit — 2026-10-15

## Scope and method

Ran the lecture use case against every learnable concept in the six development graph artifacts using `LectureUseCase(None, InMemoryPhaseBStore())`. This intentionally exercises deterministic fallback and no-source paths without external paid model, embedding, or network calls. Independently checked each citation's absolute offsets against the corresponding raw chunk segment, including exact quote equality. Also created and exported one document on each of two real graphs with the local deterministic `DemoModel` and an in-memory store.

The machine-readable result and 10 lecture plus 2 document examples are under [`tmp/phase-b-lectures`](../tmp/phase-b-lectures/sweep.json).

## Results

| Document | Graph / chunks / parse | Concepts | Result status | `thieu_cong_thuc` | Citation segments checked | p50 / p90 (ms) |
|---|---:|---:|---|---:|---:|---:|
| doc-1 | 37 / 5 / 5 | 218 | 218 fallback | 0 | 1,306 | 35 / 80 |
| nhap-mon-ml | 37 / 2 / 2 | 75 | 73 fallback, 2 no_source | 0 | 416 | 23 / 41 |
| naive-bayes | 37 / 1 / 1 | 33 | 33 fallback | 0 | 169 | 5 / 39 |
| doc-6 | 8 / 2 / 2 | 28 | 27 fallback, 1 no_source | 0 | 118 | 4 / 12 |
| xstk-ch3-1 | 46 / 5 / 2 | 72 | 72 fallback | 0 | 485 | 20.5 / 37 |
| doc-4 | 12 / 6 / 2 | 489 | 489 fallback | 0 | 3,193 | 37 / 69 |
| **Total** | — | **915** | **912 fallback, 3 no_source** | **0** | **5,687** | — |

All 912 fallback rows report `model_unavailable`; the three no-source rows report `khong_co_doan_day` and include mention-only sources. The fallback result now retains `thieu_cong_thuc` when the assembled formula evidence is missing; none of these 915 lecture outputs required that flag. All 5,687 returned citation segments were within their source chunk bounds and matched their quoted text exactly.

The two offline document examples, for doc-1 graph 37 and doc-4 graph 12, both returned `ready`, exported Markdown, cited one source, and reported $0.00. The full examples are in `tmp/phase-b-lectures/samples/document-*.json`.

## Limits

This audit establishes fallback citation grounding and local document wiring. It does not establish provider-generated lecture quality because no provider calls were made. The measured p50/p90 are local use-case timings and exclude provider latency.
