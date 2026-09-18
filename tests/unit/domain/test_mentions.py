from types import SimpleNamespace

from doc2roadmap.domain.mentions import (
    build_mention_derivatives,
    dense_mentions,
    exact_mentions,
)


def node(node_id, name, *, aliases=(), symbols=(), cluster="g1", defining=(), extracted=()):
    return {
        "node_id": node_id,
        "name": name,
        "aliases": [{"name": value} for value in aliases],
        "symbols": list(symbols),
        "learnable": True,
        "cluster_id": cluster,
        "defining_chunk_ids": list(defining),
        "source_chunk_ids": list(extracted or defining),
    }


def chunk(chunk_id, text, section="s1", order=0):
    return SimpleNamespace(
        chunk_id=chunk_id,
        text=text,
        parent_section_id=section,
        order_index=order,
    )


def test_exact_is_accent_sensitive_normalizes_i_y_and_keeps_leftmost_longest():
    nodes = [
        node("long", "Kỹ thuật"),
        node("short", "Kỹ"),
        node("symbol", "μ", symbols=("μ",)),
    ]
    matches = exact_mentions(
        nodes,
        [
            chunk("c1", "Kĩ thuật dùng μ."),
            chunk("c2", "ky thuat khong dau"),
        ],
        common_names=set(),
    )
    assert matches == {"c1": {"long"}}


def test_dense_uses_row_and_chunk_centering_then_top_k():
    matches, scores = dense_mentions(
        {"a": (1.0, 0.0), "b": (0.0, 1.0)},
        {"hub": (1.0, 1.0), "a-only": (1.0, 0.0), "b-only": (0.0, 1.0)},
        top_k=1,
        min_z=0.0,
    )
    assert matches == {"a-only": {"a"}, "b-only": {"b"}}
    assert scores[("a", "a-only")] > scores[("a", "hub")]
    assert scores[("b", "b-only")] > scores[("b", "hub")]


def test_dense_has_no_absolute_cosine_floor():
    matches, _ = dense_mentions(
        {"a": (1.0, 0.0), "b": (0.0, 1.0)},
        {"x": (-1.0, -0.2), "y": (-0.2, -1.0)},
        top_k=1,
        min_z=0.0,
    )
    assert matches == {"y": {"a"}, "x": {"b"}}


def test_derivatives_keep_directions_channels_and_all_four_pair_sources():
    nodes = [
        node("a", "A", cluster="g1", defining=("c1",)),
        node("b", "B", cluster="g2", defining=("c2",)),
        node("c", "C", cluster="g1", defining=("c3",)),
    ]
    chunks = [
        chunk("c1", "A B", "s1", 0),
        chunk("c2", "B", "s1", 1),
        chunk("c3", "C", "s2", 2),
    ]
    mentions = {
        "c1": {
            "a": {"level": "definition", "channels": ["provenance"], "confidence": 1.0},
            "b": {"level": "mention", "channels": ["exact"]},
            "c": {"level": "mention", "channels": ["dense"]},
        },
        "c2": {"b": {"level": "definition", "channels": ["provenance"], "confidence": 1.0}},
        "c3": {"c": {"level": "definition", "channels": ["provenance"], "confidence": 1.0}},
    }
    result = build_mention_derivatives(
        nodes,
        chunks,
        mentions,
        [{"source": "b", "target": "c", "edge_type": "subtype_of", "origins": ["a3"]}],
        pair_cluster_top_k=1,
    )
    assert {tuple((row["source"], row["target"])) for row in result["citations"]} >= {("b", "a"), ("c", "a")}
    assert any({row["left"], row["right"]} == {"a", "b"} for row in result["contact_pairs"])
    assert not any({row["left"], row["right"]} == {"a", "c"} for row in result["contact_pairs"])
    ledger = result["pair_cluster_ledger"][0]
    assert set(ledger) >= {"exact_weight", "dense_weight", "selected"}
    assert ledger["selected"]
    pairs = {frozenset((row["left"], row["right"])): set(row["sources"]) for row in result["suspected_pairs"]}
    assert "same_section" in pairs[frozenset(("a", "b"))]
    assert "citation_hard" in pairs[frozenset(("a", "b"))]
    assert "contact" in pairs[frozenset(("a", "b"))]
    assert "proposed_relation" in pairs[frozenset(("b", "c"))]


def test_citations_exclude_co_definitions_and_split_hard_from_dense_only():
    nodes = [
        node("a", "A", defining=("c1",)),
        node("b", "B", defining=("c1",)),
        node("c", "C", defining=("c2",)),
    ]
    mentions = {
        "c1": {
            "a": {"level": "definition", "channels": ["provenance"]},
            "b": {"level": "definition", "channels": ["provenance"]},
            "c": {"level": "mention", "channels": ["dense"]},
        },
        "c2": {
            "c": {"level": "definition", "channels": ["provenance"]},
            "a": {"level": "mention", "channels": ["exact", "dense"]},
        },
    }
    result = build_mention_derivatives(
        nodes,
        [chunk("c1", "A B C"), chunk("c2", "C A")],
        mentions,
        [],
        pair_cluster_top_k=1,
    )
    citations = {(row["source"], row["target"]): row for row in result["citations"]}
    assert ("a", "b") not in citations and ("b", "a") not in citations
    assert citations["c", "a"]["strength"] == "soft"
    assert citations["a", "c"]["strength"] == "hard"


def test_pair_cluster_ledger_does_not_mix_exact_and_dense_counters():
    nodes = [
        node("a", "A", cluster="g1"),
        node("b", "B", cluster="g2"),
        node("c", "C", cluster="g3"),
        node("d", "D", cluster="g4"),
        node("e", "E", cluster="g5"),
    ]
    chunks = [chunk("c1", "A B"), chunk("c2", "C D")]
    mentions = {
        "c1": {
            "a": {"channels": ["exact"]},
            "b": {"channels": ["exact"]},
            "e": {"channels": ["exact"]},
        },
        "c2": {"c": {"channels": ["dense"]}, "d": {"channels": ["dense"]}},
    }
    result = build_mention_derivatives(nodes, chunks, mentions, [], pair_cluster_top_k=0)
    ledger = {
        (row["left_cluster"], row["right_cluster"]): row
        for row in result["pair_cluster_ledger"]
    }
    assert ledger["g1", "g2"]["exact_weight"] > 0
    assert ledger["g1", "g2"]["dense_weight"] == 0
    assert ledger["g3", "g4"]["exact_weight"] == 0
    assert ledger["g3", "g4"]["dense_weight"] > 0
    assert all(row["selected"] for row in ledger.values())
