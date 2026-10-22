"""Sequential UI mutations; restore source bytes before returning or running a gate."""
from hashlib import sha256
import json
from pathlib import Path
import socket
import subprocess
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "report/w14-react-evidence/ui-mutations"
CASES = (
    ("auto-confirm", "Builds.tsx", "Builds.test.tsx", "requires rights confirmation",
     "const uploaded = await uploadDocument(file, controller.signal);",
     "const uploaded = await uploadDocument(file, controller.signal); "
     "await confirmBuild(uploaded.upload_id, 'Automatic mutation title', controller.signal);"),
    ("missing-course-query", "builds-api.ts", "Builds.test.tsx", "polls active builds every three seconds",
     "`/api/v1/builds/${encodeURIComponent(id)}?course_id=${encodeURIComponent(courseId)}`",
     "`/api/v1/builds/${encodeURIComponent(id)}`"),
    ("no-card-poll", "Courses.tsx", "Courses.test.tsx", "refreshes active build cards after three seconds",
     "poll = setTimeout(() => setReload(current => current + 1), 3000);",
     "/* mutation: active card polling removed */"),
)


def main():
    with socket.socket() as probe:
        if probe.connect_ex(("127.0.0.1", 8014)) == 0:
            raise RuntimeError("Stop the W-14 browser runtime before mutating source")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    results = []
    for name, source, test, match, old, new in CASES:
        path = ROOT / "src/web/frontend/src" / source
        original = path.read_bytes()
        text = original.decode("utf-8")
        if text.count(old) != 1:
            raise RuntimeError(f"Mutation {name} does not match exactly one source statement")
        report = OUTPUT / f"{name}.xml"
        command = ["npm.cmd", "--prefix", "src/web/frontend", "test", "--", f"src/{test}",
                   "-t", match, "--pool=threads", "--maxWorkers=1", "--reporter=junit",
                   f"--outputFile={report.as_posix()}"]
        try:
            path.write_bytes(text.replace(old, new).encode("utf-8"))
            process = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=90)
            (OUTPUT / f"{name}.log").write_bytes(process.stdout + process.stderr)
            if not report.is_file():
                raise RuntimeError(f"Mutation {name} produced no JUnit")
            suites = ET.parse(report).getroot()
            failures = suites.findall(".//testcase/failure")
            errors = suites.findall(".//testcase/error")
            if process.returncode != 1 or not failures or errors:
                raise RuntimeError(f"Mutation {name} did not fail through a runnable assertion")
            results.append({"name": name, "command": command, "native_exit_code": process.returncode,
                            "assertion_failures": len(failures), "errors": len(errors),
                            "original_sha256": sha256(original).hexdigest()})
        finally:
            path.write_bytes(original)
            assert path.read_bytes() == original, f"Source not restored for {name}"
        results[-1]["restored_sha256"] = sha256(path.read_bytes()).hexdigest()
    (OUTPUT / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(results)} UI mutations caught; source restored byte-for-byte")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
