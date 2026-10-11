import pytest

from doc2roadmap.application.ports import ParsedDocument
from doc2roadmap.application.use_cases import IngestDocument
from doc2roadmap.application.use_cases.ingest_document import _text_quality, tree_text_quality
from doc2roadmap.domain.models import DocumentNode, DocumentTree
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore
from tests.conftest import WordCounter, splitter
from tests.unit.application.test_ingest import FakeParser


CLEAN = "Không gian vector và ánh xạ tuyến tính được trình bày trong chương này. " * 100
BROKEN = "T'p c¡c ph†p bi,n Œi tuy,n t‰nh cıa V. " * 100


class SwitchingParser(FakeParser):
    def __init__(self, backend="docling-parse", *, both_bad=False):
        super().__init__()
        self.pdf_backend = backend
        self.identifier = "fake:" + backend
        self.both_bad = both_bad

    def with_pdf_backend(self, backend):
        return SwitchingParser(backend, both_bad=self.both_bad)

    def parse(self, source, filename):
        self.calls += 1
        text = BROKEN if self.both_bad or self.pdf_backend == "docling-parse" else CLEAN
        return ParsedDocument(DocumentTree([DocumentNode("paragraph", text, 0, page=1)]))


def test_bad_parser_switches_before_chunking_and_records_actual_backend(tmp_path):
    store = JsonArtifactStore(tmp_path)
    summary = IngestDocument(SwitchingParser(), store, WordCounter(), splitter()).execute(b"pdf", "book.pdf", "book")
    chunks = store.load_latest_chunks("book")
    assert "c¡c" not in " ".join(c.text for c in chunks.result.chunks)
    assert chunks.manifest["config"]["parser"]["adapter"] == "fake:pypdfium2"
    assert chunks.manifest["text_quality_selection"]["selected_backend"] == "pypdfium2"
    assert summary.quality_warnings == []


def test_both_bad_publish_no_chunks(tmp_path):
    store = JsonArtifactStore(tmp_path)
    with pytest.raises(ValueError, match="chất lượng chữ"):
        IngestDocument(SwitchingParser(both_bad=True), store, WordCounter(), splitter()).execute(b"pdf", "book.pdf", "book")
    with pytest.raises(FileNotFoundError):
        store.load_latest_chunks("book")


def test_syllable_metrics_separate_clean_split_and_corrupt():
    clean = _text_quality([CLEAN])
    split = _text_quality(["Ph ươ ng pháp và gi ớ i thiệu. " * 100])
    broken = _text_quality([BROKEN])
    assert clean["valid_vietnamese_syllable_ratio"] > split["valid_vietnamese_syllable_ratio"] > broken["valid_vietnamese_syllable_ratio"]
    assert broken["strange_character_ratio"] > clean["strange_character_ratio"]
    assert split["single_letter_token_ratio"] > clean["single_letter_token_ratio"]


def test_local_vni_header_is_not_diluted_by_clean_body_and_math_is_excluded():
    tree = DocumentTree([DocumentNode("title", "BOÄ MOÂN TOAÙN", 0, page=7),
                         DocumentNode("paragraph", CLEAN, 1, page=7),
                         DocumentNode("formula", BROKEN, 2, page=8),
                         DocumentNode("table", BROKEN, 3, page=8)])
    assert any("VNI" in warning and "7" in warning for warning in tree_text_quality(tree)["warnings"])
    assert tree_text_quality(DocumentTree(tree.nodes[1:]))["warnings"] == []


def test_clean_foreign_terms_are_not_rejected_by_syllable_ratio_alone():
    text = "Nhóm acid amin gồm phenylalanine tyrosine tryptophan aspartate glutamate. " * 30
    assert _text_quality([text])["valid_vietnamese_syllable_ratio"] < 0.8
    assert tree_text_quality(DocumentTree([DocumentNode("paragraph", text, 0, page=1)]))["warnings"] == []


def test_unicode_giup_is_not_a_vni_sequence():
    text = "Cây giúp giữ đất, giúp chống bệnh và giúp bảo vệ mùa màng. " * 30
    assert _text_quality([text])["vni_sequence_count"] == 0
    assert tree_text_quality(DocumentTree([DocumentNode("paragraph", text, 0, page=1)]))["warnings"] == []


@pytest.mark.parametrize("stage", ["roles", "a3", "roadmap"])
def test_paid_stages_refuse_unconfirmed_warning_before_model_calls(tmp_path, stage):
    from tests.unit.application.test_label_chunk_roles import stored, Model
    from tests.unit.application.test_build_clusters import Store, Embedding
    from doc2roadmap.application.use_cases.label_chunk_roles import LabelChunkRoles
    from doc2roadmap.application.use_cases.extract_entities import ExtractEntities
    from doc2roadmap.application.use_cases.build_clusters import BuildClusters
    if stage == "roadmap":
        store, model = Store(), Embedding()
        store.chunks.manifest["text_quality"] = {"warnings": ["bad font"]}
        use_case = BuildClusters(store, model)
        doc_id = "doc"
    else:
        store, base = stored(tmp_path)
        store.save_parse("roles", "source", "parser", "config", {},
                         DocumentTree([DocumentNode("paragraph", CLEAN, 0, page=1)]), {})
        store.save_chunks("roles", "source", "warn", {"chunk": {}}, 1, base.result,
                          manifest_fields={"text_quality": {"warnings": ["bad font"]}})
        model = Model()
        model.identifier = "fake"
        use_case = LabelChunkRoles(store, model, allow_spend=True) if stage == "roles" else ExtractEntities(
            store, model, None, generation={})
        doc_id = "roles"
    with pytest.raises(ValueError, match="chất lượng chữ chưa xác nhận"):
        use_case.execute(doc_id)
    assert model.calls == []


def test_explicit_reason_is_persisted_and_empty_reason_is_rejected(tmp_path):
    from doc2roadmap.application.use_cases.ingest_document import require_text_quality
    store = JsonArtifactStore(tmp_path)
    use_case = IngestDocument(SwitchingParser(both_bad=True), store, WordCounter(), splitter())
    with pytest.raises(ValueError, match="rỗng"):
        use_case.execute(b"pdf", "book.pdf", "book", quality_reason=" ")
    use_case.execute(b"pdf", "book.pdf", "book", quality_reason="User accepts font loss")
    chunks = store.load_latest_chunks("book")
    assert chunks.manifest["text_quality_override_reason"] == "User accepts font loss"
    assert chunks.manifest["text_quality"]["warnings"]
    require_text_quality(chunks)


def test_historic_chunks_without_warning_are_checked_against_pinned_parse(tmp_path):
    from doc2roadmap.application.use_cases.ingest_document import require_text_quality
    from tests.unit.application.test_label_chunk_roles import stored
    store, base = stored(tmp_path)
    store.save_parse("roles", "source", "parser", "config", {},
                     DocumentTree([DocumentNode("title", "BOÄ MOÂN TOAÙN", 0, page=9)]), {})
    assert "text_quality" not in base.manifest
    with pytest.raises(ValueError, match="9"):
        require_text_quality(base, store=store)


def test_cached_bad_dry_run_selects_existing_clean_parse_without_writes(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from doc2roadmap.presentation.cli.main import _ingest
    from doc2roadmap.application.use_cases.ingest_document import parse_config, _hash
    store = JsonArtifactStore(tmp_path / "artifacts")
    source = tmp_path / "book.pdf"
    source.write_bytes(b"pdf")
    import hashlib
    source_hash = hashlib.sha256(b"pdf").hexdigest()
    for parser, text in ((SwitchingParser(), BROKEN), (SwitchingParser("pypdfium2"), CLEAN)):
        config = parse_config(parser)
        store.save_parse("book", source_hash, _hash(config), "chunk-key", {"parser": config},
                         DocumentTree([DocumentNode("paragraph", text, 0, page=1)]), {})
    use_case = IngestDocument(SwitchingParser(), store, WordCounter(), splitter())
    monkeypatch.setattr("doc2roadmap.presentation.cli.main.build_ingest", lambda *a, **kw: (use_case, SimpleNamespace()))
    before = {p: p.read_bytes() for p in store.root.rglob("*") if p.is_file()}
    monkeypatch.setattr(SwitchingParser, "parse", lambda *a: pytest.fail("dry-run parsed"))
    _ingest(source, "book", dry_run=True)
    assert before == {p: p.read_bytes() for p in store.root.rglob("*") if p.is_file()}
    # The report must name the clean backend, not just claim the old cache can be reused.
    assert use_case.last_parse_selection["selected_backend"] == "pypdfium2"
