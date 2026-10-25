# W08 evidence

## Source and final gate

Final handoff source: `e6b336e6b31466a89b8a9893312f10f40d75cb8a`, main base `e5fa4924cc7e3d6eda924d6668c8c15b453cea91`, including reviewed SA65 page-image support (`4a4b957`). `final5-source-manifest.json` pins 1007 gate files. The final commands are `final5-python/react/build/browser-command.json`; results and precise audit scope are in `gate-results.json`, named assertions in `invariant-map.json`. `source-blob-manifest.json` reconciles actual gate files with committed Git blobs, allowing only checkout newline conversion. The subsequent handoff commit adds W08 evidence/documentation only.

Earlier final3 source `76a129ef1c495984796e6114ed6d5ba4e0f87c45` adds the real OpenAPI export: five W08 routes and typed schemas. The original equality and added-route mutation guards remain. The first full Python run caught this missing export (2372 pass, one snapshot failure, one live Cloudinary skip). The second full Python run was intentionally stopped with the obsolete export, native 4294967295, and is never counted as passed. Final3 passed 2373 Python tests. Source `d07c31ed0a9020f50d2bcd9e45e1b5cc7af29487` then corrects the DOCX no-page button label with its own RED/GREEN test; final4 passed 2373 Python and 158 React tests before receiving SA65.

`final2-source-manifest.json` pins the final source after test setup correction, main base `710d01352f70d7e0b70d3bf3065469cb3c5c4445`, and 1003 SHA-256 file hashes. The preceding source `f34111d0d01a6ab3d340bc857ed3ff22242c94ae` is separately recorded in `final-source-manifest.json`. Their only changed source path is `Learning.test.tsx`: it loads the real Markdown module before starting the scripted stream clock; no production code or assertion changed. SA64 was received through main merge `1d91b0b`; no core SA file is changed by W08.

- `final5-python.*`: whole-repository runner with mandatory PostgreSQL, basetemp under tmp. All earlier native exits and logs remain separate; no two full Python gates run concurrently.
- `final5-react.*`, `final5-build.*`: the complete React suite and production build. The earlier `final-react.*` caught a module-loading race in test setup; its RED result remains.
- `final5-browser.*`, `browser-final5/`: final browser against real HTTP/CSRF/accounts/Lecture3UseCase/PostgreSQL, fake text model/local media/FakeMailer. Commands record native exit and source commit. Runtime records no dirty source paths; earlier runs do not replace this final matrix.
- Full browser matrix: 390/768/1280 × light/dark × normal/reduced motion. Layout/touch checks run per capture; Axe scope is named per audit and is narrower than the screenshot matrix.
- Original Axe incomplete findings remain in JSON. Short KaTeX fractions receive an independent computed foreground/background contrast check (4.5:1), including a rejected same-color counterexample, then restored colors. Other incomplete findings must be resolved.
- `regression-exports/` contains generated HTTP/SQL test contracts, not browser screenshots. Raw copies retain byte hashes; basetemp and synthetic fixtures stay under tmp.
- `taste-direction/` records the dealt app style and seed. The inspector is run on a design-only snapshot from the actual authenticated DOM. Snapshot fonts are embedded to avoid file-origin CORS; this does not replace live browser checks.
- Historical screenshots/videos/design snapshots remain at their original local paths and are excluded from Git. `local-historical-assets.json` records their SHA-256 and sizes; their audit JSON, logs and native results remain published. Final5 screenshots/video are published. No historical file, worktree or snapshot is deleted.

## RED and counterexamples

`contract-red.*` reproduces absent lecture routes (2 failures, 2 negative controls pass); `contract-green.*` is the next implementation slice. `markdown-red.*` fails on the initial Markdown renderer; `markdown-green.*` passes with math, safe links, registered/unknown source labels and code preservation.

`mutation-source-match.json` proves all 13 deliberately wrong variants match the final source bytes: eight backend cases from `mutations3/results.json`, five UI cases refreshed in `mutations4/results.json` after the DOCX patch. Each has a failing assertion, native exit 1, no setup error and exact restoration. These ran sequentially before final servers/gates. Early mutation runs remain: one stopped at a CRLF replacement mismatch; another removed only half the cross-site check so Origin still protected the route. The final cross-site variant removes both checks. The first-delta timeout becomes an explicit assertion that text must arrive before model completion.

`browser-dev*` and `browser-smoke*` are historical look-and-fix runs, including setup and real accessibility failures. They do not substitute for browser-final5. `smoke4-independent-cleanup.json` records removal of that run's exact UUID after an assertion interrupted its original finally block. Later cleanup always removes its own DB before asserting server shutdown. Smoke5 passed 13 captures/5 scoped Axe audits, but covers only one configuration. `cleanup-check.json` independently checks all harness DB names and port 8018 after the final run.

`npm-audit.log` records a transitive old KaTeX advisory. The committed override deduplicates all consumers onto root KaTeX 0.19.0; `npm-audit-fixed.*` records the subsequent native audit. See [upstream advisory](https://github.com/advisories/GHSA-238p-pmpm-9mq7).

Published logs redact disposable session/CSRF values from failed test diagnostics; raw copies are retained locally under tmp before normalization. JUnit testcase identities, counts, failure states and native exits remain intact. Evidence SHA manifest is generated after normalization.

No live model, embedding, SMTP, or Cloudinary call is permitted. Provider charge: 0 USD. Lesson prose is scripted fixture content; source PDF imagery is locally rendered from manifest-verified copies. This handoff does not self-accept W08 or start W09.
