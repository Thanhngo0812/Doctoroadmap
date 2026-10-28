# R10 command record

Working root: `C:/Users/ngoco/Desktop/Doctoroadmap`.

Read-only review commands used `Get-Content -Encoding UTF8`, focused `rg -n`, `git diff`, `git log`, `git merge-base`, `git rev-parse`, and `git status --short` in root/delivery. The root and delivery HEADs were 776f1f00b13726fcdc95f12bfd18a2b937bbd153 and 9cf405acbbf8838d05a17b4bb7936d171cb5afa5. Existing unrelated working changes were retained. No .env content was read.

Source isolation used PowerShell `Copy-Item` on the allowlisted runner, pyproject, OpenAPI, W17 test and Python source files under `src/doc2roadmap` and `src/web/backend/wayfinder`. SHA256 recorded before/after in source-copy-manifest.json. Only regular copied files were used; no symlinks/junctions/hardlinks were created. No cache, heldout data or fixture artifact data were copied.

Executed from scratch:

```powershell
& ./run-probes.ps1 -Label baseline-01
& ./run-probes.ps1 -Label baseline-02
& ./run-mutations.ps1
& ./run-probes.ps1 -Label final-restored
```

Each probe command invokes the unchanged `scripts/w05_run_tests.py` with explicit test file and unique JUnit/basetemp. It sets a synthetic SQLite URL before entering the runner, so runner credential-loading is bypassed. Every native command, argument, cwd, elapsed time, exit code and backend source hash is retained in `runs/*-exit.json`; stdout/stderr and JUnit are retained alongside it. No direct `python -m pytest` or alternate Python script launcher was used.

`run-mutations.ps1` changes ordinary scratch copies only, saves original bytes, runs the named independent assertion, then restores exact bytes in finally and verifies SHA256. Native exit 1 counts as caught only with at least one assertion failure and zero JUnit errors. Author mutation/evidence hashes were audited with PowerShell Get-FileHash and through the standard runner test.

The initial baseline-01 result is a disclosed reviewer SQLite UUID fixture defect, not regression RED. Baseline-02 and final-restored are green; all six explicit product mutants are assertion-red. Final copy restoration, author-source hashes, test/script hashes and XML aggregates are separately saved for provenance.

After the owner's new first-admin policy arrived, a separate test file was added and run without changing product source or rerunning the original full suite:

```powershell
& ./run-probes.ps1 -Label owner-policy-red -TestFile test_owner_policy.py
```

The harness gained an optional TestFile parameter; the original 23-test file was unchanged. This later assertion fails on the delivered behavior (1 assertion failure, 0 errors). It is owner-policy RED, separate from original-contract GREEN. See policy-addendum.md and runs/owner-policy-red*.
