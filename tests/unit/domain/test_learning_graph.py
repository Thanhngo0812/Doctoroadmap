from types import SimpleNamespace

from doc2roadmap.domain.learning_graph import LearningGraph
from doc2roadmap.domain.source_labels import SourceRegistry


def chunk(chunk_id, text, *, page=4, start=100):
    return SimpleNamespace(chunk_id=chunk_id, text=text, page=page, char_start=start,
                           char_end=start + len(text), section_path=["Chương 1"])


def test_source_registry_maps_normalized_quote_back_to_raw_absolute_offsets():
    source = chunk("c1", "Trước\n  định nghi\u0303a sau")
    registry = SourceRegistry([source])
    label = registry.label("c1", "Q")

    citation = registry.citation(label, "định nghĩa")

    assert citation["chunk_id"] == "c1"
    assert citation["page"] == 4
    assert source.text[citation["char_start"] - source.char_start:citation["char_end"] - source.char_start] == "định nghi\u0303a"


def test_source_registry_quote_starting_with_combining_mark_excludes_preceding_newline():
    source = SimpleNamespace(chunk_id="c1", text="đoạn\n\u0338tiếp", char_start=50,
                             char_end=61, page=2, section_path=[])
    registry = SourceRegistry([source])

    cited = registry.citation_for_chunk("c1", "Q", "\u0338tiếp")

    assert cited is not None
    label, citation = cited
    start = citation["char_start"] - source.char_start
    end = citation["char_end"] - source.char_start
    assert source.text[start:end] == "\u0338tiếp"
    assert registry.raw_text(label) == source.text


def test_source_registry_merge_preserves_nonconflicting_labels_and_relabels_collisions():
    left = SourceRegistry([chunk("c1", "a"), chunk("c2", "b")])
    right = SourceRegistry([chunk("c3", "c"), chunk("c4", "d")])
    assert left.label("c1", "S") == "S1"
    assert right.label("c3", "S") == "S1"
    assert right.label("c4", "S") == "S2"

    mapping = left.merge(right)

    assert mapping == {"S1": "S2", "S2": "S3"}
    assert left.raw_text("S2") == "c"
    assert left.resolve("S3")["chunk_id"] == "c4"


def test_why_here_uses_display_hasse_and_only_verbatim_quote_sources():
    chunks = [chunk("qa", "Câu trích hợp lệ."), chunk("qb", "Nguồn khác."),
              chunk("anchor", "Khái niệm A là nền tảng.")]
    nodes = [
        {"node_id": "a", "name": "A", "learnable": True, "module_id": "m1",
         "anchor": {"chunk_id": "anchor", "sentence": "Khái niệm A là nền tảng."}},
        {"node_id": "b", "name": "B", "learnable": True, "module_id": "m2"},
        {"node_id": "c", "name": "C", "learnable": True, "module_id": "m3",
         "display_prerequisites": ["a"]},
    ]
    payload = {
        "nodes": nodes,
        "modules": [{"module_id": "m1", "index": 0}, {"module_id": "m2", "index": 1},
                    {"module_id": "m3", "index": 2}],
        "requires_edges": [
            {"source": "a", "target": "c", "edge_type": "requires", "chunk_ids": ["qa"],
             "quote": "Câu trích hợp lệ."},
            {"source": "b", "target": "c", "edge_type": "requires", "chunk_ids": ["qb"],
             "quote": "Nguồn khác."},
        ],
        "open_edges": [{"source": "a", "target": "c", "edge_type": "requires", "quote": "Câu trích hợp lệ."}],
    }

    result = LearningGraph(payload, chunks).why_here("c", source_registry=SourceRegistry(chunks))

    assert [row["node_id"] for row in result["prerequisites"]] == ["a"]
    row = result["prerequisites"][0]
    assert row["source_label"] == "Q1"
    assert row["citation"]["quote"] == "Câu trích hợp lệ."
    assert row["anchor_label"] == "N1"
    assert row["anchor_citation"]["chunk_id"] == "anchor"


def test_why_here_uses_chunk_ids_when_legacy_edge_has_no_quote_field():
    source_name = "Biến đổi sơ cấp trên ma trận"
    target_name = "Cộng nhiều hàng vào một hàng"
    raw = f"{source_name}:\n+) {target_name};\n+) Đổi chỗ hai hàng."
    chunks = [chunk("c1", raw)]
    graph = LearningGraph({
        "nodes": [
            {"node_id": "parent", "name": source_name, "learnable": True},
            {"node_id": "child", "name": target_name, "learnable": True,
             "display_prerequisites": ["parent"]},
        ],
        "requires_edges": [{"source": "parent", "target": "child", "edge_type": "requires",
                            "chunk_ids": ["c1"], "reason": "generated explanation"}],
    }, chunks)

    result = graph.why_here("child", source_registry=graph.new_source_registry())

    assert len(result["prerequisites"]) == 1
    row = result["prerequisites"][0]
    assert "generated explanation" not in row["quote"]
    assert row["quote"] in raw
    assert row["citation_source"] == "legacy_excerpt"
    assert row["warning"] == "missing_edge_quote"
    assert row["note"] == "Đoạn liên quan; artifact cũ thiếu câu trích bằng chứng của cạnh"
    assert row["source_label"].startswith("S")
    assert row["citation"]["chunk_id"] == "c1"


def test_traverse_hides_unconfirmed_or_uncited_edges_and_caps_results():
    nodes = [{"node_id": f"n{i}", "learnable": True} for i in range(8)]
    edges = [{"source": "n0", "target": f"n{i}", "edge_type": "supports", "quote": f"q{i}"}
             for i in range(1, 7)]
    edges += [{"source": "n0", "target": "n7", "edge_type": "supports", "confirmed": True}]
    graph = LearningGraph({"nodes": nodes, "open_edges": edges}, [])

    result = graph.traverse("n0", "supports")

    assert len(result["edges"]) == 5
    assert all(edge["quote"] for edge in result["edges"])


def test_get_media_includes_only_confirmed_media_even_when_not_in_learnable_nodes():
    graph = LearningGraph({
        "nodes": [{"node_id": "concept", "learnable": True}],
        "non_learnable_nodes": [
            {"node_id": "fig1", "learnable": False, "media_id": "img1", "caption_source": "machine"},
            {"node_id": "fig2", "learnable": False, "media_id": "img2"},
        ],
        "open_edges": [
            {"source": "concept", "target": "fig1", "edge_type": "illustrates", "confirmed": True},
            {"source": "concept", "target": "fig2", "edge_type": "illustrates", "confirmed": False},
        ],
    }, [])

    result = graph.get_media("concept")

    assert len(result) == 1
    assert result[0]["media_id"] == "img1"
    assert result[0]["caption_source"] == "machine"


def test_lookup_returns_bounded_ambiguous_candidates():
    graph = LearningGraph({"nodes": [
        {"node_id": f"n{i}", "name": "Định lý", "learnable": True} for i in range(5)
    ]}, [])

    result = graph.lookup_concept("định lý")

    assert len(result["matches"]) == 3


def test_lookup_accepts_concept_question_wrapper_but_blocks_common_word_in_question():
    chunks = [chunk(f"c{i}", text) for i, text in enumerate([
        "Định thức được xác định từ ma trận.",
        "Định thức cấp hai có công thức.",
        "Định thức cấp ba được khai triển.",
        "Ma trận biểu diễn phép biến đổi.",
        "Ma trận vuông có số hàng bằng số cột.",
        "Ma trận khả nghịch có định thức khác không.",
    ])]
    graph = LearningGraph({"nodes": [
        {"node_id": "det", "display_name": "Định thức", "learnable": True},
        {"node_id": "matrix", "display_name": "Ma trận", "learnable": True},
    ]}, chunks)

    assert graph.lookup_concept("Định thức là gì?")["matches"][0]["node_id"] == "det"
    assert graph.lookup_concept("Ma trận được dùng để biểu diễn gì?")["matches"] == []
