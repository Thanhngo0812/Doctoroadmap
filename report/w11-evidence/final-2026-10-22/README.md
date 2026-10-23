# W11 evidence — final integration, 2026-10-22

## Final acceptance run

- Source: `b9b5e6817390f8189813707095a04eeac16df95a`.
- Main base: `dee87ccde928100c7e6168a348040d77d197ebfb`.
- `acceptance-python.*`: whole repository through the PostgreSQL-aware runner, fresh basetemp under `tmp/`.
- `acceptance-react.*`, `acceptance-build.*`: all React tests and production build.
- `browser-final/`: real HTTP/PostgreSQL UI evidence; 36 PNG screenshots, owner/learner videos, HTTP and accessibility audit, SQL/runtime summary and taste inspector.
- `source-manifest.json`: tracked source/test SHA-256 at the tested commit.
- `migration-chain.json`: exactly one Alembic head, W11 after W14.
- `cleanup-check.json`: independent read-only PostgreSQL catalog and free-port check after all browser runs.
- `gate-results.json`: commands, native exits, counts and run provenance.
- `normalization.json`: available pre/post hashes for encoding/newline normalization and disposable test-token redaction. The partial earlier pass is explicitly disclosed; unavailable original byte hashes are not reconstructed. JUnit status/counts are preserved.
- `sha256-manifest.json`: final evidence file hashes (excluding that manifest itself).

## Counterexamples and history

- `mutations/`: eight serial deliberately wrong variants, each failing a named assertion; exact original source bytes restored before full gates and servers. This directory is test evidence, not UI imagery.
- `regions-red/green.*`: loading/denied-state accessible label regressions.
- `join-label-red/green.*`: invalid join heading regression.
- `browser-alignment-red2.*` and `browser-alignment-green/`: real-browser geometry counterexample and corrected layout.
- `migration-red.*`: intentional schema/setup RED; not a business-logic mutation.
- `full-*`, `final-*`, `main-*`, `handoff-*`, `release-*`, development and alignment captures: historical iterations, not substitutes for the acceptance run. In particular `browser-alignment-red` passed without the new assertion because its preparation command had failed; only `browser-alignment-red2` is the actual geometry RED.
- `regression-run*/`: preserved generated HTTP/SQL exports from older W06/W14/W25 tests. They include fake-data contracts and are not browser screenshots. Their original tracked paths were restored after hashing the copies.

All browser fixture data is isolated in UUID databases; all such runtime databases are independently verified absent afterwards. No live model, email or media provider is called. Tokens are redacted in captures/audits; no cookie, auth or CSRF response is recorded. Basetemp and synthetic image fixtures stay under `tmp/`.

The inspector's DOM/CSS snapshot is for design review only. Axe covers each of the six UI states in light/dark at 1280 (12 audits), not every screenshot. Three widths are checked for layout/touch targets; the HTTP/SQL assertions establish real service integration. UI-only mocks do not replace that evidence.
