from dataclasses import dataclass
from pathlib import Path

from doc2roadmap.application.use_cases.index_document import (
    IndexDocument,
    SearchDocument,
    retriever_from_payload,
)
from doc2roadmap.domain.models import Chunk, ChunkingResult, DocumentTree, Section
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore


@dataclass
class _Embedding:
    embedding_model_id: str = "fixture-model:2"
    identifier: str = "fixture-embedding:v1"

    def __post_init__(self) -> None:
        self.requests = []

    def embed(self, requests):
        requests = list(requests)
        self.requests.extend(requests)
        return [[1.0, float(index)] for index, _ in enumerate(requests)]


def _chunk(chunk_id: str, text: str, order: int, stage_id: str | None = None) -> Chunk:
    return Chunk(
        chunk_id=chunk_id,
        doc_id="book",
        order_index=order,
        split_index=0,
        page=order + 1,
        char_start=order * 100,
        char_end=order * 100 + len(text),
        parent_section_id=f"s{order}",
        section_path=["Chương 1", f"Mục {order}"],
        heading_level=2,
        block_types=["text"],
        text=text,
        context_prefix=None,
        image_refs=[],
        token_count=10,
        tokenizer_id="test",
    )


def _store(tmp_path: Path) -> tuple[JsonArtifactStore, list[Chunk]]:
    store = JsonArtifactStore(tmp_path)
    chunks = [
        _chunk("c1", "Công thức P(A|B).", 0),
        _chunk("c2", "Quá khớp làm giảm khả năng tổng quát.", 1),
    ]
    parse = store.save_parse(
        "book", "source", "parser", "parse-config", {}, DocumentTree([])
    )
    sections = [
        Section(
            chunk.parent_section_id,
            "book",
            chunk.section_path[-1],
            2,
            2,
            None,
            chunk.section_path,
            chunk.order_index,
            True,
        )
        for chunk in chunks
    ]
    store.save_chunks(
        "book",
        "source",
        "chunk-config",
        {"tokenizer_id": "test"},
        parse.version,
        ChunkingResult("book", sections, chunks, "\n".join(c.text for c in chunks)),
    )
    return store, chunks


def test_index_embeds_section_context_but_persists_unchanged_chunk_text_and_reuses(
    tmp_path: Path,
) -> None:
    store, chunks = _store(tmp_path)
    original = [(chunk.chunk_id, chunk.text) for chunk in chunks]
    embedding = _Embedding()
    use_case = IndexDocument(store, embedding)

    first = use_case.execute("book")
    second = use_case.execute("book")

    assert not first.reused and second.reused
    assert len(embedding.requests) == 2
    assert embedding.requests[0].text == (
        "Chương 1 > Mục 0\n\nCông thức P(A|B)."
    )
    assert [(chunk.chunk_id, chunk.text) for chunk in chunks] == original
    assert first.payload["documents"][0]["text"] == "Công thức P(A|B)."
    assert first.artifact_path.joinpath("retrieval.json").is_file()
    assert first.manifest["embedding_model_id"] == "fixture-model:2"

    retriever = retriever_from_payload(first.payload)
    assert retriever.search_bm25("P(A|B)")[0].chunk_id == "c1"


def test_embedding_model_change_creates_a_new_retrieval_version(tmp_path: Path) -> None:
    store, _ = _store(tmp_path)

    first = IndexDocument(store, _Embedding("model-a:2")).execute("book")
    changed = IndexDocument(store, _Embedding("model-b:2")).execute("book")

    assert first.artifact_version == 1
    assert changed.artifact_version == 2
    assert first.config_hash != changed.config_hash


def test_search_embeds_query_and_applies_stage_filter(tmp_path: Path) -> None:
    store, _ = _store(tmp_path)
    embedding = _Embedding()
    indexed = IndexDocument(store, embedding).execute("book")
    indexed.payload["documents"][0]["stage_id"] = "stage-a"
    indexed.payload["documents"][1]["stage_id"] = "stage-b"
    store.save_retrieval(
        "book",
        "source",
        "staged-config",
        {},
        indexed.payload,
        upstream_version=1,
        manifest_fields={"embedding_model_id": embedding.embedding_model_id},
    )

    hits = SearchDocument(store, embedding).execute(
        "book", "Naïve Bayes", top_k=5, allowed_stage_ids={"stage-b"}
    )

    assert embedding.requests[-1].task_type == "RETRIEVAL_QUERY"
    assert [hit.document.stage_id for hit in hits] == ["stage-b"]
