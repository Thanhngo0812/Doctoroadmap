# Correction review

Source `b4136987668c3fb822ea374f399b947064ce7f18`. This is the web author's review, not coordinator acceptance.

Correctness: related lesson labels now derive from the same current progress nodes as checkboxes and counts. Deferred response tests cover optimistic state, successful save and rollback without fetching/regenerating the open lesson. The streaming heading expression matches core's existing grammar; final uses the authoritative body/self_check, preserving text if splitting was impossible. Core SA70 is received through main and tested separately at the HTTP delta boundary.

Simplicity and architecture: the production change stays in Learning.tsx. Passing current progress to the lesson avoids another store, cache, refetch or use case. No migration, gateway, authorization, Markdown renderer or media delivery behavior is rewritten. Coordinator cases keep identical test bodies; a static real-module preload removes cold hook I/O without changing assertions/timeouts.

Security: existing membership, actor, course/version and media/source guard coverage remains. The wire assertion is independent from DOM hiding: SA70 HTTP deltas must exclude self-check content while final still supplies the folded answer. Fake providers and isolated UUID PostgreSQL are mandatory; no paid rerun or live mail/media operation occurs.

Performance: progress saves update existing React state only. Both fake-model call count and lecture HTTP count are independently checked to remain unchanged. A successful unmark and a failed SQL unmark cannot cause background regeneration.

Interface: the accepted layout/tokens/fonts/logo remain. The W24 HTML preview is used as reference for folded answers and related lessons, not copied over React. Browser checks retain keyboard/focus, 44px targets, three widths, both themes and real reduced motion. Extra correction screenshots are not represented as extra Axe audits.

Limits: scripted prose establishes behavior, not live-model quality. The existing answer-2 replay xfail and explicit Cloudinary live skip belong to main; no test is skipped or weakened by this patch. W09 remains a separate next ticket after coordinator acceptance/merge of W08.

The preceding required2 run passed Python/React/build but stopped when DevTools could not retrieve an SSE body. The corrected collector tees the actual browser fetch response with Response.clone().text(), returning the original response without changing its request, status, headers or body, or adding artificial delays. Five actual wire traces are published under audit.sseWire. The exact parsing/equality guard also rejects a synthetic unsafe SSE fixture; that counterexample is explicitly distinct from real HTTP evidence. A one-configuration smoke passed before the final full matrix.

The response tee is test instrumentation and consumes a second stream branch. Disconnect completion is therefore established by the separate direct HTTP/PostgreSQL regression test, not inferred from the instrumented browser collector.
