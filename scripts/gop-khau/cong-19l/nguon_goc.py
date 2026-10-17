"""Cổng 19l: bảng nguồn gốc artifact mới (đường dẫn, version, SHA-256 manifest và payload, commit) và artifact thượng nguồn tái dùng. 0 USD."""
import hashlib, json
from pathlib import Path
COMMIT = "f4871fd83aa8169d771b8cbfe40d0a61d7baf56a"
WORKSPACE = "workspace d03f9e3 + bản vá src sha256 7d40e166…; tái lập trùng khít nội dung từ " + COMMIT[:12]
NEW = {("canonical", "doc-1"): [5], ("canonical", "nhap-mon-ml"): [8], ("canonical", "naive-bayes"): [8], ("canonical", "doc-6"): [2],
       ("canonical", "xstk-ch3-1"): [8], ("canonical", "doc-4"): [2],
       ("graph", "doc-1"): list(range(46, 54)), ("graph", "xstk-ch3-1"): list(range(49, 57)), ("graph", "doc-4"): list(range(16, 24))}
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
rows, upstream = [], {}
for (kind, doc), versions in NEW.items():
    for v in versions:
        d = Path("artifacts", kind, doc, f"v{v}")
        payload = next(f for f in d.iterdir() if f.name != "manifest.json" and f.suffix == ".json")
        m = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
        rows.append({"path": str(d).replace("\\", "/"), "version": v, "stage": m.get("stage") or m.get("artifact_type"),
                     "manifest_sha256": sha(d / "manifest.json"), "payload": payload.name, "payload_sha256": sha(payload),
                     "commit": WORKSPACE if (kind, doc, v) == ("canonical", "doc-1", 5) else COMMIT, "created_at": m.get("created_at")})
        cfg = m.get("config", {})
        for key in ("chunks_version", "candidates_version", "extraction_version", "retrieval_version", "parse_tree_version", "role_chunks_version"):
            if cfg.get(key) is not None:
                upstream.setdefault(doc, {})[key] = cfg[key]
Path("tmp/v4-19l/nguon-goc.json").write_text(json.dumps({"new": rows, "upstream_reused": upstream}, ensure_ascii=False, indent=1), encoding="utf-8")
for r in rows: print(r["path"], r["stage"], r["manifest_sha256"][:12], r["payload_sha256"][:12], r["commit"][:12])
print(json.dumps(upstream, ensure_ascii=False))
