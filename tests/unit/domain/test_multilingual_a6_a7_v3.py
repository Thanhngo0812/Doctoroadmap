from types import SimpleNamespace

from doc2roadmap.domain.mentions import document_common_names


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
