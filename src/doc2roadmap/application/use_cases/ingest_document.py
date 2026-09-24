from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from doc2roadmap.application.ports import ArtifactStore, DocumentParser
from doc2roadmap.application.windows import assemble_windows
from doc2roadmap.domain.chunking import CHUNK_ALGORITHM_ID, chunk_document
from doc2roadmap.domain.models import DocumentTree
from doc2roadmap.domain.ports import SentenceSplitter, TokenCounter


_DOC_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def validate_doc_id(doc_id: str) -> str:
    if not _DOC_ID.fullmatch(doc_id):
        raise ValueError("doc_id chỉ được chứa chữ, số, '.', '_' và '-', tối đa 128 ký tự")
    return doc_id


def _hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _text_quality(texts: list[str]) -> dict[str, Any]:
    text = "".join(texts)
    letters = [char for char in text if char.isalpha() and unicodedata.category(char) != "Co"]
    accented = sum(
        char in "ăâđêôơưĂÂĐÊÔƠƯ"
        or any(mark in unicodedata.normalize("NFD", char) for mark in "\u0300\u0301\u0303\u0309\u0323")
        for char in letters
    )
    private_use = sum(unicodedata.category(char) == "Co" for char in text)
    replacement = text.count("\ufffd")
    letter_count = len(letters)
    accent_ratio = accented / letter_count if letter_count else 0.0
    private_ratio = private_use / letter_count if letter_count else 0.0
    replacement_ratio = replacement / len(text) if text else 0.0
    warnings = []
    if letter_count >= 1000 and accent_ratio < 0.01 and (
        private_ratio >= 0.001 or replacement_ratio >= 0.001
    ):
        warnings.append(
            "Lớp text có thể hỏng font: "
            f"{letter_count} chữ cái đọc được, {accent_ratio:.2%} có dấu, "
            f"{private_ratio:.2%} ký tự vùng dùng riêng, "
            f"{replacement_ratio:.2%} ký tự thay thế; "
            "không đủ chất lượng làm nguồn bộ vàng."
        )
    return {
        "readable_letter_count": letter_count,
        "accented_letter_ratio": accent_ratio,
        "private_use_ratio": private_ratio,
        "replacement_character_ratio": replacement_ratio,
        "warnings": warnings,
    }


def _strip_line_patterns(tree: DocumentTree, patterns: list[str]) -> int:
    if not patterns:
        return 0
    matchers = [
        re.compile(r"\s+".join(re.escape(part) for part in pattern.split()))
        for pattern in patterns
    ]
    removed = 0
    for node in tree.nodes:
        def clean(value: str) -> tuple[str, int]:
            lines = []
            count = 0
            for line in value.splitlines(keepends=True):
                original = line
                for matcher in matchers:
                    line = matcher.sub("", line)
                count += line != original
                lines.append(line)
            return "".join(lines).strip(), count

        node.text, count = clean(node.text)
        counts = [count]
        if node.raw_text is not None:
            node.raw_text, count = clean(node.raw_text)
            counts.append(count)
        if node.context_prefix is not None:
            node.context_prefix, count = clean(node.context_prefix)
            counts.append(count)
        if node.table_rows is not None:
            rows = []
            table_count = 0
            for row in node.table_rows:
                cleaned = [clean(cell) for cell in row]
                rows.append([value for value, _ in cleaned])
                table_count += sum(count for _, count in cleaned)
            node.table_rows = rows
            counts.append(table_count)
        removed += max(counts)
    return removed


@dataclass(slots=True)
class IngestSummary:
    doc_id: str
    section_count: int
    chunk_count: int
    window_count: int
    structure_warnings: list[str]
    parse_stats: dict[str, Any]
    quality_warnings: list[str]
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
        strip_lines: list[str] | tuple[str, ...] = (),
        heading_scheme: str | None = None,
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
        normalized_patterns = list(dict.fromkeys(" ".join(value.split()) for value in strip_lines))
        if any(not value for value in normalized_patterns):
            raise ValueError("strip_lines không được chứa mẫu rỗng")

        source_hash = hashlib.sha256(source).hexdigest()
        parser_config = {
            "adapter": self.parser.identifier,
            "adapter_version": self.parser.adapter_version,
            "image_scale": self.parser.image_scale,
        }
        if normalized_patterns:
            parser_config["strip_lines"] = normalized_patterns
            parser_config["strip_line_algorithm"] = "normalized-substring-all-fields-v3"
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
        if heading_scheme is not None:
            # chỉ ghi khi bật, để hash cấu hình của tài liệu cũ không đổi
            config["chunk"]["heading_scheme"] = heading_scheme
        config_hash = _hash(config)
        stored_parse = self.store.find_parse(doc_id, source_hash, parser_config_hash)
        source_seen_before = stored_parse is not None
        stripped_line_count = 0
        if stored_parse is None:
            parsed = self.parser.parse(source, filename)
            stripped_line_count = _strip_line_patterns(parsed.tree, normalized_patterns)
            manifest_fields = (
                {
                    "strip_lines": normalized_patterns,
                    "stripped_line_count": stripped_line_count,
                }
                if normalized_patterns
                else None
            )
            stored_parse = self.store.save_parse(
                doc_id,
                source_hash,
                parser_config_hash,
                config_hash,
                config,
                parsed.tree,
                parsed.images,
                manifest_fields=manifest_fields,
            )
        elif normalized_patterns:
            stripped_line_count = int(stored_parse.manifest["stripped_line_count"])

        manifest_fields = (
            {
                "strip_lines": normalized_patterns,
                "stripped_line_count": stripped_line_count,
            }
            if normalized_patterns
            else None
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
            heading_scheme=heading_scheme,
        )
        windows = assemble_windows(result.chunks)
        quality = _text_quality([chunk.text for chunk in result.chunks])
        manifest_fields = {**(manifest_fields or {}), "text_quality": quality}
        stored_chunks = self.store.save_chunks(
            doc_id,
            source_hash,
            config_hash,
            config,
            stored_parse.version,
            result,
            manifest_fields=manifest_fields,
        )
        return IngestSummary(
            doc_id=doc_id,
            section_count=len(result.sections),
            chunk_count=len(result.chunks),
            window_count=len(windows),
            structure_warnings=result.structure_warnings,
            parse_stats=stored_parse.tree.parse_stats,
            quality_warnings=quality["warnings"],
            source_seen_before=source_seen_before,
            parse_version=stored_parse.version,
            chunk_version=stored_chunks.version,
            artifact_path=stored_chunks.path,
        )
