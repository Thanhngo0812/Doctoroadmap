"""T-01b: bảng nguồn gốc artifact mới (đường dẫn, version, stage, SHA-256 manifest và payload, commit mã). Chỉ in số và hash. 0 USD."""
import hashlib, json
from pathlib import Path
A, B, C = "2c93c5aa94951834468d3caf0242a522734951a9", "36b81ff2bb5cfc18fffc4fca5d13cdc3beca6a71", "8655791735cca7c4c0db237327437fc98675f6aa"
NEW = [("graph", "d01-t01", range(1, 12), A), ("graph", "d01-t02", range(1, 12), A),
       ("canonical", "d01-t01", [2], B), ("graph", "d01-t01", range(12, 20), B),
       ("canonical", "d01-t02", [2], B), ("graph", "d01-t02", range(12, 20), B),
       ("chunks", "d01-t02", [3], C), ("canonical", "d01-t02", [3], C), ("graph", "d01-t02", range(20, 28), C)]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()  # noqa: E731
rows = []
for kind, doc, versions, commit in NEW:
    for v in versions:
        d = Path("artifacts", kind, doc, f"v{v}")
        m = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
        rows.append({"path": f"artifacts/{kind}/{doc}/v{v}", "stage": m.get("stage") or m.get("artifact_type"),
                     "manifest_sha256": sha(d / "manifest.json"),
                     "payloads": {f.name: sha(f) for f in sorted(d.iterdir()) if f.suffix == ".json" and f.name != "manifest.json"},
                     "commit": commit})
Path("scripts/t01/nguon-goc-t01b.json").write_text(json.dumps({"new": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(rows), "artifact")
