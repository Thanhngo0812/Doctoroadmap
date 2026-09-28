"""Phân rã Q6/Q7 của một lộ trình `stages` theo nguyên nhân — công cụ chẩn đoán của reviewer, không thay điểm chính thức.

In (1) từng cạnh vàng chưa được bảo đảm, kèm trạng thái dạy, vùng nhắc và câu căn cứ của đầu nằm ngoài dãy học, để người đọc phán cạnh
rơi vì thiết kế v3 (bài tập, chỉ-nhắc) hay vì lỗi; (2) Q7 chính thức và Q7 chỉ trên các đích nằm trong dãy học; (3) cạnh vàng có hai
đầu trong dãy học mà máy không có đường đi — phần thiếu hồi tưởng của A8. Mẫu số chính thức của Q6 giữ nguyên toàn bộ bộ vàng.
Không gọi mô hình. Chạy từ gốc repo:
  .venv/Scripts/python.exe scripts/doc-lo-trinh/phan_ra_pham_vi_vang.py <doc> <tệp vàng> [--goc=<kho>] [--phien-ban=<v>]
ví dụ:  ... phan_ra_pham_vi_vang.py doc-2 doc-2-98-115-vang.json --goc=artifacts/v3-05b-a9v10-evaluation --phien-ban=6
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, "src")
from doc2roadmap.application.use_cases.a8_score import load_gold, merge_gold, score_roadmap_order  # noqa: E402
from doc2roadmap.domain.gold_scoring import target_coverage, transitive_closure  # noqa: E402

NODE_LISTS = ("nodes", "excluded_nodes", "merged_nodes", "mentioned_nodes")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    doc, gold_name = args[0], args[1]
    root = Path(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--goc=")), "artifacts"))
    version = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--phien-ban=")), None)
    graph_dir = root / "graph" / doc
    if version is None:
        version = max(int(p.name[1:]) for p in graph_dir.glob("v*")
                      if json.loads((p / "manifest.json").read_text(encoding="utf-8")).get("stage") == "stages")
    graph_path = graph_dir / f"v{version}" / "graph.json"
    gold_path = Path("artifacts/a8-gold") / gold_name
    payload = json.loads(graph_path.read_text(encoding="utf-8"))
    info = {node["node_id"]: (key, node) for key in NODE_LISTS for node in payload.get(key, [])}
    name = lambda node_id: info.get(node_id, (None, {}))[1].get("name", node_id)  # noqa: E731
    sequence = set(payload["sequence"])
    identity = payload.get("identity_map", {})

    score = score_roadmap_order(graph_path, [gold_path])
    order = score["gold_order"]
    print(f"# {doc} v{version}: {score['gold_edge_count']} cạnh vàng (sau bản đồ danh tính; "
          f"{score['identity_dropped_gold_edges']} cạnh thành tự nối) — giữ {order['respected']}, ngược {order['violated']}, "
          f"cùng vị trí {order['same_stage']}, ngoài phạm vi {order['out_of_scope']}; Q6 {order['learning_order_error']:.3f}")
    print("\n## Cạnh vàng chưa được bảo đảm")
    outside = {}
    for row in score["violations"]:
        print(f"  [{row['bucket']}] {row['prerequisite_name']} → {row['target_name']}")
        for end in ("prerequisite", "target"):
            if row[f"{end}_stage"] is None:
                outside.setdefault(row[end], 0)
                outside[row[end]] += 1
    if outside:
        print("\n## Đầu nằm ngoài dãy học (số cạnh vàng chạm) — căn cứ để phán")
        for node_id, count in sorted(outside.items(), key=lambda item: -item[1]):
            key, node = info.get(node_id, ("?", {}))
            quote = next((span.get("quote", "") for span in node.get("evidence", []) if isinstance(span, dict)), "")
            print(f"  {name(node_id)} ×{count} | {key}, {node.get('teaching_status')}, nhắc ở {node.get('mentioned_in')}, "
                  f"{node.get('node_type')}\n      căn cứ A3: {quote[:160]!r}")

    gold = load_gold(gold_path)
    edges = {(identity.get(a, a), identity.get(b, b)) for a, b in merge_gold([gold], mode="union")}
    edges = {(a, b) for a, b in edges if a != b}
    rows = [*payload.get("requires_edges", []), *payload.get("bypassed_edges", []),
            *payload.get("soft_backward_edges", [])]
    machine = {(edge["source"], edge["target"]) for edge in rows
               if edge.get("edge_type", "requires") == "requires" and not edge.get("soft")
               and {edge["source"], edge["target"]} <= sequence}
    targets = sorted({identity.get(target, target) for target in gold["targets"]})
    inside = [target for target in targets if target in sequence]
    print(f"\n## Q7: chính thức {target_coverage(edges, machine, targets)['mean_coverage']:.3f}; "
          f"chỉ trên {len(inside)}/{len(targets)} đích trong dãy học "
          f"{target_coverage(edges, machine, inside)['mean_coverage']:.3f} (chẩn đoán)")
    ancestors = {}
    for source, target in transitive_closure(machine):
        ancestors.setdefault(target, set()).add(source)
    both = [(a, b) for a, b in edges if a in sequence and b in sequence]
    missing = sorted((name(a), name(b)) for a, b in both if a not in ancestors.get(b, set()))
    print(f"\n## Cạnh vàng hai đầu trong dãy học mà máy không có đường đi: {len(missing)}/{len(both)}")
    for a, b in missing:
        print(f"  {a} → {b}")


if __name__ == "__main__":
    main()
