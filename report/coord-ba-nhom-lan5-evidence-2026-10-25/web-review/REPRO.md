# W09 reviewer counterexamples

Pin: `da4d6399965f5a67accaacc6ea34af8ce56f0dd5`; base `46d829a55a62d852897f07102e89cf9a1fd5185e`. No worker file was modified. Both helpers use fake data only; neither starts PostgreSQL, a browser server, a real provider, or ADC.

## R-W09-1 — question disappears after final while usage refresh is pending

From the repository root:

```powershell
node tmp/w09-assistant/src/web/frontend/node_modules/vitest/vitest.mjs run --config tmp/coord-r5-web-review-20261025/vitest.review.config.mjs --pool=threads --maxWorkers=1 --reporter=junit --outputFile=C:/Users/ngoco/Desktop/Doctoroadmap/tmp/coord-r5-web-review-20261025/final-usage-race-rerun.xml
```

The helper renders the actual AssistantDock/AuthProvider/Markdown from the pinned worker. Fake fetch completes the first SSE with final and EOF, then holds the second `/me/usage` request indefinitely. The composer is enabled; typing and submitting a second question empties the draft, but there is still only one POST `/turns`. `final-usage-race-red2.xml` records one assertion failure and the independent POST/draft observation. `repro-native.json` records native exit 1. The first `final-usage-race.xml` was a scratch module-resolution setup failure and is not counted as regression proof.

Root cause: `Assistant.tsx:67` clears the draft before calling send. `useAssistant.ts:98` clears the live turn at final, enabling the composer. `:73` silently rejects the new run because active.current is retained until `:110`, after the usage request at `:102`.

For integration as a temporary focused test within another worktree's frontend source, change its three relative production imports to `./Auth`, `./Assistant`, `./LectureMarkdown`; the rest is self-contained. No test timeout or application mock is needed.

## R-W09-2 — ordinary tool get_lecture inherits the focus-only cache restriction

```powershell
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe -B -X utf8 tmp/coord-r5-web-review-20261025/repro_ordinary_lecture.py
```

This runs actual WebLearningRuntime and AssistantUseCase against `_sample_graph`, InMemoryPhaseBStore, FakeClock and ScriptedModel. The model explicitly calls `get_lecture` on an uncached concept without a focus. Actual runtime returns not_cached and empty body with zero lecture calls. Replacing only the callback in the in-memory control with the canonical cache_only/allow_spend forwarding produces ready and one scripted lecture call. The final assertion intentionally fails on the pinned worker.

Source requirement: task/web/W-09-tro-ly-va-phien.md:27–29 explicitly requires forwarding cache_only as in composition_phase_b.py and covering ordinary tool calls as well as focus hit/miss. doc/tro-ly-3-spec.md:43 and :186 prohibit generation for the focus prefetch. The ordinary tool path is assistant.py:302 and canonical composition_phase_b.py:230–231; it does not pass cache_only=True. The current web callback at learning_runtime.py:54–57 forces True for every invocation and also drops allow_spend. Fixing this callback must keep focus cache misses at zero generation while allowing a normal explicitly requested tool call to use the existing guarded generation path.
