import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BROWSER = ROOT.parent / "coord-r4-tools-20261024/design-browser"

observations = json.loads((BROWSER / "observations.json").read_text(encoding="utf-8"))
refs = [{"path": str(BROWSER / name), "sha256": hashlib.sha256((BROWSER / name).read_bytes()).hexdigest()}
        for name in ("observations.json", "w09-active-1280.png", "w08-ready-390.png")]
w09 = next(row for row in observations["rows"] if row["ticket"] == "w09" and row["width"] == 1280
           and row["theme"] == "light" and row["reducedMotion"] == "no-preference")
w08 = next(row for row in observations["rows"] if row["ticket"] == "w08" and row["width"] == 390
           and row["theme"] == "light" and row["reducedMotion"] == "no-preference")
reused = {"producer": "root coordinator", "reviewer_directly_executed_browser": False,
          "reviewer_read_exact_runtime_json_and_viewed_both_png": True,
          "diagnostic_only": observations["diagnosticOnly"], "browser_version": observations["browserVersion"],
          "worker_commit": observations["workerCommit"], "row_count": len(observations["rows"]),
          "any_overflow": any(row["overflow"] for row in observations["rows"]),
          "references": refs, "w09_1280_light_math": w09["math"],
          "w09_1280_light_accessibility_snapshot": w09["mathAccessibilitySnapshots"],
          "w08_390_light_accessibility_snapshot": w08["mathAccessibilitySnapshots"],
          "w08_first_katex_nested_count": w08["math"][0]["nested"],
          "w08_first_katex_outer": w08["math"][0]["outer"]}
(ROOT / "browser-evidence-reused.json").write_text(json.dumps(reused, indent=2, ensure_ascii=False), encoding="utf-8")

summary = json.loads((ROOT / "summary.json").read_text(encoding="utf-8"))
summary["required_findings"][0]["browser_status"] = "Confirmed in root browser: base and subscript at same y=998.5625, 14px font, verticalAlign baseline; screenshot visibly has no subscripts"
summary["required_findings"][1]["browser_status"] = "Confirmed in root accessibility snapshots: W09 and W08 display snapshots empty; first W08 snapshot contains only following prose, no mathematical content"
summary["required_findings"][2]["browser_status"] = "Confirmed in root DOM: nested count 1, first formula contains display formula and prose; screenshot shows prose inheriting serif formula typography"
summary["optional_findings"].append({"id": "D-R4-DOC-02", "severity": "Optional",
    "path": "design/preview/w08_lecture_screens.html", "line": 327,
    "title": "Tail-error wording says safely saved although cat_ngan is intentionally excluded from shared cache",
    "action": "Clarify that received content stays visible on screen; avoid durable/cache promise",
    "source": "src/doc2roadmap/application/phase_b/lecture3.py:229-231"})
summary["verification"]["browser_evidence_reviewed_from_root"] = {"rows": 24, "configs_per_page": 12,
    "widths": [390, 768, 1280], "themes": ["light", "dark"], "reduced_motion": ["no-preference", "reduce"],
    "diagnostic_only": True, "any_overflow": False, "ref": "browser-evidence-reused.json"}
summary["evidence"].append("browser-evidence-reused.json")
(ROOT / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

manifest = json.loads((ROOT / "copy-manifest.json").read_text(encoding="utf-8"))
for entry in manifest["files"]:
    source = Path(manifest["source"]) / entry["path"]
    copy = ROOT / "isolated" / entry["path"]
    assert hashlib.sha256(source.read_bytes()).hexdigest() == entry["source_sha256"]
    assert hashlib.sha256(copy.read_bytes()).hexdigest() == entry["copy_sha256"]
print(json.dumps({"required": len(summary["required_findings"]), "optional": len(summary["optional_findings"]),
                  "files_sha_verified": len(manifest["files"]), "root_browser_rows_reviewed": len(observations["rows"])}))
