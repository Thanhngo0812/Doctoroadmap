import pytest

from doc2roadmap.domain.canonical_nominations import additional_nominations


def nominate(names, *, evidence=None, **kwargs):
    nodes = [{"node_id": key, "name": name, "aliases": [], "media_id": None,
              "evidence": [{"quote": quote} for quote in (evidence or {}).get(key, [])]}
             for key, name in names.items()]
    return additional_nominations(nodes, **kwargs)


@pytest.mark.parametrize("names,source", [
    ({"a": "Upper triangular matrix", "b": "Upper-triangular matrix"}, "normalized_name"),
    ({"a": "CSDL", "b": "Cơ sở dữ liệu"}, "initialism"),
    ({"a": "Cộng", "b": "Phép cộng"}, "generic_prefix"),
    ({"a": "𝐅^{m,n}", "b": "F m,n"}, "normalized_name"),
])
def test_reuses_identity_name_sources(names, source):
    assert source in nominate(names)[0]["reasons"]


def test_same_a3_sentence_remains_an_optional_literal_evidence_source():
    names = {"a": "Ảnh ánh xạ", "b": "Im f", "c": "Khác"}
    evidence = {"a": ["Một câu bằng chứng."], "b": ["Một câu bằng chứng."]}
    assert nominate(names, evidence=evidence, same_evidence_enabled=True) == [
        {"left": "a", "right": "b", "reasons": ["same_evidence"]}]
    assert not nominate(names, evidence=evidence)
