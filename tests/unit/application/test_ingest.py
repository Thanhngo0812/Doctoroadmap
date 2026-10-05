import json
import hashlib
from pathlib import Path

import pytest

from doc2roadmap.application.ports import ParsedDocument
from doc2roadmap.application.use_cases import IngestDocument
from doc2roadmap.application.use_cases.ingest_document import _text_quality
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
    parse_manifest = store.load_parse("book", 1).manifest
    chunk_manifest = store.load_latest_chunks("book").manifest
    assert chunk_manifest["parse_reused"] is True
    assert chunk_manifest["parse_runtime_seconds"] == 0
    assert "strip_lines" not in parse_manifest
    assert "stripped_line_count" not in parse_manifest
    assert "strip_lines" not in parse_manifest["config"]["parser"]
    assert "strip_lines" not in chunk_manifest
    assert "stripped_line_count" not in chunk_manifest
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


def test_ingest_records_parse_duration_and_page_count_without_hashing_time(tmp_path, monkeypatch):
    import doc2roadmap.application.use_cases.ingest_document as ingest
    class Parser(FakeParser):
        def parse(self, source, filename):
            parsed = super().parse(source, filename)
            parsed.tree.parse_stats["page_count"] = 3  # includes a blank final page
            return parsed
    clock = iter([10.0, 14.0])
    monkeypatch.setattr(ingest, "perf_counter", lambda: next(clock))
    store = JsonArtifactStore(tmp_path)
    summary = IngestDocument(Parser(), store, WordCounter(), splitter()).execute(b"A sentence.", "book.pdf", "book")
    manifest = store.load_chunks("book", summary.chunk_version).manifest
    assert manifest["page_count"] == 3
    assert manifest["parse_runtime_seconds"] == 4
    assert manifest["stats"]["runtime_seconds"] >= 0
    assert manifest["stats"]["model_calls"] == 0
    assert "parse_runtime_seconds" not in manifest["config"]
    assert "runtime_seconds" not in manifest["config"]


def test_refresh_roles_uses_only_saved_sections_keeps_chunks_and_is_idempotent(tmp_path):
    from doc2roadmap.application.use_cases.ingest_document import refresh_chunk_roles
    from doc2roadmap.domain.chunking import chunk_document

    store = JsonArtifactStore(tmp_path)
    tree = DocumentTree([DocumentNode("section_header", "Câu hỏi ôn tập", 0, level=1),
                         DocumentNode("text", "Một câu hỏi.", 1)])
    result = chunk_document(tree, "doc", WordCounter(), splitter())
    result.sections[-1].role = result.chunks[0].role = "noi_dung"  # giả lập artifact trước R1
    config = {"chunk": {"algorithm_id": "section-id-v8"}}
    original = store.save_chunks("doc", "source", "old", config, 1, result)
    original_bytes = (original.path / "chunks.json").read_bytes()
    original_chunks = [c.to_dict() for c in original.result.chunks]
    updated = refresh_chunk_roles(store, "doc")
    assert updated.version == 2 and updated.result.chunks[0].role == "noi_dung"
    assert updated.result.sections[-1].role_source == ''  # v14: semantic words await the separate classifier
    assert [c.chunk_id for c in updated.result.chunks] == [c["chunk_id"] for c in original_chunks]
    assert [{k: v for k, v in c.to_dict().items() if k != "role"} for c in updated.result.chunks] == [
        {k: v for k, v in c.items() if k != "role"} for c in original_chunks]
    assert (original.path / "chunks.json").read_bytes() == original_bytes
    assert updated.manifest["config"]["chunk"]["role_algorithm_id"] == CHUNK_ALGORITHM_ID
    assert refresh_chunk_roles(store, "doc").version == 2


def test_strip_lines_before_chunking_and_record_both_manifests(tmp_path: Path) -> None:
    parser = FakeParser()
    store = JsonArtifactStore(tmp_path)
    use_case = IngestDocument(parser, store, WordCounter(), splitter())

    summary = use_case.execute(
        b"Alpha MARKER   CODE Omega.\nMARKER\tCODE",
        "book.pdf",
        "book",
        strip_lines=["MARKER CODE"],
    )

    parse = store.load_parse("book", summary.parse_version)
    chunks = store.load_latest_chunks("book")
    assert summary.parse_version == 1 and summary.chunk_version == 1
    assert "MARKER" not in parse.tree.nodes[0].text
    assert "Alpha" in parse.tree.nodes[0].text and "Omega" in parse.tree.nodes[0].text
    assert all("MARKER" not in chunk.text for chunk in chunks.result.chunks)
    for manifest in (parse.manifest, chunks.manifest):
        assert manifest["strip_lines"] == ["MARKER CODE"]
        assert manifest["stripped_line_count"] == 2


def test_no_strip_lines_preserves_parse_text_exactly(tmp_path: Path) -> None:
    store = JsonArtifactStore(tmp_path)
    source = b"  keep original spacing  "

    summary = IngestDocument(FakeParser(), store, WordCounter(), splitter()).execute(
        source, "book.pdf", "book"
    )

    assert store.load_parse("book", summary.parse_version).tree.nodes[0].text == source.decode()


def test_text_quality_warns_for_damaged_vietnamese_but_not_clean_or_english(tmp_path: Path) -> None:
    damaged = _text_quality(["a" * 42000 + "á" * 24 + "\ue000" * 60])
    clean = _text_quality(["a" * 47000 + "á" * 16000 + "\ue000" * 44])
    english = _text_quality(["a" * 42000])

    assert damaged["readable_letter_count"] == 42024
    assert damaged["accented_letter_ratio"] < 0.001
    assert damaged["private_use_ratio"] > 0.001
    assert len(damaged["warnings"]) == 1
    assert "không đủ chất lượng làm nguồn bộ vàng" in damaged["warnings"][0]
    assert clean["warnings"] == english["warnings"] == []
    assert clean["accented_letter_ratio"] > 0.25
    assert english["replacement_character_ratio"] == 0

    store = JsonArtifactStore(tmp_path)
    summary = IngestDocument(FakeParser(), store, WordCounter(), splitter()).execute(
        ("a" * 42000 + "á" * 24 + "\ue000" * 60).encode(), "book.pdf", "book"
    )
    assert summary.quality_warnings == damaged["warnings"]
    assert store.load_latest_chunks("book").manifest["text_quality"] == damaged


def test_strip_lines_cleans_raw_text_without_double_counting(tmp_path: Path) -> None:
    class RawParser(FakeParser):
        def parse(self, source: bytes, filename: str) -> ParsedDocument:
            parsed = super().parse(source, filename)
            parsed.tree.nodes[0].raw_text = source.decode()
            return parsed

    store = JsonArtifactStore(tmp_path)
    summary = IngestDocument(RawParser(), store, WordCounter(), splitter()).execute(
        b"Alpha MARKER   CODE Omega.",
        "book.pdf",
        "book",
        strip_lines=["MARKER CODE"],
    )
    parse = store.load_parse("book", summary.parse_version)

    assert parse.tree.nodes[0].text == parse.tree.nodes[0].raw_text
    assert parse.manifest["stripped_line_count"] == 1
    assert store.load_latest_chunks("book").manifest["stripped_line_count"] == 1


def test_strip_lines_counts_matched_lines_not_occurrences(tmp_path: Path) -> None:
    store = JsonArtifactStore(tmp_path)
    summary = IngestDocument(FakeParser(), store, WordCounter(), splitter()).execute(
        b"Alpha MARKER CODE and MARKER CODE Omega.",
        "book.pdf",
        "book",
        strip_lines=["MARKER CODE"],
    )

    assert store.load_parse("book", summary.parse_version).manifest["stripped_line_count"] == 1


def test_strip_lines_also_cleans_table_cells_and_context_prefix(tmp_path: Path) -> None:
    class TableParser(FakeParser):
        def parse(self, source: bytes, filename: str) -> ParsedDocument:
            parsed = super().parse(source, filename)
            parsed.tree.nodes[0].table_rows = [["label", "MARKER  CODE"]]
            parsed.tree.nodes[0].context_prefix = "heading MARKER\tCODE"
            return parsed

    store = JsonArtifactStore(tmp_path)
    summary = IngestDocument(TableParser(), store, WordCounter(), splitter()).execute(
        b"ordinary text", "book.pdf", "book", strip_lines=["MARKER CODE"]
    )
    node = store.load_parse("book", summary.parse_version).tree.nodes[0]

    assert node.table_rows == [["label", ""]]
    assert node.context_prefix == "heading"
    assert store.load_latest_chunks("book").manifest["stripped_line_count"] > 0


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


def test_text_quality_warns_when_vietnamese_syllables_are_split_apart() -> None:
    # Mẫu thật của doc-6 đọc bằng docling-parse: phụ âm đầu và vần bị tách thành hai token ("th ứ c").
    split = "D ữ li ệ u là m ộ t mô t ả hình th ứ c v ề nh ữ ng s ự ki ệ n. "
    clean = "Dữ liệu là một mô tả hình thức về những sự kiện. "
    math = "Suppose n m v are vectors and T is a linear map on V with n rows. "
    broken = _text_quality([split * 30])
    assert broken["split_syllable_ratio"] > 0.01
    assert len(broken["warnings"]) == 1 and "pypdfium2" in broken["warnings"][0]
    assert _text_quality([clean * 30])["warnings"] == []
    assert _text_quality([math * 30])["split_syllable_ratio"] == 0
    assert _text_quality([split * 2 + clean * 200])["warnings"] == []  # dưới 20 lần xuất hiện: không cảnh báo
