# W11 auth return evidence — 2026-10-23

## Final source and gates

- Approved source: `2c5166bfcf30ee8cd1a784f8da6891278b260522`, main base `865974ae14e03bdc5e37283aa496972f8c3c622d`, explicitly frozen by the project owner for this patch.
- Final browser and extra gates: `33f9c2521ba0379d89c3fe942ea754f9f06b49a6`. Documentation-only main `1d193735a9ba1bde3c7316d5372fcd0be0e0f12a` had already been received before the asynchronous freeze reply. Only the received Pha B plan differs; all 639 runtime/test/script hashes are identical. No further main receipt follows that decision. See `baseline-approval.json`.
- `final-python.*`: whole repository through the PostgreSQL-aware runner, fresh basetemp under `tmp/`.
- `final-react.*`, `final-build.*`: all React tests and production build.
- `latest-python.*`, `latest-react.*`, `latest-build.*`: extra gates after that documentation receipt; command metadata records the exact source commit.
- `browser-final/`: real HTTP/PostgreSQL captures, 48 screenshots, 16 Axe audits, eight authentication return cases, SQL/runtime results and owner/learner/auth-return videos.
- `source-manifest.json`, `latest-source-manifest.json`: identical source hashes at both tested commits; verified before and after gates.
- `gate-results.json`: source/commands/native exits/counts, proof scope and provider cost.
- `migration-chain.json`: exactly one Alembic head, W11 after W14.
- `cleanup-check.json`: independent check of browser UUID databases and harness port.
- `normalization.json`: durable pre/post hashes and local raw backup hashes for text encoding/newline normalization and disposable test-token redaction. JUnit case states and native exits are preserved.
- `sha256-manifest.json`: all final evidence hashes, excluding itself.

## Counterexamples

- `repro-import.json`: only the reviewer test file was imported from `3f3e923`; its branch was not merged. Four unsupported ByRoleOptions.exact properties were removed for TypeScript compatibility, without changing the name matching or assertions.
- `auth-return-red.*`: the original eight form-switch cases fail while two direct-auth controls pass.
- `auth-return-green.*`: eight switch cases, two controls and twelve unsafe-next cases pass.
- `unsafe-next-final-mutation.*`: removing sanitization makes the twelve unsafe-next cases fail. The exact source bytes are restored before servers/full gates. Other cases are not selected in this mutation run; no skip marker was added.
- `mutations/`: the original eight backend counterexamples still fail on deliberately wrong source, with zero setup errors and exact source restoration.
- `build-dev.log`: TypeScript correctly rejects unsupported options in the imported reviewer test.
- `browser-dev/`, `browser-dev2/`: Axe requires manual contrast review for a visible Unicode theme glyph, including when wrapped in aria-hidden. `browser-dev3/` passes after reusing the approved CourseShell SVG. These are historical development runs, not the final gate.
- `browser-base-check.json`: an earlier scheduled browser command stopped before starting the server because main had advanced. This is a provenance check, not a product failure or a completed browser run. The final run is recorded separately in `final-browser-command.json`.

## Proof boundaries

The browser uses real Auth/CSRF/SharingService/PostgreSQL and fake mail, with no model/media calls. It is not an intercepted HTTP mock. Each of eight cases switches forms through the chosen header/footer link, authenticates, returns to the exact invitation, joins the course, verifies access, then leaves. Native transition calls are counted by a delegating wrapper, not replaced by fake transitions. Reduced motion uses browser media settings and is observed through matchMedia.

Axe covers eight states in light/dark at 1280, not all 48 screenshots. Layout/touch checks cover 390/768/1280. Separate SQL reads verify eight distinct accounts consumed eight invitation uses and left no membership behind. Original one-time URL, invalid-link, membership and private-progress flows remain in the same browser run.

`regression-exports/` contains generated W06/W14/W15/W25 unit/integration HTTP/SQL contracts, not UI screenshots. Those copies preserve original bytes and hashes. Basetemp and synthetic images stay under `tmp/`. Raw normalization backups remain local under `tmp/` and are not staged, because deliberately wrong variants may print disposable bearer tokens. Published evidence redacts them.

No live model, mail or Cloudinary request is permitted. Provider cost for this patch is 0 USD. This handoff does not accept or merge W11, W15, or any core SA ticket.
