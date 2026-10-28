# R11 — W-17.1 backend

Pinned delivery: 862dd805180201647cd6a3dda54c2083073d1e84; main before DG20: 26d43b83ba0d3f265f28ea7d3220f924ba96a97d; independent HTTP/PG candidate 98f9c38dee5dcdb27c0553fda477394064e7a390. Reviewer worker stopped before final verdict; coordinator completed the review and independent probe.

**REQUEST CHANGES — CORE-R11-01 (Required/P2)** at src/web/backend/wayfinder/application/admin.py:57. admin_count() now counts active admins but the demotion guard applies to disabled targets too. Repro: bootstrap A; create B admin; A disables B; A PATCH B role=user (with quota=7). Expected200: A stays active/protected; actual409 conflict lastadmin. PostgreSQL shows A active/admin and B disabled/admin; no active administrator is being removed. Independent test native1, one assertion failure, zero setup errors; owner first-admin protection control passed. See test_core_probe.py, core-probe-proof.json and runs/core-independent.xml in the coordinator scratch/evidence.

Apply the last-active-admin rule only when the transition removes an active admin. Keep immutable first-admin policy and atomic rejection, do not remove authorization/counting globally. Add disabled-later-admin demotion and combined enable+demote controls; preserve first-admin failures and login/session/audit concurrency.

POL-R10-01 is substantively addressed: singleton persistent UUID, immutable registry and account DB triggers, same admin/account locks, transaction-bound bootstrap/assignment/audit, explicit legacy CLI, nullable public DTO, no HTTP identity-write. Legacy DB migration was not applied to shared DB and remains an operator task after acceptance. W20 delete APIs remain absent; SQL guard is lower-level protection.

Source/test review found no new private-data exposure or provider call: bounded parameterized queries, live actor checks, metadata DTO, no extra dependencies; migration adds one head w17_0009 after w12_0008. First-admin guard control on actualPG passed. Broader3600pass/14mutant claims are worker evidence, not a coordinator full acceptance gate.

FYI: source/evidence audit verified378/380 manifest entries; packaging-note.json and redactions.json were edited after their manifest rows (bytes/SHA differ). Regenerate those rows after final edits. Git long paths required per-command core.longpaths=true for some evidence names; no globalconfig change required.

No source fixes by coordinator, no main/shared DB migration, no push,0USD.
