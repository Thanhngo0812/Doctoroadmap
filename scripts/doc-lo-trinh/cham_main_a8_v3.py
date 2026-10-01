"""Chấm A8 main-only cũ/mới và đếm cặp pass phụ trong hai chương vàng; không gọi mô hình."""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

from doc2roadmap.application.use_cases.a8_score import load_gold, merge_gold
from doc2roadmap.application.use_cases.build_secondary_edges import BuildSecondaryEdges
from doc2roadmap.domain.gold_scoring import score_edges, transitive_closure
from doc2roadmap.domain.global_validation import validate_graph_rules
from doc2roadmap.domain.sequence import transitive_reduction
from doc2roadmap.domain.secondary import select_secondary_pairs
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore

CASES = (("doc-1", 4, 42, "doc-1-10-12-vang.json"),
         ("doc-2", 4, 34, "doc-2-98-115-vang.json"))


def grade(payload, gold, identity, present):
    representative = lambda node_id: identity.get(node_id, node_id)
    targets = {representative(node_id) for node_id in gold["targets"]} & present
    gold_edges = {(representative(a), representative(b)) for a, b in merge_gold([gold], mode="union")}
    gold_edges = {(a, b) for a, b in gold_edges if a != b and a in targets and b in targets}
    predicted = {(representative(edge["source"]), representative(edge["target"]))
                 for edge in payload["main_edges"] if not edge.get("soft")}
    predicted = {(a, b) for a, b in predicted if a != b and a in targets and b in targets}
    direct = score_edges(predicted, gold_edges)
    closure = score_edges(transitive_closure(predicted), transitive_closure(gold_edges))
    return {"gold_targets_present": len(targets), "direct": direct, "closure": closure,
            "gold_direct_reached_by_machine_path": len(gold_edges & transitive_closure(predicted)),
            "hard_main_edges_total": sum(not edge.get("soft") for edge in payload["main_edges"]),
            "soft_main_edges_total": sum(bool(edge.get("soft")) for edge in payload["main_edges"])}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    store = JsonArtifactStore(Path("artifacts"))
    for doc_id, old_version, new_version, gold_file in CASES:
        gold = load_gold(Path("artifacts/a8-gold") / gold_file)
        old = store.load_graph(doc_id, old_version).payload
        main_artifact = store.load_graph(doc_id, new_version)
        new = main_artifact.payload
        identity = new.get("identity_map", {})
        present = {node["node_id"] for node in new["nodes"]}
        targets = {identity.get(node_id, node_id) for node_id in gold["targets"]}
        askable, _ = select_secondary_pairs(new["nodes"], new["suspected_pairs"],
                                            new["pair_cluster_ledger"], new["main_edges"],
                                            route=new["routing"]["route"])
        pilot = [pair for pair in askable if pair["left"] in targets and pair["right"] in targets]
        pilot_artifact = SimpleNamespace(payload={**new, "suspected_pairs": pilot},
                                         manifest=main_artifact.manifest, version=main_artifact.version)
        pilot_plan = BuildSecondaryEdges(store, SimpleNamespace(model_id="gemini-3.1-flash-lite"),
                                         generation=main_artifact.manifest["config"]["generation"])
        pilot_estimate = pilot_plan.plan(doc_id, upstream=pilot_artifact).to_dict()
        pilot_result = JsonArtifactStore(Path("artifacts/v3-r12-secondary-pilot")).load_graph(doc_id, 1).payload
        with_pilot = {**new, "main_edges": [*new["main_edges"], *pilot_result["secondary_edges"]]}
        structural = validate_graph_rules(new["nodes"], with_pilot["main_edges"], [], type_aliases={})
        direct_after_a9 = transitive_reduction(structural["requires_edges"])
        with_reduction = {**new, "main_edges": [{"source": source, "target": target}
                                                 for source, target in direct_after_a9]}
        representative = lambda node_id: identity.get(node_id, node_id)
        gold_direct = {(representative(a), representative(b)) for a, b in merge_gold([gold], mode="union")}
        gold_path = transitive_closure(gold_direct)
        pilot_hard = {(representative(edge["source"]), representative(edge["target"]))
                      for edge in pilot_result["secondary_edges"] if not edge.get("soft")}
        names = {node["node_id"]: node["name"] for node in new["nodes"]}
        for edge in pilot_result["secondary_edges"]:
            pair = (representative(edge["source"]), representative(edge["target"]))
            if edge.get("soft") or pair in gold_path:
                continue
            print(json.dumps({"doc_id": doc_id, "review_pair": [names.get(edge["source"]), names.get(edge["target"])],
                              "opposes_gold_path": pair[::-1] in gold_path,
                              "quote": edge.get("quote"), "reason": edge.get("reason")}, ensure_ascii=False))
        print(json.dumps({"doc_id": doc_id, "old_main": grade(old, gold, identity, present),
                          "new_main": grade(new, gold, identity, present),
                          "new_main_plus_pilot": grade(with_pilot, gold, identity, present),
                          "pilot_after_a9_reduction": grade(with_reduction, gold, identity, present),
                          "pilot_secondary_edges": len(pilot_result["secondary_edges"]),
                          "pilot_hard_direct_gold": len(pilot_hard & gold_direct),
                          "pilot_hard_gold_path": len(pilot_hard & gold_path),
                          "pilot_hard_opposite_gold_path": len({(b, a) for a, b in pilot_hard} & gold_path),
                          "secondary_askable_all": len(askable), "secondary_pairs_within_gold_targets": len(pilot),
                          "pilot_calls_estimate": pilot_estimate["calls_estimate"],
                          "pilot_usd_estimate": pilot_estimate["usd_estimate"],
                          }, ensure_ascii=False))


if __name__ == "__main__":
    main()
