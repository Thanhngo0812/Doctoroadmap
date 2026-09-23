from doc2roadmap.domain.identity import apply_identity_map, identity_candidates


def node(node_id, name, aliases=(), anchor=None):
    return {"node_id": node_id, "name": name, "aliases": [{"name": a} for a in aliases], "anchor": anchor}


def test_candidates_come_only_from_narrow_signals_never_from_plain_containment():
    nodes = [
        node("dltt", "Độc lập tuyến tính"),
        node("hvdltt", "Hệ véc tơ độc lập tuyến tính"),  # tiền tố chung chung → ứng viên
        node("mt", "Ma trận"),
        node("mtnd", "Ma trận nghịch đảo"),  # chỉ "chứa tên" → KHÔNG phải ứng viên
        node("lm", "Linear map", aliases=["linear maps"]),
        node("lvw", "ℒ(V,W)", aliases=["linear maps"]),  # chung alias → ứng viên (chưa phải bằng chứng trùng)
        node("a", "Phần tử trung hòa", anchor={"chunk_id": "c1", "char_start": 10}),
        node("b", "Véc tơ không", anchor={"chunk_id": "c1", "char_start": 10}),  # cùng câu neo → ứng viên
    ]
    pairs = {(row["left"], row["right"]): row["reasons"] for row in identity_candidates(nodes)}
    assert set(pairs) == {("dltt", "hvdltt"), ("lm", "lvw"), ("a", "b")}
    assert pairs[("dltt", "hvdltt")] == ["generic_prefix"]
    assert pairs[("lm", "lvw")] == ["shared_name_or_alias"]
    assert pairs[("a", "b")] == ["same_anchor"]


def edge(source, target):
    return {"source": source, "target": target, "edge_type": "requires"}


def test_merging_redirects_edges_drops_self_loops_and_reports_cycles_it_creates():
    # a → b → a2, và a2 gộp vào a: gộp sinh chu trình a → b → a, phải được báo để A9 gỡ lại.
    edges = [edge("a", "b"), edge("b", "a2"), edge("a2", "c"), edge("a", "a2")]
    merged, cycles = apply_identity_map(edges, {"a2": "a"})
    assert {(e["source"], e["target"]) for e in merged} == {("a", "b"), ("b", "a"), ("a", "c")}
    assert cycles == [["a", "b"]]


def test_only_verified_cliques_merge_and_a_chain_of_same_verdicts_is_not_enough():
    from doc2roadmap.domain.identity import identity_map

    position = {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5}
    verdicts = [
        {"left": "a", "right": "b", "verdict": "same"},
        {"left": "b", "right": "c", "verdict": "same"},  # a–c chưa ai phán → nhóm {a,b,c} không được gộp
        {"left": "d", "right": "e", "verdict": "same"},
        {"left": "a", "right": "d", "verdict": "different"},
    ]
    mapping, open_groups = identity_map(verdicts, position)
    assert mapping == {"e": "d"}  # đại diện là khái niệm được dạy sớm hơn
    assert open_groups == [["a", "b", "c"]]
    verdicts.append({"left": "a", "right": "c", "verdict": "same"})
    mapping, open_groups = identity_map(verdicts, position)
    assert mapping == {"b": "a", "c": "a", "e": "d"} and open_groups == []


def test_merging_then_breaking_cycles_leaves_a_dag():
    from doc2roadmap.domain.identity import merge_and_break_cycles

    edges = [edge("a", "b"), edge("b", "a2"), edge("a2", "c")]
    merged, removed = merge_and_break_cycles(edges, {"a2": "a"})
    pairs = {(e["source"], e["target"]) for e in merged}
    assert len(removed) == 1 and {(e["source"], e["target"]) for e in removed} <= {("a", "b"), ("b", "a")}
    assert ("a", "c") in pairs and not ({("a", "b"), ("b", "a")} <= pairs)


def test_the_judge_contract():
    import pytest

    from doc2roadmap.domain.identity import validate_identity_response

    validate_identity_response({"pair_id": "p1", "verdict": "same", "reason": "cùng định nghĩa"}, pair_id="p1")
    for bad, match in (({"pair_id": "p2", "verdict": "same", "reason": "x"}, "pair_id"),
                       ({"pair_id": "p1", "verdict": "maybe", "reason": "x"}, "verdict"),
                       ({"pair_id": "p1", "verdict": "same", "reason": " "}, "reason")):
        with pytest.raises(ValueError, match=match):
            validate_identity_response(bad, pair_id="p1")
