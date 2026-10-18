"""Run lecture K6 mutants in isolated Python processes and save named assertions."""
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
CASES = {
    "k6_scans_serialized_metadata": (
        "tests/unit/application/test_phase_b_sa45_lecture_audit.py::test_k6_scans_idea_text_without_serialized_citation_metadata",
        "import json; from doc2roadmap.application.phase_b import lectures; lectures._lecture_output_text = lambda output: json.dumps(output, ensure_ascii=False)",
    ),
    "k6_disabled": (
        "tests/unit/application/test_phase_b_lecture_sa30.py::test_k6_third_occurrence_after_gate_keeps_two_qualified_ideas",
        "from doc2roadmap.application.phase_b import lectures; lectures._has_repeated_ngram = lambda text: False",
    ),
}


def main():
    base = ROOT / "tmp/sa45-lecture-mutants"
    base.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, (assertion, mutation) in CASES.items():
        args = [assertion, "-q", "-p", "no:cacheprovider", "--basetemp", str(base / name)]
        runner = mutation + "\nimport pytest\nraise SystemExit(pytest.main(" + repr(args) + "))\n"
        result = subprocess.run([sys.executable, "-c", runner], cwd=ROOT, text=True,
                                encoding="utf-8", errors="replace", capture_output=True)
        killed = result.returncode == 1 and "FAILED" in result.stdout and "AssertionError" in result.stdout
        rows.append({"mutation": name, "assertion": assertion, "killed": killed,
                     "exit_code": result.returncode,
                     "failure_excerpt": result.stdout[-1800:],
                     "stderr_excerpt": result.stderr[-500:]})
    regression = "tests/unit/application/test_phase_b_sa45_lecture_audit.py::test_same_prerequisite_has_only_one_bridge_in_lecture_sections"
    bridge_checks = {}
    for name, extra in (("normal_xfail", []), ("runxfail", ["--runxfail"])):
        args = [regression, "-q", *extra, "-p", "no:cacheprovider",
                "--basetemp", str(base / name)]
        result = subprocess.run([sys.executable, "-m", "pytest", *args], cwd=ROOT, text=True,
                                encoding="utf-8", errors="replace", capture_output=True)
        bridge_checks[name] = {"assertion": regression, "command_args": args,
                               "exit_code": result.returncode,
                               "expected": result.returncode == (0 if name == "normal_xfail" else 1),
                               "output_excerpt": result.stdout[-1800:],
                               "stderr_excerpt": result.stderr[-500:]}
    output = ROOT / "tmp/sa45-lecture-mutations.json"
    payload = {"mutants": rows, "bridge_regression": bridge_checks}
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"mutants": len(rows), "killed": sum(row["killed"] for row in rows),
                      "bridge_regression": {k: v["expected"] for k, v in bridge_checks.items()},
                      "output": str(output.relative_to(ROOT))}, ensure_ascii=False))
    if any(not row["killed"] for row in rows) or not all(v["expected"] for v in bridge_checks.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
