import json
import hashlib
from pathlib import Path

import pytest

from doc2roadmap.application.ports import ParsedDocument
from doc2roadmap.application.use_cases import IngestDocument
from doc2roadmap.domain.chunking import CHUNK_ALGORITHM_ID, OVERSIZE_SENTENCE_BOUNDARY
from doc2roadmap.domain.models import DocumentNode, DocumentTree
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore

from tests.conftest import WordCounter, splitter


class FakeParser:
    identifier = "fake:v1"

    def __init__(self) -> None:
        self.calls = 0
        self.adapter_version = 1
        self.image_scale = 2.0

    def parse(self, source: bytes, filename: str) -> ParsedDocument:
        self.calls += 1
        return ParsedDocument(
            DocumentTree(
                [DocumentNode("paragraph", source.decode(), 0)],
                parse_stats={"items_total": 1, "nodes_kept": 1, "dropped": {}},
            )
        )


def test_frozen_parse_is_reused_but_new_chunk_config_gets_new_version(tmp_path: Path) -> None:
    parser = FakeParser()
    store = JsonArtifactStore(tmp_path)
    use_case = IngestDocument(parser, store, WordCounter(), splitter())

    source = "Câu một. Câu hai.".encode()
    first = use_case.execute(source, "book.pdf", "book", max_tokens=512, target_tokens=1)
    second = use_case.execute(source, "book.pdf", "book", max_tokens=3, target_tokens=1)

    assert parser.calls == 1
    assert first.parse_version == second.parse_version == 1
    assert first.chunk_version == 1
    assert second.chunk_version == 2
    assert second.source_seen_before
    assert first.artifact_path.parent.name == "book"
    assert first.artifact_path.joinpath("manifest.json").is_file()
    assert not tmp_path.joinpath("parse_tree", "book", "v1", "images").exists()
    chunk_config = store.load_latest_chunks("book").manifest["config"]["chunk"]
    assert chunk_config["algorithm_id"] == CHUNK_ALGORITHM_ID
    assert chunk_config["max_table_tokens"] == 2048
    assert chunk_config["hard_cap_tokens"] == 6000
    assert chunk_config["target_tokens"] == 1 and "min_tokens" not in chunk_config
    payload = json.loads(second.artifact_path.joinpath("chunks.json").read_text(encoding="utf-8"))
    assert all(
        chunk["table_refs"] == []
        and chunk["formula_refs"] == []
        and chunk["oversize_reason"] is None
        for chunk in payload
    )


def test_new_source_hash_creates_new_parse_version(tmp_path: Path) -> None:
    parser = FakeParser()
    use_case = IngestDocument(parser, JsonArtifactStore(tmp_path), WordCounter(), splitter())

    first = use_case.execute("Câu cũ.".encode(), "book.pdf", "book")
    second = use_case.execute("Câu mới.".encode(), "book.pdf", "book")

    assert parser.calls == 2
    assert first.parse_version == 1
    assert second.parse_version == 2
    assert not second.source_seen_before
    assert first.artifact_path != second.artifact_path


def test_rejects_invalid_input_before_parser(tmp_path: Path) -> None:
    parser = FakeParser()
    use_case = IngestDocument(parser, JsonArtifactStore(tmp_path), WordCounter(), splitter())

    for filename, doc_id, source in [("book.txt", "book", b"x"), ("book.pdf", "../book", b"x"), ("book.pdf", "book", b"")]:
        try:
            use_case.execute(source, filename, doc_id)
        except ValueError:
            pass
        else:
            raise AssertionError("đầu vào không hợp lệ phải bị từ chối")
    try:
        use_case.execute(b"x", "book.pdf", "book", max_tokens=10, target_tokens=11)
    except ValueError:
        pass
    else:
        raise AssertionError("cấu hình chunk không hợp lệ phải bị từ chối")
    for kwargs in ({"max_table_tokens": 0}, {"hard_cap_tokens": 0}):
        with pytest.raises(ValueError):
            use_case.execute(b"x", "book.pdf", "book", **kwargs)
    assert parser.calls == 0


def test_table_and_hard_thresholds_each_create_a_new_chunk_version(tmp_path: Path) -> None:
    parser = FakeParser()
    store = JsonArtifactStore(tmp_path)
    use_case = IngestDocument(parser, store, WordCounter(), splitter())

    first = use_case.execute(b"content", "book.pdf", "book")
    table_changed = use_case.execute(
        b"content", "book.pdf", "book", max_table_tokens=1024
    )
    hard_changed = use_case.execute(
        b"content", "book.pdf", "book", hard_cap_tokens=5000
    )

    assert parser.calls == 1
    assert [first.chunk_version, table_changed.chunk_version, hard_changed.chunk_version] == [1, 2, 3]
    table_config = json.loads(
        tmp_path.joinpath("chunks", "book", "v2", "manifest.json").read_text(encoding="utf-8")
    )["config"]["chunk"]
    hard_config = json.loads(
        tmp_path.joinpath("chunks", "book", "v3", "manifest.json").read_text(encoding="utf-8")
    )["config"]["chunk"]
    assert table_config["max_table_tokens"] == 1024
    assert hard_config["hard_cap_tokens"] == 5000


def test_adapter_version_invalidates_frozen_parse_and_is_recorded(tmp_path: Path) -> None:
    parser = FakeParser()
    store = JsonArtifactStore(tmp_path)
    use_case = IngestDocument(parser, store, WordCounter(), splitter())

    first = use_case.execute(b"noi dung", "book.pdf", "book")
    parser.adapter_version = 2
    changed = use_case.execute(b"noi dung", "book.pdf", "book")
    repeated = use_case.execute(b"noi dung", "book.pdf", "book")

    assert parser.calls == 2
    assert first.parse_version == 1 and changed.parse_version == repeated.parse_version == 2
    assert not changed.source_seen_before and repeated.source_seen_before
    parse_manifest = json.loads(
        tmp_path.joinpath("parse_tree", "book", "v2", "manifest.json").read_text(encoding="utf-8")
    )
    assert parse_manifest["config"]["parser"]["adapter_version"] == 2
    assert parse_manifest["config"]["parser"]["image_scale"] == 2.0
    assert parse_manifest["parse_stats"]["nodes_kept"] == 1


def test_image_scale_invalidates_frozen_parse(tmp_path: Path) -> None:
    parser = FakeParser()
    use_case = IngestDocument(parser, JsonArtifactStore(tmp_path), WordCounter(), splitter())

    first = use_case.execute(b"noi dung", "book.pdf", "book")
    parser.image_scale = 1.0
    changed = use_case.execute(b"noi dung", "book.pdf", "book")

    assert parser.calls == 2
    assert first.parse_version == 1 and changed.parse_version == 2


def test_images_and_references_survive_ingest_storage(tmp_path: Path) -> None:
    image = b"png bytes"
    image_id = hashlib.sha256(image).hexdigest()

    class ImageParser:
        identifier = "fake:v1"
        adapter_version = 1
        image_scale = 2.0

        def parse(self, source: bytes, filename: str) -> ParsedDocument:
            return ParsedDocument(
                DocumentTree([DocumentNode("figure", "Hình minh họa", 0, image_id=image_id)]),
                {image_id: image},
            )

    store = JsonArtifactStore(tmp_path)
    use_case = IngestDocument(ImageParser(), store, WordCounter(), splitter())

    summary = use_case.execute(b"source", "book.pdf", "book")
    stored = store.load_latest_chunks("book").result.chunks[0]

    assert tmp_path.joinpath(
        "parse_tree", "book", f"v{summary.parse_version}", "images", f"{image_id}.png"
    ).read_bytes() == image
    assert stored.block_types == ["figure"]
    assert stored.image_refs[0].image_id == image_id
    assert stored.image_refs[0].char_start == stored.char_start == 0


def test_table_reference_survives_ingest_storage(tmp_path: Path) -> None:
    table_id = "a" * 64

    class TableParser:
        identifier = "fake:v1"
        adapter_version = 1
        image_scale = 2.0

        def parse(self, source: bytes, filename: str) -> ParsedDocument:
            return ParsedDocument(
                DocumentTree(
                    [
                        DocumentNode(
                            "table",
                            "",
                            0,
                            table_rows=[["Name", "Value"], ["A", "1"]],
                            table_id=table_id,
                        )
                    ]
                )
            )

    store = JsonArtifactStore(tmp_path)
    summary = IngestDocument(TableParser(), store, WordCounter(), splitter()).execute(
        b"source", "book.docx", "book"
    )
    stored = store.load_latest_chunks("book").result.chunks[0]

    assert stored.table_refs[0].table_id == table_id
    assert stored.table_refs[0].char_start == stored.char_start == 0
    assert stored.text.startswith("| Name | Value |")
    payload = json.loads(summary.artifact_path.joinpath("chunks.json").read_text(encoding="utf-8"))
    assert payload[0]["table_refs"] == [{"table_id": table_id, "char_start": 0}]


def test_formula_reference_survives_ingest_storage(tmp_path: Path) -> None:
    formula_id = "f" * 64

    class FormulaParser:
        identifier = "fake:v1"
        adapter_version = 1
        image_scale = 2.0

        def parse(self, source: bytes, filename: str) -> ParsedDocument:
            return ParsedDocument(
                DocumentTree(
                    [
                        DocumentNode(
                            "formula",
                            "[formula]",
                            0,
                            raw_text="raw formula",
                            formula_id=formula_id,
                        )
                    ]
                )
            )

    store = JsonArtifactStore(tmp_path)
    summary = IngestDocument(FormulaParser(), store, WordCounter(), splitter()).execute(
        b"source", "book.pdf", "book"
    )
    stored = store.load_latest_chunks("book").result.chunks[0]

    assert stored.formula_refs[0].formula_id == formula_id
    assert stored.formula_refs[0].char_start == stored.char_start == 0
    payload = json.loads(summary.artifact_path.joinpath("chunks.json").read_text(encoding="utf-8"))
    assert payload[0]["formula_refs"] == [{"formula_id": formula_id, "char_start": 0}]


def test_unsplittable_warning_is_stored_in_chunk_manifest(tmp_path: Path) -> None:
    store = JsonArtifactStore(tmp_path)
    use_case = IngestDocument(FakeParser(), store, WordCounter(), splitter())

    summary = use_case.execute(
        " ".join(f"word{index}" for index in range(20)).encode(),
        "book.pdf",
        "book",
        max_tokens=10,
        target_tokens=1,
    )

    warning = f"{OVERSIZE_SENTENCE_BOUNDARY}: section <document>"
    assert summary.structure_warnings == [warning]
    assert store.load_latest_chunks("book").manifest["structure_warnings"] == [warning]
