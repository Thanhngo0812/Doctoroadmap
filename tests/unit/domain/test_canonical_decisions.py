from types import SimpleNamespace
import pytest

from doc2roadmap.domain.canonical_decisions import validate_partition, guarded_components, validate_description, document_language, vietnamese
from doc2roadmap.domain.nomination import nomination_graph
from doc2roadmap.domain.entities import EntityCandidate, EvidenceSpan, VerifiedAlias


def test_partition_guards_and_transitive_conflict():
    source = {"a": ["ca"], "b": ["cb"], "c": ["cc"]}
    good = {"nodes": [{"groups": ["a", "b"], "reason": "same"}, {"groups": ["c"], "reason": "other"}],
            "deferred": [], "subtype_edges": [{"child": "a", "parent": "c", "chunk_ids": ["ca"], "reason": "subtype"}]}
    assert validate_partition(good, source) is good
    import copy
    for mutate in [lambda v: v["nodes"][0]["groups"].pop(),
                   lambda v: v["nodes"][0]["groups"].append("c"),
                   lambda v: v["subtype_edges"][0].update(edge_type="requires")]:
        bad = copy.deepcopy(good); mutate(bad)
        with pytest.raises(ValueError):
            validate_partition(bad, source)
    result, conflict = guarded_components(["a", "b", "c"], [("a", "b"), ("b", "c")], [("a", "c")])
    assert sorted(result) == [["a"], ["b"], ["c"]] and conflict == [["a", "b", "c"]]
    assert guarded_components(["a", "b"], [("a", "b")], [])[0] == [["a", "b"]]


def test_description_and_language_boundaries():
    good = {"sentences": [{"text": "Học máy.", "chunk_ids": ["c"]}], "defining_chunk_ids": ["c"], "nghi_gop_nham": True, "reason": "sources conflict"}
    validate_description(good, ["c"])
    for value in [{**good, "defining_chunk_ids": ["outside"]}, {**good, "sentences": []},
                  {**good, "reason": ""}, {**good, "sentences": [{"text": "text", "chunk_ids": ["outside"]}]}]:
        with pytest.raises(ValueError):
            validate_description(value, ["c"])
    assert vietnamese("học one two three four")
    assert not vietnamese("học one two three four five")
    chunks = [SimpleNamespace(text="học máy", token_count=100), SimpleNamespace(text="English text", token_count=99)]
    assert document_language(chunks) == "vi"
    chunks[1].token_count = 101
    assert document_language(chunks) == "en"
    chunks[1].token_count = 100
    assert document_language(chunks) == "vi"


def test_description_rejects_multiple_sentences_per_citation():
    value = {"sentences": [{"text": "One. Two. Three. Four. Five.", "chunk_ids": ["c"]}],
             "defining_chunk_ids": ["c"], "nghi_gop_nham": False, "reason": ""}
    with pytest.raises(ValueError):
        validate_description(value, ["c"])


def test_nomination_mutual_neighbors_symbols_seed_and_cluster_cap():
    def entity(id, name):
        return EntityCandidate(id, "doc", "concept", name, None)
    a, b, c = entity("a", "Alpha"), entity("b", "Beta"), entity("c", "Gamma")
    a.aliases = [VerifiedAlias("f", EvidenceSpan("c", 0, 1, "f"))]
    b.aliases = [VerifiedAlias("f", EvidenceSpan("d", 0, 1, "f"))]
    graph = nomination_graph({"a": [a], "b": [b]}, {"a": [1., 0.], "b": [0., 1.]})
    assert graph["edges"] == []
    graph = nomination_graph({"a": [a], "b": [b], "c": [c]}, {"a": [1., 0.], "b": [.9, .1], "c": [.1, .9]}, k=1)
    assert [(e["source"], e["target"]) for e in graph["edges"]] == [("a", "b")]
    groups = {str(i): [entity(str(i), "Shared name " + str(i))] for i in range(12)}
    vectors = {str(i): [1., .001*i] for i in range(12)}
    first = nomination_graph(groups, vectors, resolution=.01, cap=9)
    assert first == nomination_graph(groups, vectors, resolution=.01, cap=9)
    assert max(map(len, first["clusters"]), default=0) <= 9
    assert first["cut_edges"]


def test_subtype_edges_are_filtered_separately_from_the_partition():
    from doc2roadmap.domain.canonical_decisions import split_subtype_edges
    import copy
    source = {"a": ["ca"], "b": ["cb"], "c": ["cc"]}
    good = {"nodes": [{"groups": ["a", "b"], "reason": "same"}, {"groups": ["c"], "reason": "other"}],
            "deferred": [], "subtype_edges": [{"child": "a", "parent": "c", "chunk_ids": ["ca"], "reason": "subtype"}]}
    for mutate in [lambda v: v["subtype_edges"][0].update(parent="b"),
                   lambda v: v["subtype_edges"][0].update(chunk_ids=["outside"])]:
        bad = copy.deepcopy(good); mutate(bad)
        assert validate_partition(bad, source) is bad
        kept, rejected = split_subtype_edges(bad, source)
        assert kept == [] and len(rejected) == 1 and rejected[0]["error"]
    assert split_subtype_edges(good, source) == (good["subtype_edges"], [])


def test_tables_and_code_do_not_decide_description_language():
    prose = SimpleNamespace(text="Phân lớp là quá trình dự đoán nhãn lớp cho dữ liệu đầu vào dựa trên các đặc trưng.",
                            token_count=40, block_types=["text"])
    table = SimpleNamespace(text="| Outlook | Temp | Humidity | Windy | Play |\n| Sunny | Hot | High | False | No |" * 8,
                            token_count=500, block_types=["table"])
    code = SimpleNamespace(text="from sklearn.naive_bayes import MultinomialNB\nmodel = MultinomialNB()",
                           token_count=200, block_types=["code"])
    assert document_language([prose, prose, table, code]) == "vi"
    assert document_language([table, code]) == "en"


def test_subtype_conflicting_with_a3_relation_is_found_in_either_direction():  # F75
    from doc2roadmap.domain.canonical_decisions import find_subtype_conflicts
    a3 = [{"source": "a", "target": "b", "edge_type": "component_of"},
          {"source": "d", "target": "c", "edge_type": "uses"},
          {"source": "e", "target": "f", "edge_type": "example_of"},
          {"source": "g", "target": "h", "edge_type": "requires"}]
    proposed = [{"source": s, "target": t, "edge_type": "subtype_of"} for s, t in
                [("a", "b"), ("c", "d"), ("e", "f"), ("g", "h"), ("i", "j")]]
    conflicts = find_subtype_conflicts(a3, proposed)
    assert [(e["source"], e["target"], e["a3_edge_types"]) for e in conflicts] == [
        ("a", "b", ["component_of"]), ("c", "d", ["uses"])]
