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
PIN = "eb29f291709245a9ccf3d121415f6202fdeaae7f"
PYTHON = str(ROOT.parents[1] / ".venv/Scripts/python.exe")
COPY = ROOT / "isolated"
RECORDS = []


def run(name: str, argv: list[str], *, cwd: Path = COPY) -> subprocess.CompletedProcess:
    start = time.time()
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8")
    (ROOT / f"{name}.stdout.log").write_text(result.stdout, encoding="utf-8")
    (ROOT / f"{name}.stderr.log").write_text(result.stderr, encoding="utf-8")
    RECORDS.append({"name": name, "argv": argv, "cwd": str(cwd), "native_exit_code": result.returncode,
                    "started_epoch": start, "elapsed_seconds": round(time.time() - start, 3)})
    (ROOT / "native-records.json").write_text(json.dumps(RECORDS, indent=2), encoding="utf-8")
    return result


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=SOURCE, text=True).strip()
    assert head == PIN, (head, PIN)
    selected = list((SOURCE / "design/preview").glob("*.html"))
    selected += list((SOURCE / "design/tokens").glob("*"))
    selected += [SOURCE / p for p in (
        "design/figma-plugin/code.js", "design/Untitled_Artwork.gif", "design/Untitled_Artwork_static.png",
        "scripts/verify_figma_plugin_vm.cjs", "scripts/verify_wcag_contrast.py",
        "tests/unit/presentation/test_tokens_and_wcag.py", "report/w24-kiem-lai-2026-10-22.md")]
    manifest = []
    for src in selected:
        dst = COPY / src.relative_to(SOURCE)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        manifest.append({"path": src.relative_to(SOURCE).as_posix(), "source_sha256": sha(src),
                         "copy_sha256": sha(dst), "bytes": dst.stat().st_size})
    (ROOT / "copy-manifest.json").write_text(json.dumps({"source": str(SOURCE), "pin": PIN,
        "method": "ordinary shutil.copyfile; isolated selected unit tests, not repo PostgreSQL gate", "files": manifest}, indent=2), encoding="utf-8")
    config = ROOT / "pytest-review.ini"
    config.write_text("[pytest]\n", encoding="utf-8")
    baseline = run("pytest-focused-baseline", [PYTHON, "-m", "pytest", "--noconftest", "-c", str(config), "--rootdir=" + str(COPY), "-q",
                    "-p", "no:cacheprovider", "--junitxml=" + str(ROOT / "pytest-focused-baseline.xml"),
                    "tests/unit/presentation/test_tokens_and_wcag.py"])
    assert baseline.returncode == 0, baseline.stdout + baseline.stderr
    for name, args in [("baseline", []), ("fault-create-primary", ["--fault-var", "color/primary"]),
                       ("removed-accounting", ["--remove-accounting"])]:
        result = run("vm-" + name, ["node", "scripts/verify_figma_plugin_vm.cjs", *args])
        assert result.returncode == 0
        payload = json.loads(result.stdout)
        (ROOT / ("vm-" + name + ".json")).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    plugin = COPY / "design/figma-plugin/code.js"
    original = plugin.read_bytes()
    try:
        mutant = original.replace(b"variableReport.created += 1;", b"/* reviewer mutation: removed created accounting */")
        assert mutant != original
        plugin.write_bytes(mutant)
        result = run("mutation-removed-accounting-existing-baseline-test", [PYTHON, "-m", "pytest", "--noconftest", "-c", str(config), "--rootdir=" + str(COPY), "-q", "-p", "no:cacheprovider",
            "tests/unit/presentation/test_tokens_and_wcag.py::test_figma_plugin_runtime_output_and_real_execution"])
        assert result.returncode == 1, "Existing output guard must fail when accounting is removed"
    finally:
        plugin.write_bytes(original)
    verification = []
    for item in manifest:
        src = SOURCE / item["path"]
        dst = COPY / item["path"]
        verification.append({"path": item["path"], "source_unchanged": sha(src) == item["source_sha256"],
                             "copy_restored": sha(dst) == item["copy_sha256"]})
    assert all(x["source_unchanged"] and x["copy_restored"] for x in verification)
    (ROOT / "post-run-hash-verification.json").write_text(json.dumps(verification, indent=2), encoding="utf-8")
    print(json.dumps({"baseline_exit": baseline.returncode, "copied_files": len(manifest), "native_records": len(RECORDS), "all_source_and_copy_hashes_match": True}))


if __name__ == "__main__":
    main()
