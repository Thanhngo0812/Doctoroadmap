# Group 3 V2 live quiz run — 2026-10-15

The six approved pinned graphs completed live generation at Gemini 3.1 Flash-Lite with 1200-token generation and 400-token verifier caps. This report was reconstructed from the V2 plan, the append-only usage ledger, and saved recordings after the runner stopped during replay setup; it made no provider calls.

Live usage: **$0.104364** across 34 calls (34 generator, 0 verifier). V1 had already spent $0.175942, so V1+V2 measured spend is **$0.280306**; adding the reported unsettled reserve of $0.003240 gives $0.283546 against the $0.50 Group 3 cap, within the approved $1.50 aggregate ceiling. No holdout documents were read.

| Document | Graph | Module | Concepts | Ready items | Preflight USD | Measured USD | Gen/verify calls | Generators |
|---|---:|---|---:|---:|---:|---:|---:|---|
| doc-1 | v37 | module_001 | 2 | 2 | $0.016898 | $0.010783 | 4/0 | cloze |
| nhap-mon-ml | v37 | module_001 | 2 | 2 | $0.015016 | $0.008476 | 4/0 | cloze |
| naive-bayes | v37 | module_001 | 2 | 0 | $0.015007 | $0.007723 | 4/0 | none |
| doc-6 | v8 | module_001 | 2 | 0 | $0.014667 | $0.006725 | 4/0 | none |
| xstk-ch3-1 | v46 | module_001 | 2 | 2 | $0.017459 | $0.011685 | 4/0 | cloze |
| doc-4 | v12 | module_001 | 7 | 3 | $0.070623 | $0.058972 | 14/0 | cloze |

Preflight estimates summed to $0.149670. The run returned 9 items from 17 concepts. `naive-bayes` and `doc-6` ended with zero ready items after their model candidates failed local guards and the independent cloze fallback found no eligible question. The JSON plan retains per-document submissions, history checks, timings, and transport errors.

Replay did not run: only `quiz_gen.json` was recorded. No bank passed local validation far enough to invoke the verifier, so `quiz_verify.json` was absent. Replay provider spend is $0. V2 left the recorded store and fixtures intact for review.

Plan: [`tmp/phaseb-live-group3-v2.json`](../tmp/phaseb-live-group3-v2.json). Store: `artifacts\phase_b\acceptance-group3-v2.json`. Recordings: `artifacts\phase_b\recordings\acceptance-group3-v2`.
