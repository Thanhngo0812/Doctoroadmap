"""Vé 19j: thí nghiệm pass chính A8 trên upstream cố định của 17i — đo nhiễu (15) và chạy song song (14).

Mỗi lượt chép kho riêng 17i của một tài liệu sang thư mục mới, chỉ giữ graph tới artifact `mentions` đã chọn (không checkpoint), nên pass
chính chạy lại từ đầu mà đầu vào thượng nguồn y hệt lượt cuối 17i. Sau pass chính chạy tiếp pass phụ ML, kiểm đồ thị, nhãn khái niệm và
dãy học như sản phẩm (bỏ đặt tên module), rồi chấm E4 bằng `cham_gop.score`.

Biến thể:
- `noi`: như sản phẩm — các phiên trong một chương chạy nối tiếp, phiên sau nhận cạnh của phiên trước (`previous_edges_in_chapter`);
- `song`: mọi phiên chạy một đợt, nên không phiên nào nhận cạnh của phiên trước. Chỉ vá `BuildMainEdges._waves` trong tiến trình này.

`--xao=<hạt>`: xáo thứ tự `mentioned_elsewhere` của từng phiên (hạt + id phiên), một nhiễu đầu vào không đổi nghĩa. Lượt chạy lại không xáo
ra y hệt từng byte lượt 17i (128/128 lời gọi, Vertex flash-lite, temperature 0), nên nhiễu E4 chỉ đo được bằng nhiễu đầu vào.

Không sửa mã sản phẩm, không đụng kho chính. Mặc định là dry-run (0 USD): in số phiên và ước USD của pass chính.
Chạy từ gốc repo:
  .venv/Scripts/python.exe scripts/gop-khau/thu_pass_chinh.py <doc> <noi|song> <nhãn> [--chi] [--xao=<hạt>] [--kho=tmp/v4-17i/artifacts]
"""
import json
import os
import random
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
OUT = ROOT / "tmp/v4-19j"
# Artifact mentions mà lượt cuối 17i dùng làm đầu vào pass chính
MENTIONS = {"doc-1": 10, "xstk-ch3-1": 10, "doc-4": 2}
PRICE = (0.25, 1.5)  # USD / triệu token vào, ra (flash-lite)


def copy_store(source, target, doc, mentions_version):
    if target.exists():
        raise SystemExit(f"{target} đã có; đổi nhãn lượt")
    for kind in ("candidates", "canonical", "chunks", "parse_tree", "retrieval"):
        if (source / kind / doc).is_dir():
            shutil.copytree(source / kind / doc, target / kind / doc)
    for version in range(1, mentions_version + 1):
        shutil.copytree(source / "graph" / doc / f"v{version}", target / "graph" / doc / f"v{version}")
    for path in source.iterdir():
        if path.is_file():
            shutil.copy2(path, target / path.name)


def usd(stats):
    return (stats.get("input_tokens") or 0) * PRICE[0] / 1e6 + (stats.get("output_tokens") or 0) * PRICE[1] / 1e6


def main(argv):
    flags = {a.split("=")[0]: (a.split("=", 1)[1] if "=" in a else True) for a in argv if a.startswith("--")}
    doc, variant, tag = [a for a in argv if not a.startswith("--")]
    if variant not in ("noi", "song"):
        raise SystemExit("biến thể phải là noi hoặc song")
    spend = bool(flags.get("--chi"))
    source = ROOT / flags.get("--kho", "tmp/v4-17i/artifacts")
    target = OUT / "kho" / f"{doc}-{variant}-{tag}"
    copy_store(source, target, doc, MENTIONS[doc])
    os.environ["DOC2ROADMAP_ARTIFACT_DIR"] = str(target)

    from doc2roadmap.composition import build_learning_graph
    from doc2roadmap.application.use_cases.build_main_edges import BuildMainEdges
    if variant == "song":
        BuildMainEdges._waves = staticmethod(lambda sessions: [sessions] if sessions else [])
    seed = flags.get("--xao")
    if seed is not None:
        original = BuildMainEdges._input

        def shuffled(self, session, *args):
            data = original(self, session, *args)
            random.Random(f"{seed}:{session['session_id']}").shuffle(data["mentioned_elsewhere"])
            return data
        BuildMainEdges._input = shuffled
    graph, settings = build_learning_graph(allow_spend=spend, upstream_chain="gop")
    store = graph.main_edges.store
    mentions = store.load_graph(doc, MENTIONS[doc])
    if not spend:
        plan = graph.main_edges.plan(doc, upstream=mentions).to_dict()
        shutil.rmtree(target)
        print(json.dumps({"doc": doc, "variant": variant, "dry_run": True, "model": settings.roadmap_model_id,
                          "transport": settings.llm_transport, "main_plan": plan}, ensure_ascii=False, indent=1))
        return
    rows, artifact = [], mentions
    for name, use_case in (("main_edges", graph.main_edges), ("secondary_edges", graph.secondary_edges),
                           ("validated", graph.validator), ("concept_labels", graph.concept_labels),
                           ("stages", graph.roadmap)):
        started = time.perf_counter()
        artifact, reused = use_case.execute(doc, upstream=artifact)
        stats = artifact.manifest.get("stats", {})
        rows.append({"stage": name, "version": artifact.version, "reused": reused,
                     "seconds": round(time.perf_counter() - started, 1), "model_calls": stats.get("model_calls"),
                     "usd": round(usd(stats), 4)})
        print(json.dumps(rows[-1], ensure_ascii=False), flush=True)
    from cham_gop import score
    result = {"doc": doc, "variant": variant, "tag": tag, "store": str(target.relative_to(ROOT)),
              "mentions_version": MENTIONS[doc], "xao": seed, "model": settings.roadmap_model_id, "transport": settings.llm_transport,
              "stages": rows, "usd": round(sum(row["usd"] for row in rows), 4),
              "e4": score(doc, target, artifact.version)}
    (OUT / "ket-qua").mkdir(parents=True, exist_ok=True)
    (OUT / "ket-qua" / f"{doc}-{variant}-{tag}.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(result["e4"], ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1:])
