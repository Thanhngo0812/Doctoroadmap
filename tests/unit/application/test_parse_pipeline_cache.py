from dataclasses import replace

import pytest

from doc2roadmap.application.use_cases import IngestDocument
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore
from tests.conftest import WordCounter, splitter
from tests.unit.application.test_ingest import FakeParser
from doc2roadmap.application.use_cases.ingest_document import _hash, parse_config
from doc2roadmap.infrastructure.parsing.docling_parser import DoclingParser, PipelineConfig


@pytest.mark.parametrize("option,value", [("do_ocr", False), ("table_mode", "fast"),
                                          ("ocr_engine", "easyocr")])
def test_pipeline_change_does_not_reuse_parse(tmp_path, option, value):
    parser = FakeParser()
    parser.pipeline_config = {}
    store = JsonArtifactStore(tmp_path)
    ingest = IngestDocument(parser, store, WordCounter(), splitter())
    first = ingest.execute(b"A sentence.", "book.pdf", "book")
    parser.pipeline_config = {option: value}
    second = ingest.execute(b"A sentence.", "book.pdf", "book")
    assert parser.calls == 2
    assert second.parse_version != first.parse_version
    assert not second.source_seen_before
    assert store.load_parse("book", second.parse_version).manifest["config"]["parser"]["pipeline"] == {option: value}


def test_default_hash_matches_old_artifact_without_pipeline_field():
    # Frozen hash from artifacts/parse_tree/doc-1/v1/manifest.json (adapter v8).
    parser = DoclingParser()
    config = parse_config(parser)
    config.update(adapter="docling:2.114.0", adapter_version=8)
    assert "pipeline" not in config
    assert _hash(config) == "c4ce696fe6b6a5d1164a592a967b66accb949f3c1cd72b1dd3ea98a452e375dc"


def test_threads_do_not_invalidate_cache_and_new_parse_records_threads(tmp_path):
    parser = FakeParser()
    parser.pipeline_config = DoclingParser(pipeline=PipelineConfig(num_threads=4)).pipeline_config
    parser.runtime_config = {"num_threads": 4}
    store = JsonArtifactStore(tmp_path)
    ingest = IngestDocument(parser, store, WordCounter(), splitter())
    first = ingest.execute(b"A sentence.", "book.pdf", "book")
    parser.pipeline_config = DoclingParser(pipeline=PipelineConfig(num_threads=8)).pipeline_config
    parser.runtime_config = {"num_threads": 8}
    reused = ingest.execute(b"A sentence.", "book.pdf", "book")
    assert parser.calls == 1 and first.parse_version == reused.parse_version
    assert store.load_parse("book", first.parse_version).manifest["parser_runtime"] == {"num_threads": 4}
    fresh = ingest.execute(b"A different sentence.", "book.pdf", "book")
    assert store.load_parse("book", fresh.parse_version).manifest["parser_runtime"] == {"num_threads": 8}


@pytest.mark.parametrize("name", [n for n in PipelineConfig.__dataclass_fields__ if n != "num_threads"])
def test_every_exposed_output_option_changes_the_cache_key(name):
    defaults = PipelineConfig()
    alternatives = {"ocr_engine": "easyocr", "ocr_backend": "onnxruntime",
                    "table_mode": "fast", "layout_model": "egret-medium"}
    current = getattr(defaults, name)
    value = alternatives.get(name, not current if isinstance(current, bool) else current * 2)
    assert _hash(parse_config(DoclingParser(pipeline=replace(defaults, **{name: value})))) != _hash(parse_config(DoclingParser()))


def test_pipeline_is_frozen_and_converter_options_follow_it(monkeypatch):
    from dataclasses import FrozenInstanceError
    config = PipelineConfig(do_ocr=False, table_mode="fast", bitmap_area_threshold=0.75,
                            num_threads=8, layout_model="heron-101", force_full_page_ocr=True)
    with pytest.raises(FrozenInstanceError):
        config.do_ocr = True
    parser = DoclingParser(pipeline=config)
    with pytest.raises(AttributeError):
        parser.pipeline = PipelineConfig()
    options = config.options()
    assert options.do_ocr is False
    assert options.ocr_options.backend == "torch"
    assert options.ocr_options.bitmap_area_threshold == 0.75
    assert options.ocr_options.force_full_page_ocr is True
    assert options.table_structure_options.mode.value == "fast"
    assert options.layout_options.model_spec.repo_id.endswith("heron-101")
    assert options.accelerator_options.num_threads == 8
    assert parser.runtime_config == {"num_threads": 8}
    from docling.datamodel.base_models import InputFormat
    import docling.document_converter
    captured = []
    monkeypatch.setattr(docling.document_converter, "DocumentConverter",
                        lambda **kw: captured.append(kw) or object())
    parser._get_converter()
    actual = captured[0]["format_options"][InputFormat.PDF].pipeline_options
    assert actual == options
