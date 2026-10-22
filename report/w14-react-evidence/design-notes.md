# W-14 frontend design notes

## Direction

The app-screen draw selected a framed-sheet direction (seed `1059735927`) for a learner-facing document workflow. I used its quiet, structured hierarchy for upload review and build status, while retaining WayFinder's existing Be Vietnam Pro typography, blue brand palette, tokens, shared course shell, and flat bordered surfaces. The draw was a composition reference, not a replacement design system.

## Screen decisions

- `/tai-len` keeps file choice, rights confirmation, and the upload action together. The rights checkbox is required before sending the file; upload creates an awaiting state only.
- `/ban-dung/:buildId` displays server state and the four actual build stages. A separate title confirmation starts work; polling and cancellation use the API state and permissions.
- A learner's own upload remains confirmable when its document build is shared with another course. The title and confirmation belong to the learner's course; no build starts automatically.
- The status screen uses one bounded content column and restrained bordered panels so the step list, error recovery, and next action stay legible without adding dashboard decoration.
- Controls retain the shared mobile touch target and reduced-motion behavior. `TaskWait` is used only when the API reports an active processing step.

## Integration boundary

The frontend targets the W-14 API contract and exports `BuildView`, `buildPath`, and `buildStatusLabel` for course cards. This local check covers the focused React tests and production build only; API/database/browser acceptance remains with the root integration run.

## Integration review updates

Root's real-browser review found the native file control's intrinsic width overflowing at390. The corrected chooser keeps the native input focusable, uses the visible Vietnamese “Chọn tệp” target, and supports single-file drag/drop without auto-upload. Rights confirmation remains required. A long user course name also made the combined status h1 exceed two lines; the final screen now uses a short status h1 and a separate full wrapping course title.

Generated direction archived at `design-direction.json`. Root recorded inspector results and its two-round screenshot critique in `visual-critique.md`; that review distinguishes design-only DOM snapshots from real API/browser workflow evidence.
