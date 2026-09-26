"""Thí nghiệm cho vé v3-10b (không gọi mô hình, không ghi vào artifacts/): gỡ chu trình sau gộp theo vị trí đại diện.

Lấy bản đồ danh tính của bản thử v3-10, tính lại `order_relation` của mọi cạnh bị đổi đầu mút bằng vị trí dạy của khái niệm
đại diện (như `JudgeIdentity` chọn đại diện), rồi mới gỡ chu trình bằng đúng hàm của A9. Dựng lại dãy học bằng BuildRoadmap
(luật thuần) vào kho nháp `tmp/thu-go-chu-trinh`, chấm Q6/Q7/Q7b so với dãy học của bản thử.

Chạy từ gốc repo:
  .venv/Scripts/python.exe scripts/doc-lo-trinh/thu_go_chu_trinh_sau_gop.py doc-1 33 artifacts/a8-gold/doc-1-10-12-vang.json
Kết quả 2026-09-26: doc-1 Q6 3/39 → 1/39; doc-2 (teaching v27) không đổi 3/61.
"""
import sys
from pathlib import Path

sys.path.insert(0, "src")
from doc2roadmap.application.use_cases.a8_score import score_roadmap_order  # noqa: E402
from doc2roadmap.application.use_cases.build_roadmap import BuildRoadmap  # noqa: E402
from doc2roadmap.domain.canonical import digest  # noqa: E402
from doc2roadmap.domain.global_validation import _feedback_edges, strongly_connected_components  # noqa: E402
from doc2roadmap.domain.identity import apply_identity_map  # noqa: E402
from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore  # noqa: E402

TRIAL = Path("artifacts/v3-identity-evaluation")
OUTPUT = Path("tmp/thu-go-chu-trinh")


class ScratchStore:
    """Đọc đầu vào từ kho chính, ghi mọi thứ vào kho nháp."""

    def __init__(self, base, output):
        self.base = base
        self.find_graph, self.save_graph = output.find_graph, output.save_graph

    def __getattr__(self, name):
        return getattr(self.base, name)


def merge_by_representative_position(edges, identity, position):
    merged, _ = apply_identity_map(edges, identity)
    heads = set(identity.values())
    recomputed = []
    for edge in merged:
        if edge["source"] in heads or edge["target"] in heads:
            source, target = position.get(edge["source"]), position.get(edge["target"])
            relation = "cùng chunk" if source == target else ("thuận" if source < target else "ngược")
            edge = {**edge, "order_relation": relation, "order_relation_before_merge": edge.get("order_relation")}
        recomputed.append(edge)
    nodes = {node for edge in recomputed for node in (edge["source"], edge["target"])}
    removed = []
    for component in sorted(sorted(c) for c in strongly_connected_components(nodes, recomputed) if len(c) > 1):
        members = set(component)
        internal = [edge for edge in recomputed if edge["source"] in members and edge["target"] in members]
        removed += _feedback_edges(sorted(members), internal)[0]
    dropped = {id(edge) for edge in removed}
    return [edge for edge in recomputed if id(edge) not in dropped], removed


def main(doc, teaching_version, gold_paths):
    base = JsonArtifactStore(Path("artifacts"))
    teaching = base.load_graph(doc, teaching_version)
    trial = JsonArtifactStore(TRIAL)
    identity = next(trial.load_graph(doc, v) for v in (1, 2) if trial.load_graph(doc, v).payload["stage"] == "identity")
    nodes = teaching.payload["nodes"]
    names = {n["node_id"]: n.get("name") for n in [*nodes, *teaching.payload.get("excluded_nodes", [])]}
    position = {n["node_id"]: (n.get("teaching_order_index") if n.get("teaching_order_index") is not None
                               else n.get("first_order_index", 0)) for n in nodes}
    edges, removed = merge_by_representative_position(teaching.payload["requires_edges"], identity.payload["identity_map"],
                                                      position)
    print("gỡ (bản thử):  ", [(names[e["source"]], names[e["target"]]) for e in identity.payload["identity_removed_edges"]])
    print("gỡ (tính lại): ", [(names[e["source"]], names[e["target"]], e["order_relation"]) for e in removed])
    payload = {**identity.payload, "requires_edges": edges, "identity_removed_edges": removed}
    config = {**identity.manifest["config"], "experiment": "v3-10b-order-by-representative"}
    store = ScratchStore(base, JsonArtifactStore(OUTPUT))
    artifact = store.save_graph(doc, digest(payload), digest(config), config, payload,
                                upstream_version=teaching.version, manifest_fields={"stage": "identity"})
    roadmap, _ = BuildRoadmap(store).execute(doc, upstream=artifact)
    trial_stages = next(TRIAL / "graph" / doc / f"v{v}" / "graph.json" for v in (2, 1)
                        if trial.load_graph(doc, v).payload["stage"] == "stages")
    for label, path in (("bản thử", trial_stages), ("tính lại", Path(roadmap.path) / "graph.json")):
        report = score_roadmap_order(path, gold_paths)
        print(f"{label:<9} Q6 {report['gold_order']['violated']}/{report['gold_edge_count']}"
              f"  Q7 {report['target_coverage']['mean_coverage']:.2%}  Q7b {report['target_precision']['mean_precision']:.2%}")
        for row in report["violations"]:
            print(f"          {row['prerequisite_name']} → {row['target_name']} "
                  f"(vị trí {row['prerequisite_stage']} → {row['target_stage']})")


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]), [Path(p) for p in sys.argv[3:]])
