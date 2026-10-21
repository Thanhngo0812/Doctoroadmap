# W-07 React design decisions

## Screen inventory and question

- **Objects:** one member course; ordered modules (`module_id`, index, title, description, module progress); ordered learnable concepts (`node_id`, name, learner state); course progress totals.
- **Data source:** live W-07 API only. No seeded course counts, percentages, titles, or simulated content. The progress contract is actor-bound; the browser sends only `{ learned: boolean }` for a node.
- **People and use:** a learner returning to a shared or owned course, mostly on a laptop and sometimes on a phone, checks where they are and marks concepts as learned or not learned.
- **Most frequent job:** continue through the ordered modules, then mark a concept from the module view.
- **Screen question:** “Bạn đang ở đâu trong tài liệu, và có thể học tiếp phần nào?” The course total and ordered module rows answer this; each row exposes its own learned/total count.
- **First-screen blocks:** course title and description, course progress, ordered module list with module progress, and an expandable module’s concept checklist. W-08/W-09/W-10 have no active controls or fabricated content here.

## Visual direction

- Applied `design-taste-frontend` (v2), its full `references/app-screens.md` app-screen run, `frontend-ui-engineering`, and `ponytail`'s simplicity rule. App direction was drawn with `draw.mjs --app --kind workspace --brief "WayFinder learner roadmap: ordered course modules, module progress, expandable concept checklist" --screens overview,detail --keep palette,type --seed 70321`; saved sheet: `design-direction.json` (moved from the generated `.taste-skill/w07/direction.json` for handoff).
- Dealt style: **Achromatic ledger**, seed `70321`. Its data-led colour, flat surfaces, honest zeros, concise section hierarchy, and one question per screen fit a learner’s progress view. The face is the actual per-concept learning record: ordered concepts, each with a persistent learner mark; the brand blue appears on real progress data, not decorative chrome.
- Adapted the direction’s no-sidebar open plane to reuse the existing authenticated `CourseShell` and its WayFinder top bar. W-07 is one course workspace inside the current app; adding a second navigation shell would duplicate chrome. Kept the direction’s flat, restrained surfaces and progress as the main data element.
- Project tokens take precedence over generic direction values: Be Vietnam Pro; light/dark brand palette and semantic colors from `design/tokens/tokens.css`; project spacing, radius, focus, and motion tokens. No new color values or typeface. Titles use the course-page text tokens, and UI labels remain “tài liệu” / “bài học”.
- The W-24 W-07 preview and Frame 9 report are references for module expansion and undoable learner marks only; their sample course, progress values, controls for quiz/share, and markup are not copied. The W-24 report itself notes that its Figma/Cloud claims require independent verification.

## Interaction and layout decisions

- Roadmap and module detail remain separate routes. The roadmap lists modules in API order and uses one expanded module at a time; the module route shows that module’s ordered concepts. Every module remains openable regardless of prior completion.
- Each concept uses a native checkbox with the visible label “Đã học: {tên khái niệm}”; the whole row is a mobile-sized target. Pending state is per node, repeated submits for that node are ignored, and an error restores only that node while announcing the error. Concurrent responses merge their node result into current state; totals are derived from node states to avoid stale full-response snapshots overwriting other changes.
- Course and module progress show numeric learned/total values beside a native progress indicator; zero is rendered as zero. The expanded module count and overall count derive from the same node states and are checked against the API summary.
- Motion is limited to module disclosure and control feedback, using `motion-fast` / `motion-base`; `prefers-reduced-motion` removes nonessential transitions. Focus remains visible, checkboxes are keyboard-native, and heading/focus order follows the route content.
- Responsive intent: one column at 390px; module rows remain compact but readable at 768px; at 1280px the ordered list uses the available content width without introducing dashboard KPI tiles or decorative side panels. All touch controls meet 44px on mobile.

## Boundary

Only the W-07 roadmap, module concept marks, and the minimal course-entry integration are in scope. Lecture content, assistant sessions, quizzes, library, and document creation remain owned by W-08/W-09/W-10 and have no fake actions here.
