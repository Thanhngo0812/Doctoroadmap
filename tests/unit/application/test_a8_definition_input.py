from types import SimpleNamespace

from doc2roadmap.application.use_cases.build_main_edges import BuildMainEdges


def test_mentioned_only_node_is_context_not_allowed_target():
    use_case = object.__new__(BuildMainEdges)
    nodes = [{"node_id": "t", "name": "Target", "learnable": True, "teaching_status": "taught",
              "defining_chunk_ids": ["c"], "anchor": {"chunk_id": "c", "char_start": 0,
              "sentence": "Target is introduced."}},
             {"node_id": "m", "name": "Mention", "learnable": True, "teaching_status": "mentioned_only",
              "defining_chunk_ids": ["c"]}]
    chunk = SimpleNamespace(chunk_id="c", order_index=0, text="Target is introduced. Mention appears.")
    session = {"session_id": "s", "route": "chapter", "chapter_id": "h", "chunk_ids": ["c"],
               "target_node_ids": ["t"], "allowed_node_ids": ["t"]}
    data = use_case._input(session, nodes, [chunk], {"c": {"t": {}, "m": {}}}, [], [], {"s": session})
    assert [row["node_id"] for row in data["target_concepts"]] == ["t"]
    assert [row["node_id"] for row in data["mentioned_elsewhere"]] == ["m"]
    assert data["allowed_node_ids"] == ["t"]
