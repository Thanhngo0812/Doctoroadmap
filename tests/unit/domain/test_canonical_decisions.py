from types import SimpleNamespace
import pytest

from doc2roadmap.domain.canonical_decisions import (
    ContradictionError,
    validate_partition,
    split_relation_edges,
    guarded_components,
    validate_description,
    document_language,
    vietnamese,
)
from doc2roadmap.domain.nomination import nomination_graph
from doc2roadmap.domain.entities import EntityCandidate, EvidenceSpan, VerifiedAlias


def test_partition_guards_and_transitive_conflict():
    source = {"a": ["ca"], "b": ["cb"], "c": ["cc"]}
    good = {"nodes": [{"groups": ["a", "b"], "reason": "same"}, {"groups": ["c"], "reason": "other"}],
            "deferred": [], "relations": [{"source": "a", "target": "c", "edge_type": "subtype_of",
                                                "chunk_ids": ["ca"], "reason": "subtype"}]}
    assert validate_partition(good, source) is good
    import copy
    for mutate in [lambda v: v["nodes"][0]["groups"].pop(),
                   lambda v: v["nodes"][0]["groups"].append("c"),
                   lambda v: v["relations"][0].update(unexpected=True)]:
        bad = copy.deepcopy(good); mutate(bad)
        with pytest.raises(ValueError):
            validate_partition(bad, source)
    result, conflict = guarded_components(["a", "b", "c"], [("a", "b"), ("b", "c")], [("a", "c")])
    assert sorted(result) == [["a"], ["b"], ["c"]] and conflict == [["a", "b", "c"]]
    assert guarded_components(["a", "b"], [("a", "b")], [])[0] == [["a", "b"]]


@pytest.mark.parametrize("edge_type", ["subtype_of", "precedes", "example_of"])
def test_partition_rejects_nonidentity_relation_inside_one_node(edge_type):
    source = {"a": ["ca"], "b": ["cb"]}
    value = {
        "nodes": [{"groups": ["a", "b"], "reason": "same"}],
        "deferred": [],
        "relations": [{"source": "a", "target": "b", "edge_type": edge_type,
                       "chunk_ids": ["ca"], "reason": "fixture"}],
    }

    with pytest.raises(ContradictionError) as error:
        validate_partition(value, source)

    assert all(part in str(error.value) for part in ("a", "b", edge_type))


@pytest.mark.parametrize("edge_type", ["equivalent_to", "Same_As"])
def test_partition_rejects_identity_relation_between_two_nodes(edge_type):
    source = {"a": ["ca"], "b": ["cb"]}
    value = {
        "nodes": [{"groups": ["a"], "reason": "a"}, {"groups": ["b"], "reason": "b"}],
        "deferred": [],
        "relations": [{"source": "a", "target": "b", "edge_type": edge_type,
                       "chunk_ids": ["ca"], "reason": "fixture"}],
    }

    with pytest.raises(ContradictionError) as error:
        validate_partition(value, source)

    assert all(part in str(error.value) for part in ("a", "b", edge_type))


def test_identity_relation_inside_one_node_is_redundant_not_contradictory():
    source = {"a": ["ca"], "b": ["cb"]}
    value = {
        "nodes": [{"groups": ["a", "b"], "reason": "same"}],
        "deferred": [],
        "relations": [{"source": "a", "target": "b", "edge_type": "same_as",
                       "chunk_ids": ["ca"], "reason": "fixture"}],
    }

    assert validate_partition(value, source) is value
    kept, rejected = split_relation_edges(value, source)
    assert kept == [] and len(rejected) == 1


def test_partition_reports_every_consistency_contradiction_together():
    source = {id: ["c" + id] for id in "abcd"}
    value = {
        "nodes": [{"groups": ["a", "b"], "reason": "same"},
                  {"groups": ["c"], "reason": "c"}, {"groups": ["d"], "reason": "d"}],
        "deferred": [],
        "relations": [
            {"source": "a", "target": "b", "edge_type": "precedes",
             "chunk_ids": ["ca"], "reason": "fixture"},
            {"source": "c", "target": "d", "edge_type": "alias_of",
             "chunk_ids": ["cc"], "reason": "fixture"},
        ],
    }

    with pytest.raises(ContradictionError) as error:
        validate_partition(value, source)

    message = str(error.value)
    assert all(part in message for part in ("a", "b", "precedes", "c", "d", "alias_of"))


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


def test_relation_edges_are_normalized_deduplicated_and_keep_first_reason():
    source = {"a": ["ca"], "b": ["cb"], "c": ["cc"]}
    value = {"nodes": [{"groups": ["a"], "reason": "a"}, {"groups": ["b"], "reason": "b"},
                       {"groups": ["c"], "reason": "c"}], "deferred": [],
             "relations": [
                 {"source": "a", "target": "b", "edge_type": " Uses ", "chunk_ids": ["ca"], "reason": "first"},
                 {"source": "a", "target": "b", "edge_type": "uses", "chunk_ids": ["cb"], "reason": "second"},
             ]}

    assert validate_partition(value, source) is value
    kept, rejected = split_relation_edges(value, source)

    assert rejected == []
    assert kept == [{"source": "a", "target": "b", "edge_type": "uses",
                     "chunk_ids": ["ca", "cb"], "reason": "first"}]


@pytest.mark.parametrize(
    "relation,nodes,deferred",
    [
        ({"source": "missing", "target": "b", "edge_type": "uses", "chunk_ids": ["cb"], "reason": "r"},
         [["a"], ["b"], ["c"]], []),
        ({"source": "a", "target": "missing", "edge_type": "uses", "chunk_ids": ["ca"], "reason": "r"},
         [["a"], ["b"], ["c"]], []),
        ({"source": "a", "target": "c", "edge_type": "uses", "chunk_ids": ["ca"], "reason": "r"},
         [["a"], ["b"]], ["c"]),
        ({"source": "a", "target": "b", "edge_type": "uses", "chunk_ids": [], "reason": "r"},
         [["a"], ["b"], ["c"]], []),
        ({"source": "a", "target": "b", "edge_type": "uses", "chunk_ids": ["outside"], "reason": "r"},
         [["a"], ["b"], ["c"]], []),
        ({"source": "a", "target": "b", "edge_type": "uses", "chunk_ids": ["ca"], "reason": " "},
         [["a"], ["b"], ["c"]], []),
        ({"source": "a", "target": "b", "edge_type": " ", "chunk_ids": ["ca"], "reason": "r"},
         [["a"], ["b"], ["c"]], []),
        ({"source": "a", "target": "b", "edge_type": "requires", "chunk_ids": ["ca"], "reason": "r"},
         [["a"], ["b"], ["c"]], []),
        ({"source": "a", "target": "b", "edge_type": "depends_on", "chunk_ids": ["ca"], "reason": "r"},
         [["a"], ["b"], ["c"]], []),
        ({"source": "a", "target": "b", "edge_type": "illustrates", "chunk_ids": ["ca"], "reason": "r"},
         [["a"], ["b"], ["c"]], []),
        ({"source": "a", "target": "b", "edge_type": "tabulates", "chunk_ids": ["ca"], "reason": "r"},
         [["a"], ["b"], ["c"]], []),
    ],
    ids=["unknown-source", "unknown-target", "deferred-target", "empty-chunks",
         "foreign-chunk", "empty-reason", "empty-type", "requires", "requires-alias", "illustrates", "tabulates"],
)
def test_invalid_relation_is_rejected_without_invalidating_partition(relation, nodes, deferred):
    source = {"a": ["ca"], "b": ["cb"], "c": ["cc"]}
    value = {"nodes": [{"groups": groups, "reason": "fixture"} for groups in nodes],
             "deferred": [{"group_id": group, "reason": "fixture"} for group in deferred],
             "relations": [relation]}

    assert validate_partition(value, source) is value
    kept, rejected = split_relation_edges(value, source)

    assert kept == []
    assert len(rejected) == 1
    assert rejected[0]["error"]
    assert "allowed_chunk_ids" in rejected[0]


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
    proposed.append({"source": "a", "target": "b", "edge_type": "uses"})
    conflicts = find_subtype_conflicts(a3, proposed)
    assert [(e["source"], e["target"], e["a3_edge_types"]) for e in conflicts] == [
        ("a", "b", ["component_of"]), ("c", "d", ["uses"])]
