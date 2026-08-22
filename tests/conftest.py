from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from doc2roadmap.domain.models import DocumentNode, DocumentTree
from doc2roadmap.infrastructure.text import UnicodeSentenceSplitter


@dataclass(slots=True)
class WordCounter:
    identifier: str = "test-word-counter:v1"

    def count(self, text: str) -> int:
        return len(text.split())


def reference_tree(prefix: list[DocumentNode] | None = None) -> DocumentTree:
    nodes = [*(prefix or [])]
    order = len(nodes)

    def add(node_type: str, text: str, level: int | None = None) -> None:
        nonlocal order
        nodes.append(DocumentNode(node_type, text, order, level=level, page=1))
        order += 1

    add("section_header", "Chương 2: Mô hình ngôn ngữ", 1)
    add("paragraph", "Chương này trình bày kiến trúc nền tảng.")
    add("paragraph", "Ta bắt đầu từ kiến trúc nền tảng.")
    add("section_header", "2.1 Kiến trúc Transformer", 2)
    add("paragraph", "Transformer bỏ hồi quy.")
    add("paragraph", "Gồm encoder và decoder.")
    add("section_header", "2.1.1 Cơ chế Attention", 3)
    add("paragraph", "Attention gán trọng số.")
    add("paragraph", "Với scaled dot-product.")
    add("formula", "softmax(QK / sqrt(d))V")
    add("table", "Ký hiệu Q, K, V, d")
    add("section_header", "2.1.2 Multi-head Attention", 3)
    add("paragraph", "Multi-head chạy h phép.")
    return DocumentTree(nodes)


def splitter() -> UnicodeSentenceSplitter:
    return UnicodeSentenceSplitter()


@lru_cache(maxsize=None)
def load_docling_fixture(name: str = "nhap-mon-ml"):
    from docling_core.types.doc import DoclingDocument

    path = Path("tests/fixtures/docling") / f"{name}.json"
    return DoclingDocument.model_validate_json(path.read_text(encoding="utf-8"))
