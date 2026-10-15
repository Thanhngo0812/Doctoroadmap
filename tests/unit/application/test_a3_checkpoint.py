from doc2roadmap.application.use_cases.extract_entities import ExtractEntities
from tests.unit.application.test_a3_extract import _chunk, _stored_document, _Extractor, _Embedding, _reply
import pytest


def script(chunk, name):
    return [_reply(entities=[{"name": name, "node_type": "concept", "description_draft": name,
                             "evidence": chunk.text, "aliases": []}]),
            _reply(), {"remove_entity_ids": [], "remove_edge_ids": []}]


def test_resume_asks_only_missing_section_and_matches_uninterrupted_payload(tmp_path):
    chunks = [_chunk("Concept A được giảng.", chunk_id="c1"),
              _chunk("Concept B được giảng.", chunk_id="c2", section_id="s2", char_start=600)]
    store = _stored_document(tmp_path / "resume", chunks)
    model = _Extractor([script(chunks[0], "Concept A"), [RuntimeError("429")], [RuntimeError("429")]])
    use_case = ExtractEntities(store, model, _Embedding(), generation={"temperature": 0})
    partial = use_case.execute("book", max_workers=1)
    assert partial.artifact_path is None
    model.scripts.append(script(chunks[1], "Concept B"))
    resumed = use_case.execute("book", max_workers=1)
    assert len(model.sessions) == 4  # 1 completed + 2 failed + ONLY 1 missing section.
    assert not resumed.result.coverage_incomplete
    fresh_store = _stored_document(tmp_path / "fresh", chunks)
    fresh = ExtractEntities(fresh_store, _Extractor([script(chunks[0], "Concept A"), script(chunks[1], "Concept B")]),
                            _Embedding(), generation={"temperature": 0}).execute("book", max_workers=1)
    assert resumed.result.to_payload() == fresh.result.to_payload()
    assert list((store.root / "checkpoints/graph/book").glob("a3-*.json")) == []


def test_restored_empty_sections_cannot_bypass_empty_rate_gate():
    from doc2roadmap.application.use_cases.extract_entities import (
        _run_contexts, SectionContext, SectionExtraction, ExtractionGateError, load_prompts)
    context = SectionContext("s1", "Section", ["Section"], [], [], [])
    restored = SectionExtraction("s1", "Section", [], [], {"missing_media_descriptions": 0})
    with pytest.raises(ExtractionGateError, match="40%"):
        _run_contexts([context], _Extractor([]), max_workers=1, prompts=load_prompts(), completed=[restored])
