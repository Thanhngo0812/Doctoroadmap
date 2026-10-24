> Historical required2 run: Python/React/build passed, browser failed in the SSE body collector. Final handoff evidence is ../required3-2026-10-24/. This run is not counted as a complete passing gate.

# W08 Required corrections after SA70

Final tested source: `f2e1e98414e7c6cd5b5ebb8bc2718f618ba448d1`, main base `5936a5d91b6c3979f1918b33ce330403414b776f`. The web patch receives reviewed SA70 (`5188908`); it does not edit core code. The handoff commit following this source adds evidence/documentation only.

- `source-manifest.json` hashes actual source files used by the gate. `source-blob-manifest.json` reconciles their Git blobs, allowing checkout newlines only.
- `python/react/build/browser-command.json` records argv, source, main base, native exit and timestamps. The browser run is `../browser-required2-20261024/`, with real PostgreSQL, HTTP/SSE and Lecture3UseCase; model/media/mailer are fake. Provider calls remain forbidden.
- `gate-results.json` contains actual counts and scoped audit results. `invariant-map.json` names runnable assertions and independent observations. `cleanup-check.json` independently checks known harness UUIDs and port 8018 after the run.
- `review-test-preservation.json` verifies every coordinator test body is unchanged. The only later setup change is a static import of the actual Markdown renderer, replacing a timed async preload hook; no assertion or timeout is removed or weakened.
- `mutation-source-match.json` matches eight unchanged backend guard sources from the accepted W08 evidence and seven UI mutants refreshed after SA70/static preload. Mutants run sequentially, before all full gates and browser servers; exact bytes are restored.
- `../required-2026-10-24/` retains the first correction run, including RED6/GREEN17, the earlier full Python failure against prompt/spec mismatch, and the cold async-import hook timeout. These are not counted as final passing gates.
- The first correction's browser images/videos/snapshots remain locally at their original paths. `historical-browser-assets.json` records hashes and sizes; its JSON audit/log/native outputs are published. Final browser captures are published. Nothing is deleted or cleaned.
- `normalization.json` records raw local backups and per-file before/after hashes. Only the newly added Required evidence is normalized; the old W08 handoff is unchanged. JSON semantics, JUnit case identities/states/counts and native exits are preserved; disposable bearer diagnostics may be redacted. Raw generated regression contracts retain their bytes.

The full matrix checks 390/768/1280, light/dark and real reduced-motion preference. Axe scope is 17 audits at 1280 (module, ready, source, failure across themes/motion and one rollback), rather than every screenshot. Short KaTeX-glyph incomplete findings remain with independent computed contrast and a rejected same-colour counterexample.

R-W08-1 independently reads PostgreSQL after saving B, a deliberately failed unmark/rollback, and a successful unmark while A remains open; no extra lecture request/generation occurs. R-W08-2 inspects raw HTTP delta frames after SA70, in addition to React visibility and folded final answers. The React tests inject full raw deltas independently, so server filtering cannot make the web regression guards vacuous. A final with null self-check retains its complete body.

Pending independent coordinator review. No main merge/push and no W09 implementation before W08 acceptance.
