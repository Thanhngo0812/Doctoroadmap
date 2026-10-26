> Historical required2 run: Python/React/build passed, browser failed in the SSE body collector. Final handoff evidence is ../required3-2026-10-24/. This run is not counted as a complete passing gate.

# Correction review

Source `f2e1e98414e7c6cd5b5ebb8bc2718f618ba448d1`. This is the web author's review, not coordinator acceptance.

Correctness: related lesson labels now derive from the same current progress nodes as checkboxes and counts. Deferred response tests cover optimistic state, successful save and rollback without fetching/regenerating the open lesson. The streaming heading expression matches core's existing grammar; final uses the authoritative body/self_check, preserving text if splitting was impossible. Core SA70 is received through main and tested separately at the HTTP delta boundary.

Simplicity and architecture: the production change stays in Learning.tsx. Passing current progress to the lesson avoids another store, cache, refetch or use case. No migration, gateway, authorization, Markdown renderer or media delivery behavior is rewritten. Coordinator cases keep identical test bodies; a static real-module preload removes cold hook I/O without changing assertions/timeouts.

Security: existing membership, actor, course/version and media/source guard coverage remains. The wire assertion is independent from DOM hiding: SA70 HTTP deltas must exclude self-check content while final still supplies the folded answer. Fake providers and isolated UUID PostgreSQL are mandatory; no paid rerun or live mail/media operation occurs.

Performance: progress saves update existing React state only. Both fake-model call count and lecture HTTP count are independently checked to remain unchanged. A successful unmark and a failed SQL unmark cannot cause background regeneration.

Interface: the accepted layout/tokens/fonts/logo remain. The W24 HTML preview is used as reference for folded answers and related lessons, not copied over React. Browser checks retain keyboard/focus, 44px targets, three widths, both themes and real reduced motion. Extra correction screenshots are not represented as extra Axe audits.

Limits: scripted prose establishes behavior, not live-model quality. The existing answer-2 replay xfail and explicit Cloudinary live skip belong to main; no test is skipped or weakened by this patch. W09 remains a separate next ticket after coordinator acceptance/merge of W08.
