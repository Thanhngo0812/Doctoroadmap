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
