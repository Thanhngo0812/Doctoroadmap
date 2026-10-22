# Read-only W-14 React/DTO review

Reviewed 6494f51eb6b1033150d041197745b4d88a8a69da against W-25 c00c028. No Critical/Required product logic finding; eligible to receive approved backend main and enter final integration gates. Worker source/evidence was not modified; reviewer did not independently rerun the complete local web tests/browser.

- upload_id is selected using actor/build/course, not a shared job's source upload. A learner receives null; one actor's two courses retain separate upload contexts.
- confirmed_at belongs to each upload, enabling an explicit name/confirmation for a reused running or succeeded build without automatic confirmation or extra runner calls.
- Poll/actions retain course_id, validate returned identities and abort on route departure; cancel/retry respect server capabilities. No money/internal worker details shown.
- Test/evidence review covers explicit confirmation, scoped reload, 3-second polling, reuse/name isolation, aborts, learner card and meaningful UI mutation assertions.
- Reviewer viewed confirmation390dark and running1280light; branding, hierarchy and controls were clear.

Required before merging: remove32 tracked synthetic-image pytest outputs from the two basetemp-contract-green directories in report/w14-react-evidence, keep local bytes, and add ignore. The exact paths are in web-handoff-hygiene.json.

The current Axe run covers the rejected page only;47 screenshots are not47 Axe audits. Images/video predate the final stopped-state copy change. New complete gates/browser evidence are still required on the integrated tip after main a572459 or later is received. The coordinator has not accepted/merged this React branch in this review.
