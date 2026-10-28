# Policy addendum — owner decision after the original R10 contract review

Date: 2026-10-28. Delivery remains `9cf405acbbf8838d05a17b4bb7936d171cb5afa5`.

**Current disposition: HOLD W17.1 delivery. Required POL-R10-01 supersedes the original optional policy-gap finding.** The original `review.md` and its 23-pass result record the earlier written contract; they do not establish compliance with this later owner instruction. Root has limited the accepted integration gate to W04 only.

New owner instruction, quoted exactly: **“admin đầu tiên ko đc khóa hay gì”**.

The coordinator's interpretation, already stated to the owner, is that the first/bootstrap admin is protected from **disable, role demotion and deletion**, while ordinary profile/password operations remain available. This explicit owner decision is now mandatory and overrides the earlier unresolved disable-policy gap. It is not an allegation that the worker violated a decision that had not yet arrived.

## Required POL-R10-01 — persist bootstrap-admin identity and protect its account

The delivery permits its first and only admin to disable itself. The original independent SQL probe proved that this leaves zero active admins. The new owner-policy assertion instead expects rejection and is **RED on the unmodified delivery source**:

- Assertion: `test_owner_policy.py::test_new_owner_policy_first_admin_cannot_be_disabled`.
- Execution: `./run-probes.ps1 -Label owner-policy-red -TestFile test_owner_policy.py`, through the unchanged `scripts/w05_run_tests.py`.
- Result: native exit **1**, **1 failed assertion, 0 setup errors**. JUnit failure is `DID NOT RAISE AuthError`, because `AdminService.update_user` accepts the forbidden status change. See `runs/owner-policy-red.xml`, `.log`, and `-exit.json`.
- The synthetic fixture creates this first and only admin before its learner. That one account is both bootstrap and last admin, so it is a sufficient counterexample to the new owner policy. It is not proof that a last-admin count identifies the bootstrap account.

The fix must preserve the **first/bootstrap account's stable identity persistently on the server** and enforce that identity across all disable/demotion/deletion entry points and callers, including self-actions. Do not infer the protected identity from the current number of admins, the current role/status, query ordering, pagination or a filtered users response. Adding another admin, changing another account's role, restarting the service, or filtering the user list must not transfer or remove this protection. Existing installations need a deterministic, explicit way to establish the protected identity; the implementation must not guess from whichever account a request happens to return first.

The existing last-role-admin demotion guard remains a separate invariant. By itself it does not satisfy first-admin protection, since the bootstrap account must stay protected even when other admins exist. Rejected operations must leave account/session/audit state unchanged. Normal profile/password flows remain allowed under the coordinator's interpretation. These are requirements for the follow-up implementation and regression evidence, not claims already verified by this addendum.

No fix, PostgreSQL gate, full-suite rerun or extra product mutation was performed for this addendum. All product source remains unchanged; only review harness/artifacts were added. The earlier 23-pass suite and six caught mutants retain their historical meaning for the old contract. A compliant follow-up and the coordinator's appropriate fresh exact-commit checks are required before W17.1 acceptance.
