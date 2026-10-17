"""Kiểm thuần B/C vé 10b trên phán của bản thử cũ; không gọi mô hình, không duyệt gộp mới."""
from pathlib import Path

from evaluation_runtime import EvaluationStore, TEACHING
from doc2roadmap.application.use_cases.a8_score import score_roadmap_order
from doc2roadmap.application.use_cases.build_roadmap import BuildRoadmap
from doc2roadmap.domain.canonical import digest
from doc2roadmap.domain.identity import identity_map, merge_and_break_cycles, merge_identity_nodes
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore


def main():
    base = JsonArtifactStore(Path("artifacts"))
    trial = JsonArtifactStore(Path("artifacts/v3-identity-evaluation"))
    output = JsonArtifactStore(Path("tmp/v3-10b-pure"))
    store = EvaluationStore(base, output)
    report = {}
    for doc, version in TEACHING.items():
        teaching, old = base.load_graph(doc, version), trial.load_graph(doc, 1)
        nodes = teaching.payload["nodes"]
        position = {n["node_id"]: n["teaching_order_index"] if n.get("teaching_order_index") is not None
                    else n.get("first_order_index", 0) for n in nodes}
        mapping, opened = identity_map(old.payload["identity_log"], position,
            taught={n["node_id"] for n in nodes if n.get("teaching_status") == "taught"})
        edges, removed = merge_and_break_cycles(teaching.payload["requires_edges"], mapping, position)
        payload = {**old.payload, "nodes": merge_identity_nodes(nodes, mapping), "identity_map": mapping,
                   "merged_nodes": [{**n, "merged_into": mapping[n["node_id"]]} for n in nodes if n["node_id"] in mapping],
                   "identity_open_groups": opened, "requires_edges": edges, "identity_removed_edges": removed}
        config = {**old.manifest["config"], "experiment": "10b-pure-B-C-only"}
        artifact = output.save_graph(doc, digest(teaching.payload), digest(config), config, payload,
                                      upstream_version=version, manifest_fields={"stage": "identity"})
        roadmap, _ = BuildRoadmap(store).execute(doc, upstream=artifact)
        row = {"stages_path": str(roadmap.path), "removed_edges": removed, "merged_nodes": len(mapping)}
        if doc in ("doc-1", "doc-2"):
            gold = Path("artifacts/a8-gold/" + ("doc-1-10-12-vang.json" if doc == "doc-1" else "doc-2-98-115-vang.json"))
            score = score_roadmap_order(Path(roadmap.path) / "graph.json", [gold])
            row["score"] = score
            assert score["gold_order"]["violated"] <= (1 if doc == "doc-1" else 3), score["gold_order"]
            print(doc, "Q6", score["gold_order"], "Q7", score["target_coverage"]["mean_coverage"],
                  "Q7b", score["target_precision"]["mean_precision"], flush=True)
        else:
            database = next(n for n in payload["nodes"] if n["name"] == "Cơ sở dữ liệu")
            assert database["teaching_status"] == "taught" and "CSDL" in {a["name"] for a in database["aliases"]}
            print(doc, "đại diện Cơ sở dữ liệu taught, alias CSDL", flush=True)
        report[doc] = row
    output._write(output.root / "summary.json", report)


if __name__ == "__main__":
    main()
