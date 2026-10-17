from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from collections import defaultdict
from pathlib import Path
from time import perf_counter
from typing import Any

from doc2roadmap.application.stage_measurements import measure_stage
from doc2roadmap.application.ports import ArtifactStore, DocumentParser
from doc2roadmap.application.windows import assemble_windows
from doc2roadmap.domain.chunking import CHUNK_ALGORITHM_ID, ROLE_ALGORITHM_ID, assign_section_roles, chunk_document
from doc2roadmap.domain.models import DocumentTree
from doc2roadmap.domain.document_structure import RESULT_MIN_COUNT, RESULT_MAX_BODY_CHARS
from doc2roadmap.domain.ports import SentenceSplitter, TokenCounter


_DOC_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def validate_doc_id(doc_id: str) -> str:
    if not _DOC_ID.fullmatch(doc_id):
        raise ValueError("doc_id chỉ được chứa chữ, số, '.', '_' và '-', tối đa 128 ký tự")
    return doc_id


def _hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def parse_config(parser: DocumentParser, strip_lines=()) -> dict[str, Any]:
    config = {"adapter": parser.identifier, "adapter_version": parser.adapter_version,
              "image_scale": parser.image_scale}
    pipeline = getattr(parser, "pipeline_config", {})
    if pipeline:
        config["pipeline"] = pipeline
    patterns = list(dict.fromkeys(" ".join(value.split()) for value in strip_lines))
    if any(not value for value in patterns):
        raise ValueError("strip_lines không được chứa mẫu rỗng")
    if patterns:
        config["strip_lines"] = patterns
        config["strip_line_algorithm"] = "normalized-substring-all-fields-v3"
    return config


def refresh_chunk_roles(store: ArtifactStore, doc_id: str, *, version: int | None = None):
    """Bổ sung R1 từ cây section có sẵn, giữ nguyên toàn bộ định danh và văn bản.

    Chỉ lớp cấu trúc; nhãn nghĩa qua LabelChunkRoles (vé 14). Không đổi cây heading hoặc dùng từ khóa tiêu đề.
    """
    validate_doc_id(doc_id)
    stored = store.load_chunks(doc_id, version) if version is not None else store.load_latest_chunks(doc_id)
    assign_section_roles(stored.result.sections, stored.result.chunks)
    config = {**stored.manifest["config"], "chunk": {**stored.manifest["config"]["chunk"],
              "role_algorithm_id": ROLE_ALGORITHM_ID}}
    return store.save_chunks(doc_id, stored.manifest["source_hash"], _hash(config), config,
                             stored.manifest["parse_version"], stored.result,
                             manifest_fields={"roles_from_chunks_version": version or stored.version,
                                              **{key: stored.manifest[key] for key in
                                                 ("text_quality", "text_quality_selection", "text_quality_override_reason",
                                                  "strip_lines", "stripped_line_count")
                                                 if key in stored.manifest}})


# Âm tiết tiếng Việt bị tách ("th ứ c", "Gi ớ i"): một token chỉ gồm phụ âm đầu đứng ngay trước một token mở đầu bằng
# nguyên âm tiếng Việt có dấu. Văn bản thường gần như không có mẫu này; biến toán học một chữ ("n", "m") không đứng trước
# nguyên âm tiếng Việt. Đo trên kho: bản vỡ chữ doc-4 22,4%, doc-6 3,6%; mọi bản sạch <= 0,27%.
_ONSET = r"(?:ngh|ng|nh|ch|tr|th|ph|kh|gh|gi|qu|[bcdđghklmnpqrstvx])"
_VIETNAMESE_VOWELS = "ăâêôơưàáảãạằắẳẵặầấẩẫậèéẻẽẹềếểễệìíỉĩịòóỏõọồốổỗộờớởỡợùúủũụừứửữựỳýỷỹỵ"
_SPLIT_SYLLABLE = re.compile(rf"(?<!\S){_ONSET} [{_VIETNAMESE_VOWELS}]", re.IGNORECASE)
SPLIT_SYLLABLE_RATIO = 0.01
SPLIT_SYLLABLE_MIN = 20
_SYLLABLE = re.compile(rf"^{_ONSET}?[aeiouy{_VIETNAMESE_VOWELS}]{{1,3}}(?:ch|ng|nh|[cmnpt])?$", re.IGNORECASE)
_STRANGE = re.compile(r"[†‰ıŒœ¡⁄�]")
_VNI = re.compile(r"(?:[aeou][äøùûï]|oâ|eâ|[a-z]ö[ôùûú]|ñ)", re.IGNORECASE)
_QUALITY_TEXT_TYPES = {"paragraph", "title", "list_item", "text", "section_header"}
NON_LATIN_GREEK_RATIO = 0.01


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
    joined = unicodedata.normalize("NFC", " ".join(texts))
    split_count = len(_SPLIT_SYLLABLE.findall(joined))
    word_count = len(joined.split())
    split_ratio = split_count / word_count if word_count else 0.0
    tokens = re.findall(r"[^\W\d_]+", joined.casefold().replace("ƣ", "ư").replace("Ƣ", "Ư"))
    syllables = [token for token in tokens if len(token) >= 2]
    normalized_letters = [c for c in unicodedata.normalize("NFKC", text) if c.isalpha()]
    foreign_letters = sum(not any(script in unicodedata.name(c, "") for script in ("LATIN", "GREEK"))
                          for c in normalized_letters)
    if split_count >= SPLIT_SYLLABLE_MIN and split_ratio >= SPLIT_SYLLABLE_RATIO:
        warnings.append(
            f"Chữ tiếng Việt có thể bị tách rời âm tiết: {split_count} chỗ ({split_ratio:.2%} số từ) dạng \"th ứ c\"; "
            "đọc lại bằng `ingest --pdf-backend pypdfium2` trước khi chạy A3."
        )
    return {
        "readable_letter_count": letter_count,
        "non_latin_greek_letter_count": foreign_letters,
        "nfkc_letter_count": len(normalized_letters),
        "non_latin_greek_letter_ratio": foreign_letters / max(len(normalized_letters), 1),
        "split_syllable_ratio": split_ratio,
        "accented_letter_ratio": accent_ratio,
        "private_use_ratio": private_ratio,
        "replacement_character_ratio": replacement_ratio,
        "valid_vietnamese_syllable_ratio": sum(bool(_SYLLABLE.fullmatch(t)) for t in syllables) / max(len(syllables), 1),
        "single_letter_token_ratio": sum(len(t) == 1 for t in tokens) / max(len(tokens), 1),
        "strange_character_ratio": len(_STRANGE.findall(joined)) / max(len(joined), 1),
        "vni_sequence_count": len(_VNI.findall(joined)),
        "vni_sequence_ratio": len(_VNI.findall(joined)) / max(len(tokens), 1),
        "warnings": warnings,
    }


def tree_text_quality(tree: DocumentTree) -> dict[str, Any]:
    pages = defaultdict(list)
    for node in tree.nodes:
        if node.node_type in _QUALITY_TEXT_TYPES:
            pages[node.page].append(node.text)

    def assess(texts):
        quality = _text_quality(texts)
        if quality["nfkc_letter_count"] >= 100 and quality["non_latin_greek_letter_ratio"] >= NON_LATIN_GREEK_RATIO:
            quality["warnings"].append(
                f"Chữ ngoài hệ Latin/Hy Lạp: {quality['non_latin_greek_letter_ratio']:.2%} "
                "chữ cái sau NFKC; có thể bị thay hệ chữ/font.")
        # English and short labels alone must not trigger the Vietnamese syllable gate.
        if quality["readable_letter_count"] >= 100 and (
            quality["strange_character_ratio"] >= 0.005
            or (quality["vni_sequence_count"] >= 3 and quality["vni_sequence_ratio"] >= 0.01)
            or (quality["valid_vietnamese_syllable_ratio"] < 0.80
                and quality["split_syllable_ratio"] >= 0.01)
        ):
            quality["warnings"].append("Chất lượng chữ không đạt: âm tiết/font tiếng Việt")
        return quality

    overall = assess([text for texts in pages.values() for text in texts])
    page_metrics = [{"page": page, **assess(texts)} for page, texts in pages.items()]
    bad = [row for row in page_metrics if row["warnings"]]
    bad_vni_nodes = [node.page for node in tree.nodes
                     if node.node_type in _QUALITY_TEXT_TYPES
                     and len(_VNI.findall(node.text)) >= 3
                     and _text_quality([node.text])["vni_sequence_ratio"] >= 0.05]
    if bad_vni_nodes:
        overall["warnings"].append("Dòng mã VNI chưa chuyển Unicode ở trang: " + ", ".join(map(str, dict.fromkeys(bad_vni_nodes))))
    if bad:
        overall["warnings"].append("Trang có chất lượng chữ chưa đạt: " + ", ".join(str(r["page"]) for r in bad))
    overall["pages"] = page_metrics
    return overall


def require_text_quality(stored, *, reason=None, store=None) -> None:
    if reason is not None and not reason.strip():
        raise ValueError("lý do cho phép chữ hỏng không được rỗng")
    warnings = list(stored.manifest.get("text_quality", {}).get("warnings", []))
    # Historic chunks predate the page-level gate; inspect their pinned parse,
    # not today's PDF or the newest parse from another backend.
    if store is not None and "parse_version" in stored.manifest:
        try:
            tree = store.load_parse(stored.result.doc_id, stored.manifest["parse_version"]).tree
        except FileNotFoundError:
            pass  # Legacy/in-memory stores may have chunks without a parse tree.
        else:
            warnings.extend(tree_text_quality(tree)["warnings"])
    if warnings and not (reason or stored.manifest.get("text_quality_override_reason")):
        raise ValueError("chất lượng chữ chưa xác nhận; dừng trước khi chi tiền: "
                         + "; ".join(dict.fromkeys(warnings))
                         + ". Đọc lại PDF hoặc dùng --allow-text-quality-reason với lý do.")


def quality_selection_report(selection):
    """Keep full measurements in manifests, but CLI shows only the worst pages."""
    attempts = []
    for attempt in selection["attempts"]:
        quality = attempt["quality"]
        if quality is not None:
            pages = quality.get("pages", [])
            quality = {**quality, "pages_checked": len(pages),
                       "pages": [page for page in pages if page["warnings"]][:10]}
        attempts.append({**attempt, "quality": quality})
    return {**selection, "attempts": attempts}


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
        *,
        allow_backend_fallback: bool = True,
        pdf_scope_validator=None,
    ) -> None:
        self.parser = parser
        self.store = store
        self.counter = counter
        self.splitter = splitter
        self.allow_backend_fallback = allow_backend_fallback
        self.pdf_scope_validator = pdf_scope_validator

    def select_parse(self, source, filename, doc_id, strip_lines=(), *, dry_run=False, quality_reason=None):
        if quality_reason is not None and not quality_reason.strip():
            raise ValueError("lý do cho phép chữ hỏng không được rỗng")
        if Path(filename).suffix.lower() == ".pdf" and self.pdf_scope_validator is not None:
            self.pdf_scope_validator(source)
        source_hash = hashlib.sha256(source).hexdigest()
        parser = self.parser
        attempts = []
        candidates = []
        elapsed = 0.0
        for index in range(2):
            pconfig = parse_config(parser, strip_lines)
            stored = self.store.find_parse(doc_id, source_hash, _hash(pconfig))
            parsed = None
            stripped = 0
            if stored is None and not dry_run:
                started = perf_counter()
                parsed = parser.parse(source, filename)
                elapsed += perf_counter() - started
                stripped = _strip_line_patterns(parsed.tree, list(strip_lines))
            tree = stored.tree if stored else parsed.tree if parsed else None
            quality = tree_text_quality(tree) if tree is not None else None
            backend = getattr(parser, "pdf_backend", parser.identifier)
            attempts.append({"backend": backend, "reused": stored is not None, "quality": quality,
                             "quality_status": "chưa đo" if quality is None else "cảnh báo" if quality["warnings"] else "đạt"})
            candidates.append((parser, stored, parsed, stripped, quality))
            if (not self.allow_backend_fallback or quality is None or not quality["warnings"]
                    or not hasattr(parser, "with_pdf_backend") or Path(filename).suffix.lower() != ".pdf"):
                break
            parser = parser.with_pdf_backend("pypdfium2" if backend == "docling-parse" else "docling-parse")
        selected = min(candidates, key=lambda c: (2 if c[4] is None else int(bool(c[4]["warnings"])),
                                                 -(c[4] or {}).get("valid_vietnamese_syllable_ratio", 1)))
        parser, stored, parsed, stripped, quality = selected
        self.last_parse_selection = {"selected_backend": getattr(parser, "pdf_backend", parser.identifier) if quality is not None else None,
                                     "planned_backend": getattr(parser, "pdf_backend", parser.identifier),
                                     "mode": "auto" if self.allow_backend_fallback else "pinned",
                                     "reason": "unmeasured" if quality is None else "quality_fallback" if parser is not self.parser else "requested_backend",
                                     "attempts": attempts}
        if quality and quality["warnings"] and (hasattr(self.parser, "with_pdf_backend")
                                                 or self.parser.identifier.startswith("a1-nhe:")) and not quality_reason:
            raise ValueError("chất lượng chữ không đạt ở bộ đọc đã đo: " + json.dumps(quality_selection_report(self.last_parse_selection), ensure_ascii=False)
                             + "; thử --a1 docling với --pdf-backend, hoặc --allow-text-quality-reason với lý do")
        return parser, stored, parsed, stripped, quality, elapsed

    @measure_stage
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
        result_min_count: int = RESULT_MIN_COUNT,
        result_max_body_chars: int = RESULT_MAX_BODY_CHARS,
        quality_reason: str | None = None,
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
        if quality_reason is not None and not quality_reason.strip():
            raise ValueError("lý do cho phép chữ hỏng không được rỗng")
        selected_parser, stored_parse, parsed, stripped_line_count, tree_quality, parse_runtime_seconds = self.select_parse(
            source, filename, doc_id, normalized_patterns, quality_reason=quality_reason)
        parser_config = parse_config(selected_parser, normalized_patterns)
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
                "result_min_count": result_min_count,
                "result_max_body_chars": result_max_body_chars,
            },
            "tokenizer_id": self.counter.identifier,
        }
        if heading_scheme is not None:
            # chỉ ghi khi bật, để hash cấu hình của tài liệu cũ không đổi
            config["chunk"]["heading_scheme"] = heading_scheme
        config_hash = _hash(config)
        source_seen_before = stored_parse is not None
        if stored_parse is None:
            manifest_fields = (
                {
                    "strip_lines": normalized_patterns,
                    "stripped_line_count": stripped_line_count,
                }
                if normalized_patterns
                else None
            )
            manifest_fields = {**(manifest_fields or {}), "parse_runtime_seconds": parse_runtime_seconds,
                               "parser_runtime": getattr(selected_parser, "runtime_config", {}),
                               "text_quality_selection": self.last_parse_selection}
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
            result_min_count=result_min_count,
            result_max_body_chars=result_max_body_chars,
        )
        windows = assemble_windows(result.chunks)
        quality = _text_quality([chunk.text for chunk in result.chunks])
        if hasattr(self.parser, "with_pdf_backend") or self.parser.identifier.startswith("a1-nhe:"):
            quality = tree_quality
        manifest_fields = {**(manifest_fields or {}), "text_quality": quality,
                           "text_quality_selection": self.last_parse_selection,
                           **({"text_quality_override_reason": quality_reason} if quality_reason else {}),
                           "page_count": stored_parse.tree.parse_stats.get("page_count"),
                           "parse_runtime_seconds": parse_runtime_seconds,
                           "parse_reused": source_seen_before}
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
