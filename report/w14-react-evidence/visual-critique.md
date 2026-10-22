# W-14 visual review — app-screen scope

Direction: framed-sheet, seed `1059735927`. Existing WayFinder tokens, Be Vietnam Pro, Artboard 24/28 and waiting illustrations override the dealt shell/palette. No stock photography or external illustrative assets were added. Border panels and the numbered four-stage workflow carry actual app structure/data under the skill's app-screen rules.

ROUND 1
Seen in one second: a real four-stage build with its current lesson-extraction step.
Idea (one sentence): keep the document, editable course name and actual build state legible across upload, reload and reuse.
Live thing: upload/explicit confirmation and real server-driven progress with cancel/retry.
Layout words by section: header=brand/account / heading=status+course / workflow=steps+waiting illustration+action.
Scores: design 6.5 · usability 7.0 · creativity 6.0 · content 8.0 → overall 6.7; inspector FAIL cap → 6.0.
Caps applied: the 390px heading wraps to three lines. App-screen conventions apply to structural panel borders and stage numbering; this is not a marketing page requiring photographs.
Top three problems (most visible first), each with the screenshot it shows in and the fix:
1. `review-round-1/reading-reloaded-390-dark.png`: status plus a long user course title forms a three-line h1. Fix: short status heading, full title in a wrapping paragraph; preserve the user's words.
2. Early `browser-run-2.log`: native file input reaches x422 at a 390px viewport. Fix: constrain the input's intrinsic width, then use a Vietnamese visible chooser with a genuine focusable native input and 44px target.
3. `review-round-1/taste-inspect/desktop-fold.jpg`: the right side of a single-task progress panel is quiet. Keep a bounded one-column workflow; extra metrics, invented progress or decorative content would have no user task here. Record the desktop `hero-void` WARN rather than claiming zero warnings.

ROUND 2
Seen in one second: “Đang dựng lộ trình”, followed by the correct full course name and actual active stage.
Idea (one sentence): show what is happening to this course and what the learner can do next.
Live thing: actual progress/cancel/retry backed by FastAPI and PostgreSQL; the inspector snapshot is design-only.
Layout words by section: header=existing shell / heading=short status+full course / workflow=ordered steps / feedback=current task and safe action.
Scores: design 6.5 · usability 8.0 · creativity 6.0 · content 8.5 → overall 7.1.
Caps applied: sparse desktop app canvas limits design to 6.5. This is a focused utility screen, not a gallery landing page.
Top three problems (most visible first), each with the screenshot it shows in and the fix:
1. `taste-inspect/desktop-fold.jpg`: `hero-void` WARN remains on 1280. Accepted for a bounded single-task form/progress column; full-width filler would add no information. This is the only documented inspector warning.
2. `taste-inspect/mobile-fold.jpg`: the “Khoá học của tôi” return link wraps, but retains its full label and 44px target. Keep it readable rather than reducing type size.
3. `taste-inspect/tablet-fold.jpg`: the task message repeats the active stage below the illustration. Keep it because the waiting-asset spec requires a descriptive message and assistive status; the h2 states the current step.

Root opened all six inspector fold/page images at 1280/768/390, the initial 390 light/dark and 1280 light/dark upload views, and real reading/running screenshots. Inspector result after the heading fix: **0 FAIL, 1 WARN**. Final workflow screenshots are separate HTTP evidence, not the static snapshot. No design score of 7.5+ is claimed.
