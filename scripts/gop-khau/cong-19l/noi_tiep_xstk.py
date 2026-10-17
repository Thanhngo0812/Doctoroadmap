"""Cổng 19l, chẩn đoán: chạy lại pass chính xstk ở chế độ NỐI TIẾP trên đúng canonical/mentions của cổng, để tách ảnh hưởng của chạy song
song khỏi ảnh hưởng của canonical mới. Mã từ worktree sạch tmp/v4-19l/ma. Chép kho riêng (không đụng kho chính), rồi chạy pass chính → pass
phụ ML → kiểm đồ thị → nhãn khái niệm → dãy học và chấm E4 như 19j. Mặc định dry-run; --chi để chi tiền.
Chạy từ gốc repo: .venv/Scripts/python.exe scripts/gop-khau/cong-19l/noi_tiep_xstk.py <mentions_version> [--chi]"""
import json
import os
import shutil
import sys
import time
from pathlib import Path

ROOT = Path.cwd()
WT = ROOT / "tmp/v4-19l/ma"
sys.path.insert(0, str(WT / "src"))
sys.path.insert(0, str(WT / "scripts/gop-khau"))
import doc2roadmap  # noqa: E402
assert Path(doc2roadmap.__file__).resolve().is_relative_to(WT.resolve()), doc2roadmap.__file__

DOC, MAIN = "xstk-ch3-1", ROOT / "artifacts"
mentions_version, spend = int(sys.argv[1]), "--chi" in sys.argv
KHO = ROOT / "tmp/v4-19l/noi-tiep/kho"
if KHO.exists():
    shutil.rmtree(KHO)
for kind in ("candidates", "canonical", "chunks", "parse_tree", "retrieval"):
    shutil.copytree(MAIN / kind / DOC, KHO / kind / DOC)
upstream = json.loads((MAIN / "graph" / DOC / f"v{mentions_version}" / "manifest.json").read_text(encoding="utf-8"))["upstream_version"]
for version in (upstream, mentions_version):
    shutil.copytree(MAIN / "graph" / DOC / f"v{version}", KHO / "graph" / DOC / f"v{version}")
os.environ["DOC2ROADMAP_ARTIFACT_DIR"] = str(KHO)
os.environ["DOC2ROADMAP_ROADMAP_MAIN_PARALLEL"] = "false"
from doc2roadmap.composition import build_learning_graph  # noqa: E402
graph, settings = build_learning_graph(allow_spend=spend, upstream_chain="gop")
assert graph.main_edges.parallel_sessions is False
mentions = graph.main_edges.store.load_graph(DOC, mentions_version)
assert mentions.payload["stage"] == "mentions", mentions.payload["stage"]
if not spend:
    print(json.dumps(graph.main_edges.plan(DOC, upstream=mentions).to_dict(), ensure_ascii=False, indent=1))
    shutil.rmtree(KHO)
    raise SystemExit(0)
rows, artifact = [], mentions
for name, use_case in (("main_edges", graph.main_edges), ("secondary_edges", graph.secondary_edges), ("validated", graph.validator),
                       ("concept_labels", graph.concept_labels), ("stages", graph.roadmap)):
    started = time.perf_counter()
    artifact, reused = use_case.execute(DOC, upstream=artifact)
    stats = artifact.manifest.get("stats", {})
    rows.append({"stage": name, "version": artifact.version, "seconds": round(time.perf_counter() - started, 1),
                 "model_calls": stats.get("model_calls"), "main_edge_count": stats.get("main_edge_count"),
                 "usd": (artifact.manifest.get("cost_summary") or artifact.payload.get("cost_summary") or {}).get("usd")})
    print(json.dumps(rows[-1], ensure_ascii=False), flush=True)
from cham_gop import score  # noqa: E402
result = {"doc": DOC, "mode": "noi", "commit": "f4871fd83aa8169d771b8cbfe40d0a61d7baf56a", "mentions_version": mentions_version,
          "stages": rows, "e4": score(DOC, KHO, artifact.version)}
(ROOT / "tmp/v4-19l/noi-tiep/ket-qua.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(result["e4"], ensure_ascii=False))
