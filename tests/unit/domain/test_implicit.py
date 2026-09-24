import pytest

from doc2roadmap.domain.implicit import (
    add_implicit_edges,
    implicit_candidates,
    validate_implicit_response,
)


def edge(source, target, kind="noi_ro"):
    return {"source": source, "target": target, "edge_type": "requires", "evidence_kind": kind}


def test_candidates_are_the_k_concepts_taught_just_before_minus_those_already_required():
    order = ["a", "b", "c", "d", "e"]  # theo thứ tự dạy
    edges = [edge("a", "c"), edge("c", "e")]  # a đã tới e qua c
    candidates = implicit_candidates(order, edges, k=3)
    assert candidates["e"] == ["d", "b"]  # 3 khái niệm ngay trước e là b, c, d; c và a đã là tổ tiên
    assert candidates["a"] == []  # không ai dạy trước a
    assert candidates["c"] == ["b"]  # a đã là tiên quyết trực tiếp của c


def test_a_reply_must_pick_listed_candidates_and_quote_the_target_definition_verbatim():
    definition = "Tích của hai ma trận A và B là ma trận có phần tử hàng i cột j bằng tổng các tích."
    ok = {"node_id": "tich", "prerequisites": [{"node_id": "hang", "quote": "phần tử hàng i cột j", "reason": "dùng hàng"}]}
    validate_implicit_response(ok, node_id="tich", candidates=["hang", "cot"], definition_text=definition)
    validate_implicit_response({"node_id": "tich", "prerequisites": []}, node_id="tich", candidates=["hang"],
                               definition_text=definition)
    for bad, match in (
        ({**ok, "node_id": "khac"}, "node_id"),
        ({"node_id": "tich", "prerequisites": [{**ok["prerequisites"][0], "node_id": "xa"}]}, "ứng viên"),
        ({"node_id": "tich", "prerequisites": [{**ok["prerequisites"][0], "quote": "câu bịa"}]}, "định nghĩa"),
        ({"node_id": "tich", "prerequisites": [{**ok["prerequisites"][0], "reason": " "}]}, "reason"),
        ({"node_id": "tich", "prerequisites": [ok["prerequisites"][0], ok["prerequisites"][0]]}, "lặp"),
        ({**ok, "confidence": 0.9}, "confidence"),
    ):
        with pytest.raises(ValueError, match=match):
            validate_implicit_response(bad, node_id="tich", candidates=["hang", "cot"], definition_text=definition)


def test_an_implicit_edge_that_closes_a_cycle_is_the_one_removed():
    # b → a có căn cứ nói rõ; cạnh ngầm a → b khép chu trình và phải là cạnh bị gỡ.
    existing = [edge("b", "a", "noi_ro")]
    new = [edge("a", "b", "ngam"), edge("a", "c", "ngam")]
    edges, removed = add_implicit_edges(existing, new)
    pairs = {(e["source"], e["target"]) for e in edges}
    assert pairs == {("b", "a"), ("a", "c")}
    assert [(e["source"], e["target"]) for e in removed] == [("a", "b")]
