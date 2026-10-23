# W11 auth return patch review

Source reviewed: `2c5166bfcf30ee8cd1a784f8da6891278b260522`, based on main `865974ae14e03bdc5e37283aa496972f8c3c622d`.

The owner froze that main baseline. Documentation-only main had already been received at `33f9c2521ba0379d89c3fe942ea754f9f06b49a6` before the asynchronous reply arrived. All 639 source hashes are identical; final browser and extra gates record that latter commit explicitly. No source change or further main receipt is made after the freeze.

## Correctness and scope

The loss occurred in the shared form-switch destination, after the existing sanitization. The patch builds one destination using sanitized next and reuses it in both Link targets and the view-transition navigate callback. Direct navigation with no next retains the old target. Login/register API and backend sharing behavior are unchanged by the patch.

The only additional product markup change replaces the auth theme glyph with the existing CourseShell SVG and accessible button label. The visible non-text glyph had made Axe require manual contrast review. No CSS, token, palette, typeface or motion rule is changed.

The reviewer test import retains all original assertions and adds unsafe-next coverage. Removing four unsupported ByRoleOptions.exact properties is a type compatibility correction: string accessible-name matching remains exact. No assertion is removed, no skip is added, and no threshold is lowered.

## Security and regression evidence

The raw requestedNext is never forwarded as the destination. Existing checks still reject external schemes, protocol-relative URLs, backslashes and whitespace. Twelve unsafe inputs across transition/fallback paths pass; removing the sanitizer makes all twelve fail. The mutation restores exact source bytes before any browser or full gate.

Eight original backend mutations are retained and caught. The source receiving main keeps W14 DTO upload/confirmation context, W11 migration lineage, sharing transactions/count/capacity and membership/private-data rules. New backend code is received from main; the web patch does not rewrite it or alter transport.

## Runtime and appearance

The final browser run covers all eight form-switch combinations with real native transitions or real reduced-motion media settings, then actual authentication and join requests in isolated PostgreSQL. All original W11 flows remain. Independent SQL verifies uses/membership and retained progress. Final gate results are separate from this review.

Auth screenshots at 390 dark and 1280 light were inspected in development and in the final run. Existing WayFinder logo, typography, semantic colors and layout remain consistent; the SVG matches CourseShell. Taste app-screen rules are applied through the existing W11 direction and main tokens. No unaccepted W24 preview is imported.

No Required finding remains from this code review. The coordinator still decides acceptance and merging after reviewing final executable evidence. W08 starts only after that acceptance.
