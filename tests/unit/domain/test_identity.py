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


def test_v3_name_sources_nominate_but_never_merge_by_themselves():
    cases = [
        ("CSDL", "Cơ sở dữ liệu", "initialism"),
        ("Upper triangular matrix", "Upper-triangular matrix", "normalized_name"),
        ("𝐅^{m,n}", "F m,n", "normalized_name"),
        ("Độc lập tuyến tính cực đại", "Hệ độc lập tuyến tính cực đại", "generic_prefix"),
        ("Cộng", "Phép cộng", "generic_prefix"),
    ]
    for first, second, reason in cases:
        assert reason in identity_candidates([node("a", first), node("b", second)])[0]["reasons"]
    assert not identity_candidates([node("a", "C"), node("b", "Cơ sở dữ liệu")])


def test_description_neighbors_are_bounded_thresholded_and_deterministic():
    nodes = [node("a", "Im f"), node("b", "Ảnh"), node("c", "Unrelated"), node("d", "Different")]
    vectors = {"a": [1, 0], "b": [1, 0.01], "c": [0, 1], "d": [0, -1]}
    pairs = identity_candidates(nodes, vectors=vectors, semantic_top_k=3, semantic_min_similarity=0.9)
    assert pairs == [{"left": "a", "right": "b", "reasons": ["description_similarity"]}]
    assert identity_candidates(nodes[::-1], vectors=vectors, semantic_top_k=3, semantic_min_similarity=0.9) == pairs
    assert identity_candidates(nodes, vectors=vectors, semantic_min_similarity=1.0) == []


def test_top_k_limits_semantic_pairs_and_uses_union_not_mutual():
    # Sáu vector bằng nhau: mỗi node chỉ chọn ba ID nhỏ nhất khác nó. d-e không lọt; a-f vẫn lọt từ đầu f.
    nodes = [node(key, "Concept " + key) for key in "abcdef"]
    pairs = {(p["left"], p["right"]) for p in identity_candidates(nodes, vectors={k: [1, 0] for k in "abcdef"})}
    assert len(pairs) == 12 and ("d", "e") not in pairs and ("a", "f") in pairs


def test_representative_prefers_taught_then_earliest_and_falls_back_without_taught():
    from doc2roadmap.domain.identity import identity_map

    verdicts = [{"left": "a", "right": "b", "verdict": "same"}]
    assert identity_map(verdicts, {"a": 1, "b": 20}, taught={"b"})[0] == {"a": "b"}
    assert identity_map(verdicts, {"a": 1, "b": 20}, taught=set())[0] == {"b": "a"}


def test_changed_endpoints_recompute_order_before_cycle_breaking_but_unchanged_edges_keep_a8():
    from doc2roadmap.domain.identity import merge_and_break_cycles

    def e(a, b, relation="ngược"):
        return {**edge(a, b), "order_relation": relation, "evidence_kind": "explicit", "independent_source_count": 1}

    # Khi còn thành viên cũ, cả ba cạnh đều ngược. Sau gộp chỉ R→P còn ngược.
    edges = [e("P", "M2"), e("M2", "R"), e("R", "P2"), e("X", "Y", "ngược"), e("M2", "Z")]
    position = {"P": 131, "M": 139, "R": 160, "M2": 163, "P2": 170, "X": 1, "Y": 2, "Z": 139}
    kept, removed = merge_and_break_cycles(edges, {"M2": "M", "P2": "P"}, position)
    assert [(e["source"], e["target"]) for e in removed] == [("R", "P")]
    by_pair = {(e["source"], e["target"]): e for e in kept}
    assert by_pair["P", "M"]["order_relation"] == "thuận"
    assert by_pair["P", "M"]["order_relation_before_merge"] == "ngược"
    assert by_pair["M", "Z"]["order_relation"] == "cùng chunk"
    assert by_pair["X", "Y"]["order_relation"] == "ngược"
    assert "order_relation_before_merge" not in by_pair["X", "Y"]
    assert all(e["order_relation"] == "ngược" for e in edges)  # không sửa đầu vào
