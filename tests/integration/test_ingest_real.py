from pathlib import Path

import pytest

from doc2roadmap.application.use_cases import IngestDocument
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore
from doc2roadmap.infrastructure.parsing import DoclingParser
from doc2roadmap.infrastructure.text import SentencePieceTokenCounter, UnicodeSentenceSplitter


class CountingParser:
    def __init__(self) -> None:
        self.inner = DoclingParser()
        self.calls = 0

    @property
    def identifier(self) -> str:
        return self.inner.identifier

    @property
    def adapter_version(self) -> int:
        return self.inner.adapter_version

    @property
    def image_scale(self) -> float:
        return self.inner.image_scale

    def parse(self, source: bytes, filename: str):
        self.calls += 1
        return self.inner.parse(source, filename)


@pytest.mark.integration
def test_real_ingest_reuses_parse_and_keeps_unchanged_chunk_ids(tmp_path: Path) -> None:
    original = Path("tests/fixtures/smoke.pdf")
    updated = Path("tests/fixtures/smoke-updated.pdf")
    if not original.exists() or not updated.exists():
        pytest.skip("fixtures được tạo bởi scripts/create_smoke_pdf.py")
    parser = CountingParser()
    counter = SentencePieceTokenCounter(
        Path("vendor/gemma/tokenizer.model"), "google-gemma-sentencepiece-v1"
    )
    use_case = IngestDocument(
        parser,
        JsonArtifactStore(tmp_path),
        counter,
        UnicodeSentenceSplitter(),
    )

    first = use_case.execute(original.read_bytes(), original.name, "real-book", target_tokens=1)
    repeated = use_case.execute(original.read_bytes(), original.name, "real-book", target_tokens=1)
    first_ids = {
        chunk.text: chunk.chunk_id
        for chunk in JsonArtifactStore(tmp_path).load_latest_chunks("real-book").result.chunks
    }
    assert first.chunk_version == repeated.chunk_version == 1
    assert parser.calls == 1
    assert repeated.source_seen_before

    changed = use_case.execute(updated.read_bytes(), updated.name, "real-book", target_tokens=1)
    changed_ids = {
        chunk.text: chunk.chunk_id
        for chunk in JsonArtifactStore(tmp_path).load_latest_chunks("real-book").result.chunks
    }
    unchanged_text = "This paragraph proves leaf extraction works."
    assert changed_ids[unchanged_text] == first_ids[unchanged_text]
    assert parser.calls == 2
    assert changed.parse_version == 2


@pytest.mark.integration
def test_docx_table_reference_survives_real_ingest(tmp_path: Path) -> None:
    fixture = Path("tests/fixtures/smoke.docx")
    if not fixture.exists():
        pytest.skip("fixture được tạo bởi scripts/create_smoke_pdf.py")
    counter = SentencePieceTokenCounter(
        Path("vendor/gemma/tokenizer.model"), "google-gemma-sentencepiece-v1"
    )
    store = JsonArtifactStore(tmp_path)

    IngestDocument(DoclingParser(), store, counter, UnicodeSentenceSplitter()).execute(
        fixture.read_bytes(), fixture.name, "table-book"
    )
    result = store.load_latest_chunks("table-book").result
    references = [reference for chunk in result.chunks for reference in chunk.table_refs]

    assert len(references) == 1
    assert result.normalized_full_text[references[0].char_start :].startswith("| Name | Value |")
