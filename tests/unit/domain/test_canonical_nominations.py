from types import SimpleNamespace

import pytest

from doc2roadmap.domain.canonical_nominations import additional_nominations


def nominate(names, *, evidence=None, vectors=None, **kwargs):
    nodes = [{"node_id": key, "name": name, "aliases": [], "media_id": None,
              "evidence": [{"quote": quote} for quote in (evidence or {}).get(key, [])]}
             for key, name in names.items()]
    groups = {key: [SimpleNamespace(candidate_id=key)] for key in names}
    return additional_nominations(nodes, groups, vectors or {}, **kwargs)


@pytest.mark.parametrize("names,source", [
    ({"a": "Upper triangular matrix", "b": "Upper-triangular matrix"}, "normalized_name"),
    ({"a": "CSDL", "b": "Cơ sở dữ liệu"}, "initialism"),
    ({"a": "Cộng", "b": "Phép cộng"}, "generic_prefix"),
    ({"a": "𝐅^{m,n}", "b": "F m,n"}, "normalized_name"),
])
def test_reuses_identity_name_sources(names, source):
    assert source in nominate(names)[0]["reasons"]


def test_same_a3_sentence_and_description_are_separate_nomination_sources():
    names = {"a": "Ảnh ánh xạ", "b": "Im f", "c": "Vắng vector"}
    rows = nominate(names, evidence={"a": ["Một câu bằng chứng."], "b": ["Một câu bằng chứng."]},
                    vectors={"a": [1., 0.], "b": [1., .01]}, same_evidence_enabled=True)
    assert rows == [{"left": "a", "right": "b", "reasons": ["description_similarity", "same_evidence"]}]
    assert not nominate(names, vectors={"a": [1., 0.]})
    assert not nominate(names, vectors={"a": [1., 0.], "b": [1., .01]}, semantic_min_similarity=1.)


def test_description_neighbors_respect_top_k_and_missing_member_vectors():
    names = {key: f"Nội dung {index}" for index, key in enumerate("abcdef")}
    rows = nominate(names, vectors={key: [1., 0.] for key in names}, semantic_top_k=1)
    assert len(rows) == 5 and not any({row["left"], row["right"]} == {"e", "f"} for row in rows)
    nodes = [{"node_id": key, "name": name, "aliases": [], "media_id": None} for key, name in names.items()]
    groups = {key: [SimpleNamespace(candidate_id=key)] for key in names}
    groups["a"].append(SimpleNamespace(candidate_id="missing"))
    rows = additional_nominations(nodes, groups, {key: [1., 0.] for key in names})
    assert not any("a" in (row["left"], row["right"]) for row in rows)
