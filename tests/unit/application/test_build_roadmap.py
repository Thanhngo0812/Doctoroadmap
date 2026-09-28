import json
from types import SimpleNamespace

from doc2roadmap.application.use_cases.build_roadmap import BuildRoadmap


class Store:
    def __init__(self, root):
        nodes = [
            {"node_id": "a", "name": "Alpha", "learnable": True, "cluster_id": "g1", "first_order_index": 0, "defining_chunk_ids": ["c1"]},
            {"node_id": "b", "name": "Beta", "learnable": True, "cluster_id": "g1", "first_order_index": 1, "defining_chunk_ids": ["c1"]},
        ]
        edge = {"source": "a", "target": "b", "edge_type": "requires", "chunk_ids": ["c1"], "redundant_via": ["a", "x", "b"]}
        self.validated = SimpleNamespace(
            payload={
                "stage": "validated",
                "nodes": nodes,
                "requires_edges": [edge],
                "quality_gate": {"passed": True},
                "main_sessions": [{"session_id": "main", "target_node_ids": ["a", "b"]}],
                "completed_secondary_pairs": [],
                "suspected_pairs": [],
                "validation_flags": [{"kind": "review_me"}],
                "suspected_pairs": [],
            },
            version=5,
            manifest={"source_hash": "validated-source", "config_hash": "validated-config"},
        )
        self.validated.manifest["config"] = {"chunks_version": 1}
        self.latest = self.validated
        self.root = root
        self.saved = None
        sections = [
            SimpleNamespace(section_id="root", title="<document>", level=0, parent_section_id=None, order_index=-1),
            SimpleNamespace(section_id="ch1", title="Chương 1", level=1, parent_section_id="root", order_index=0),
            SimpleNamespace(section_id="s1", title="1.1 Mở đầu", level=2, parent_section_id="ch1", order_index=1),
            SimpleNamespace(section_id="s2", title="1.2 Tiếp theo", level=2, parent_section_id="ch1", order_index=2),
        ]
        chunks = [SimpleNamespace(chunk_id=f"c{i}", order_index=i, parent_section_id="s1" if i < 5 else "s2")
                  for i in range(1, 9)]
        self.chunks = SimpleNamespace(result=SimpleNamespace(chunks=chunks, sections=sections), version=1)

    def load_chunks(self, doc_id, version):
        assert version == 1
        return self.chunks

    load_role_chunks = load_chunks

    def load_latest_graph(self, doc_id):
        return self.latest

    def load_graph(self, doc_id, version):
        assert version == 5
        return self.validated

    def find_graph(self, doc_id, source_hash, config_hash):
        if self.saved and self.saved.manifest["source_hash"] == source_hash and self.saved.manifest["config_hash"] == config_hash:
            return self.saved
        return None

    def save_graph(self, doc_id, source_hash, config_hash, config, payload, **kwargs):
        path = self.root / "graph" / doc_id / "v6"
        path.mkdir(parents=True, exist_ok=True)
        self.saved = SimpleNamespace(
            payload=json.loads(json.dumps(payload)), version=6, path=path,
            manifest={"source_hash": source_hash, "config_hash": config_hash, "config": config, "upstream_version": kwargs["upstream_version"]},
        )
        self.latest = self.saved
        return self.saved


def test_roadmap_stage_writes_static_review_page_and_reuses(tmp_path):
    store = Store(tmp_path)
    first, reused = BuildRoadmap(store, stage_cap=5).execute("doc")
    assert not reused and first.payload["stage"] == "stages"
    html = (first.path / "roadmap.html").read_text(encoding="utf-8")
    assert "Alpha" in html and "review_me" in html and "redundant" in html and "c1" in html
    second, reused = BuildRoadmap(store, stage_cap=5).execute("doc")
    assert reused and second is first


def test_roadmap_rejects_unvalidated_edges(tmp_path):
    store = Store(tmp_path)
    store.validated.payload["stage"] = "edges"
    try:
        BuildRoadmap(store, stage_cap=5).execute("doc")
    except ValueError as error:
        assert "validated" in str(error)
    else:
        raise AssertionError("roadmap must not duplicate validation")


def test_invalid_main_session_does_not_mark_its_targets_as_reviewed(tmp_path):
    store = Store(tmp_path)
    store.validated.payload["main_flags"] = [{"kind": "invalid_main_session", "session_id": "main"}]
    artifact, _ = BuildRoadmap(store, stage_cap=5).execute("doc")
    assert {node["node_id"]: node["coverage_status"] for node in artifact.payload["nodes"]} == {
        "a": "unreviewed",
        "b": "unreviewed",
    }


def test_nodes_that_are_not_subject_matter_leave_the_stages_but_their_order_constraints_stay(tmp_path):
    store = Store(tmp_path)

    def taught(node_id, name, status, order):
        return {"node_id": node_id, "name": name, "learnable": True, "cluster_id": "g1", "first_order_index": order,
                "defining_chunk_ids": ["c1"], "teaching_status": status}

    store.validated.payload.update({
        "stage": "teaching",
        "nodes": [taught("a", "Alpha", "taught", 0), taught("x", "Thang điểm chữ", "not_subject_matter", 1),
                  taught("p", "Python", "prior_knowledge", 2), taught("b", "Beta", "mentioned_only", 3)],
        "requires_edges": [
            {"source": "a", "target": "x", "edge_type": "requires", "chunk_ids": ["c1"]},
            {"source": "x", "target": "b", "edge_type": "requires", "chunk_ids": ["c1"]},
        ],
        "main_sessions": [{"session_id": "main", "target_node_ids": ["a", "x", "p", "b"]}],
    })
    artifact, _ = BuildRoadmap(store, stage_cap=5).execute("doc")
    index = {node_id: i for i, node_id in enumerate(artifact.payload["sequence"])}
    assert set(index) == {"a"}
    assert {row["node_id"]: row["teaching_status"] for row in artifact.payload["excluded_nodes"]} == {
        "x": "not_subject_matter", "p": "prior_knowledge"}
    assert [n["node_id"] for n in artifact.payload["mentioned_nodes"]] == ["b"]
    html = (artifact.path / "roadmap.html").read_text(encoding="utf-8")
    assert "Kiến thức nền cần có" in html and "Python" in html
    assert "Không đưa vào lộ trình" in html and "Thang điểm chữ" in html


def test_mentioned_node_is_bypassed_and_not_a_lesson(tmp_path):
    store = Store(tmp_path)
    store.chunks.result.chunks[0].text = "Alpha then Middle"
    store.chunks.result.chunks[0].role = "noi_dung"
    for chunk in store.chunks.result.chunks[1:]:
        chunk.text = "Beta"
        chunk.role = "noi_dung"
    nodes = [concept("a","Alpha","c1",1),concept("m","Middle","c1",2),concept("b","Beta","c2",3)]
    for node,status in zip(nodes,("taught","mentioned_only","taught"),strict=True):
        node["teaching_status"] = status
        node["teaching_chunk_ids"] = [node["defining_chunk_ids"][0]] if status=="taught" else []
    store.validated.payload.update(stage="teaching",nodes=nodes,requires_edges=[
        {"source":"a","target":"m","edge_type":"requires"},
        {"source":"m","target":"b","edge_type":"requires"}])
    artifact,_ = BuildRoadmap(store).execute("doc")
    assert artifact.payload["sequence"]==["a","b"]
    assert artifact.payload["bypassed_edges"]==[
        {"source":"a","target":"b","edge_type":"requires","via_excluded":["m"]}]
    assert artifact.payload["mentioned_nodes"][0]["mention_module_id"]=="module_001"
    assert "Nhắc tới" in (artifact.path/"roadmap.html").read_text(encoding="utf-8")


def concept(node_id, name, chunk, order):
    return {"node_id": node_id, "name": name, "learnable": True, "cluster_id": "g1", "first_order_index": order,
            "defining_chunk_ids": [chunk]}


def test_backward_edge_does_not_pull_later_chapter_ahead(tmp_path):
    # Sách dạy b (chunk 1), c (2), a (3); cạnh a → b ngược sách chỉ còn là căn cứ mềm.
    store = Store(tmp_path)
    store.validated.payload.update({
        "nodes": [concept("a", "Alpha", "c3", 3), concept("b", "Beta", "c1", 1), concept("c", "Gamma", "c2", 2)],
        "requires_edges": [{"source": "a", "target": "b", "edge_type": "requires", "chunk_ids": ["c1"]}],
        "main_sessions": [{"session_id": "main", "target_node_ids": ["a", "b", "c"]}],
    })
    artifact, _ = BuildRoadmap(store, stage_cap=5).execute("doc")
    payload = artifact.payload
    assert payload["sequence"] == ["b", "c", "a"]
    assert "stages" not in payload and "chunk_stage_map" not in payload
    assert artifact.manifest["config"]["algorithm_id"] == "a10-book-anchored-sequence-v2"
    nodes = {node["node_id"]: node for node in payload["nodes"]}
    assert [nodes[n]["sequence_index"] for n in ("b", "c", "a")] == [0, 1, 2]
    assert nodes["b"]["prerequisites"] == []
    assert payload["soft_backward_edges"][0]["soft_reason"] == "ngược thứ tự sách"
    assert [module["node_ids"] for module in payload["modules"]] == [["b", "c", "a"]]
    html = (artifact.path / "roadmap.html").read_text(encoding="utf-8")
    assert html.index("Beta") < html.index("Gamma") < html.index("Alpha") and "cần: Alpha" not in html


def test_display_reduces_transitive_prerequisites_but_keeps_full_graph(tmp_path):
    store = Store(tmp_path)
    store.validated.payload.update(
        nodes=[concept("a", "Alpha", "c1", 1), concept("b", "Beta", "c2", 2),
               concept("c", "Gamma", "c3", 3)],
        requires_edges=[{"source": source, "target": target, "edge_type": "requires"}
                        for source, target in (("a", "b"), ("b", "c"), ("a", "c"))],
    )
    artifact, _ = BuildRoadmap(store, stage_cap=5).execute("doc")
    nodes = {node["node_id"]: node for node in artifact.payload["nodes"]}
    assert nodes["c"]["prerequisites"] == ["a", "b"]
    assert nodes["c"]["display_prerequisites"] == ["b"]
    assert "cần: Beta" in (artifact.path / "roadmap.html").read_text(encoding="utf-8")
    assert len(artifact.payload["requires_edges"]) == 3


def test_display_caps_prerequisites_at_three(tmp_path):
    store = Store(tmp_path)
    letters = "abcde"
    store.validated.payload.update(
        nodes=[concept(letter, letter.upper(), f"c{i}", i) for i, letter in enumerate(letters, 1)],
        requires_edges=[{"source": letter, "target": "e", "edge_type": "requires"} for letter in "abcd"],
    )
    artifact, _ = BuildRoadmap(store, stage_cap=8).execute("doc")
    node = next(node for node in artifact.payload["nodes"] if node["node_id"] == "e")
    assert len(node["display_prerequisites"]) == 3
    assert node["display_prerequisites_more_count"] == 1
    assert "và 1 khái niệm khác" in (artifact.path / "roadmap.html").read_text(encoding="utf-8")


def test_module_dependencies_are_reduced_and_target_keeps_complete_modules(tmp_path):
    from doc2roadmap.application.use_cases.build_roadmap import target_roadmap

    store = Store(tmp_path)
    store.validated.payload.update(
        nodes=[concept("a", "Alpha", "c1", 1), concept("b", "Beta", "c2", 2),
               concept("c", "Gamma", "c3", 3)],
        requires_edges=[{"source": source, "target": target, "edge_type": "requires"}
                        for source, target in (("a", "b"), ("b", "c"), ("a", "c"))],
    )
    artifact, _ = BuildRoadmap(store, stage_cap=1).execute("doc")
    modules = artifact.payload["modules"]
    assert [module["module_dependencies"] for module in modules] == [[], ["module_001"], ["module_002"]]
    result = target_roadmap(artifact.payload, ["Gamma"])
    assert [module["module_id"] for module in result["modules"]] == ["module_001", "module_002", "module_003"]
    assert result["modules"][-1]["target_node_ids"] == ["c"]
    assert "Học trước: module 002" in (artifact.path / "roadmap.html").read_text(encoding="utf-8")


def test_modules_follow_the_sections_of_the_book_and_map_chunks_back(tmp_path):
    store = Store(tmp_path)
    # Mỗi mục bốn khái niệm: trung vị 4 ≥ W/2 nên cấp mục đủ điều kiện (W4). Mục ba khái niệm thì hai mục sẽ gộp
    # thành một buổi sáu khái niệm — đúng thiết kế, nên test dùng mục bốn khái niệm.
    first = [concept(f"s1_{i}", f"Một {i}", f"c{i + 1}", i + 1) for i in range(4)]   # mục 1.1 (chunk 1–4)
    second = [concept(f"s2_{i}", f"Hai {i}", f"c{i + 5}", i + 5) for i in range(4)]  # mục 1.2 (chunk 5–8)
    store.validated.payload.update({
        "nodes": first + second, "requires_edges": [],
        "main_sessions": [{"session_id": "main", "target_node_ids": [n["node_id"] for n in first + second]}],
    })
    artifact, _ = BuildRoadmap(store, stage_cap=8).execute("doc")
    modules = artifact.payload["modules"]
    assert [module["node_ids"] for module in modules] == [[n["node_id"] for n in first], [n["node_id"] for n in second]]
    assert [module["module_id"] for module in modules] == ["module_001", "module_002"]
    assert [module["title"] for module in modules] == ["1.1 Mở đầu", "1.2 Tiếp theo"]
    assert artifact.payload["chunk_module_map"]["c5"] == {"module_id": "module_002", "all_module_ids": ["module_002"]}
