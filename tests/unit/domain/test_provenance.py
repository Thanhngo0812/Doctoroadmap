from types import SimpleNamespace

import pytest

from doc2roadmap.domain.provenance import (
    DEFAULT_DEFINITION_SIGNALS,
    definition_signals_near_name,
    quote_is_verbatim,
    select_provenance_candidates,
)


def chunk(chunk_id, text, order_index):
    return SimpleNamespace(chunk_id=chunk_id, text=text, order_index=order_index)


def test_definition_signal_must_share_a_sentence_with_name_or_alias():
    names = ("alpha", "tên khác")

    assert definition_signals_near_name(
        "Alpha được định nghĩa là đại lượng thứ nhất.", names, DEFAULT_DEFINITION_SIGNALS
    ) == ["được định nghĩa", "định nghĩa là"]
    assert definition_signals_near_name(
        "Alpha xuất hiện ở đây. Đại lượng được định nghĩa là số thực.",
        names,
        DEFAULT_DEFINITION_SIGNALS,
    ) == []
    assert definition_signals_near_name(
        "Ta gọi Tên khác là đại lượng thứ nhất.", names, DEFAULT_DEFINITION_SIGNALS
    ) == ["ta gọi"]


def test_candidates_include_exact_and_dense_exclude_existing_and_cap_in_document_order():
    node = {
        "node_id": "a",
        "name": "Alpha",
        "aliases": [],
        "defining_chunk_ids": ["existing"],
    }
    chunks = [chunk("existing", "Alpha", -1)] + [
        chunk(f"c{index}", f"Alpha is called item {index}.", index)
        for index in range(14)
    ]
    mention_map = {
        "existing": {"a": {"channels": ["exact"]}},
        **{
            f"c{index}": {
                "a": {"channels": ["exact"] if index % 2 else ["dense"]}
            }
            for index in range(14)
        },
    }

    rows = select_provenance_candidates(
        node,
        chunks,
        mention_map,
        signals=DEFAULT_DEFINITION_SIGNALS,
        limit=12,
    )

    assert [row["chunk_id"] for row in rows] == [f"c{index}" for index in range(12)]
    assert rows[0]["channels"] == ["dense"]
    assert rows[1]["channels"] == ["exact"]
    assert all(row["definition_signals"] == ["is called"] for row in rows)


def test_quote_verification_only_normalizes_unicode_and_whitespace():
    assert quote_is_verbatim("Alpha   is defined as one.", "Prefix\nAlpha is defined as one. Suffix")
    assert not quote_is_verbatim("Alpha is one.", "Alpha is defined as one.")
    assert not quote_is_verbatim("", "Alpha is defined as one.")


@pytest.mark.parametrize("limit", [0, -1, 1.5, True])
def test_candidate_limit_must_be_a_positive_integer(limit):
    with pytest.raises(ValueError, match="trần ứng viên"):
        select_provenance_candidates(
            {"node_id": "a", "name": "Alpha"},
            [],
            {},
            signals=DEFAULT_DEFINITION_SIGNALS,
            limit=limit,
        )
