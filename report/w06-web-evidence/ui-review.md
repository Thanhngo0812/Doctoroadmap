# W-06 independent UI and flow review

## Review scope

Reviewed `Courses.tsx`, `courses-api.ts`, W-06 routes in `App.tsx`, auth redirects/session handling in `Auth.tsx`, the current `courses.css`, the W-06 React tests, and the 390/768/1280 light/dark captures. Also checked null progress, building/failed courses, join races/focus, stale requests, local `next` handling, and reduced-motion CSS.

## Visual review

Reviewed all six refreshed captures: 390, 768, and 1280px in light and dark mode.

- **390px:** The logo, theme control, and account menu fit without the upload action covering them. The skip link is out of layout at rest. The verification reminder wraps into a full-width brand-tint panel with a readable resend action. Course cards remain one column, with no clipped labels or horizontal overflow.
- **768px:** Header and verification reminder remain readable; course lists use two columns and preserve card spacing.
- **1280px:** Course lists use three columns; the final partial row remains aligned to the grid. The page retains a quiet workspace hierarchy and avoids card shadows.
- **Both themes:** Brand, surface, border, and muted text colors remain consistent with the project tokens; logos render in the correct light/dark variants.

The three issues in the earlier 10:31 captures are resolved in the latest CSS and the refreshed screenshots confirm the fixes. Visual review is approved.

## Flow and code review

- `CoursesPage` now guards the list response against an aborted effect before setting state. Join requests are deduplicated by course ID, aborted on unmount, and checked again before updating state. `CourseEntry` guards both course/roadmap requests and its final state update against stale route requests.
- `joinSample` uses the shared API client, so the browser session cookie and in-memory CSRF token are included. A failed join leaves the sample card available and announces the API error. On success, the card moves to the owned/joined section and a ref focuses its next action; the test asserts this focus result.
- `progress: null` renders “Chưa có tiến độ”; a sample course has no invented progress. `total: 0` avoids rendering a zero-denominator progress element.
- Building and failed courses do not offer a false “Học tiếp” action or fake progress. Their link opens a membership-checked detail summary with the corresponding state message.
- Guest redirects preserve only the internal course pathname in `next`. `AuthPage` rejects protocol-relative paths, backslashes, and whitespace before navigating; the redirect remains same-origin. Tests cover external URL and `//host` inputs.
- No W-06 motion is essential. Card hover uses a small border transition and the reduced-motion rule removes it; the existing shared reduced-motion rule also disables transitions and animations globally.
- Course entry intentionally stays a membership-checked summary/resume view; the full roadmap is W-07. `/tai-len` links point to the later W-14 upload flow as scoped in the task; they do not claim uploads work in W-06.
- The CSS adds no external resource or inline style and does not change CSP policy or allowlists.

## Verdict

**Approve.** No required correctness or visual issue remains in this review. Root reports 77 frontend tests and the build passing; I did not run tests or a build. The refreshed browser captures provide the final visual evidence.

## Final capture check

Rechecked all six `courses-{390,768,1280}-{light,dark}.png` captures from frontend `f1ec3bb`. The page content inset is 16px at 390px and 24px at 768px. At 1280px, the centered 1200px content area leaves 40px on each side; the header logo itself is inset 32px. The 40px page inset reads as deliberate max-width spacing, though it is not a literal 32px gutter. Light/dark logo variants and the theme control SVG render clearly at every size; course arrows and actions remain legible, with no clipping or horizontal overflow.

## Post-label-change check — commit `627578e`

Reviewed the refreshed `courses-390-light.png`, `courses-390-dark.png`, and `courses-1280-light.png` captures. The updated wording (“tài liệu” and “bài học”) fits without changing wrapping or card height; both mobile themes retain the 16px content inset, clear logo/theme SVG, and unclipped course cards. The 1280px light view remains balanced with the 40px page inset noted above. No visual issue found.
