"""Claude's independent mutations for W-17.1 React. Each mutant edits Admin.tsx, runs only Admin.test.tsx,
records native exit and failed assertions, then restores the original bytes and checks SHA-256 before the next."""
import hashlib, json, re, subprocess, sys
from pathlib import Path

WT = Path(r"C:/Users/ngoco/Desktop/Doctoroadmap/tmp/coord-r13-acceptance-20261029")
SRC = WT / "src/web/frontend/src/Admin.tsx"
OUT = WT / "report/coord-r13-evidence-2026-10-29/mutations"
OUT.mkdir(parents=True, exist_ok=True)

MUTANTS = [
    ("thua-truong", "if(limit!==row.build_monthly_max)changes.build_monthly_max=limit;", "changes.build_monthly_max=limit;", 1),
    ("bo-xac-nhan", "if(changes.role||changes.status)setConfirm(changes);else void send(changes);", "void send(changes);", 1),
    ("null-la-dau-tien", "disabled={row.is_first_admin===true}", "disabled={row.is_first_admin!==false}", 2),
    ("han-muc-0", "Number(quota)<1", "Number(quota)<0", 1),
    ("lo-meta", "<td>{row.ip||'—'}</td>", "<td>{row.ip||'—'}{JSON.stringify(row)}</td>", 1),
    ("giu-offset", "next.set('offset','0');setFieldError(null);apply(next);",
     "next.set('offset',params.get('offset')||'0');setFieldError(null);apply(next);", 1),
    ("mui-gio", "new Date(value+'+07:00')", "new Date(value+'Z')", 1),
    ("patch-403-giu-du-lieu", "if(cause instanceof ApiError&&cause.code==='forbidden'){",
     "if(cause instanceof ApiError&&cause.code==='forbidden'&&false){", 1),
]

original = SRC.read_bytes()
original_sha = hashlib.sha256(original).hexdigest()
only = set(sys.argv[1:])
results = []
for name, old, new, expected in MUTANTS:
    if only and name not in only:
        continue
    text = original.decode("utf-8")
    assert text.count(old) == expected, (name, text.count(old))
    try:
        SRC.write_bytes(text.replace(old, new).encode("utf-8"))
        xml = OUT / f"{name}.xml"
        proc = subprocess.run(
            ["npx.cmd", "vitest", "run", "src/Admin.test.tsx", "--pool=threads", "--maxWorkers=1",
             "--reporter=default", "--reporter=junit", f"--outputFile={xml}"],
            cwd=WT / "src/web/frontend", capture_output=True, text=True, encoding="utf-8", errors="replace")
        (OUT / f"{name}.log").write_text(proc.stdout + proc.stderr, encoding="utf-8")
        body = xml.read_text(encoding="utf-8") if xml.exists() else ""
        failed = re.findall(r'<testcase[^>]*name="([^"]+)"[^>]*>\s*<failure', body)
        errors = body.count("<error")
        results.append({"mutant": name, "native": proc.returncode, "failed_cases": failed, "error_tags": errors,
                        "verdict": "bat" if proc.returncode != 0 and failed else "song-sot"})
    finally:
        SRC.write_bytes(original)
        assert hashlib.sha256(SRC.read_bytes()).hexdigest() == original_sha
    print(json.dumps(results[-1], ensure_ascii=False), flush=True)

(OUT / "summary.json").write_text(json.dumps({"source_sha256": original_sha, "results": results}, ensure_ascii=False, indent=1),
                                  encoding="utf-8")
