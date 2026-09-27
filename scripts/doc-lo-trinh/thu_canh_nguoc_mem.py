"""Thí nghiệm (không gọi mô hình, không ghi vào artifacts/): cạnh ngược thứ tự sách không ép dãy học.

Cạnh `requires` mà nguồn được dạy SAU đích (theo `teaching_order_index`) được chuyển sang `soft_backward_edges`, không còn ràng buộc
dãy học; cạnh còn lại giữ nguyên. Dựng lại dãy học bằng BuildRoadmap (luật thuần) vào kho nháp `tmp/thu-canh-nguoc`, rồi chấm Q6/Q7/Q7b
và in số cạnh bị chuyển. Đầu vào mặc định: artifact danh tính của kho thử vé 05/14/16.

Chạy từ gốc repo:
  .venv/Scripts/python.exe scripts/doc-lo-trinh/thu_canh_nguoc_mem.py doc-1 artifacts/a8-gold/doc-1-10-12-vang.json
"""
import sys
from pathlib import Path

sys.path.insert(0, "src")
from doc2roadmap.application.use_cases.a8_score import score_roadmap_order  # noqa: E402
from doc2roadmap.application.use_cases.build_roadmap import BuildRoadmap  # noqa: E402
from doc2roadmap.domain.canonical import digest  # noqa: E402
from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore  # noqa: E402

TRIAL = Path("artifacts/v3-region-anchor-evaluation")
OUTPUT = Path("tmp/thu-canh-nguoc")


class ScratchStore:
    """Đọc đầu vào từ kho chính (chunks, canonical), ghi mọi thứ vào kho nháp."""

    def __init__(self, base, output):
        self.base = base
        self.find_graph, self.save_graph = output.find_graph, output.save_graph

    def __getattr__(self, name):
        return getattr(self.base, name)


def latest(store, doc, stage):
    version = max(v for v in range(1, 50) if (TRIAL / "graph" / doc / f"v{v}").exists()
                  and store.load_graph(doc, v).payload.get("stage") == stage)
    return store.load_graph(doc, version)


def main(doc, gold_paths):
    trial = JsonArtifactStore(TRIAL)
    upstream = latest(trial, doc, "identity")
    nodes = {n["node_id"]: n for n in upstream.payload["nodes"]}

    def position(node_id):
        return nodes.get(node_id, {}).get("teaching_order_index")

    keep, soft = [], []
    for edge in upstream.payload["requires_edges"]:
        source, target = position(edge["source"]), position(edge["target"])
        (soft if source is not None and target is not None and source > target else keep).append(edge)
    payload = {**upstream.payload, "requires_edges": keep, "soft_backward_edges": soft}
    config = {**upstream.manifest["config"], "experiment": "backward-edges-soft-v1"}
    store = ScratchStore(JsonArtifactStore(Path("artifacts")), JsonArtifactStore(OUTPUT))
    artifact = store.save_graph(doc, digest(payload), digest(config), config, payload,
                                upstream_version=upstream.version, manifest_fields={"stage": "identity"})
    roadmap, _ = BuildRoadmap(store).execute(doc, upstream=artifact)
    base_stages = latest(trial, doc, "stages")
    print(f"{doc}: chuyển {len(soft)}/{len(soft) + len(keep)} cạnh ngược thành mềm; dãy mới ở {roadmap.path}")
    for label, path in (("trước", base_stages.path / "graph.json"), ("cạnh ngược mềm", Path(roadmap.path) / "graph.json")):
        if not gold_paths:
            break
        report = score_roadmap_order(path, gold_paths)
        print(f"  {label:<15} Q6 {report['gold_order']['violated']}/{report['gold_edge_count']}"
              f"  Q7 {report['target_coverage']['mean_coverage']:.2%}  Q7b {report['target_precision']['mean_precision']:.2%}")
        for row in report["violations"]:
            print(f"      {row['prerequisite_name']} → {row['target_name']}")


if __name__ == "__main__":
    main(sys.argv[1], [Path(p) for p in sys.argv[2:]])
