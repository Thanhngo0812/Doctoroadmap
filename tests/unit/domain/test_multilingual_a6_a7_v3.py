from types import SimpleNamespace

from doc2roadmap.domain.mentions import document_common_names
from doc2roadmap.domain.provenance import select_provenance_candidates


def chunk(name, text, order):
    return SimpleNamespace(chunk_id=name, text=text, order_index=order)


def test_common_names_are_measured_on_this_document_in_japanese_and_thai():
    nodes = [{"node_id": "j", "name": "行列", "learnable": True},
             {"node_id": "t", "name": "เมทริกซ์", "learnable": True}]
    chunks = [chunk("c1", "行列とเมทริกซ์", 0), chunk("c2", "行列の例", 1),
              chunk("c3", "行列の定義", 2), chunk("c4", "เมทริกซ์", 3)]
    assert document_common_names(nodes, chunks, threshold=0.5) == {"行列"}


def test_common_name_count_includes_nested_occurrences():
    nodes = [{"node_id": "m", "name": "Matrix", "learnable": True},
             {"node_id": "mm", "name": "Matrix multiplication", "learnable": True}]
    chunks = [chunk("c1", "Matrix multiplication", 0), chunk("c2", "Matrix multiplication", 1),
              chunk("c3", "Vector", 2)]
    assert "Matrix" in document_common_names(nodes, chunks, threshold=0.5)


def test_a7_definition_evidence_is_quote_not_language_specific_signal():
    node = {"node_id": "j", "name": "行列", "defining_chunk_ids": [],
            "evidence": [{"chunk_id": "c1", "quote": "行列は数の配列"}]}
    chunks = [chunk("c1", "行列は数の配列。", 0), chunk("c2", "行列の練習。", 1)]
    mention_map = {"c1": {"j": {"channels": ["exact"]}},
                   "c2": {"j": {"channels": ["exact"]}}}
    rows = select_provenance_candidates(node, chunks, mention_map, limit=12)
    assert [row["definition_evidence"] for row in rows] == [True, False]
    anchored = {**node, "evidence": [], "anchor": {"chunk_id": "c2", "sentence": "行列の練習。"}}
    assert select_provenance_candidates(anchored, chunks, mention_map, limit=12)[1]["definition_evidence"]
