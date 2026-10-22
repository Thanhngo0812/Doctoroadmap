# W-07 visual review

**Capture set:** `roadmap-{390,768,1280}-{light,dark}.png`, latest refresh from source `8f7fd4e`. Reviewed all six captures from the prior `8c54b14` set and rechecked the four refreshed 390px/1280px light/dark captures.

The WayFinder mark, Be Vietnam Pro typography, and brand colors match the existing app shell and token palette. The course title remains the published graph title, while learner-facing progress uses “bài học.” On mobile, the account control is shortened to “Tài khoản” while retaining the learner's full name in its accessible label. Blue is reserved for progress and navigation; green marks learned concepts. Dark mode keeps the same hierarchy and makes dividers, text, and controls legible against the dark surface.

| Viewport | Visual check |
| --- | --- |
| 390 px | Header and account controls fit in one row. The course title, total, expanded module, checklist, and ordered module rows stay within the viewport with no visible clipping or horizontal overflow. The reserved sections follow the roadmap. |
| 768 px | The course information and module list remain a single reading column; the two reserved sections sit side by side after the list. Module counts and checklist labels remain aligned and readable. |
| 1280 px | The ordered roadmap occupies the main column. The reserved sections align beside the course summary near the top, leaving the full module list in order. Main content and rail have clear separation. |

The long mobile and desktop pages reflect the real 35-module roadmap rather than a shortened preview. The expanded module shows its description, progress, and concept checklist before the remaining modules; counts are visible at both course and module level. The calm, text-led treatment supports this dense data without adding decorative cards or competing metrics. The taste inspector reports one unused-canvas warning at 1280px because the reserved rail has short content; the rail stays alongside the roadmap as specified, so this is intentional whitespace rather than missing content. No required visual fixes found in this capture set.
