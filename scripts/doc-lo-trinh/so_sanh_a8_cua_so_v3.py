"""Bảng A8 cửa sổ mới so đồ thị cuối luồng cũ sau rút gọn; không gọi LLM."""
import sys
from pathlib import Path

sys.path.insert(0, "src")
from thu_cua_so_rong_a8 import fmt, grade, reduced  # noqa: E402
from doc2roadmap.application.use_cases.a8_score import load_gold, merge_gold  # noqa: E402
from doc2roadmap.domain.global_validation import validate_graph_rules  # noqa: E402
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore  # noqa: E402


CASES = (("doc-1", "doc-1-10-12-vang.json"), ("doc-2", "doc-2-98-115-vang.json"))


def hard_pairs(edges, identity, targets):
    return {(identity.get(edge["source"], edge["source"]), identity.get(edge["target"], edge["target"]))
            for edge in edges if not edge.get("soft")
            and identity.get(edge["source"], edge["source"]) in targets
            and identity.get(edge["target"], edge["target"]) in targets}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    base = JsonArtifactStore(Path("artifacts"))
    evaluation = JsonArtifactStore(Path("artifacts/v3-r12-window-evaluation"))
    old_store = JsonArtifactStore(Path("artifacts/v3-05b-a9v10-evaluation"))
    for doc_id, gold_name in CASES:
        main = evaluation.load_graph(doc_id, 1).payload
        pilot = evaluation.load_graph(doc_id, 2).payload
        old = old_store.load_graph(doc_id, 6).payload
        gold = load_gold(Path("artifacts/a8-gold") / gold_name)
        identity = main.get("identity_map", {})
        present = {node["node_id"] for node in main["nodes"]}
        old_present = {node["node_id"] for node in [*old["nodes"], *old.get("mentioned_nodes", [])]}
        structural = validate_graph_rules(main["nodes"], [*main["main_edges"], *pilot["secondary_edges"]],
                                          [], type_aliases={})
        new_final = reduced(structural["requires_edges"])
        old_final = reduced(old["requires_edges"])
        print(f"# {doc_id} (hai đầu thuộc chương vàng)")
        for name, edges, mapping, node_set in (
            ("đồ thị cuối luồng cũ, rút gọn", old_final, old.get("identity_map", {}), old_present),
            ("pass chính mới", main["main_edges"], identity, present),
            ("chính + pilot qua luật A9, rút gọn", new_final, identity, present),
        ):
            direct, closure = grade(edges, gold, mapping, node_set)
            print(f"  {name:<42} trực tiếp {fmt(direct):<16} bao đóng {fmt(closure)}")
        targets = {identity.get(node_id, node_id) for node_id in gold["targets"]} & present
        new_pairs = hard_pairs(new_final, identity, targets)
        old_pairs = hard_pairs(old_final, old.get("identity_map", {}), targets)
        gold_pairs = {(identity.get(a, a), identity.get(b, b)) for a, b in merge_gold([gold], mode="union")}
        names = {node["node_id"]: node["name"] for node in main["nodes"]}
        print(f"  Cạnh cứng mới trong phạm vi vàng: {len(new_pairs - old_pairs)}")
        for source, target in sorted(new_pairs - old_pairs):
            print(f"    {'VÀNG' if (source, target) in gold_pairs else 'CHƯA VÀNG'}: "
                  f"{names.get(source, source)} → {names.get(target, target)} [{source} → {target}]")


if __name__ == "__main__":
    main()
