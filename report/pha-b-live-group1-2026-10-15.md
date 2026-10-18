# Phase B live acceptance: Group 1

Run date: 2026-10-15. Scope was the six approved development documents only; no held-out documents were accessed. Naming used `gemini-3.1-flash-lite`; concept indexing used `gemini-embedding-001:768` over Vertex.

The cumulative group usage ledger is **$0.3096655** against the approved **$0.50** group cap. The v3 pass took **632,247 ms** (10m 32s) and recorded 159 `module_title` sessions, one per module. The cumulative ledger includes 376 `module_title` usage rows ($0.2917630) across the group's attempts, plus six `embedding` rows ($0.0179025).

| Document | Source graph | Named graph | Modules | LLM title + description | Fallback | Concepts | Index reused | Elapsed |
|---|---:|---:|---:|---:|---:|---:|:---:|---:|
| doc-6 | v8 | v17 | 4 | 4 | 0 | 28 | yes | 14.7s |
| doc-1 | v37 | v45 | 39 | 39 | 0 | 218 | yes | 116.8s |
| nhap-mon-ml | v37 | v46 | 15 | 14 | 1 | 75 | yes | 45.3s |
| naive-bayes | v37 | v45 | 5 | 5 | 0 | 33 | yes | 17.8s |
| xstk-ch3-1 | v46 | v48 | 9 | 9 | 0 | 72 | yes | 44.6s |
| doc-4 | v12 | v14 | 87 | 81 | 6 | 489 | yes | 377.4s |
| **Total** | — | — | **159** | **152** | **7** | **915** | — | **632.2s** |

All 159 module title/description outputs were inspected from their named graph artifacts. No descriptions were empty or contained technical `node_…`/`module_…` IDs. Seven modules used deterministic fallback after validation: three duplicate-title validations, three vocabulary validations, and one title-form validation. There were no `model_error` fallbacks. A whole-document duplicate remains in nhap-mon-ml: “Vài vấn đề cần biết khi dùng học máy” is assigned to module_009 and module_013; the local collision check only addresses nearby modules.

Every naming result reports `second_run_calls_estimate=0`; all six concept-index results report reuse in v3. The group ledger records one embedding operation per document for the 915 concepts; v3 reused those vectors rather than embedding them again.

The named artifacts preserve all module IDs, node assignments, section assignments, ordering/index fields, and all non-module payload fields. The only change outside title/description/source/validation fields was `section_code`: naming fills it from section metadata where available and serializes it as an empty string where unavailable. Section IDs and node membership remain identical.

| Document | Naming cost | Embedding cost |
|---|---:|---:|
| doc-6 | $0.0087210 | $0.0003785 |
| doc-1 | $0.0815998 | $0.0032213 |
| nhap-mon-ml | $0.0304720 | $0.0012508 |
| naive-bayes | $0.0083415 | $0.0007768 |
| xstk-ch3-1 | $0.0172503 | $0.0014358 |
| doc-4 | $0.1453785 | $0.0108395 |

Reproduction artifacts:

- Result JSON: `tmp/phaseb-live-group1-v3.json`
- Recorded model responses: `artifacts/phase_b/recordings/acceptance-group1-v3/module_title.json`
- Cumulative group ledger: `artifacts/phase_b/acceptance-group1.json`
- Named graph artifacts: the versions listed above under `artifacts/graph/<doc_id>/vN`

Final offline correction: doc-4 v15 supersedes v14 for the preview. The v14 fallback for module_062 was an 87-character author heading. The fallback policy now selects a complete concept name within the 60-character limit: “Trình độ lực lượng sản xuất” (27 characters). Its regression test failed before the change and passes after it. Algorithm ID is `phase-b-module-names-v3`; provider prompts and response cache keys are unchanged. A cache-only refresh from pinned v12 estimated zero calls and used a network-blocking stub with zero calls. All 81 accepted LLM outputs, the six fallback flags, and all non-presentation graph fields remain unchanged. There is no added spend.

The `second_run_calls_estimate=0` measurements above used the same pinned A10 input and cache. The final runtime also follows a previously named graph back to its A10 input for a default repeat command; selecting an explicit graph version instead uses that version's actual neighbor-title context.
