from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from doc2roadmap.application.ports import ArtifactStore, DocumentParser
from doc2roadmap.application.windows import assemble_windows
from doc2roadmap.domain.chunking import CHUNK_ALGORITHM_ID, chunk_document
from doc2roadmap.domain.ports import SentenceSplitter, TokenCounter


_DOC_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def validate_doc_id(doc_id: str) -> str:
    if not _DOC_ID.fullmatch(doc_id):
        raise ValueError("doc_id chỉ được chứa chữ, số, '.', '_' và '-', tối đa 128 ký tự")
    return doc_id


def _hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(slots=True)
class IngestSummary:
    doc_id: str
    section_count: int
    chunk_count: int
    window_count: int
    structure_warnings: list[str]
    parse_stats: dict[str, Any]
    source_seen_before: bool
    parse_version: int
    chunk_version: int
    artifact_path: Path


class IngestDocument:
    def __init__(
        self,
        parser: DocumentParser,
        store: ArtifactStore,
        counter: TokenCounter,
        splitter: SentenceSplitter,
    ) -> None:
        self.parser = parser
        self.store = store
        self.counter = counter
        self.splitter = splitter

    def execute(
        self,
        source: bytes,
        filename: str,
        doc_id: str,
        *,
        max_tokens: int = 512,
        max_table_tokens: int = 2048,
        hard_cap_tokens: int = 6000,
        target_tokens: int = 256,
        sentence_overlap: int = 1,
    ) -> IngestSummary:
        validate_doc_id(doc_id)
        suffix = Path(filename).suffix.lower()
        if suffix not in {".pdf", ".docx"}:
            raise ValueError("chỉ hỗ trợ file .pdf hoặc .docx")
        if not source:
            raise ValueError("file đầu vào rỗng")
        if not 0 < target_tokens <= max_tokens:
            raise ValueError("target_tokens phải lớn hơn 0 và không vượt max_tokens")
        if max_table_tokens <= 0 or hard_cap_tokens <= 0:
            raise ValueError("max_table_tokens và hard_cap_tokens phải lớn hơn 0")
        if sentence_overlap < 0:
            raise ValueError("sentence_overlap không được âm")

        source_hash = hashlib.sha256(source).hexdigest()
        parser_config = {
            "adapter": self.parser.identifier,
            "adapter_version": self.parser.adapter_version,
            "image_scale": self.parser.image_scale,
        }
        parser_config_hash = _hash(parser_config)
        config = {
            "parser": parser_config,
            "normalization": {
                "unicode": "NFC",
                "dehyphenate": True,
                "punctuation": "ascii-quotes-dashes",
            },
            "chunk": {
                "algorithm_id": CHUNK_ALGORITHM_ID,
                "max_tokens": max_tokens,
                "max_table_tokens": max_table_tokens,
                "hard_cap_tokens": hard_cap_tokens,
                "target_tokens": target_tokens,
                "sentence_overlap": sentence_overlap,
            },
            "tokenizer_id": self.counter.identifier,
        }
        config_hash = _hash(config)
        stored_parse = self.store.find_parse(doc_id, source_hash, parser_config_hash)
        source_seen_before = stored_parse is not None
        if stored_parse is None:
            parsed = self.parser.parse(source, filename)
            stored_parse = self.store.save_parse(
                doc_id,
                source_hash,
                parser_config_hash,
                config_hash,
                config,
                parsed.tree,
                parsed.images,
            )

        result = chunk_document(
            stored_parse.tree,
            doc_id,
            self.counter,
            self.splitter,
            max_tokens=max_tokens,
            max_table_tokens=max_table_tokens,
            hard_cap_tokens=hard_cap_tokens,
            target_tokens=target_tokens,
            sentence_overlap=sentence_overlap,
        )
        windows = assemble_windows(result.chunks)
        stored_chunks = self.store.save_chunks(
            doc_id,
            source_hash,
            config_hash,
            config,
            stored_parse.version,
            result,
        )
        return IngestSummary(
            doc_id=doc_id,
            section_count=len(result.sections),
            chunk_count=len(result.chunks),
            window_count=len(windows),
            structure_warnings=result.structure_warnings,
            parse_stats=stored_parse.tree.parse_stats,
            source_seen_before=source_seen_before,
            parse_version=stored_parse.version,
            chunk_version=stored_chunks.version,
            artifact_path=stored_chunks.path,
        )
