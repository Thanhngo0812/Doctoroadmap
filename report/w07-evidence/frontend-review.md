# W07 frontend review

Scope: `Roadmap.tsx`, `courses-api.ts`, App route integration, and `Roadmap.test.tsx`. Read-only review; no tests were run.

## Findings

No blocking findings in the reviewed W07 frontend scope.

## Reviewed behavior

- The request carries course and node IDs only; actor identity remains session-cookie based. `apiFetch` includes credentials and adds the CSRF header for the PUT.
- Optimistic node changes are isolated per node. A node has at most one active write; successful concurrent writes merge only their own node from the returned full snapshot, and failures restore that node. Tests cover out-of-order responses, failed writes, and a successful response missing the requested node.
- The new test `clears an expired session after a progress write returns 401` checks that an unauthenticated response redirects to login. The initial GET path also clears the session on the same error code.
- Unknown/missing module routes render a not-found message. A 404 from progress PUT is surfaced inline and the optimistic checkbox is rolled back through the common error path.
- Both authenticated course routes are wrapped in `RequireAccount`; module IDs are URL-encoded in navigation and API requests.
- Course-to-course navigation clears `data`, unmounting `RoadmapModules`; the new roadmap mounts with its first module selected.

## Verdict

Approve the reviewed W07 frontend scope. The frontend implementation and available tests show no blocker.
