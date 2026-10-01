from types import SimpleNamespace

from doc2roadmap.domain.prerequisites import definition_window, plan_main_sessions, validate_main_proposals
from doc2roadmap.domain.global_validation import validate_graph_rules
from doc2roadmap.domain.secondary import select_secondary_pairs


def test_a8_targets_only_taught_or_uncertain_identity_representatives():
    nodes = [
        {"node_id": "原理", "name": "原理", "learnable": True, "cluster_id": "g", "defining_chunk_ids": ["c"],
         "teaching_status": "taught", "anchor": {"chunk_id": "c", "char_start": 0, "sentence": "原理を学ぶ。"}},
        {"node_id": "別名", "name": "別名", "learnable": True, "cluster_id": "g", "defining_chunk_ids": ["c"],
         "teaching_status": "taught", "merged_into": "原理"},
        {"node_id": "例", "name": "例", "learnable": True, "cluster_id": "g", "defining_chunk_ids": ["c"],
         "teaching_status": "mentioned_only"},
    ]
    chunks = [SimpleNamespace(chunk_id="c", parent_section_id="s", order_index=0, text="原理を学ぶ。")]
    sections = [SimpleNamespace(section_id="s", level=1, order_index=0)]
    sessions = plan_main_sessions(nodes, chunks, sections, {"c": {n["node_id"]: {} for n in nodes}}, single_limit=20)
    assert sessions[0]["target_node_ids"] == ["原理"]
    assert sessions[0]["allowed_node_ids"] == ["原理"]


def test_can_de_hieu_quote_must_be_in_target_window_not_merely_same_chunk():
    nodes = [
        {"node_id": "a", "name": "เวกเตอร์", "learnable": True, "cluster_id": "g", "defining_chunk_ids": ["c"],
         "teaching_status": "taught", "anchor": {"chunk_id": "c", "char_start": 0, "sentence": "เวกเตอร์เป็นวัตถุพื้นฐาน."}},
        {"node_id": "b", "name": "เมทริกซ์", "learnable": True, "cluster_id": "g", "defining_chunk_ids": ["c"],
         "teaching_status": "taught", "anchor": {"chunk_id": "c", "char_start": 27, "sentence": "เมทริกซ์ใช้คอลัมน์ของ A."}},
    ]
    text = "เวกเตอร์เป็นวัตถุพื้นฐาน.\n\nเมทริกซ์ใช้คอลัมน์ของ A. ตัวอย่างใช้เวกเตอร์."
    chunks = [SimpleNamespace(chunk_id="c", parent_section_id="s", order_index=0, text=text)]
    session = {"session_id": "s", "allowed_node_ids": ["a", "b"], "chunk_ids": ["c"]}
    mentions = {"c": {"a": {"channels": ["exact"]}, "b": {"channels": ["exact"]}}}
    good = {"target": "b", "prerequisite": "a", "prerequisite_kind": "can_de_hieu", "evidence_kind": "trong_dinh_nghia",
            "chunk_ids": ["c"], "quote": "เมทริกซ์ใช้คอลัมน์ของ A.", "reason": "Cần hiểu cột của A"}
    bad = {**good, "quote": "เวกเตอร์เป็นวัตถุพื้นฐาน."}
    accepted, _, _, retry = validate_main_proposals({"edges": [good, bad], "flags": []}, session, nodes, chunks, mentions, existing_edges=[])
    assert len(accepted) == 1 and accepted[0]["prerequisite_kind"] == "can_de_hieu"
    assert retry[0]["error"] == "quote_outside_definition_window"


def test_definition_window_is_configurable_and_stays_inside_paragraph():
    text = "Earlier paragraph.\n\nFirst. Second. Third. Fourth. Fifth. Matrix is defined. Example. Next. Last.\n\nExercises."
    chunk = SimpleNamespace(chunk_id="c", order_index=0, text=text)
    node = {"name": "Matrix", "anchor": {"chunk_id": "c", "char_start": text.index("Matrix"),
            "sentence": "Matrix is defined."}}
    window = definition_window(node, [chunk], before=4, after=2)
    assert "Second." in window and "Last." not in window
    assert "First." not in window and "Earlier paragraph." not in window and "Exercises." not in window
    assert "Fourth." in definition_window(node, [chunk], before=2, after=0)
    assert "Third." not in definition_window(node, [chunk], before=2, after=0)


def test_definition_quote_auto_attaches_anchor_chunk_and_mentioned_target_is_rejected():
    text = "Assume A. Matrix uses A."
    nodes = [{"node_id": "a", "name": "A", "learnable": True, "teaching_status": "taught",
              "defining_chunk_ids": ["c"]},
             {"node_id": "b", "name": "Matrix", "learnable": True, "teaching_status": "taught",
              "defining_chunk_ids": ["c"], "anchor": {"chunk_id": "c", "char_start": text.index("Matrix"),
              "sentence": "Matrix uses A."}},
             {"node_id": "m", "name": "Mentioned", "learnable": True, "teaching_status": "mentioned_only",
              "defining_chunk_ids": ["c"], "anchor": {"chunk_id": "c", "char_start": 0,
              "sentence": "Assume A."}}]
    chunks = [SimpleNamespace(chunk_id="c", order_index=0, text=text)]
    session = {"session_id": "s", "allowed_node_ids": ["a", "b", "m"], "chunk_ids": ["c"]}
    edge = {"target": "b", "prerequisite": "a", "prerequisite_kind": "can_de_hieu",
            "evidence_kind": "trong_dinh_nghia", "chunk_ids": [], "quote": "Assume A.", "reason": "A is assumed"}
    mentioned = {**edge, "target": "m"}
    accepted, _, _, retry = validate_main_proposals({"edges": [edge, mentioned], "flags": []}, session,
        nodes, chunks, {}, existing_edges=[], require_kind=True)
    assert len(accepted) == 1 and accepted[0]["chunk_ids"] == ["c"]
    assert retry[0]["error"] == "target_not_taught"


def test_cong_cu_is_soft_with_its_own_reason():
    nodes = [{"node_id": i, "name": i, "learnable": True, "cluster_id": "g", "defining_chunk_ids": ["c"]}
             for i in ("a", "b")]
    chunks = [SimpleNamespace(chunk_id="c", parent_section_id="s", order_index=0, text="例では道具を使う。")]
    edge = {"target": "b", "prerequisite": "a", "prerequisite_kind": "cong_cu", "evidence_kind": "noi_ro",
            "chunk_ids": ["c"], "quote": "例では道具を使う。", "reason": "Ví dụ"}
    accepted, _, _, retry = validate_main_proposals({"edges": [edge], "flags": []},
        {"session_id": "s", "allowed_node_ids": ["a", "b"], "chunk_ids": ["c"]}, nodes, chunks,
        {"c": {"a": {"channels": ["exact"]}, "b": {"channels": ["exact"]}}}, existing_edges=[])
    assert not retry
    assert accepted[0]["soft"] is True and accepted[0]["soft_reason"] == "cong_cu"


def test_definition_can_paraphrase_prerequisite_without_literal_name():
    nodes = [
        {"node_id": "a", "name": "Column vector", "learnable": True, "cluster_id": "g", "defining_chunk_ids": ["c1"],
         "teaching_status": "taught"},
        {"node_id": "b", "name": "Matrix", "learnable": True, "cluster_id": "g", "defining_chunk_ids": ["c2"],
         "teaching_status": "taught", "anchor": {"chunk_id": "c2", "char_start": 0,
         "sentence": "A matrix is formed from the columns of A."}},
    ]
    chunks = [SimpleNamespace(chunk_id="c1", order_index=0, text="Column vector."),
              SimpleNamespace(chunk_id="c2", order_index=1, text="A matrix is formed from the columns of A.")]
    edge = {"target": "b", "prerequisite": "a", "prerequisite_kind": "can_de_hieu", "evidence_kind": "trong_dinh_nghia",
            "chunk_ids": ["c2"], "quote": "the columns of A", "reason": "The definition uses columns."}
    accepted, _, _, retry = validate_main_proposals({"edges": [edge], "flags": []},
        {"session_id": "s", "allowed_node_ids": ["a", "b"], "chunk_ids": ["c2"]}, nodes, chunks,
        {"c1": {"a": {"channels": ["exact"]}}, "c2": {"b": {"channels": ["exact"]}}},
        existing_edges=[], require_kind=True)
    assert not retry and len(accepted) == 1


def test_quote_in_other_chunk_with_both_names_is_not_definition_evidence():
    nodes = [{"node_id": "a", "name": "Alpha", "learnable": True, "cluster_id": "g", "defining_chunk_ids": ["c1"]},
             {"node_id": "b", "name": "Beta", "learnable": True, "cluster_id": "g", "defining_chunk_ids": ["c1"],
              "anchor": {"chunk_id": "c1", "char_start": 0, "sentence": "Beta uses a quantity."}}]
    chunks = [SimpleNamespace(chunk_id="c1", order_index=0, text="Beta uses a quantity."),
              SimpleNamespace(chunk_id="c2", order_index=1, text="Alpha and Beta solve exercises.")]
    edge = {"target": "b", "prerequisite": "a", "prerequisite_kind": "can_de_hieu",
            "evidence_kind": "trong_dinh_nghia", "chunk_ids": ["c2"],
            "quote": "Alpha and Beta solve exercises.", "reason": "Only exercise"}
    accepted, _, _, retry = validate_main_proposals({"edges": [edge], "flags": []},
        {"session_id": "s", "allowed_node_ids": ["a", "b"], "chunk_ids": ["c1", "c2"]}, nodes, chunks,
        {"c2": {"a": {}, "b": {}}}, existing_edges=[], require_kind=True)
    assert not accepted and retry[0]["error"] == "definition_chunk_not_cited"


def test_a9_does_not_treat_tool_edge_as_hard_cycle():
    nodes = [{"node_id": i, "learnable": True} for i in ("a", "b")]
    hard = {"source": "a", "target": "b", "edge_type": "requires", "evidence_kind": "trong_dinh_nghia"}
    tool = {"source": "b", "target": "a", "edge_type": "requires", "evidence_kind": "noi_ro",
            "soft": True, "soft_reason": "cong_cu"}
    result = validate_graph_rules(nodes, [hard, tool], [], type_aliases={})
    assert result["removed_cycle_edges"] == []
    assert {e["source"] for e in result["requires_edges"] if not e.get("soft")} == {"a"}


def test_tool_edge_does_not_prune_hard_secondary_question():
    nodes = [{"node_id": i, "cluster_id": "g", "learnable": True} for i in ("a", "b")]
    pair = {"pair_id": "ab", "left": "a", "right": "b"}
    tool = {"source": "a", "target": "b", "edge_type": "requires", "soft": True,
            "soft_reason": "cong_cu", "explicit_evidence": True}
    selected, pruned = select_secondary_pairs(nodes, [pair], [], [tool], route="chapter")
    assert selected == [pair] and not pruned
