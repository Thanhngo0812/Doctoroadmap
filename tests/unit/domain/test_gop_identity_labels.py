import pytest

from doc2roadmap.domain.canonical_decisions import ContradictionError, validate_partition


LABELS = ("synonym", "synonym_of", "same_as", "alias", "alias_of", "abbreviation", "abbreviation_of",
          "acronym", "acronym_of", "initialism_of", "translation", "translation_of", "equivalent_to", "identical_to")


def partition(label, same=False):
    return {"nodes": [{"groups": ["a", "b"], "reason": "same"}] if same else
            [{"groups": [key], "reason": "different"} for key in "ab"], "deferred": [],
            "relations": [{"source": "a", "target": "b", "edge_type": label, "chunk_ids": ["c"], "reason": "fixture"}]}


@pytest.mark.parametrize("label", LABELS)
def test_gop_rejects_each_normalized_identity_label_between_separate_nodes(label):
    with pytest.raises(ContradictionError, match="R2:"):
        validate_partition(partition("  " + label.upper() + "  "), {"a": ["c"], "b": ["c"]}, gop=True)
    assert validate_partition(partition(label, same=True), {"a": ["c"], "b": ["c"]}, gop=True)


@pytest.mark.parametrize("label", ["same_category", "synonym_candidate", "non_alias_of", "translation_method"])
def test_gop_does_not_match_identity_label_substrings(label):
    assert validate_partition(partition(label), {"a": ["c"], "b": ["c"]}, gop=True)


def test_v3_keeps_its_original_identity_label_set():
    assert validate_partition(partition("synonym"), {"a": ["c"], "b": ["c"]})
