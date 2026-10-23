# W-11 sharing UI design notes

## Product inventory

- A course is the shareable classroom; its title and published module count come from the course API.
- One owner creates an invite link; each link has a six-character tail, creation time, expiry, optional use limit, usage count, and active/revoked state.
- The full invite URL is returned only once at creation. The screen must offer a real copy action before the one-time value is cleared.
- An invitation is bearer access: anyone holding an active URL can preview the course and join when signed in.
- The public preview identifies the course, its owner, module count, and concept count without disclosing membership or learner data.
- A signed-in learner sees the data disclosure before joining: the owner sees display name, join date, recent activity, and per-module learned-concept counts; the owner cannot see chats, documents, or quiz answers.
- An owner sees all members with display name, join date, recent activity, and join source. W-11 has no member progress summary.
- A learner sees the course owner and total member count, not other learners' identities.
- Removing a member or leaving a course removes membership access but does not erase that learner's existing study data.
- Existing WayFinder shell, Be Vietnam Pro, Artboard 24/28, color palette, semantic tokens, and Vietnamese labels remain the visual source of truth.

## Screen questions and hierarchy

- **Share dialog:** “Can I make a link for this class, and what does it let someone do?” Lead with expiry and optional use limit; after creation show the one-time URL and copy result, then the active/revoked link list with only each six-character tail.
- **Join preview:** “Which class is this, and what will its owner learn about me?” Lead with course title, owner, and module count. Guests get login/register return links. Signed-in learners get the disclosure followed by “Tham gia”. The invalid-link state uses only the common `link_invalid` message.
- **Members:** “Who belongs to this class, and what can I do here?” Owners get the member list and an explicit remove confirmation; learners get owner, member count, and a leave confirmation. No per-member progress, email invitation, or co-owner affordances.

## Direction and tokens

- Applied `design-taste-frontend` app-screen run, `frontend-ui-engineering`, and ponytail simplicity guidance. Draw command: `node <skill>/scripts/draw.mjs --app --kind workspace --brief "WayFinder course sharing and membership: owner creates a revocable invite link, learners preview data disclosure, owners manage course members" --screens detail,list,settings --keep palette,type --style achromatic-ledger --out .taste-skill/w11`.
- Chosen direction: **Achromatic ledger**, seed `566999260`. Its quiet, ruled list treatment fits link and member records. The product's face is a real one-time invite link: its full URL exists only in the immediate creation result; the persistent list identifies it by the six-character tail. The visible data-disclosure statement is the signature element of join preview.
- The sheet's “no brand colour in chrome” and its open-plane/sidebar shell are explicitly overridden by WayFinder's existing semantic tokens and authenticated top-bar shell. Keep the project’s brand-blue primary action, tokenized light/dark surfaces, existing compact control and spacing rules, and Artboard logo; do not introduce a second navigation shell. No new palette, typeface, icons-in-tinted-squares, or decorative cards.
- The app uses the existing `CourseShell` for protected course screens and the same visual shell for public join preview. Join is a public route so the guest can preview before authentication.
- At desktop the dialog stays a compact form/list, and the owner/member page uses one column with clear row actions. On 390px, dialog sections stack; every control/link hit area is at least 44px. Respect reduced motion and use native `<dialog>.showModal()` for focus containment/restoration rather than an overlay imitation.

## State and privacy constraints

- Creation uses contract fields `expires_in_days` (`7` default; `null` for no expiry) and `max_uses` (`null` unlimited). No unsupported custom expiry picker.
- The raw token/URL is held in component memory only after create. Never place it in local storage, test logs, report artifacts, or debug output. Closing the dialog clears that state. Copy success is shown only after `navigator.clipboard.writeText` resolves; failure remains actionable and does not claim success.
- List responses display the tail only. Revoke does not alter membership.
- Public join route keeps the token in the route as required for preview; auth return uses the existing approved local `/join/:token` `next` path. Join itself requires an authenticated session and CSRF.
- Empty, loading, server, permission, invalid-link, validation, clipboard, and confirmation states use the common Vietnamese API messages and existing alert/status patterns. Error and confirmation feedback must remain keyboard reachable and visible in both themes.

## Contract and integration boundary

The generated direction artifact is archived at `report/w11-evidence/design-direction.json`. Browser screenshots, the taste inspector, and the look-and-fix loop are pending the owner's instruction to resume integration; this checkpoint does not claim visual acceptance.

- API source of truth: `report/w11-evidence/api-contract.md`.
- UI uses the approved POST/GET/DELETE share-link endpoints; guest GET preview and authenticated POST join; and GET members, owner DELETE member, learner POST leave.
- Email invitations (W-12), member progress summaries (W-18), co-owners, and backend/schema work are excluded. Keep `/khoa-hoc/:cid/thanh-vien` as the proposed frontend route unless the root integration harness specifies an alternate path.
