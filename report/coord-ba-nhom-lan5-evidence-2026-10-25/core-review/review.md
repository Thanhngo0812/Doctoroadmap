# W15 round five independent source review — 2026-10-25

Pinned `work/w15-real-build` at `fb0c769ad146d1aa6a5b2b2e1648a12a359ad194`, clean tracked tree, relative to main `46d829a55a62d852897f07102e89cf9a1fd5185e`. Read the R4 follow-up report, source changes and selected evidence. This review did not run a PG gate, connect to a DB, call a provider/ADC/SMTP/Cloudinary, read global live artifacts/held-out data, edit worker/root source, push, or authorize spending. Only this scratch folder was written.

**Conditional source approval for the whole `fb0c769` package, subject to root's current integration gates. No new Required functional finding. W15 remains open and neither paid run is approved.** This replaces the previous Windows rejection for this exact new source. It does not turn the demo price assumption into verified Google online pricing.

## R4 Windows defect closed

`w15_operator_run.prepare` now serializes `run_dir.relative_to(ROOT).as_posix()` in commit `3d5e1cd`. The regression `test_prepare_saved_plan_roundtrips_to_execute_composition_and_rejects_escape` genuinely calls prepare, reads its saved JSON, creates a fake approval and sends the unchanged plan into execute. Its composition sentinel stops before paid work; the test does not pretend to run a live operator.

Recorded RED is one assertion failure, zero setup errors, with the original `Path escapes its root` rejection. Recorded GREEN is one pass. The test also rejects parent traversal, absolute Unix, Windows drive, and backslash paths using the unchanged safe_path guard.

Independent `offline_roundtrip.py` exercised the same real prepare/write/read/execute path code with every DB/runtime/dry-run composition stubbed. New source reached only a fake composition sentinel. The old serializer was compiled into a separate in-memory namespace and reproduced the original rejection on this Windows host. Four hostile path controls still failed; saved plan bytes stayed unchanged and no execution.json was created. Native exit 0, no source mutations or DB/provider access. This is an independent offline serializer/validation proof; the real pipeline/PG aspect is supported by recorded tests and root's separate gates.

## Demo price assumption and authorization boundary

The report at `report/w15-sua-operator-lan4-2026-10-25.md:66` contains one quotation attributed to the owner, asking the team to choose a theoretical number for a demo. The documented resulting assumption is 0.15 USD per million input tokens, named `owner-demo-embedding-token-20261025`. I found the quote in the report, not an independently authenticated original session transcript. This provenance limitation is FYI, not a code blocker. It does not prove forgery, and this review makes no such claim.

The quoted scope is permission to choose a theoretical demo number. It names no PDF SHA, pipeline version, database/attempt/reference, or 1 USD/3 USD ceiling. It is not an exact-run paid approval. The report, summary and local approval request explicitly keep `owner_paid_approval_received=false` and `paid_run_executed=false`. The possibility of a future cap increase adds no current permission.

Commit `cfabaeb` intentionally replaces the earlier unconditional fail-closed policy with an explicit demo-profile exception. The code still has a narrow boundary:

- Normal RealBuildAdapter with no grant constructs the pipeline with allow_spend=False.
- BuildSpendApproval requires full file SHA, u-hash, pipeline version and supported model/location profile. At build_spend.py:175 it requires the exact demo price profile before accessing or consuming the PG approval record or constructing a paid pipeline.
- Missing/wrong demo profile is denied; old approval files are not upgraded implicitly. Execute matches the plan and approval on the explicit profile in addition to SHA/version/database.
- Plan, guard snapshot and approval record retain `embedding_billing_verified=false`. A character-only metadata response does not fill in missing token usage. The guard's demo totals remain token-arithmetic assumptions, not reconciled invoice charges.
- No API body, UI or settings/environment flag creates the trusted grant. The local approval JSON remains a trusted-operator attestation rather than a cryptographic signature from the owner.

Independent `offline_spend.py` confirms normal no-spend construction, missing/wrong grant profile refusal before fake-store access/factory, correct-profile reference consumption once, zero embedding dispatch with a missing profile, known token-price arithmetic, and unknown retention when only character metadata is returned. It also checks that a timeout after earlier known usage keeps both 0.000265 known USD and 0.360448 unknown upper USD and prevents a following fake dispatch. All calls in these probes were in-process fakes. The one-use fake-store probe is not a substitute for PG concurrency testing; that remains root's gate.

The online Vertex SKU billing unit remains unverified, as the report says. No new pricing research or undercharge claim is needed to review this explicitly labeled demo assumption. Accepting the source/profile does not close the old prerequisite as verified tariff evidence and does not authorize a paid run under it.

## Receipts, accounting and selected evidence

`verify_evidence.py` verified 22 selected manifest entries by SHA and byte count, and all 23 current source byte hashes captured by the recorded full-gate native metadata at `cfabaeb`. The final `fb0c769` adds reports/evidence rather than changing those tested sources.

Recorded final counts are full Python 2641 passed of 2643 with the existing Cloudinary skip/replay xfail, no failures/errors, native 0; focused 39 passed; React 181 passed; build native 0. Precommit focused/mutation metadata correctly retains its earlier HEAD plus source hashes; it must not be recast as a clean-tree run at that earlier HEAD. Root is running new gates on the actual combined integration tree; historical green does not replace those gates.

Four final mutation records have at least one assertion kill each, zero setup errors and source-restored flags. I read their selected JUnit rather than rerunning source-mutating tests. The unverified-grant mutation has one direct assertion showing entry into the forbidden paid factory; its second parametrized failure is an already-consumed reference after the first mutation failure. Count the mutation as caught once, not as two independent authorization proofs.

The selected latest synthetic SQL success receipt retains raw build trace detail while typed trace cost/tokens are zero; summed build ledger matches the build receipt. The guard's audit budget does not create another billed ledger. Existing adapter receipt logic still marks unknown/stopped attempts failed and retains core-meter known usage. This review did not establish durable final receipts after an abrupt process kill; the report correctly does not claim that.

Both current local plan hashes match `tmp/w15-r4-approval-request.json`. Their prepared commit/pipeline version is `fb0c769`, paths are portable, approved=false, explicit demo profile present and billing_verified=false. Those metadata checks did not read their PDF/artifact contents or query their DBs. Latest selected internal dry-run exports retain one collector receipt, no queue/provider, and zero relevant SQL counts. Doc6 actual-byte cache-only evidence still ends failed on its uncached stage with zero provider calls; it does not show a ready course or successful mail. Synthetic bootstrap/cache-reuse rehearsal is not actual-book provider/quality evidence.

## Merge choice and handoff

Whole `fb0c769` is conditionally source-approved as an opt-in operator feature with no default spend, subject to root's successful combined gates. If a smaller operationally disabled milestone is desired, `7f90749ef237b5c47625a3bbbea67e116000b7fe` is the clean prefix including portable paths and unconditional refusal of paid grants/embedding while the online price remains unresolved. The earlier prefix through `3d5e1cd` fixes only paths and inherits the old unverified paid-price behavior; it is not the safer fail-closed split. The source delta through `7f90749` also brings the previous operator feature/tests relative to main, so it is not merely a one-line path cherry-pick.

After merging or any HEAD/config change, prepare fresh plans because the pipeline version includes HEAD; preserve earlier plans as evidence. Keep the report quote and its provenance limitation distinct from a future exact-run decision. Before either actual execution, the owner must approve that precise PDF SHA/version/profile/run/database/reference/ceiling; no execution or cap increase is authorized here. Afterwards, actual usage, output quality, doc6 cache reuse/ready/mail and learning usefulness still need measurement/review. Keep W15 open. No deployment, publication, push or paid retry follows from this code review.

Reproduce these independent offline checks with the workspace Python and `-B`:

```powershell
& 'C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe' -B 'C:/Users/ngoco/Desktop/Doctoroadmap/tmp/coord-r5-core-review-20261025/offline_roundtrip.py'
& 'C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe' -B 'C:/Users/ngoco/Desktop/Doctoroadmap/tmp/coord-r5-core-review-20261025/offline_spend.py'
& 'C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe' -B 'C:/Users/ngoco/Desktop/Doctoroadmap/tmp/coord-r5-core-review-20261025/verify_evidence.py'
```

All three returned native exit 0. The first intentionally creates fresh fake-input plan folders only under this scratch directory; it never calls the real operator with a paid approval.
