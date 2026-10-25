# W08 implementation review

Review source: `e6b336e6b31466a89b8a9893312f10f40d75cb8a`, main base `e5fa4924cc7e3d6eda924d6668c8c15b453cea91`, including the reviewed SA65 merge. The final handoff commit adds only W08 evidence/report files. This is the web author's review, not independent coordinator acceptance. See `gate-results.json`, `invariant-map.json` and `mutation-source-match.json` for executable evidence.

## Correctness and scope

The patch uses reviewed Lecture3UseCase from main, never the old lecture-2 use case. GET reads cache without spending; SSE may generate under the current actor/course/document/version. A worker thread continues after disconnect; HTTP integration observes the first delta before releasing the fake model, explicitly observes disconnect, and reads completed shared cache through an independent PostgreSQL connection.

There is one Alembic head and no new table/migration. Existing W14 upload context DTOs and W11 sharing service are unchanged. The self-check answer is collapsed; streaming text after its heading is held until final parsing. If the core cannot split a self-check, the contract keeps the original body and self_check null; the web does not invent a question.

## Security

Membership is checked before graph work and before SSE headers. Published learnable nodes are required; actor/doc/version from a query cannot override server context. Source and media guard precedes MediaStore access, including immediately after member removal. Asset lookup is pinned to published graph references, not arbitrary DB keys or request paths.

The web projection selects learner fields and attaches current learner states; typed HTTP/SSE DTOs provide a second structural allowlist. Cache/admin validation is tested through a separately read cache row and is absent from JSON/SSE. Models and Markdown are untrusted: no raw HTML plugin, no external Markdown image loading, default safe URL transform, KaTeX trust false and bounded expansion/size. Registered source labels are explicit actions; unknown labels remain text and code/math nodes are not rewritten.

CSP permits inline style attributes for KaTeX's generated layout while retaining restrictions on scripts, stylesheet elements, image origin, frames and objects. SPA navigation makes document-level per-route permission unsuitable; the Markdown renderer cannot introduce raw style/HTML. A native npm audit found old transitive KaTeX copies; the override now uses the same patched root version for all consumers.

## Interface and accessibility

CourseShell and accepted main tokens/fonts/logo remain. Desktop uses the module list and a reading column capped at 680px; mobile moves between list and lesson, retaining a back link. Progress state is optimistic with rollback and actionable error. The source viewer traps modal focus natively, supports Escape, restores the citation even if Markdown replaced it, separates requested page from loaded-image page, and exposes its scroll region to keyboard.

Real-browser findings were repaired before source freeze: lost citation focus, non-focusable source scroll, long progress error wrapping and sticky sidebar positioning. KaTeX short-glyph contrast incompletes are measured independently and retained with scope; no Axe rule is disabled. Source page images are real fixture PDF renders through fake media, not synthetic screenshot fixtures.

The last DOCX regression has a named RED/GREEN test: even if a core failure suggests a page number, a DOCX source displays the disabled no-page label and retains the original-file action. Receiving SA65 changes no W08 mutation source bytes; all thirteen counterexample guards remain matched to the final source. Final5 reruns Python/PostgreSQL, React/build and the browser after that main merge, rather than reusing earlier gate results.

## Limits

W09 assistant is not implemented or mocked as a functioning tutor; its W08 action gives a clear unavailable notice. W19 content reports and W10 quiz are outside this patch. Fake model prose proves behavior and integration, not provider output quality. The coordinator decides acceptance after final evidence review; no main merge/push is performed by the web worker.
