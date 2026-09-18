from types import SimpleNamespace

from doc2roadmap.domain.prerequisites import (
    merge_main_proposals,
    plan_main_sessions,
    validate_main_proposals,
)


def node(node_id, *, learnable=True, cluster="g1", defining=()):
    return {
        "node_id": node_id,
        "name": node_id,
        "learnable": learnable,
        "cluster_id": cluster,
        "defining_chunk_ids": list(defining),
    }


def chunk(chunk_id, section_id, order):
    return SimpleNamespace(chunk_id=chunk_id, parent_section_id=section_id, order_index=order, text=chunk_id)


def test_routing_uses_single_chapters_or_topic_clusters():
    small_nodes = [node(str(i), defining=("c1",)) for i in range(2)]
    flat_sections = [SimpleNamespace(section_id="s1", parent_section_id=None, level=1, order_index=0)]
    assert plan_main_sessions(small_nodes, [chunk("c1", "s1", 0)], flat_sections, {}, single_limit=20)[0]["route"] == "single"

    many_nodes = [node(str(i), cluster=f"g{i % 2}", defining=(f"c{i % 2 + 1}",)) for i in range(21)]
    hierarchical = [
        SimpleNamespace(section_id="root", parent_section_id=None, level=0, order_index=0),
        SimpleNamespace(section_id="chapter", parent_section_id="root", level=1, order_index=1),
        SimpleNamespace(section_id="s1", parent_section_id="chapter", level=2, order_index=1),
        SimpleNamespace(section_id="s2", parent_section_id="chapter", level=2, order_index=2),
    ]
    chapter_sessions = plan_main_sessions(
        many_nodes,
        [chunk("c1", "s1", 0), chunk("c2", "s2", 1)],
        hierarchical,
        {},
        single_limit=20,
    )
    assert {row["route"] for row in chapter_sessions} == {"chapter"}
    assert [row["sequence"] for row in chapter_sessions] == [0, 1]

    cluster_sessions = plan_main_sessions(
        many_nodes,
        [chunk("c1", "s1", 0), chunk("c2", "s1", 1)],
        flat_sections,
        {},
        single_limit=20,
    )
    assert {row["route"] for row in cluster_sessions} == {"topic_cluster"}
    assert len(cluster_sessions) == 2


def test_routing_ignores_level_zero_root_and_uses_distinct_chapter_lanes():
    nodes = [node(str(i), cluster=f"g{i % 2}", defining=(f"c{i % 2 + 1}",)) for i in range(21)]
    flat = [
        SimpleNamespace(section_id="root", parent_section_id=None, level=0, order_index=0),
        SimpleNamespace(section_id="s1", parent_section_id="root", level=1, order_index=1),
        SimpleNamespace(section_id="s2", parent_section_id="root", level=1, order_index=2),
    ]
    sessions = plan_main_sessions(nodes, [chunk("c1", "s1", 0), chunk("c2", "s2", 1)], flat, {}, single_limit=20)
    assert {row["route"] for row in sessions} == {"topic_cluster"}

    hierarchical = [
        *flat,
        SimpleNamespace(section_id="s1_1", parent_section_id="s1", level=2, order_index=3),
        SimpleNamespace(section_id="s2_1", parent_section_id="s2", level=2, order_index=4),
    ]
    sessions = plan_main_sessions(
        nodes,
        [chunk("c1", "s1_1", 0), chunk("c2", "s2_1", 1)],
        hierarchical,
        {},
        single_limit=20,
    )
    assert {row["chapter_id"] for row in sessions} == {"s1", "s2"}


def test_exactly_twenty_concepts_use_single_route():
    nodes = [node(str(i), defining=("c1",)) for i in range(20)]
    sections = [SimpleNamespace(section_id="s1", parent_section_id=None, level=1, order_index=0)]
    assert plan_main_sessions(nodes, [chunk("c1", "s1", 0)], sections, {}, single_limit=20)[0]["route"] == "single"


def test_executor_rejects_every_structural_violation_but_does_not_block_cycles():
    nodes = [
        node("a", defining=("c1",)),
        node("b", defining=("c2",)),
        node("c", defining=("c1",)),
        node("media", learnable=False),
    ]
    chunks = [chunk("c1", "s1", 0), chunk("c2", "s1", 1), chunk("c3", "s1", 2)]
    mention_map = {
        "c1": {"a": {}, "b": {}, "c": {}},
        "c2": {"a": {}, "b": {}},
        "c3": {"a": {}},
    }
    session = {"session_id": "one", "allowed_node_ids": ["a", "b", "media"], "chunk_ids": ["c1", "c2", "c3"]}
    output = {
        "edges": [
            {"target": "b", "prerequisite": "a", "evidence_kind": "noi_ro", "chunk_ids": ["c1"], "reason": "ok"},
            {"target": "a", "prerequisite": "b", "evidence_kind": "noi_ro", "chunk_ids": ["c2"], "reason": "cycle is deferred"},
            {"target": "outside", "prerequisite": "a", "evidence_kind": "noi_ro", "chunk_ids": ["c1"], "reason": "bad"},
            {"target": "c", "prerequisite": "a", "evidence_kind": "noi_ro", "chunk_ids": ["c1"], "reason": "bad"},
            {"target": "media", "prerequisite": "a", "evidence_kind": "noi_ro", "chunk_ids": ["c1"], "reason": "bad"},
            {"target": "b", "prerequisite": "a", "evidence_kind": "noi_ro", "chunk_ids": ["missing"], "reason": "bad"},
            {"target": "b", "prerequisite": "a", "evidence_kind": "noi_ro", "chunk_ids": ["c3"], "reason": "bad"},
            {"target": "b", "prerequisite": "a", "evidence_kind": "suy_doan", "chunk_ids": ["c1"], "reason": "bad"},
            {"target": "b", "prerequisite": "a", "edge_type": "prerequisite_of", "evidence_kind": "noi_ro", "chunk_ids": ["c1"], "reason": "bad"},
            {"target": "b", "prerequisite": "a", "evidence_kind": "noi_ro", "chunk_ids": ["c1"], "reason": "bad", "confidence": 1.0},
        ],
        "flags": [],
    }
    accepted, _, log, retry = validate_main_proposals(output, session, nodes, chunks, mention_map, existing_edges=[])
    assert {(edge["source"], edge["target"]) for edge in accepted} == {("a", "b"), ("b", "a")}
    assert {row["error"] for row in retry} == {
        "unknown_node",
        "outside_session",
        "non_learnable_node",
        "unknown_evidence_chunk",
        "evidence_missing_both_endpoints",
        "speculative_evidence",
        "relation_type_must_be_requires",
        "model_confidence_forbidden",
    }
    assert all(edge["edge_type"] == "requires" for edge in accepted)
    assert {edge["confidence"] for edge in accepted} == {0.8, 0.9}
    assert {edge["order_relation"] for edge in accepted} == {"thuận", "ngược"}
    assert sum(row["status"] == "accepted" for row in log) == 2


def test_reverse_order_needs_explicit_evidence_and_loses_point_one():
    nodes = [node("a", defining=("c1",)), node("b", defining=("c2",))]
    chunks = [chunk("c1", "s1", 0), chunk("c2", "s1", 1)]
    mention_map = {"c1": {"a": {}, "b": {}}, "c2": {"a": {}, "b": {}}}
    session = {"session_id": "one", "allowed_node_ids": ["a", "b"], "chunk_ids": ["c1", "c2"]}
    output = {"edges": [
        {"target": "a", "prerequisite": "b", "evidence_kind": "mach_trinh_bay", "chunk_ids": ["c2"], "reason": "weak reverse"},
        {"target": "a", "prerequisite": "b", "evidence_kind": "noi_ro", "chunk_ids": ["c2"], "reason": "explicit reverse"},
        {"target": "b", "prerequisite": "a", "evidence_kind": "mach_trinh_bay", "chunk_ids": ["c1"], "reason": "forward"},
    ], "flags": []}
    accepted, _, _, retry = validate_main_proposals(output, session, nodes, chunks, mention_map, existing_edges=[])
    assert [row["error"] for row in retry] == ["reverse_order_requires_explicit_evidence"]
    assert [(edge["order_relation"], edge["confidence"]) for edge in accepted] == [("ngược", 0.8), ("thuận", 0.7)]


def test_merger_is_independent_of_completion_order_and_logs_duplicates():
    first = {"session_id": "b", "operation_index": 0, "source": "a", "target": "b", "edge_type": "requires"}
    duplicate = {**first, "session_id": "a"}
    other = {"session_id": "c", "operation_index": 0, "source": "b", "target": "a", "edge_type": "requires"}
    left = merge_main_proposals([first, duplicate, other], [])
    right = merge_main_proposals([other, duplicate, first], [])
    assert left == right
    edges, log = left
    assert [(edge["source"], edge["target"]) for edge in edges] == [("a", "b"), ("b", "a")]
    assert any(row["status"] == "dropped_duplicate" for row in log)
