"""Vé 05b: bảng nguồn gốc artifact mới (đường dẫn, version, SHA-256 manifest và payload, commit mã). 0 USD."""
import hashlib, json
from pathlib import Path
COMMIT = "36b81ff2bb5cfc18fffc4fca5d13cdc3beca6a71"
NEW = {("chunks", "xstk-ch3-1"): [6, 7], ("canonical", "xstk-ch3-1"): [9], ("graph", "xstk-ch3-1"): list(range(57, 65)),
       ("chunks", "doc-4"): [7, 8]}
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()  # noqa: E731
rows = []
for (kind, doc), versions in NEW.items():
    for v in versions:
        d = Path("artifacts", kind, doc, f"v{v}")
        m = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
        payloads = sorted(f for f in d.iterdir() if f.name != "manifest.json" and f.suffix == ".json")
        rows.append({"path": str(d).replace("\\", "/"), "version": v, "stage": m.get("stage") or m.get("artifact_type"),
                     "manifest_sha256": sha(d / "manifest.json"),
                     "payloads": {f.name: sha(f) for f in payloads}, "commit": COMMIT, "created_at": m.get("created_at")})
Path("scripts/a2-de-cuong/nguon-goc-05b.json").write_text(json.dumps({"new": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
for r in rows:
    print(r["path"], r["stage"], r["manifest_sha256"][:12], {k: v[:12] for k, v in r["payloads"].items()})
