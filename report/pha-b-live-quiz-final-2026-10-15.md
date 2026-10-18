# Phase B quiz live acceptance — Group 3 — 2026-10-15

This report consolidates the saved Group 3 live runs and their replay checks. Scope was six pinned A10 graph versions: `doc-1` v37, `nhap-mon-ml` v37, `naive-bayes` v37, `doc-6` v8, `xstk-ch3-1` v46, and `doc-4` v12. The V2 pass covered two first-module concepts per document and all seven concepts in `doc-4`; no evaluation holdouts 19–23 were read.

Measured Group 3 provider usage across V1–V4 was **$0.290979**. Including the saved unsettled reserve of **$0.0032421**, the upper bound is **$0.2942211**, within the approved **$0.50 Group 3 cap**. The V4 replay made zero provider calls.

| Run | Scope and spend | Outcome |
|---|---:|---|
| V1 | First five pinned documents; $0.175942 | Generated answers used chunk IDs where short source labels were required, so local validation rejected model banks and used cloze fallback. No verifier calls occurred. An XSTK generation response also failed JSON decoding; its usage remained in the ledger. |
| V2 | All six documents; two first-module concepts each and all seven `doc-4` concepts; $0.104364 | 34 generation calls and no verifier calls. Candidates still failed before blind verification because the prompt did not fully state source-label matching and option-overlap rules. Nine items were ready from 17 concepts, all via cloze. Replay could not start because no verifier recording existed. |
| V3 | One `doc-1` concept; $0.00715875 | Generation produced candidates and the verifier returned a valid correct choice, but marked both distractors “source does not say.” The guard correctly rejected that bank; the public quiz used a cloze fallback. Recorded replay cost $0. |
| V4 | Same one-concept contract smoke; $0.00351425 | The generated item passed blind verification and was returned with `generator: llm`. Replay returned the same item from recordings with zero provider calls. |

The V1/V2 failures led to explicit generation rules for short context labels, matching `from` and `sources`, source-backed `moi` options, same-chunk and alias-overlap filtering, nonoverlapping options, and the existing answer-length guard. V3 exposed a separate verifier-routing gap: its prompt did not clearly explain that `distractor_sources` contains definitions for distractor concepts. V4 used the updated instruction to compare target chunks with the matching candidate anchor, while retaining rejection when the evidence is inconclusive.

V4 used two Gemini calls: one generator call costing $0.002821 and one verifier call costing $0.00069325. It returned one answer-free public item, passed verification, and replayed successfully for $0.00. V4 dry-run estimated $0.008757 for the concept, above measured usage. No model calls were made while preparing this report.

Saved run plans: [V1](../tmp/phaseb-live-group3.json), [V2](../tmp/phaseb-live-group3-v2.json), [V3](../tmp/phaseb-live-quiz-contract-v3.json), and [V4](../tmp/phaseb-live-quiz-contract-v4.json). V1/V2 recordings and stores remain under `artifacts/phase_b/`; V4's result, cost breakdown, events, and replay status are in its plan.
