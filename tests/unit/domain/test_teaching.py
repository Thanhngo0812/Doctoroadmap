from doc2roadmap.domain.teaching import bypass_excluded


def edge(source, target, **extra):
    return {"source": source, "target": target, "edge_type": "requires", **extra}


def test_bypassing_an_excluded_node_keeps_every_learn_before_constraint():
    # a → x → y → b với x, y bị loại: bỏ hai node mà không co thì mất ràng buộc a trước b.
    edges = [edge("a", "x"), edge("x", "y"), edge("y", "b"), edge("a", "c", reason="giữ nguyên")]
    kept, added = bypass_excluded(edges, {"x", "y"})
    assert {(value["source"], value["target"]) for value in kept} == {("a", "c"), ("a", "b")}
    assert added == [{"source": "a", "target": "b", "edge_type": "requires", "via_excluded": ["x", "y"]}]
    assert next(value for value in kept if value["target"] == "c")["reason"] == "giữ nguyên"


def test_bypassing_does_not_duplicate_a_constraint_that_already_exists():
    kept, added = bypass_excluded([edge("a", "x"), edge("x", "b"), edge("a", "b")], {"x"})
    assert added == [] and [(value["source"], value["target"]) for value in kept] == [("a", "b")]


def test_an_excluded_leaf_simply_disappears():
    kept, added = bypass_excluded([edge("a", "x"), edge("a", "b")], {"x"})
    assert added == [] and [(value["source"], value["target"]) for value in kept] == [("a", "b")]


def test_soft_exercise_edge_never_becomes_hard_through_excluded_node():
    kept, added = bypass_excluded([edge("a", "x", soft=True), edge("x", "b")], {"x"})
    assert kept == [] and added == []
