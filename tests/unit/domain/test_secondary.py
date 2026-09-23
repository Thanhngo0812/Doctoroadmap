import pytest

from doc2roadmap.domain.secondary import (
    pair_dossier,
    reconcile_pair_verdicts,
    select_secondary_pairs,
    validate_secondary_response,
)


def node(node_id, cluster):
    return {
        "node_id": node_id,
        "name": node_id,
        "description": node_id,
        "cluster_id": cluster,
        "learnable": True,
        "defining_chunk_ids": ["c1"],
    }


def test_secondary_route_and_explicit_reachability_pruning():
    nodes = [node("a", "g1"), node("b", "g1"), node("c", "g2")]
    suspected = [
        {"pair_id": "ab", "left": "a", "right": "b", "sources": ["citation"], "details": {}},
        {"pair_id": "ac", "left": "a", "right": "c", "sources": ["contact"], "details": {}},
    ]
    explicit = [
        {"source": "a", "target": "x", "edge_type": "requires", "explicit_evidence": True},
        {"source": "x", "target": "b", "edge_type": "requires", "explicit_evidence": True},
    ]
    weak = [
        {"source": "a", "target": "x", "edge_type": "requires", "explicit_evidence": True},
        {"source": "x", "target": "b", "edge_type": "requires", "explicit_evidence": False},
    ]
    # Từ F126 (2026-09-23) tuyến `chapter` không lọc theo cụm nữa, nên cặp liên cụm `ac` luôn còn lại trừ khi
    # chính nó bị tỉa. Phần test này giữ nguyên mục đích cũ: ghim **phép tỉa theo khả đạt tường minh**.
    selected, pruned = select_secondary_pairs(nodes, suspected, [], explicit, route="chapter")
    assert [row["pair_id"] for row in selected] == ["ac"] and pruned[0]["pair_id"] == "ab"
    selected, pruned = select_secondary_pairs(nodes, suspected, [], weak, route="chapter")
    assert [row["pair_id"] for row in selected] == ["ab", "ac"] and not pruned
    direct_weak = [{"source": "a", "target": "b", "edge_type": "requires", "explicit_evidence": False}]
    selected, pruned = select_secondary_pairs(nodes, suspected, [], direct_weak, route="chapter")
    assert [row["pair_id"] for row in selected] == ["ac"] and pruned[0]["status"] == "pruned_direct_edge"
    selected, pruned = select_secondary_pairs(
        nodes,
        suspected,
        [],
        [{"source": "b", "target": "a", "edge_type": "requires", "explicit_evidence": True}],
        route="chapter",
    )
    assert [row["pair_id"] for row in selected] == ["ac"] and pruned[0]["edge"] == {"source": "b", "target": "a"}
    selected, _ = select_secondary_pairs(
        nodes,
        suspected,
        [{"left_cluster": "g1", "right_cluster": "g2", "selected": True, "exact_weight": 1.0, "dense_weight": 0.0}],
        [],
        route="topic_cluster",
    )
    assert [row["pair_id"] for row in selected] == ["ac"]


def test_pair_contract_rejects_outside_edge_and_two_orders_must_agree():
    pair = {"pair_id": "ab", "left": "a", "right": "b"}
    valid = {
        "pair_id": "ab",
        "decision": "create",
        "prerequisite": "a",
        "target": "b",
        "evidence_kind": "noi_ro",
        "chunk_ids": ["c1"],
        "reason": "explicit",
        "flags": [],
    }
    validate_secondary_response(valid, pair)
    with pytest.raises(ValueError, match="ngoài hồ sơ"):
        validate_secondary_response({**valid, "target": "c"}, pair)
    assert reconcile_pair_verdicts(valid, dict(valid)) == valid
    assert reconcile_pair_verdicts(valid, {**valid, "prerequisite": "b", "target": "a"})["decision"] == "defer"
    assert reconcile_pair_verdicts(valid, {"pair_id": "ab", "decision": "no_direct_relation", "flags": []})["decision"] == "defer"
    assert reconcile_pair_verdicts(
        {"pair_id": "ab", "decision": "no_direct_relation", "flags": []}, valid
    )["decision"] == "defer"


def test_secondary_flags_must_each_have_a_nonempty_kind():
    pair = {"pair_id": "ab", "left": "a", "right": "b"}
    base = {"pair_id": "ab", "decision": "defer", "flags": []}
    validate_secondary_response(base, pair)
    for malformed in ({}, {"kind": ""}, {"kind": 1}, "unknown"):
        with pytest.raises(ValueError, match="flag cần kind"):
            validate_secondary_response({**base, "flags": [malformed]}, pair)


def test_dossier_contains_sources_weights_text_descriptions_order_and_weak_path():
    nodes = [node("a", "g1"), node("b", "g1")]
    chunks = [type("Chunk", (), {"chunk_id": "c1", "text": "A needs B", "order_index": 3})()]
    pair = {"pair_id": "ab", "left": "a", "right": "b", "sources": ["citation"], "details": {"citation": ["c1"]}}
    dossier = pair_dossier(
        pair,
        nodes,
        chunks,
        {"c1": {"a": {}, "b": {}}},
        [{"left_cluster": "g1", "right_cluster": "g2", "exact_weight": 0.5, "dense_weight": 0.25}],
        [{"source": "a", "target": "b", "edge_type": "requires", "explicit_evidence": False}],
    )
    assert dossier["sources"] == ["citation"]
    assert dossier["evidence_chunks"] == [{"chunk_id": "c1", "text": "A needs B"}]
    assert dossier["nodes"][0]["description"] == "a"
    assert dossier["provenance_order"] == {"a": 3, "b": 3}
    assert dossier["indirect_path"]["all_explicit"] is False


def test_chapter_route_asks_cross_cluster_pairs_because_that_is_where_gold_edges_live():
    # F126: 78% cạnh tiên quyết vàng là liên cụm (31/40 và 48/61 trên hai chương vàng), và NMI cụm↔chương
    # là 0,756/0,789 nên "cùng cụm" gần như là "cùng chương" — đúng vùng pass chính đã quét. Luật cũ chĩa
    # pass phụ vào vùng đã phủ và cấm nó vào vùng còn trống.
    nodes = [node("a", "g1"), node("b", "g1"), node("c", "g2")]
    suspected = [
        {"pair_id": "ab", "left": "a", "right": "b", "sources": ["citation"], "details": {}},
        {"pair_id": "ac", "left": "a", "right": "c", "sources": ["contact"], "details": {}},
    ]
    selected, pruned = select_secondary_pairs(nodes, suspected, [], [], route="chapter")
    assert [row["pair_id"] for row in selected] == ["ab", "ac"] and not pruned

    # Phép tỉa theo khả đạt vẫn phải chặn cặp liên cụm đã có đường tường minh.
    path = [
        {"source": "a", "target": "x", "edge_type": "requires", "explicit_evidence": True},
        {"source": "x", "target": "c", "edge_type": "requires", "explicit_evidence": True},
    ]
    selected, pruned = select_secondary_pairs(nodes, suspected, [], path, route="chapter")
    assert [row["pair_id"] for row in selected] == ["ab"]
    assert [row["pair_id"] for row in pruned] == ["ac"]
