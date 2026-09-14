import pytest

from doc2roadmap.domain.canonical import (
    name_key, alias_kind, evidence_missing_name, candidate_warnings, group_names,
    build_nodes, remap_edges, compare_nodes, redirects,
)
from doc2roadmap.domain.entities import EntityCandidate, EvidenceSpan, VerifiedAlias, CandidateEdge


def entity(id, name, kind="concept", order=1, learnable=True):
    return EntityCandidate(id, "doc", kind, name, "shared draft",
                           [EvidenceSpan(id, 0, len(name), name)], first_order_index=order, learnable=learnable)


def test_name_and_alias_boundaries():
    for a, b in [("hoá", "hóa"), ("uỷ", "ủy"), ("thuý", "thúy")]:
        assert name_key(a) == name_key(b)
    assert name_key("tỷ lệ") != name_key("tỉ lệ")
    assert name_key("giả thiết") != name_key("giả thuyết")
    for name in ["F", "f", "μ", "x σ n", "t α", "P(A|B)"]:
        assert alias_kind(name) == "symbol"
    for name in ["ML", "JWT", "E2E"]:
        assert alias_kind(name) == "abbreviation"
    for name in ["Học", "Khoảng ước lượng của μ"]:
        assert alias_kind(name) == "name"


def test_quality_warnings_are_advisory_and_section_scoped():
    a, b = entity("a", "Học"), entity("b", "Spam Filtering")
    a.evidence = [EvidenceSpan("a", 0, 3, "hoc")]
    b.evidence = [EvidenceSpan("b", 0, 24, "hệ thống chống thư rác")]
    assert not evidence_missing_name(a)
    assert evidence_missing_name(b)
    assert candidate_warnings([a, b], {"a": "s", "b": "s"})["duplicate_description_name_count"] == 2
    assert candidate_warnings([a, b], {"a": "s", "b": "other"})["duplicate_description_count"] == 0
    b.aliases = [VerifiedAlias("chống thư rác", b.evidence[0])]
    assert not evidence_missing_name(b)
    b.evidence, b.media_evidence_id = [], "img"
    assert not evidence_missing_name(b)
    assert a.description == b.description == "shared draft"


def test_name_frequency_alias_exclusion_symbols_and_anchor_identity():
    a, b = entity("a", "Machine Learning"), entity("b", "ML", order=2)
    a.aliases = [VerifiedAlias("x", a.evidence[0]), VerifiedAlias("F", a.evidence[0]), VerifiedAlias("f", a.evidence[0])]
    first, _, _ = build_nodes([[a, b]], "ML ML ML Machine Learning x x x")
    assert first[0]["name"] == "Machine Learning"
    assert {s["name"] for s in first[0]["symbols"]} == {"x", "F", "f"}
    c = entity("b", "Học máy", order=2)
    second, _, _ = build_nodes([[a, c]], "Học máy Học máy")
    assert second[0]["name"] == "Học máy"
    assert first[0]["node_id"] == second[0]["node_id"]
    tied, _, _ = build_nodes([[a, c]], "")
    assert tied[0]["name"] == a.name
    with pytest.raises(ValueError):
        build_nodes([[entity("z", "μ")]], "μ μ")


def test_canonical_name_counts_nested_names_without_overlap():
    short = entity("a", "Naïve Bayes")
    long = entity("b", "Naïve Bayes Classification", order=2)

    nodes, _, _ = build_nodes(
        [[short, long]],
        "Naïve Bayes Classification. " * 3 + "Naïve Bayes.",
    )

    assert nodes[0]["name"] == "Naïve Bayes Classification"
    assert "Naïve Bayes" in {alias["name"] for alias in nodes[0]["aliases"]}


def test_canonical_name_tie_between_nested_names_prefers_the_fuller_one():
    cut = entity("a", "Bernoulli Naive")
    full = entity("b", "Bernoulli Naive Bayes", order=2)

    nodes, _, _ = build_nodes(
        [[cut, full]], "Bernoulli Naive Bayes và Bernoulli Naive."
    )

    assert nodes[0]["name"] == "Bernoulli Naive Bayes"


def test_canonical_name_tie_between_unrelated_names_keeps_earliest():
    vi = entity("a", "Kiến trúc phân lớp")
    en = entity("b", "Layered Architecture", order=2)

    nodes, _, _ = build_nodes(
        [[vi, en]], "kiến trúc phân lớp (Layered Architecture)"
    )

    assert nodes[0]["name"] == "Kiến trúc phân lớp"


def test_canonical_name_with_symbol_suffix_ranks_below_plain_name():
    plain = entity("a", "Phương sai tổng thể")
    symbol = entity("b", "Phương sai tổng thể σ 2", order=2)

    nodes, _, _ = build_nodes(
        [[plain, symbol]],
        "phương sai tổng thể σ 2. " * 3 + "phương sai tổng thể.",
    )

    assert nodes[0]["name"] == "Phương sai tổng thể"


def test_alias_never_repeats_the_canonical_name():
    a = entity("a", "Race Condition")
    b = entity("b", "Tranh chấp dữ liệu", order=2)
    b.aliases = [
        VerifiedAlias("Race Condition", b.evidence[0]),
        VerifiedAlias("race condition", b.evidence[0]),
    ]

    nodes, _, _ = build_nodes(
        [[a, b]], "Race Condition. Race Condition. Tranh chấp dữ liệu."
    )

    assert nodes[0]["name"] == "Race Condition"
    names = [alias["name"] for alias in nodes[0]["aliases"]]
    assert "Tranh chấp dữ liệu" in names
    assert not [name for name in names if name.casefold() == "race condition"]


def test_type_votes_specificity_frequency_alphabetical_and_review():
    a, b = entity("a", "Term", "concept"), entity("b", "Term", "method", learnable=False)
    nodes, log, review = build_nodes([[a, b]], "Term")
    assert nodes[0]["node_type"] == "method" and not nodes[0]["learnable"]
    assert log and review
    a.node_type = "algorithm"
    assert build_nodes([[a, b]], "")[0][0]["node_type"] == "algorithm"
    extra = entity("c", "Extra", "method")
    assert build_nodes([[a, b], [extra]], "")[0][0]["node_type"] == "method"
    b.node_type = "thuật toán"
    assert build_nodes([[a, b]], "", {"thuật toán": "algorithm"})[0][0]["learnable"]


def test_edge_remapping_and_redirects():
    a, b, c = entity("a", "Alpha"), entity("b", "Alpha"), entity("c", "Charlie")
    nodes, _, _ = build_nodes(group_names([a, b, c]), "")
    edges, metrics = remap_edges(nodes, [CandidateEdge("a", "b", "uses"),
        CandidateEdge("a", "c", "uses", evidence=a.evidence),
        CandidateEdge("b", "c", "USES", evidence=b.evidence, confirmed=True)])
    assert metrics["self_edges_removed"] == metrics["duplicate_edges_removed"] == 1
    assert len(edges) == 1 and edges[0]["confirmed"] and len(edges[0]["evidence"]) == 2
    assert edges[0]["origins"] == ["a3"]
    old, _, _ = build_nodes([[a], [b], [c]], "")
    redirect = redirects(old, nodes)
    assert redirect[old[1]["node_id"]] == nodes[0]["node_id"]
    assert redirects(nodes, old, redirect) == {}
    assert compare_nodes(nodes, nodes)["members"] == 1


def test_redirect_history_split_disappearance_and_return():
    old = [{"node_id": "old", "members": ["a", "b", "c"]}]
    split = [{"node_id": "left", "members": ["a"]}, {"node_id": "right", "members": ["b", "c"]}]
    history = redirects(old, split)
    assert history == {"old": "right"}
    vanished = redirects(split, [], history)
    assert vanished == {"old": None, "left": None, "right": None}
    restored = redirects([], old, vanished)
    assert "old" not in restored
    assert not {n["node_id"] for n in old} & restored.keys()
    third = [{"node_id": "third", "members": ["a", "b", "c"]}]
    assert redirects(split, third, history) == {"old": "third", "left": "third", "right": "third"}
    assert redirects(old, old) == {}
