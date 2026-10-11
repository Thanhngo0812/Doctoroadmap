import hashlib
import json
from collections import Counter
from pathlib import Path

from docling_core.types.doc import DoclingDocument

from doc2roadmap.domain.chunking import CHUNK_ALGORITHM_ID, chunk_document
from doc2roadmap.infrastructure.parsing import DoclingParser
from doc2roadmap.infrastructure.parsing.docling_parser import ADAPTER_VERSION, PipelineConfig
from doc2roadmap.infrastructure.text import (
    SentencePieceTokenCounter,
    UnicodeSentenceSplitter,
)

from tests.conftest import load_docling_fixture


# Đổi số vàng phải kèm giải thích trong cùng commit.
GOLD = {
    "nhap-mon-ml": {
        "sections": 27,
        "chunks": 41,
        "image_refs": 9,
        "table_refs": 0,
        "formula_refs": 1,
        "private_use": 0,
        "letter_count": 23_759,
        "chunk_ids_sha256": "1f69ad2ee2ae5f4e1ed2d4ba24f460660bfe7d419c7f06074bfb064723225074",
        "warnings": {"empty_node": 1, "orphan_caption": 1, "rejected_heading": 1},
    },
    "xstk-ch3-1": {
        "sections": 43,
        "chunks": 126,
        "image_refs": 5,
        "table_refs": 51,
        "formula_refs": 263,
        "private_use": 2,
        "letter_count": 53_219,
        "chunk_ids_sha256": "f12e2c21bfbd1ccf303266e22a961233ca649e767793a880b87b741e16d4b9f9",
        "warnings": {
            "orphan_caption": 2,
            "empty_node": 1,
            "remaining_private_use": 1,
            "rejected_heading_bullet": 23,
            "rejected_heading_repeated": 2,
        },
    },
    "baocao-canhan": {
        "sections": 27,
        "chunks": 26,
        "image_refs": 3,
        "table_refs": 0,
        "formula_refs": 0,
        "private_use": 0,
        "letter_count": 10_486,
        "chunk_ids_sha256": "b8f40f85dbbb3e0a1d72842a1c5e7b1d24c6bf41f5d9a7c0363523035c34a7b0",
        "warnings": {
            "empty_node": 2,
            "non_linguistic_block": 1,
            "toc_block": 1,
        },
    },
    "naive-bayes": {
        "sections": 32,
        "chunks": 40,
        "image_refs": 2,
        "table_refs": 13,
        "formula_refs": 32,
        "private_use": 0,
        "letter_count": 8_582,
        "chunk_ids_sha256": "384df010f3e2a05b3d009fef3b97d110bb3f2cf9f1887e8900dc892d289365a4",
        "warnings": {
            "empty_node": 1,
            "remaining_private_use": 1,
            "rejected_heading_repeated": 2,
            "flat_heading_tree": 1,
        },
    },
}

SOURCES = {
    "nhap-mon-ml": ".pdf",
    "xstk-ch3-1": ".pdf",
    "baocao-canhan": ".docx",
    "naive-bayes": ".pdf",
}


def _private_use(text: str) -> int:
    return sum(0xE000 <= ord(character) <= 0xF8FF for character in text)


def test_batch_versions_are_bumped_once() -> None:
    assert ADAPTER_VERSION == 13
    assert DoclingParser(pipeline=PipelineConfig(pdf_text_policy="legacy")).adapter_version == 11
    assert CHUNK_ALGORITHM_ID == "section-id-v11-document-structure"


def test_new_fixtures_round_trip_with_images_and_exact_sizes() -> None:
    expected = {
        "baocao-canhan": (396, 3, 1_677_534),
        "naive-bayes": (224, 2, 670_440),
    }

    for name, (item_count, picture_count, byte_count) in expected.items():
        document = load_docling_fixture(name)
        restored = DoclingDocument.model_validate(document.export_to_dict())
        items = list(restored.iterate_items())
        pictures = [
            item
            for item, _ in items
            if DoclingParser._label(item) == "picture"
        ]

        assert len(items) == item_count
        assert len(pictures) == picture_count
        assert all(item.get_image(doc=restored) is not None for item in pictures)
        assert Path(f"tests/fixtures/docling/{name}.json").stat().st_size == byte_count


def test_legacy_four_document_pipeline_matches_reviewed_gold() -> None:
    counter = SentencePieceTokenCounter(
        Path("vendor/gemma/tokenizer.model"), "google-gemma-sentencepiece-v1"
    )
    observed = {}

    for name, extension in SOURCES.items():
        parsed = DoclingParser(pipeline=PipelineConfig(pdf_text_policy="legacy")).adapt(
            load_docling_fixture(name), name + extension
        )
        result = chunk_document(
            parsed.tree, name, counter, UnicodeSentenceSplitter()
        )

        if name == "naive-bayes":
            assert "rejected_heading_repeated: Naïve Bayes Classification ×7" in (
                result.structure_warnings
            )
            assert [
                (chunk.token_count, chunk.oversize_reason)
                for chunk in result.chunks
                if chunk.token_count > 512
            ] == [(513, "table_kept_whole_above_text_limit")]

        # I9 và định danh trùng là bất biến cứng, không phải số vàng được phép nới.
        assert all(
            result.normalized_full_text[chunk.char_start : chunk.char_end] == chunk.text
            for chunk in result.chunks
        )
        assert len({chunk.chunk_id for chunk in result.chunks}) == len(result.chunks)

        observed[name] = {
            "sections": len(result.sections),
            "chunks": len(result.chunks),
            "image_refs": sum(len(chunk.image_refs) for chunk in result.chunks),
            "table_refs": sum(len(chunk.table_refs) for chunk in result.chunks),
            "formula_refs": sum(len(chunk.formula_refs) for chunk in result.chunks),
            "private_use": sum(_private_use(chunk.text) for chunk in result.chunks),
            "letter_count": sum(
                character.isalpha()
                for character in result.normalized_full_text
            ),
            "chunk_ids_sha256": hashlib.sha256(
                "\n".join(chunk.chunk_id for chunk in result.chunks).encode()
            ).hexdigest(),
            "warnings": dict(
                Counter(
                    warning.partition(":")[0]
                    for warning in result.structure_warnings
                )
            ),
        }

    assert observed == GOLD


def test_a3_reviewed_gold_locks_entity_media_and_vector_counts() -> None:
    metrics = json.loads(
        Path("tests/fixtures/a3/four-document-metrics.json").read_text(encoding="utf-8")
    )

    assert {
        doc_id: (
            values["total_entities"],
            values["learnable_entities"],
            values["vector_count"],
        )
        for doc_id, values in metrics["documents"].items()
    } == {
        "nhap-mon-ml": (114, 105, 114),
        "xstk-ch3-1": (209, 156, 209),
        "baocao-canhan": (75, 72, 75),
        "naive-bayes": (76, 62, 76),
    }
    corpus = metrics["corpus"]
    assert (corpus["figure_entities"], corpus["table_entities"]) == (19, 60)
    assert corpus["missing_media_descriptions"] == 0
    assert corpus["total_entities"] == 474
    assert corpus["learnable_entities"] == 395
    assert corpus["nonlearnable_context_entities"] == 0
    assert corpus["vector_count"] == 474


def test_preserving_policy_keeps_layout_assets_and_valid_chunk_references():
    import importlib.util

    path = Path('scripts/doc-nhe/do_bao_toan_production.py')
    spec = importlib.util.spec_from_file_location('preservation_audit', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    records = module.audit()['books']  # assertions validate actual geometry, assets, offsets and hashes
    assert records['nhap-mon-ml']['changed_node_fields']['text'] == 27
    assert records['xstk-ch3-1']['changed_node_fields']['table_rows'] == 5
    assert records['baocao-canhan']['changed_node_fields'] == {}
    assert records['naive-bayes']['changed_node_fields'] == {}
