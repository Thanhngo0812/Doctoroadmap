"""Read-only receipt checks for the pinned W08 handoff; no application imports or live services."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "tmp/w08-lecture"
OUT = Path(__file__).resolve().parent
EVIDENCE = WORK / "report/w08-evidence"
FINAL = EVIDENCE / "required3-2026-10-24"
PIN = "c8c687b63afff86d628688de73abb92dfd4f17a2"
SOURCE = "b4136987668c3fb822ea374f399b947064ce7f18"
MAIN = "5936a5d91b6c3979f1918b33ce330403414b776f"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=WORK)


def junit(path: Path) -> dict:
    doc = ET.parse(path).getroot()
    cases = list(doc.iter("testcase"))
    failed = [c for c in cases if c.find("failure") is not None]
    errors = [c for c in cases if c.find("error") is not None]
    xfailed = [c for c in cases if (s := c.find("skipped")) is not None and s.get("type") == "pytest.xfail"]
    skipped = [c for c in cases if c.find("skipped") is not None and c not in xfailed]
    return {"tests": len(cases), "failures": len(failed), "errors": len(errors),
            "skipped": len(skipped), "xfailed": len(xfailed),
            "passed": len(cases) - len(failed) - len(errors) - len(skipped) - len(xfailed),
            "identities": [(c.get("classname"), c.get("name")) for c in cases],
            "failedNames": [c.get("name") for c in failed],
            "skipNames": [c.get("name") for c in skipped + xfailed]}


result = {"pin": PIN, "testedSource": SOURCE, "mainBase": MAIN,
          "method": "Read-only source/receipt/JUnit/hash inspection; no tests, browser, database or provider executed.",
          "errors": []}
errors = result["errors"]
head = git("rev-parse", "HEAD").decode().strip()
if head != PIN:
    errors.append({"head": head})
result["sourceChangesAfterTestedCommit"] = git("diff", "--name-only", SOURCE, PIN, "--", "src", "scripts", "tests", "pyproject.toml", "uv.lock", "design/tokens").decode().splitlines()
if result["sourceChangesAfterTestedCommit"]:
    errors.append("Product or test source changed after gate source")

manifest = read_json(FINAL / "sha256-manifest.json")
receipt_checks = []
for row in manifest["files"]:
    # Never follow manifest paths to other evidence, document data, caches or temporary worktrees.
    rel = Path(row["path"])
    is_report = row["path"] == "report/w08-sua-tien-do-va-tu-kiem-tra-2026-10-24.md"
    if not is_report and not row["path"].replace("\\", "/").startswith("report/w08-evidence/"):
        errors.append({"disallowedReceiptPath": row["path"]})
        continue
    target = (WORK / rel).resolve()
    target.relative_to((WORK / "report").resolve() if is_report else EVIDENCE.resolve())
    if not target.is_file():
        errors.append({"missingReceipt": row["path"]})
        continue
    raw = target.read_bytes()
    if digest(raw) != row["sha256"] or len(raw) != row["bytes"]:
        errors.append({"receiptMismatch": row["path"], "actualSha256": digest(raw), "actualBytes": len(raw)})
    receipt_checks.append(row["path"])
result["receiptHashesChecked"] = len(receipt_checks)

paths = [
    "src/web/frontend/src/Learning.tsx", "src/web/frontend/src/Learning.test.tsx",
    "src/web/frontend/src/Learning.review-repro.test.tsx", "src/web/frontend/src/lecture-api.ts",
    "src/web/frontend/src/LectureMarkdown.tsx", "src/web/frontend/src/SourceViewer.tsx",
    "src/web/backend/wayfinder/api/learning.py", "src/web/backend/wayfinder/application/learning_gateway.py",
    "src/web/backend/wayfinder/application/lecture_view.py", "src/web/backend/wayfinder/infrastructure/learning_media.py",
    "src/web/backend/tests/test_lecture3_integration_w08.py", "src/web/backend/tests/test_lectures_w08.py",
    "src/doc2roadmap/application/phase_b/lecture3.py", "src/doc2roadmap/application/phase_b/lecture_context3.py",
    "tests/unit/application/test_phase_b_lecture3_sa70.py", "tests/unit/application/test_phase_b_lecture3_sa64.py",
    "scripts/w08_web_check.cjs", "scripts/w08_web_runtime.py", "scripts/w08_mutations.py",
]
source_rows = {r["path"]: r for r in read_json(FINAL / "source-manifest.json")["files"]}
blob_rows = {r["path"]: r for r in read_json(FINAL / "source-blob-manifest.json")["files"]}
source_checks = []
for rel in paths:
    raw = (WORK / rel).read_bytes()
    blob = git("show", f"{SOURCE}:{rel}")
    now_blob = git("show", f"{PIN}:{rel}")
    row, brow = source_rows[rel], blob_rows[rel]
    passed = (digest(raw) == row["sha256"] == brow["workingTreeSha256"]
              and digest(blob) == brow["gitBlobSha256"]
              and raw.replace(b"\r\n", b"\n") == blob.replace(b"\r\n", b"\n")
              and blob == now_blob)
    source_checks.append({"path": rel, "passed": passed, "worktreeSha256": digest(raw), "gitBlobSha256": digest(blob)})
    if not passed:
        errors.append({"sourceMismatch": rel})
result["sourceChecks"] = source_checks

gates = read_json(FINAL / "gate-results.json")
result["junit"] = {}
for name in ["python", "react"]:
    info = junit(FINAL / f"{name}.xml")
    result["junit"][name] = {k: v for k, v in info.items() if k not in ["identities", "failedNames"]}
    if {k: info[k] for k in gates[name]} != gates[name]:
        errors.append({"gateCountMismatch": name})
    mapping = read_json(FINAL / "invariant-map.json")[f"{name}Assertions"]
    missing = [(r["classname"], r["name"]) for r in mapping if (r["classname"], r["name"]) not in info["identities"]]
    result["junit"][name]["mappedAssertionsPresent"] = len(mapping) - len(missing)
    if missing:
        errors.append({"missingAssertions": missing})
for name in ["python", "react", "build", "browser"]:
    cmd = read_json(FINAL / f"{name}-command.json")
    if cmd != gates["commands"][name] or cmd["nativeExit"] != 0 or cmd["sourceCommit"] != SOURCE or cmd["mainBase"] != MAIN:
        errors.append({"commandMismatch": name})
    exit_path = FINAL / f"{name}-exit.txt"
    if exit_path.read_text().strip() != "0":
        errors.append({"exitMismatch": name})
result["nativeExitChecked"] = ["python", "react", "build", "browser"]

result["redGreen"] = {}
for name in ["repro-red", "repro-red2", "repro-green", "focused-green"]:
    data = junit(EVIDENCE / "required-2026-10-24" / f"{name}.xml")
    result["redGreen"][name] = {k: v for k, v in data.items() if k != "identities"}

helper = (WORK / "report/coord-ba-nhom-lan3-evidence-2026-10-23/web-review/Learning.review-repro.test.tsx").read_text(encoding="utf-8-sig")
suite = (WORK / "src/web/frontend/src/Learning.review-repro.test.tsx").read_text(encoding="utf-8-sig")
result["coordinatorTestBodiesIdentical"] = helper[helper.index("\nit("):] == suite[suite.index("\nit("):]
if not result["coordinatorTestBodiesIdentical"]:
    errors.append("Coordinator test bodies changed")

mutation_rows = read_json(FINAL / "mutation-source-match.json")["cases"]
result["mutations"] = []
for row in mutation_rows:
    rel = row["source"]
    actual = digest((WORK / rel).read_bytes())
    cmd = row["command"]
    arg = next((x for x in cmd if x.startswith("--junitxml=")), None)
    if arg:
        target_rel = arg.split("=", 1)[1].replace("\\", "/").split("/report/w08-evidence/", 1)[1]
    else:
        # Vitest outputFile option is a separate argument.
        value = cmd[cmd.index("--outputFile") + 1] if "--outputFile" in cmd else next(x.split("=", 1)[1] for x in cmd if x.startswith("--outputFile="))
        target_rel = value.replace("\\", "/").split("report/w08-evidence/", 1)[1]
    receipt = EVIDENCE / target_rel
    data = junit(receipt)
    good = (row["nativeExit"] == 1 and row["failures"] > 0 and row["errors"] == 0
            and actual == row["beforeSha256"] == row["restoredSha256"]
            and data["failures"] == row["failures"] and data["errors"] == 0)
    result["mutations"].append({"name": row["name"], "passed": good, "failures": data["failures"], "receipt": str(receipt.relative_to(WORK))})
    if not good:
        errors.append({"mutationMismatch": row["name"]})

audit = read_json(EVIDENCE / "browser-required3-20261024/audit.json")
wire_checks = []
for row in audit["sseWire"]:
    frames = []
    for raw in re.split(r"\r?\n\r?\n", row["body"]):
        lines = re.split(r"\r?\n", raw)
        event = next((x[6:].strip() for x in lines if x.startswith("event:")), None)
        data = "\n".join(x[5:].lstrip() for x in lines if x.startswith("data:"))
        if data and event:
            frames.append((event, json.loads(data)))
    text = "".join(d["text"] for e, d in frames if e == "delta")
    final = [d["lecture"] for e, d in frames if e == "final"]
    good = (text.strip() == "Phần chính hiện ngay." and len(final) == 1
            and final[0]["self_check"]["answer_md"] == "Đáp án riêng phải gập."
            and not re.search(r'"validation"|"public_id"|res\.cloudinary\.com', row["body"]))
    wire_checks.append({"scenario": row["scenario"], "passed": good, "events": [e for e, _ in frames], "deltaText": text})
    if not good:
        errors.append({"wireMismatch": row["scenario"]})
result["wireChecks"] = wire_checks
result["browserReceiptCounts"] = {"screens": len(audit["screens"]), "axeAudits": len(audit["accessibility"]),
    "httpExchanges": len(audit["http"]), "configurations": len(audit["configurations"]),
    "sseWire": len(audit["sseWire"]), "errors": audit["errors"], "pageErrors": audit["pageErrors"],
    "failedRequests": audit["failedRequests"]}
result["ok"] = not errors
(OUT / "receipt-check.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"ok": result["ok"], "errors": errors, "receiptHashesChecked": len(receipt_checks),
                  "sourceFilesChecked": len(source_checks), "mutantsChecked": len(result["mutations"]),
                  "junit": result["junit"], "wireTracesChecked": len(wire_checks)}, ensure_ascii=False, indent=2))
