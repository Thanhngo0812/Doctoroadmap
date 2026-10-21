# W-06 course screen CSS notes

## Review basis

- `design-taste-frontend` (`references/app-screens.md`) and `frontend-ui-engineering` were reviewed.
- Applied the `editorial-greeting` direction seed `307593073` only as a cue for a calm, carefully spaced workspace. The page follows the product spec instead of adopting the seed’s greeting treatment or decorative KPI patterns.
- Project guidance: `doc/web-thiet-ke-giao-dien-spec.md` sections 3, 3a, 5, and 6; `task/web/W-06-khoa-mau-khoa-hoc-cua-toi-gateway.md`; and W-24 screen-state inventory in `report/w24-bo-sung-w22-2026-10-19.md`.
- Compared with the local `/khoa-hoc` desktop, mobile, and dark previews. The previews inform content and state coverage; project tokens and current component behavior remain authoritative.

## Decisions applied

- Kept the page as a work screen: direct course heading, course groups, cards, and task actions. No marketing hero, gradients, or decorative illustration were added.
- Used existing WayFinder tokens for typography, spacing, surfaces, borders, brand/status colors, radii, shadows, and motion. The shared shell keeps the existing horizontal logo and a 64px desktop / 56px mobile header.
- Checked token names against `design/tokens/tokens.css`; the layout uses defined project values (including `--space-5`, `--line-h1`, and the 120/200ms motion tokens) without introducing replacement tokens. Course cards stay flat with a border and no shadow.
- Made the course grid one column below 640px, two columns from 640px, and three from 1024px. This yields the required one / two / three columns at 390 / 768 / 1280px while allowing intermediate widths to use available space.
- Kept card, heading, account-menu, and empty-state actions at least 44px tall. Added visible-focus-compatible control sizing without replacing the shared focus treatment.
- Matched the component’s actual markup: module count and build state share a wrapping metadata row; progress text stacks above the native progress bar; course titles remain full-size keyboard-accessible links; account-menu links retain 44px rows. The upload action moves into the account menu on mobile so the header fits beside the logo and account control.
- Styled course progress with native `<progress>` and the existing brand token; sample, building, and failed courses have restrained surface/status distinctions. Empty, loading, error, and lightweight course-entry states have their own layout hooks.
- Limited transitions to small card border feedback at the 120ms token duration. Reduced-motion mode removes that transition; no CSS animation or simulated loading delay was introduced.
- Responsive page gutters use the project’s 16px mobile, 24px tablet, and 32px desktop values through the corresponding widths.

## Scope and evidence

This file records CSS/design intent only. The React component, interaction states, dark/light screenshots, responsive review, and automated gates are owned by the W-06 integrator; this CSS-only pass did not run tests or a build.
