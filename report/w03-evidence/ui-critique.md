ROUND 2 — W-03 authentication and recovery screens

Seen in one second: “Quên mật khẩu” with one email field and one clear recovery action; verify and reset keep the same focused, branded form frame.

Idea (one sentence): WayFinder handles account recovery through a calm, one-task-at-a-time flow that does not disclose whether an email address has an account.

Live thing: Real HTTP email-request, verification and password-reset flows (with a test mailer); verification requires an explicit button press, and reset/verification links show expired, used, invalid, pending and success states.

Layout words by section: shell=slim branded header / recovery=single centered form / terminal=red alert with a clear next action / account=verification banner above account content.

Scores: design 7.5 · usability 8.5 · creativity 6.5 · content 8.0 → overall 7.7

Caps applied: None. The eyebrow is removed, and the page-only photo, motion and live-element caps do not apply to these app screens.

Top three problems (most visible first), each with the screenshot it shows in and the fix:

1. The remaining inspector warning is the large, symmetric desktop whitespace around the form (`forgot-1280-light.png`, also visible in the reset and verify screens). Keep it: the centered frame gives this single-purpose account task room to breathe, and adding decorative content would weaken its focus.

Closed since round 1: the generic uppercase eyebrow was removed from all recovery screens; the header link inset was increased to 16px at 390px. Those were the other two inspector warnings.

Review notes: I inspected all 18 final light/dark screenshots at 390/768/1280px. The latest taste inspector reports 0 FAIL and 1 WARN, with only the defended desktop whitespace finding. The browser run passed 18 layouts and 8 flow assertions; the stored audit reports no overflow or axe violations across the layouts. The final views retain Be Vietnam Pro, the WayFinder mark, primary blue action, responsive form structure and explicit red terminal-link feedback. The expired-link view has no stale verification-success notice. The design group’s W-03 preview and project tokens were comparison references, not treated as an approved final design.
