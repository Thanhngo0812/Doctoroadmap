import hashlib
import json
from types import SimpleNamespace

import pytest

from doc2roadmap.application.use_cases.a8_gold import annotation_scope
from doc2roadmap.application.use_cases.a8_score import score_from_store, score_roadmap_order


SECTIONS = [SimpleNamespace(section_id="ch1", title="Một", level=1, parent_section_id=None, order_index=1),
            SimpleNamespace(section_id="ch2", title="Hai", level=1, parent_section_id=None, order_index=2)]
CHUNKS = [SimpleNamespace(chunk_id=f"c{i}", parent_section_id=f"ch{i}", section_path=[str(i)],
                          page=i, order_index=i) for i in (1, 2)]


def node(node_id):
    return {"node_id": node_id, "name": node_id.upper(), "learnable": True, "node_type": "concept",
            "aliases": [], "defining_chunk_ids": ["c2"], "cluster_id": "g", "first_order_index": 1}


OLD_NODES = [node(key) for key in ("a", "b", "c")]
CURRENT_NODES = [node(key) for key in ("a", "d")]


class Store:
    def __init__(self, redirects=None):
        self.redirects = redirects if redirects is not None else {"b": "middle", "middle": "a", "c": "d"}

    def load_canonical(self, doc_id, version):
        assert doc_id == "book"
        assert version in (1, 2)
        return SimpleNamespace(version=version, manifest={"upstream_version": 1}, payload={
            "doc_id": "book", "stage": "complete", "nodes": OLD_NODES if version == 1 else CURRENT_NODES,
            "redirects": {} if version == 1 else self.redirects,
        })

    def load_latest_canonical(self, doc_id):
        raise AssertionError("Không được chuyển vàng theo canonical latest")

    def load_candidates(self, doc_id, version):
        return SimpleNamespace(manifest={"upstream_version": 1})

    def load_chunks(self, doc_id, version):
        return SimpleNamespace(result=SimpleNamespace(sections=SECTIONS, chunks=CHUNKS))

    def load_graph(self, doc_id, version):
        assert doc_id == "book" and version == 10
        return SimpleNamespace(payload={"doc_id": "book"}, manifest={
            "doc_id": "book", "version": 10, "config": {"canonical_version": 2}, "upstream_version": None,
        })


def write_graph(tmp_path, *, nodes=CURRENT_NODES, canonical_version=2, name="current", **extra):
    path = tmp_path / name / "graph.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"doc_id": "book", "stage": "stages", "nodes": nodes,
               "sequence": [value["node_id"] for value in reversed(nodes)], "modules": [],
               "mention_map": {"c2": {value["node_id"]: {"channels": ["exact"]} for value in nodes}},
               "suspected_pairs": [], "requires_edges": [{"source": "a", "target": "d"}], **extra}
    path.write_text(json.dumps(payload), encoding="utf-8")
    manifest = {"doc_id": "book", "version": 12, "config": {"canonical_version": canonical_version},
                "upstream_version": 10}
    path.with_name("manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return path


def write_gold(tmp_path, *, edges=(("a", "b"), ("b", "c")), targets=("a", "b", "c"), graph_payload=None,
               **extra):
    scope = annotation_scope("book", 1, OLD_NODES, SECTIONS, CHUNKS, chapter="ch2", graph_payload=graph_payload)
    value = {"doc_id": "book", "canonical_version": 1, "chapter_level": 1, "chapter": scope["chapter"],
             "concept_hash": scope["concept_hash"], "targets": list(targets), "annotator": "A",
             "edges": [{"prerequisite": a, "target": b} for a, b in edges], **extra}
    path = tmp_path / "gold.json"
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def test_order_scorer_maps_ids_before_unknown_rejection_and_preserves_the_gold_file(tmp_path):
    gold = write_gold(tmp_path)
    before = hashlib.sha256(gold.read_bytes()).hexdigest()
    report = score_roadmap_order(write_graph(tmp_path), [gold], remap_gold_ids=True, store=Store())

    assert report["gold_edge_count"] == 1
    assert report["gold_order"]["violated"] == 1
    assert report["gold_order"]["out_of_scope"] == 0
    assert report["redirect_dropped_gold_edges"] == 1
    assert report["unresolved_gold_concepts"] == []
    assert report["gold_id_remapping"]["canonical_version"] == 2
    assert hashlib.sha256(gold.read_bytes()).hexdigest() == before


def test_store_scorer_validates_old_scope_then_scores_mapped_edges_and_targets(tmp_path):
    gold = write_gold(tmp_path)
    before = gold.read_bytes()
    report = score_from_store(Store(), "book", write_graph(tmp_path, canonical_version=None), [gold],
                              remap_gold_ids=True, samples=0)
    assert report["canonical_version"] == 2
    assert report["gold"]["edges"] == 1 and report["gold"]["targets"] == 2
    assert report["prediction"]["direct"]["true_positive"] == 1
    assert report["redirect_dropped_gold_edges"] == 1
    assert gold.read_bytes() == before


@pytest.mark.parametrize("scorer", ["order", "store"])
def test_remapping_refuses_and_lists_all_unresolved_concepts_including_target_only(tmp_path, scorer):
    gold = write_gold(tmp_path, edges=(("gone", "c"), ("foreign", "c")), targets=("target_only", "c"))
    graph = write_graph(tmp_path)
    store = Store({"c": "d", "gone": None, "target_only": "missing"})
    with pytest.raises(ValueError) as error:
        if scorer == "order":
            score_roadmap_order(graph, [gold], remap_gold_ids=True, store=store)
        else:
            score_from_store(store, "book", graph, [gold], remap_gold_ids=True, samples=0)
    assert all(key in str(error.value) for key in ("gone", "foreign", "target_only"))
    assert error.value.report["unresolved_gold_concepts"] == ["foreign", "gone", "target_only"]


def test_remapping_cycle_is_an_error_in_the_full_scorer(tmp_path):
    gold = write_gold(tmp_path)
    with pytest.raises(ValueError, match="vòng"):
        score_roadmap_order(write_graph(tmp_path), [gold], remap_gold_ids=True,
                            store=Store({"b": "middle", "middle": "b", "c": "d"}))


def test_v3_identity_mapping_runs_after_canonical_redirects_and_maps_targets(tmp_path):
    gold = write_gold(tmp_path)
    graph = write_graph(tmp_path, nodes=[node("a")], merged_nodes=[node("d")],
                        identity_map={"d": "a"}, sequence=["a"])
    report = score_roadmap_order(graph, [gold], remap_gold_ids=True, store=Store())
    assert report["redirect_dropped_gold_edges"] == 1
    assert report["identity_dropped_gold_edges"] == 1
    assert report["gold_edge_count"] == 0 and report["gold_order"]["out_of_scope"] == 0
    report = score_from_store(Store(), "book", graph, [gold], remap_gold_ids=True, samples=0)
    assert report["gold"]["targets"] == 1 and report["gold"]["edges"] == 0
    assert report["identity_dropped_gold_edges"] == 1


def test_remapping_does_not_bypass_the_original_gold_concept_hash_guard(tmp_path):
    gold = write_gold(tmp_path, concept_hash="invalid")
    with pytest.raises(ValueError, match="danh sách khái niệm khác"):
        score_from_store(Store(), "book", write_graph(tmp_path), [gold], remap_gold_ids=True, samples=0)


def test_provenance_backed_gold_requires_and_accepts_its_original_graph(tmp_path):
    source_nodes = [{**value, "defining_chunk_ids": ["c1"]} if value["node_id"] == "b" else value
                    for value in OLD_NODES]
    source = write_graph(tmp_path, name="source", nodes=source_nodes, canonical_version=1)
    gold = write_gold(tmp_path, graph_payload={"nodes": source_nodes}, targets=("a", "c"))
    graph = write_graph(tmp_path)
    with pytest.raises(ValueError, match="gold-graph"):
        score_from_store(Store(), "book", graph, [gold], remap_gold_ids=True, samples=0)
    report = score_from_store(Store(), "book", graph, [gold], remap_gold_ids=True,
                              gold_graph_path=source, samples=0)
    assert report["gold"]["edges"] == 1


def test_original_gold_graph_must_be_bound_to_the_gold_canonical_version(tmp_path):
    gold = write_gold(tmp_path)
    graph = write_graph(tmp_path)
    with pytest.raises(ValueError, match="canonical.*vàng"):
        score_from_store(Store(), "book", graph, [gold], remap_gold_ids=True,
                          gold_graph_path=graph, samples=0)


def test_remapping_refuses_graph_without_canonical_lineage(tmp_path):
    gold = write_gold(tmp_path)
    graph = write_graph(tmp_path)
    graph.with_name("manifest.json").unlink()
    with pytest.raises(ValueError, match="manifest"):
        score_roadmap_order(graph, [gold], remap_gold_ids=True, store=Store())


@pytest.mark.parametrize("failure", ["foreign_document", "missing_canonical", "cyclic_upstream"])
def test_remapping_rejects_invalid_graph_manifest_lineage(tmp_path, failure):
    gold = write_gold(tmp_path)
    graph = write_graph(tmp_path, canonical_version=None)
    manifest_path = graph.with_name("manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    store = Store()
    if failure == "foreign_document":
        manifest["doc_id"] = "other"
        expected = "doc_id"
    elif failure == "missing_canonical":
        manifest["upstream_version"] = None
        expected = "không xác định được canonical"
    else:
        store.load_graph = lambda *_: SimpleNamespace(manifest=manifest)
        expected = "vòng lặp upstream"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match=expected):
        score_roadmap_order(graph, [gold], remap_gold_ids=True, store=store)


def test_remapping_order_requires_a_store_and_source_graph_requires_opt_in(tmp_path):
    gold, graph = write_gold(tmp_path), write_graph(tmp_path)
    with pytest.raises(ValueError, match="kho artifact"):
        score_roadmap_order(graph, [gold], remap_gold_ids=True)
    with pytest.raises(ValueError, match="gold-graph cần bật"):
        score_from_store(Store(), "book", graph, [gold], gold_graph_path=graph, samples=0)


def test_source_graph_from_another_document_is_refused_before_scope_validation(tmp_path):
    gold = write_gold(tmp_path)
    graph = write_graph(tmp_path)
    source = write_graph(tmp_path, name="source", nodes=OLD_NODES, canonical_version=1, doc_id="other")
    with pytest.raises(ValueError, match="graph gán vàng phải cùng doc_id"):
        score_from_store(Store(), "book", graph, [gold], gold_graph_path=source,
                          remap_gold_ids=True, samples=0)


def test_unresolved_ids_cannot_disappear_in_annotator_intersection(tmp_path):
    gold = write_gold(tmp_path, edges=(("gone", "c"),), targets=("c",))
    second = tmp_path / "second.json"
    second.write_text(json.dumps({**json.loads(gold.read_text(encoding="utf-8")), "edges": []}), encoding="utf-8")
    with pytest.raises(ValueError, match="gone"):
        score_roadmap_order(write_graph(tmp_path), [gold, second], mode="intersection",
                            remap_gold_ids=True, store=Store())


def test_without_opt_in_order_scorer_keeps_its_original_unknown_id_error(tmp_path):
    gold = write_gold(tmp_path)
    with pytest.raises(ValueError) as error:
        score_roadmap_order(write_graph(tmp_path), [gold])
    assert str(error.value) == ("2 khái niệm của bộ vàng không có trong đồ thị, ví dụ b; "
                               "bộ vàng này không thuộc danh tính của artifact đang chấm")


def test_without_opt_in_store_scorer_keeps_its_original_missing_concepts_error(tmp_path):
    gold = write_gold(tmp_path)
    with pytest.raises(ValueError, match="artifact graph thiếu 2 khái niệm của bộ vàng, ví dụ b"):
        score_from_store(Store(), "book", write_graph(tmp_path), [gold], samples=0)
