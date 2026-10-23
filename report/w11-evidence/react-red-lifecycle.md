# W-11 lifecycle regressions

Focused Vitest regressions were run against the previous behavior and failed as expected:

- `clears a one-time URL when the open dialog switches to a different course`: the previous course's one-time URL remained visible.
- `ignores a join response after the invite token changes`: the late response navigated away from the newly selected invite.
- `does not apply a deferred member removal to the next course`: the old removal changed the next course's member count/list.
- `shows one mutation alert and one heading when member removal fails`: the same mutation error rendered twice.

After the lifecycle guards and conditional error rendering, all four regressions pass. The focused suite has 12 passing tests. No URL or token value is included in this evidence.
