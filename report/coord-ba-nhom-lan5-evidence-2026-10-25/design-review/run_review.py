from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / "w24-figma-evidence"
PIN = "aa387f33542250b08487c2dd1ce105abc68fd9ed"
MAIN = "46d829a"
OLD = "eb29f29"
PYTHON = str(ROOT.parents[1] / ".venv/Scripts/python.exe")
COPY = ROOT / "isolated"
RECORDS = []
MATH_TESTS = ["test_w08_formulas_have_accessible_content", "test_w09_formulas_have_accessible_content",
              "test_w08_formula_nodes_are_not_accidentally_nested", "test_w09_formula_has_subscript_layout_styles"]


def git(*args):
    return subprocess.check_output(["git", *args], cwd=SOURCE)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(name, argv, cwd=COPY):
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    start = time.time()
    result = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8")
    (ROOT / f"{name}.stdout.log").write_text(result.stdout, encoding="utf-8")
    (ROOT / f"{name}.stderr.log").write_text(result.stderr, encoding="utf-8")
    RECORDS.append({"name": name, "argv": argv, "cwd": str(cwd), "native_exit_code": result.returncode,
                    "started_epoch": start, "elapsed_seconds": round(time.time() - start, 3)})
    (ROOT / "native-records.json").write_text(json.dumps(RECORDS, indent=2), encoding="utf-8")
    return result


def pytest_cmd(tests=None, xml=None):
    command = [PYTHON, "-m", "pytest", "--noconftest", "-c", str(ROOT / "pytest-review.ini"),
               "--rootdir=" + str(COPY), "-q", "-p", "no:cacheprovider"]
    if xml:
        command.append("--junitxml=" + str(ROOT / xml))
    command.extend(["tests/unit/presentation/test_tokens_and_wcag.py" + ("::" + t if t else "") for t in (tests or [None])])
    return command


def main():
    assert git("rev-parse", "HEAD").decode().strip() == PIN
    assert not git("status", "--porcelain").strip()
    selected = list((SOURCE / "design/preview").glob("*.html"))
    selected += list((SOURCE / "design/tokens").glob("*"))
    selected += [SOURCE / p for p in ("design/figma-plugin/code.js", "design/Untitled_Artwork.gif",
        "design/Untitled_Artwork_static.png", "scripts/verify_figma_plugin_vm.cjs", "scripts/verify_wcag_contrast.py",
        "tests/unit/presentation/test_tokens_and_wcag.py", "report/w24-kiem-lai-2026-10-22.md")]
    manifest = []
    for source in selected:
        destination = COPY / source.relative_to(SOURCE)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        manifest.append({"path": source.relative_to(SOURCE).as_posix(), "source_sha256": sha(source),
                         "copy_sha256": sha(destination), "bytes": destination.stat().st_size})
    (ROOT / "copy-manifest.json").write_text(json.dumps({"source": str(SOURCE), "pin": PIN,
        "method": "ordinary shutil.copyfile; isolated focused unit tests, not repository PostgreSQL gate", "files": manifest}, indent=2), encoding="utf-8")
    (ROOT / "pytest-review.ini").write_text("[pytest]\n", encoding="utf-8")

    baseline = run("pytest-focused-baseline", pytest_cmd(xml="pytest-focused-baseline.xml"))
    assert baseline.returncode == 0, baseline.stdout + baseline.stderr
    math_paths = [COPY / "design/preview" / name for name in ("w08_lecture_screens.html", "w09_chat_screens.html")]
    original = {p: p.read_bytes() for p in math_paths}
    try:
        for path in math_paths:
            path.write_bytes(git("show", OLD + ":" + path.relative_to(COPY).as_posix()))
        old_result = run("regression-old-html-current-guards", pytest_cmd(MATH_TESTS, "regression-old-html.xml"))
        assert old_result.returncode == 1, old_result.stdout + old_result.stderr
        assert "4 failed" in old_result.stdout
    finally:
        for path, content in original.items():
            path.write_bytes(content)

    w09 = math_paths[1]
    try:
        text = original[w09].decode("utf-8")
        import re
        mutant = re.sub(r"(?m)^\s*\.katex \.(?:msupsub|vlist-t|vlist-r|vlist |vlist-s)[^\r\n]*[\r\n]+", "\n", text)
        assert mutant != text
        w09.write_text(mutant, encoding="utf-8")
        result = run("mutation-removed-subscript-rules-css-guard", pytest_cmd([MATH_TESTS[3]]))
        assert result.returncode == 0, result.stdout + result.stderr
    finally:
        w09.write_bytes(original[w09])

    changes = git("diff", "--name-status", MAIN + ".." + PIN).decode().splitlines()
    auth = []
    for path in ("src/web/frontend/src/Auth.tsx", "src/web/frontend/src/W11AuthReturn.repro.test.tsx",
                 "design/preview/auth_screens.html", "design/preview/w03_auth_screens.html"):
        old_oid = git("rev-parse", MAIN + ":" + path).decode().strip()
        new_oid = git("rev-parse", PIN + ":" + path).decode().strip()
        auth.append({"path": path, "main_blob": old_oid, "candidate_blob": new_oid, "identical": old_oid == new_oid})
    merge_ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", MAIN, PIN], cwd=SOURCE).returncode == 0
    scope = {"main": git("rev-parse", MAIN).decode().strip(), "candidate": PIN,
             "main_is_ancestor": merge_ancestor, "changed_paths": changes,
             "changed_non_report_paths": [line for line in changes if not line.split("\t")[-1].startswith("report/")],
             "auth_identity": auth,
             "active_application_source_changes": [line for line in changes if line.split("\t")[-1].startswith("src/")]}
    (ROOT / "branch-scope.json").write_text(json.dumps(scope, indent=2), encoding="utf-8")
    verification = [{"path": item["path"], "source_unchanged": sha(SOURCE / item["path"]) == item["source_sha256"],
                     "copy_restored": sha(COPY / item["path"]) == item["copy_sha256"]} for item in manifest]
    assert all(v["source_unchanged"] and v["copy_restored"] for v in verification)
    assert not git("status", "--porcelain").strip()
    (ROOT / "post-run-hash-verification.json").write_text(json.dumps(verification, indent=2), encoding="utf-8")
    print(json.dumps({"baseline_exit": baseline.returncode, "old_html_guard_exit": old_result.returncode,
                      "copied_files": len(manifest), "source_unchanged": True,
                      "subscript_css_guard_surviving_mutation": True, "unmerged_changed_paths": len(changes)}))


if __name__ == "__main__":
    main()
