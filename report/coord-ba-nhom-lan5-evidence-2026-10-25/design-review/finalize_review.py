from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / "w24-figma-evidence"
BROWSER = ROOT.parent / "coord-r5-tools-20261025/design-browser"
PIN = "aa387f33542250b08487c2dd1ce105abc68fd9ed"
INTEGRATION = "31d14b573a8d9852bfd0aa5d5185753a99a05ecc"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=SOURCE).decode().strip()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


data = json.loads((BROWSER / "observations.json").read_text(encoding="utf-8"))
exit_record = json.loads((BROWSER.parent / "runs/design-browser-exit.json").read_text(encoding="utf-8"))
assert not data["diagnosticOnly"] and len(data["rows"]) == 24 and exit_record["native_exit_code"] == 0
assert all(not row["overflow"] for row in data["rows"])
assert all(m["mathml"] == 1 and m["nested"] == 0 and m["ariaLabel"] for row in data["rows"] for m in row["math"])
assert all("math" in snapshot and snapshot.strip() for row in data["rows"] for snapshot in row["mathAccessibilitySnapshots"])
formula_count = sum(len(row["math"]) for row in data["rows"])
for row in data["rows"]:
    if row["ticket"] == "w09":
        math = row["math"][0]
        assert float(math["subscripts"][0]["fontSize"].removesuffix("px")) < float(math["bases"][0]["fontSize"].removesuffix("px"))
        assert math["subscripts"][0]["y"] > math["bases"][0]["y"]
    else:
        assert row["waiting"]["width"] == row["waiting"]["height"] == 96
        assert row["waiting"]["src"].endswith("Untitled_Artwork_static.png" if row["reducedMotion"] == "reduce" else "Untitled_Artwork.gif")

refs = [{"path": str(path), "sha256": sha(path)} for path in (
    BROWSER / "observations.json", BROWSER / "w09-active-1280.png", BROWSER / "w08-ready-390.png",
    BROWSER.parent / "design-browser.cjs", BROWSER.parent / "runs/design-browser-exit.json")]
identity = []
for filename in ("w08_lecture_screens.html", "w09_chat_screens.html"):
    path = "design/preview/" + filename
    worker_oid, integration_oid = git("rev-parse", PIN + ":" + path), git("rev-parse", INTEGRATION + ":" + path)
    assert worker_oid == integration_oid
    identity.append({"path": path, "candidate_blob": worker_oid, "integration_blob": integration_oid, "identical": True})
w09 = next(row for row in data["rows"] if row["ticket"] == "w09" and row["width"] == 1280
           and row["theme"] == "light" and row["reducedMotion"] == "no-preference")
w08 = next(row for row in data["rows"] if row["ticket"] == "w08" and row["width"] == 390
           and row["theme"] == "light" and row["reducedMotion"] == "no-preference")
reused = {"producer": "root coordinator", "reviewer_executed_browser": False,
    "reviewer_read_exact_runtime_json_and_viewed_both_png": True, "diagnostic_only": False,
    "browser_version": data["browserVersion"], "rows": len(data["rows"]), "formula_snapshots": formula_count,
    "integration_commit": INTEGRATION, "source_commit": PIN, "math_source_identity": identity,
    "launcher_native_record": exit_record, "launcher_cwd_commit_is_not_browser_target_commit": True,
    "references": refs, "w09_1280_light_math": w09["math"],
    "w09_1280_light_accessibility": w09["mathAccessibilitySnapshots"],
    "w08_390_light_math": w08["math"], "w08_390_light_accessibility": w08["mathAccessibilitySnapshots"]}
(ROOT / "browser-evidence-reused.json").write_text(json.dumps(reused, ensure_ascii=False, indent=2), encoding="utf-8")

scope = json.loads((ROOT / "branch-scope.json").read_text())
assert scope["main_is_ancestor"] and not scope["active_application_source_changes"]
assert all(item["identical"] for item in scope["auth_identity"])
manifest = json.loads((ROOT / "copy-manifest.json").read_text())
assert git("rev-parse", "HEAD") == PIN and not git("status", "--porcelain")
for item in manifest["files"]:
    assert sha(SOURCE / item["path"]) == item["source_sha256"]
    assert sha(ROOT / "isolated" / item["path"]) == item["copy_sha256"]

summary = {
    "reviewer": "review_design_r4", "round": "R5", "review_date": "2026-10-25",
    "source_branch": "work/w24-figma-evidence", "source_commit": PIN,
    "main_baseline": scope["main"], "previous_review_commit": "eb29f291709245a9ccf3d121415f6202fdeaae7f",
    "verdict": "approve_design_math_and_unmerged_source_scope",
    "new_required_findings": [],
    "closed_findings": [
        {"id": "D-R4-01", "status": "CLOSED", "evidence": "Real browser W09 base15.4px/sub11.55px; base y998.5625/sub y1006.4375; geometry assertions passed in all12 configs"},
        {"id": "D-R4-02", "status": "CLOSED", "evidence": "Three correct sample aria-labels and unhidden MathML branches; all36 runtime formula snapshots across24 pages expose math"},
        {"id": "D-R4-03", "status": "CLOSED", "evidence": "No nested .katex in source or actual DOM; W08 explanatory prose is outside formula and screenshot shows normal body typography"},
        {"id": "D-R4-DOC-01", "status": "CLOSED", "evidence": "Report top now records accepted-with-notes web design without Cloud and historical Cloud section has non-gating disclaimer"},
        {"id": "D-R4-DOC-02", "status": "CLOSED", "evidence": "Tail text now says received content remains on screen; removed durable/cache claim"}
    ],
    "optional_findings": [{"id": "D-R5-OPT-01", "severity": "Optional", "path": "tests/unit/presentation/test_tokens_and_wcag.py", "line": 979,
        "title": "CSS structural guard accepts typography-only .katex rule after removal of actual subscript layout rules",
        "evidence": "Isolated mutant removes .msub/.vlist* rules; test_w09_formula_has_subscript_layout_styles remains green, native exit0",
        "recommendation": "Preserve runtime geometry assertions for subscript size and physical placement; root browser already supplies these for present acceptance"}],
    "handoff_limits": ["The three static formulas and their matching MathML are reviewed; there is no generic LaTeX parser or full KaTeX engine in these preview HTML files.",
        "Report wording about fallback CSS is accepted for these samples; do not interpret this as replacing React's actual math renderer.",
        "Previously accepted W22/W24 web scope remains accepted with notes. Cloud Figma is not an acceptance gate."],
    "whole_branch_source_scope": {"recommendation": "Whole branch source is reviewed-safe within accepted design scope, subject to coordinator integration gates; selective prefix is not needed for scope isolation",
        "changed_paths": len(scope["changed_paths"]), "non_report_paths": len(scope["changed_non_report_paths"]),
        "active_application_source_changes": 0, "main_is_ancestor": True, "auth_source_and_previews_identical_to_main": True,
        "previously_accepted_tokens_plugin_scope_reopened": False},
    "verification": {"focused_isolated_pytest": {"passed": 58, "seconds": 1.30, "native_exit_code": 0},
        "old_html_current_math_guards": {"failed": 4, "seconds": 1.53, "native_exit_code": 1, "expected_regression_failure": True},
        "restored_current_math_guards": {"passed": 4, "seconds": 0.78, "native_exit_code": 0},
        "independent_sample_math_structure": {"formulas": 3, "native_exit_code": 0},
        "source_files_with_sha256": 26, "source_unchanged_and_copies_restored": True,
        "root_browser_reused": {"configs": 12, "pages": 24, "formula_snapshots": formula_count, "native_exit_code": 0,
            "diagnostic_only": False, "integration_commit": INTEGRATION, "source_identity_verified": True, "any_overflow": False},
        "repo_postgresql_gate_executed_by_reviewer": False, "provider_adc_or_livecache_used": False, "worker_mutated": False},
    "evidence": ["review.md", "native-records.json", "copy-manifest.json", "post-run-hash-verification.json", "branch-scope.json",
        "pytest-focused-baseline.xml", "regression-old-html.xml", "math-guards-after-restoration.xml", "math-structure.json", "browser-evidence-reused.json"]}
(ROOT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"new_required": 0, "closed_R4_required": 3, "optional": 1, "root_browser_formula_snapshots": formula_count,
                  "source_files_sha_verified": len(manifest["files"]), "whole_branch_source_scope": "safe within accepted design scope"}))
