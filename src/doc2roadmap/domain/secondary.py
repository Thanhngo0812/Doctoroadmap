from __future__ import annotations

from collections import deque

from .prerequisites import definition_window


DECISIONS = {"create", "no_direct_relation", "indirect_path", "defer"}


def _path(edges, start, target, *, explicit_only=False):
    adjacency = {}
    for edge in edges:
        if edge.get("edge_type") != "requires" or edge.get("soft") or (explicit_only and not edge.get("explicit_evidence")):
            continue
        adjacency.setdefault(edge["source"], []).append(edge)
    queue = deque([(start, [])])
    seen = {start}
    while queue:
        node, path = queue.popleft()
        for edge in sorted(adjacency.get(node, []), key=lambda row: (row["target"], row.get("session_id", ""))):
            next_path = path + [edge]
            if edge["target"] == target:
                return next_path
            if edge["target"] not in seen:
                seen.add(edge["target"])
                queue.append((edge["target"], next_path))
    return None


def _either_path(edges, left, right, *, explicit_only=False):
    return _path(edges, left, right, explicit_only=explicit_only) or _path(
        edges, right, left, explicit_only=explicit_only
    )


def select_secondary_pairs(nodes, suspected_pairs, pair_cluster_ledger, edges, *, route):
    if route == "single":
        return [], []
    node_by_id = {node["node_id"]: node for node in nodes}
    selected_clusters = {
        frozenset((row["left_cluster"], row["right_cluster"]))
        for row in pair_cluster_ledger
        if row.get("selected")
    }
    selected, pruned = [], []
    for pair in sorted(suspected_pairs, key=lambda row: row["pair_id"]):
        left, right = pair["left"], pair["right"]
        if left not in node_by_id or right not in node_by_id:
            continue
        same_cluster = node_by_id[left]["cluster_id"] == node_by_id[right]["cluster_id"]
        # Tuyến `chapter` **không** lọc theo cụm nữa (F126, 2026-09-23). Luật cũ chỉ hỏi cặp cùng cụm, nhưng đo
        # trên hai chương vàng thì **78% cạnh tiên quyết là liên cụm** (31/40 và 48/61), và NMI cụm↔chương là
        # 0,756/0,789 nên "cùng cụm" gần như là "cùng chương" — đúng vùng pass chính vừa quét. Luật cũ vì thế
        # chĩa pass phụ vào vùng đã phủ và cấm nó vào vùng còn trống. Phép tỉa theo khả đạt bên dưới vẫn là thứ
        # giữ chi phí trong tầm.
        if route == "topic_cluster":
            cluster_pair = frozenset((node_by_id[left]["cluster_id"], node_by_id[right]["cluster_id"]))
            if same_cluster or cluster_pair not in selected_clusters:
                continue
        direct = next((
            edge for edge in edges
            if edge.get("edge_type") == "requires" and not edge.get("soft")
            and {edge.get("source"), edge.get("target")} == {left, right}
        ), None)
        path = _either_path(edges, left, right, explicit_only=True)
        if direct:
            pruned.append({
                "pair_id": pair["pair_id"],
                "status": "pruned_direct_edge",
                "edge": {"source": direct["source"], "target": direct["target"]},
            })
        elif path:
            pruned.append({
                "pair_id": pair["pair_id"],
                "status": "pruned_explicit_path",
                "path": [path[0]["source"], *[edge["target"] for edge in path]],
            })
        else:
            selected.append(pair)
    return selected, pruned


def pair_dossier(pair, nodes, chunks, mention_map, pair_cluster_ledger, edges, *, definition_before=4, definition_after=2):
    node_by_id = {node["node_id"]: node for node in nodes}
    chunk_by_id = {chunk.chunk_id: chunk for chunk in chunks}
    left, right = pair["left"], pair["right"]
    evidence_ids = sorted(
        ({chunk_id for chunk_id, rows in mention_map.items()
          if left in rows and right in rows and chunk_id in chunk_by_id}
         | {node_by_id[node_id].get("anchor", {}).get("chunk_id")
            for node_id in (left, right) if node_by_id[node_id].get("anchor")}
        ) & set(chunk_by_id),
        key=lambda chunk_id: (chunk_by_id[chunk_id].order_index, chunk_id),
    )
    cluster_pair = frozenset((node_by_id[left]["cluster_id"], node_by_id[right]["cluster_id"]))
    ledger = next((
        row for row in pair_cluster_ledger
        if frozenset((row["left_cluster"], row["right_cluster"])) == cluster_pair
    ), None)
    path = _either_path(edges, left, right)
    indirect = None
    if path:
        indirect = {
            "nodes": [path[0]["source"], *[edge["target"] for edge in path]],
            "edges": path,
            "all_explicit": all(edge.get("explicit_evidence") for edge in path),
        }
    def provenance_order(node_id):
        return min(
            (chunk_by_id[value].order_index for value in node_by_id[node_id].get("defining_chunk_ids", []) if value in chunk_by_id),
            default=None,
        )
    return {
        "pair_id": pair["pair_id"],
        "left": left,
        "right": right,
        "sources": sorted(pair.get("sources", [])),
        "source_details": pair.get("details", {}),
        "channel_weights": {
            "exact": ledger.get("exact_weight", 0.0) if ledger else 0.0,
            "dense": ledger.get("dense_weight", 0.0) if ledger else 0.0,
        },
        "evidence_chunks": [{"chunk_id": chunk_id, "text": chunk_by_id[chunk_id].text} for chunk_id in evidence_ids],
        "nodes": [
            {
                "node_id": node_id,
                "name": node_by_id[node_id]["name"],
                "description": node_by_id[node_id].get("description", ""),
                "defining_chunk_ids": node_by_id[node_id].get("defining_chunk_ids", []),
                "teaching_status": node_by_id[node_id].get("teaching_status"),
                "definition_window": definition_window(node_by_id[node_id], chunks,
                                                       before=definition_before, after=definition_after),
            }
            for node_id in (left, right)
        ],
        "provenance_order": {left: provenance_order(left), right: provenance_order(right)},
        "indirect_path": indirect,
    }


def validate_secondary_response(value, pair):
    if not isinstance(value, dict) or value.get("pair_id") != pair["pair_id"]:
        raise ValueError("phán quyết sai pair_id")
    if value.get("decision") not in DECISIONS:
        raise ValueError("phán quyết ngoài bốn giá trị cho phép")
    if not isinstance(value.get("flags"), list):
        raise ValueError("phán quyết cần flags dạng mảng")
    if any(not isinstance(flag, dict) or not isinstance(flag.get("kind"), str) or not flag["kind"].strip() for flag in value["flags"]):
        raise ValueError("flag cần kind")
    if "confidence" in value:
        raise ValueError("mô hình không được trả confidence")
    if value["decision"] != "create":
        return
    if {value.get("prerequisite"), value.get("target")} != {pair["left"], pair["right"]}:
        raise ValueError("cạnh ngoài hồ sơ cặp")
    if value.get("prerequisite") == value.get("target"):
        raise ValueError("cạnh tự nối")
    required = ("evidence_kind", "reason") + (("quote", "prerequisite_kind") if "prerequisite_kind" in value else ())
    for key in required:
        if not isinstance(value.get(key), str) or not value[key]:
            raise ValueError(f"phán quyết tạo cạnh thiếu {key}")
    if not isinstance(value.get("chunk_ids"), list) or not all(isinstance(item, str) for item in value["chunk_ids"]):
        raise ValueError("phán quyết tạo cạnh cần chunk_ids")


def reconcile_pair_verdicts(first, second):
    if first == second:
        return first
    if first["decision"] != second["decision"]:
        return {"pair_id": first["pair_id"], "decision": "defer", "reason": "inconsistent_orders", "flags": []}
    if first["decision"] == "create":
        keys = ("prerequisite", "target", "evidence_kind", "prerequisite_kind")
        if any(first.get(key) != second.get(key) for key in keys):
            return {"pair_id": first["pair_id"], "decision": "defer", "reason": "inconsistent_orders", "flags": []}
        return {
            **first,
            "chunk_ids": sorted(set(first.get("chunk_ids", [])) | set(second.get("chunk_ids", []))),
            "flags": first.get("flags", []) + second.get("flags", []),
        }
    return {**first, "flags": first.get("flags", []) + second.get("flags", [])}
