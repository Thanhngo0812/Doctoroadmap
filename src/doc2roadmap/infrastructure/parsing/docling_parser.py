from __future__ import annotations

import hashlib
import importlib.metadata
import json
import math
import re
import tempfile
from collections import Counter
from dataclasses import asdict, dataclass
from io import BytesIO
from itertools import groupby
from pathlib import Path
from typing import Any
from zipfile import BadZipFile, ZipFile

from doc2roadmap.application.ports import ParsedDocument
from doc2roadmap.domain.models import DocumentNode, DocumentTree
from doc2roadmap.domain.normalization import normalize_text
from doc2roadmap.domain.document_structure import code_sequences, section_code


ADAPTER_VERSION = 11  # Bump whenever the adapter changes how DocumentNode values are built.
IMAGE_SCALE = 2.0
UNCAPTIONED_FIGURE_TEXT = "[figure]"
FORMULA_TEXT = "[formula]"
_HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
_REPEATED_PDF_GLYPH = re.compile(r"(?<![^\W\d_])([A-Za-z])(?: \1){2,}")
_TERMINAL_PUNCTUATION = re.compile(r'''[.!?:]["'”’\)\]]*(?:\s+\d+)?\s*$''')
_TRAILING_PAGE_NUMBER = re.compile(r"\s+\d+\s*$")
_LIST_START = re.compile(r"^(?:[+\-*•▪▫◦‣⁃∙●○■□]\s*|\d+(?:\.\d+)*[.)]?\s+|[^\W\d_][.)]\s+)")
_LEADING_PRIVATE_USE = re.compile(r"^[\uE000-\uF8FF]\s*")
_DETACHED_TYPES = {"caption", "figure", "footnote", "formula"}
_STITCHABLE_TYPES = {"text", "paragraph", "list_item"}
_PRIVATE_USE = range(0xE000, 0xF900)

# Unicode's Adobe Symbol table. Corporate-use glyph fragments are intentionally absent:
# they have no non-PUA character to map to and are surfaced by remaining_private_use.
_SYMBOL_BYTES = {ord(character): character for character in " !#%&()+,./0123456789:;<=>?[]_{}|"}
_SYMBOL_BYTES.update(
    {
        0x22: "∀",
        0x24: "∃",
        0x27: "∋",
        0x2A: "∗",
        0x2D: "−",
        0x40: "≅",
        0x5C: "∴",
        0x5E: "⊥",
        0x7E: "∼",
        **dict(zip(range(0x41, 0x5B), "ΑΒΧΔΕΦΓΗΙϑΚΛΜΝΟΠΘΡΣΤΥςΩΞΨΖ", strict=True)),
        **dict(zip(range(0x61, 0x7B), "αβχδεφγηιϕκλμνοπθρστυϖωξψζ", strict=True)),
        0xA0: "€",
        0xA1: "ϒ",
        0xA2: "′",
        0xA3: "≤",
        0xA4: "⁄",
        0xA5: "∞",
        0xA6: "ƒ",
        0xA7: "♣",
        0xA8: "♦",
        0xA9: "♥",
        0xAA: "♠",
        0xAB: "↔",
        0xAC: "←",
        0xAD: "↑",
        0xAE: "→",
        0xAF: "↓",
        0xB0: "°",
        0xB1: "±",
        0xB2: "″",
        0xB3: "≥",
        0xB4: "×",
        0xB5: "∝",
        0xB6: "∂",
        0xB7: "•",
        0xB8: "÷",
        0xB9: "≠",
        0xBA: "≡",
        0xBB: "≈",
        0xBC: "…",
        0xBF: "↵",
        0xC0: "ℵ",
        0xC1: "ℑ",
        0xC2: "ℜ",
        0xC3: "℘",
        0xC4: "⊗",
        0xC5: "⊕",
        0xC6: "∅",
        0xC7: "∩",
        0xC8: "∪",
        0xC9: "⊃",
        0xCA: "⊇",
        0xCB: "⊄",
        0xCC: "⊂",
        0xCD: "⊆",
        0xCE: "∈",
        0xCF: "∉",
        0xD0: "∠",
        0xD1: "∇",
        0xD5: "∏",
        0xD6: "√",
        0xD7: "⋅",
        0xD8: "¬",
        0xD9: "∧",
        0xDA: "∨",
        0xDB: "⇔",
        0xDC: "⇐",
        0xDD: "⇑",
        0xDE: "⇒",
        0xDF: "⇓",
        0xE0: "◊",
        0xE1: "〈",
        0xE5: "∑",
        0xF1: "〉",
        0xF2: "∫",
        0xF3: "⌠",
        0xF5: "⌡",
    }
)
_SYMBOL_TRANSLATION = {0xF000 + code: character for code, character in _SYMBOL_BYTES.items()}


# Bộ đọc PDF của docling. `docling-parse` là mặc định và giữ nguyên identifier để hash parse của tài liệu cũ không đổi.
# `pypdfium2` dùng cho PDF font tiếng Việt cũ mà docling-parse tách rời âm tiết ("Ph ươ ng pháp"): doc-4 có 34% mảnh
# âm tiết với docling-parse, còn pypdfium2 cho chữ liền.
PDF_BACKENDS = ("docling-parse", "pypdfium2")


@dataclass(frozen=True, slots=True)
class PipelineConfig:
    """Docling 2.114 defaults, with its current automatic OCR pinned to torch.

    Only non-default output options enter the legacy parse key; thread count
    is execution metadata. Add future page-partition options here when used.
    """
    images_scale: float = IMAGE_SCALE
    generate_picture_images: bool = True
    do_ocr: bool = True
    ocr_engine: str = "rapidocr"
    ocr_backend: str = "torch"
    bitmap_area_threshold: float = 0.05
    force_full_page_ocr: bool = False
    do_table_structure: bool = True
    table_mode: str = "accurate"
    do_cell_matching: bool = True
    layout_model: str = "heron"
    num_threads: int | None = None
    ocr_batch_size: int = 4
    layout_batch_size: int = 4
    table_batch_size: int = 4
    queue_max_size: int = 100
    batch_polling_interval_seconds: float = 0.5

    def __post_init__(self) -> None:
        if not all(math.isfinite(n) for n in (self.images_scale, self.bitmap_area_threshold,
                                             self.batch_polling_interval_seconds)):
            raise ValueError("tuỳ chọn pipeline phải hữu hạn")
        if self.images_scale <= 0 or not 0 <= self.bitmap_area_threshold <= 1:
            raise ValueError("images_scale phải > 0; bitmap_area_threshold thuộc [0, 1]")
        if self.ocr_engine not in {"rapidocr", "easyocr"}:
            raise ValueError("ocr_engine phải là rapidocr hoặc easyocr (không tự chọn theo môi trường)")
        if self.ocr_backend not in {"torch", "onnxruntime", "openvino", "paddle"}:
            raise ValueError("ocr_backend không hợp lệ")
        if self.table_mode not in {"accurate", "fast"}:
            raise ValueError("table_mode phải là accurate hoặc fast")
        if self.layout_model not in {"heron", "heron-101", "egret-medium", "egret-large", "v2"}:
            raise ValueError("layout_model không hợp lệ")
        if any(n <= 0 for n in (self.ocr_batch_size, self.layout_batch_size,
                                self.table_batch_size, self.queue_max_size)):
            raise ValueError("batch size và queue size phải > 0")
        if self.num_threads is not None and self.num_threads <= 0:
            raise ValueError("num_threads phải > 0")
        if self.batch_polling_interval_seconds <= 0:
            raise ValueError("batch_polling_interval_seconds phải > 0")
        if self.ocr_engine != "rapidocr" and self.ocr_backend != "torch":
            raise ValueError("ocr_backend chỉ áp dụng cho rapidocr")

    def cache_options(self) -> dict[str, Any]:
        defaults = asdict(PipelineConfig())
        return {key: value for key, value in asdict(self).items()
                if key != "num_threads" and value != defaults[key]}

    def options(self) -> Any:
        from docling.datamodel.accelerator_options import AcceleratorOptions
        from docling.datamodel import layout_model_specs
        from docling.datamodel.pipeline_options import (
            EasyOcrOptions, LayoutOptions, PdfPipelineOptions,
            RapidOcrOptions, TableFormerMode, TableStructureOptions,
        )

        values = asdict(self)
        threads = values.pop("num_threads")
        engine = values.pop("ocr_engine")
        backend = values.pop("ocr_backend")
        ocr = {key: values.pop(key) for key in ("bitmap_area_threshold", "force_full_page_ocr")}
        values["ocr_options"] = (RapidOcrOptions(backend=backend, **ocr) if engine == "rapidocr"
                                 else EasyOcrOptions(**ocr))
        values["table_structure_options"] = TableStructureOptions(
            mode=TableFormerMode(values.pop("table_mode")),
            do_cell_matching=values.pop("do_cell_matching"),
        )
        model = values.pop("layout_model").upper().replace("-", "_")
        values["layout_options"] = LayoutOptions(
            model_spec=getattr(layout_model_specs, f"DOCLING_LAYOUT_{model}")
        )
        if threads is not None:
            values["accelerator_options"] = AcceleratorOptions(num_threads=threads)
        return PdfPipelineOptions(**values)


class DoclingParser:
    def __init__(self, pdf_backend: str = "docling-parse", *,
                 pipeline: PipelineConfig | None = None) -> None:
        if pdf_backend not in PDF_BACKENDS:
            raise ValueError(f"pdf_backend phải là một trong {PDF_BACKENDS}")
        self.pdf_backend = pdf_backend
        self._pipeline = pipeline or PipelineConfig()
        self._converter_instance: Any | None = None

    @property
    def pipeline(self) -> PipelineConfig:
        return self._pipeline

    @staticmethod
    def _new_converter(backend: str = "docling-parse", pipeline: PipelineConfig | None = None) -> Any:
        from docling.datamodel.base_models import InputFormat
        from docling.document_converter import DocumentConverter, PdfFormatOption

        options = (pipeline or PipelineConfig()).options()
        extra: dict[str, Any] = {}
        if backend == "pypdfium2":
            from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend

            extra["backend"] = PyPdfiumDocumentBackend
        return DocumentConverter(
            format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=options, **extra)}
        )

    def _get_converter(self) -> Any:
        if self._converter_instance is None:
            self._converter_instance = (self._new_converter(self.pdf_backend, self.pipeline)
                                        if self.pipeline != PipelineConfig()
                                        else self._new_converter() if self.pdf_backend == "docling-parse"
                                        else self._new_converter(self.pdf_backend))
        return self._converter_instance

    @property
    def identifier(self) -> str:
        base = f"docling:{importlib.metadata.version('docling')}"
        return base if self.pdf_backend == "docling-parse" else f"{base}+{self.pdf_backend}"

    @property
    def adapter_version(self) -> int:
        return ADAPTER_VERSION

    @property
    def image_scale(self) -> float:
        return self.pipeline.images_scale

    @property
    def pipeline_config(self) -> dict[str, Any]:
        return self.pipeline.cache_options()

    @property
    def runtime_config(self) -> dict[str, Any]:
        return {"num_threads": self.pipeline.options().accelerator_options.num_threads}

    @staticmethod
    def _label(item: Any) -> str:
        value = getattr(item, "label", "text")
        return str(getattr(value, "value", value)).lower()

    @staticmethod
    def _bbox(item: Any) -> tuple[float, float, float, float] | None:
        provenance = getattr(item, "prov", None) or []
        if not provenance:
            return None
        bbox = getattr(provenance[0], "bbox", None)
        if bbox is None:
            return None
        names = (("l", "t", "r", "b"), ("left", "top", "right", "bottom"))
        for fields in names:
            if all(hasattr(bbox, field) for field in fields):
                return tuple(float(getattr(bbox, field)) for field in fields)  # type: ignore[return-value]
        return None

    @staticmethod
    def _page(item: Any) -> int | None:
        provenance = getattr(item, "prov", None) or []
        return int(provenance[0].page_no) if provenance else None

    @staticmethod
    def _table_text(item: Any, document: Any) -> str:
        for kwargs in ({"doc": document}, {}):
            try:
                return str(item.export_to_markdown(**kwargs))
            except (AttributeError, TypeError):
                continue
        return str(getattr(item, "text", ""))

    @classmethod
    def _table_rows(
        cls, item: Any, *, collapse_pdf_glyphs: bool
    ) -> tuple[list[list[str]], int]:
        grid = getattr(getattr(item, "data", None), "grid", None) or []
        rows: list[list[str]] = []
        mapped = 0
        for row in grid:
            clean_row = []
            for cell in row:
                text, cell_mapped = cls._clean_text(
                    str(getattr(cell, "text", "") or ""),
                    collapse_pdf_glyphs=collapse_pdf_glyphs,
                )
                clean_row.append(text)
                mapped += cell_mapped
            rows.append(clean_row)
        return rows, mapped

    @staticmethod
    def _table_id(rows: list[list[str]]) -> str:
        normalized = [[normalize_text(cell) for cell in row] for row in rows]
        payload = json.dumps(normalized, ensure_ascii=False, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @staticmethod
    def _caption(item: Any, document: Any) -> str | None:
        try:
            value = item.caption_text(doc=document)
            return str(value).strip() or None
        except (AttributeError, TypeError):
            return None

    @staticmethod
    def _image_bytes(item: Any, document: Any) -> bytes | None:
        try:
            image = item.get_image(doc=document)
        except (AttributeError, TypeError):
            return None
        if image is None:
            return None
        output = BytesIO()
        image.save(output, format="PNG")
        return output.getvalue()

    @staticmethod
    def _clean_text(text: str, *, collapse_pdf_glyphs: bool) -> tuple[str, int]:
        text = _HTML_COMMENT.sub("", text).strip()
        if not collapse_pdf_glyphs:
            return text, 0
        text = _REPEATED_PDF_GLYPH.sub(r"\1", text)
        mapped = sum(ord(character) in _SYMBOL_TRANSLATION for character in text)
        return text.translate(_SYMBOL_TRANSLATION), mapped

    @staticmethod
    def _strip_private_use_bullet(text: str) -> tuple[str, bool]:
        stripped = _LEADING_PRIVATE_USE.sub("", text, count=1)
        return stripped, stripped != text

    @staticmethod
    def _private_use_count(node: DocumentNode) -> int:
        values = [node.text, node.raw_text or "", node.context_prefix or ""]
        values.extend(cell for row in node.table_rows or [] for cell in row)
        return sum(ord(character) in _PRIVATE_USE for value in values for character in value)

    @staticmethod
    def _has_drawingml_shape(source: bytes) -> bool:
        try:
            with ZipFile(BytesIO(source)) as archive:
                return any(
                    b"schemas.microsoft.com/office/word/2010/wordprocessingShape"
                    in archive.read(name)
                    for name in archive.namelist()
                    if name.startswith("word/") and name.endswith(".xml")
                )
        except BadZipFile:
            return False

    @staticmethod
    def _is_single_column(nodes: list[DocumentNode]) -> bool:
        if any(node.bbox is None for node in nodes):
            return False
        flow = [node for node in nodes if node.node_type not in _DETACHED_TYPES]
        # ponytail: O(n²) per page; use a sweep only if dense pages make this measurable.
        return not any(
            first.bbox[2] <= second.bbox[0] or second.bbox[2] <= first.bbox[0]  # type: ignore[index]
            for index, first in enumerate(flow)
            for second in flow[index + 1 :]
        )

    @staticmethod
    def _same_row(first: DocumentNode, second: DocumentNode) -> bool:
        assert first.bbox is not None and second.bbox is not None
        first_top, first_bottom = max(first.bbox[1], first.bbox[3]), min(
            first.bbox[1], first.bbox[3]
        )
        second_top, second_bottom = max(second.bbox[1], second.bbox[3]), min(
            second.bbox[1], second.bbox[3]
        )
        overlap = min(first_top, second_top) - max(first_bottom, second_bottom)
        return overlap > min(first_top - first_bottom, second_top - second_bottom) / 2

    @classmethod
    def _repair_pdf_order(cls, nodes: list[DocumentNode]) -> tuple[list[DocumentNode], int]:
        repaired: list[DocumentNode] = []
        pages_reordered = 0
        for page, page_group in groupby(nodes, key=lambda node: node.page):
            page_nodes = list(page_group)
            if page is not None and cls._is_single_column(page_nodes):
                by_top = sorted(
                    page_nodes,
                    key=lambda node: (
                        -max(node.bbox[1], node.bbox[3]),  # type: ignore[index]
                        node.reading_order,
                    ),
                )
                rows: list[list[DocumentNode]] = []
                for node in by_top:
                    if rows and cls._same_row(rows[-1][0], node):
                        rows[-1].append(node)
                    else:
                        rows.append([node])
                ordered = [
                    node
                    for row in rows
                    for node in sorted(
                        row,
                        key=lambda item: (item.bbox[0], item.reading_order),  # type: ignore[index]
                    )
                ]
                pages_reordered += ordered != page_nodes
                page_nodes = ordered
            repaired.extend(page_nodes)
        return repaired, pages_reordered

    @staticmethod
    def _stitch_pdf_page_breaks(nodes: list[DocumentNode]) -> int:
        stitched = 0
        index = 0
        while index < len(nodes):
            first = nodes[index]
            next_index = index + 1
            while next_index < len(nodes) and nodes[next_index].node_type in _DETACHED_TYPES:
                next_index += 1
            if next_index == len(nodes):
                break
            second = nodes[next_index]
            second_text = second.text.lstrip()
            if (
                first.node_type in _STITCHABLE_TYPES
                and second.node_type in _STITCHABLE_TYPES
                and first.page is not None
                and second.page == first.page + 1
                and not _TERMINAL_PUNCTUATION.search(first.text)
                and second_text
                and second_text[0].islower()
            ):
                first.text = f"{first.text.rstrip()} {second_text}"
                if second.raw_text:
                    first.raw_text = " ".join(
                        part for part in (first.raw_text, second.raw_text.lstrip()) if part
                    )
                del nodes[next_index]
                stitched += 1
            index += 1
        return stitched

    @staticmethod
    def _join_run_text(first: str, second: str) -> str:
        second = second.lstrip()
        separator = "" if second[:1] in ",.;:!?)]}" else " "
        return f"{first.rstrip()}{separator}{second}"

    @classmethod
    def _stitch_unpositioned_runs(cls, nodes: list[DocumentNode]) -> int:
        stitched = 0
        index = 0
        while index + 1 < len(nodes):
            first, second = nodes[index : index + 2]
            second_text = second.text.lstrip()
            if (
                first.node_type in _STITCHABLE_TYPES
                and second.node_type in _STITCHABLE_TYPES
                and first.bbox is None
                and second.bbox is None
                and not _TERMINAL_PUNCTUATION.search(first.text)
                and not _TRAILING_PAGE_NUMBER.search(first.text)
                and second_text
                and second.node_type != "list_item"
                and not _LIST_START.match(second_text)
            ):
                first_text = first.text
                first.text = cls._join_run_text(first_text, second_text)
                if first.raw_text or second.raw_text:
                    first.raw_text = cls._join_run_text(
                        first.raw_text or first_text,
                        second.raw_text or second.text,
                    )
                del nodes[index + 1]
                stitched += 1
                continue
            index += 1
        return stitched

    def adapt(self, document: Any, filename: str) -> ParsedDocument:
        suffix = Path(filename).suffix.lower()
        collapse_pdf_glyphs = suffix == ".pdf"
        items = list(document.iterate_items())
        recovered_headings = set()
        if collapse_pdf_glyphs:
            # Furniture chỉ được phục hồi khi mã thuộc một chuỗi mục đã chứng minh trong tài liệu.
            seen = {normalize_text(str(getattr(item, "text", ""))) for item, _ in items
                    if self._label(item) in {"section_header", "title"}}
            codes = code_sequences(normalize_text(str(getattr(item, "text", "")))
                                   for item in getattr(document, "texts", [])
                                   if self._label(item) in {"section_header", "title", "page_header"})
            furniture = [item for item in getattr(document,'texts',[]) if self._label(item)=='page_header']
            positions = {}
            for item in furniture:
                bbox = self._bbox(item)
                if bbox:
                    positions.setdefault((str(item.text),round(bbox[1])),set()).add(self._page(item))
            running_positions = {top for (_,top),pages in positions.items() if len(pages)>=3}
            for item in getattr(document, "texts", []):
                title = normalize_text(str(getattr(item, "text", "")))
                code = section_code(title)
                if (self._label(item) != "page_header" or code is None or code[0] not in codes
                    or title in seen or _TRAILING_PAGE_NUMBER.search(title)):
                    continue
                page, bbox = self._page(item), self._bbox(item)
                if page is None or bbox is None or round(bbox[1]) in running_positions:
                    continue
                items = [(other, depth) for other, depth in items if other is not item]
                index = next((i for i, (other, _) in enumerate(items)
                              if self._page(other) is not None and (self._page(other) > page or
                                  (self._page(other) == page and self._bbox(other) is not None
                                   and self._bbox(other)[1] < bbox[1]))), len(items))
                items.insert(index, (item, 1))
                recovered_headings.add(id(item))
                seen.add(title)
        linked_captions = {
            str(getattr(reference, "cref", ""))
            for item, _ in items
            for reference in (getattr(item, "captions", None) or [])
        }
        nodes: list[DocumentNode] = []
        images: dict[str, bytes] = {}
        dropped: Counter[str] = Counter()
        warnings: list[str] = []
        captions_recovered = 0
        captions_orphaned = 0
        symbol_characters_mapped = 0
        stripped_pua_bullets = 0

        for item_index, (item, tree_level) in enumerate(items, start=1):
            label = self._label(item)
            if id(item) in recovered_headings:
                label = "section_header"
                warnings.append("recovered_math_heading: " + str(item.text))
            image_id = None
            table_rows = None
            table_id = None
            formula_id = None
            if label == "caption" and str(getattr(item, "self_ref", "")) in linked_captions:
                dropped[label] += 1
                captions_recovered += 1
                continue
            if label in {"page_header", "page_footer", "page_number"}:
                dropped[label] += 1
                continue
            if label == "caption":
                node_type = "caption"
                level = None
                text = str(getattr(item, "text", "") or "")
                captions_orphaned += 1
            elif label in {"section_header", "title"}:
                node_type = label
                level = getattr(item, "level", None)
                if level is None:
                    level = 1 if label == "title" else max(1, int(tree_level))
                text = str(getattr(item, "text", "") or "")
            elif label == "table":
                node_type = "table"
                level = None
                text = self._table_text(item, document)
                table_rows, table_mapped = self._table_rows(
                    item, collapse_pdf_glyphs=collapse_pdf_glyphs
                )
                symbol_characters_mapped += table_mapped
                table_id = self._table_id(table_rows)
            elif label in {"picture", "figure"}:
                node_type = "figure"
                level = None
                text = self._caption(item, document) or UNCAPTIONED_FIGURE_TEXT
                image = self._image_bytes(item, document)
                if image is not None:
                    image_id = hashlib.sha256(image).hexdigest()
                    images.setdefault(image_id, image)
                else:
                    page = self._page(item)
                    location = f"page {page}" if page is not None else f"item {item_index}"
                    reason = "image bytes unavailable"
                    if suffix == ".docx":
                        reason += "; DOCX DrawingML may require LibreOffice"
                    warnings.append(f"missing_image: {location}; {reason}")
            else:
                node_type = label if label else "text"
                level = None
                text = str(getattr(item, "text", "") or "")

            text, text_mapped = self._clean_text(
                text, collapse_pdf_glyphs=collapse_pdf_glyphs
            )
            raw_text, raw_mapped = self._clean_text(
                str(getattr(item, "orig", "") or ""),
                collapse_pdf_glyphs=collapse_pdf_glyphs,
            )
            symbol_characters_mapped += text_mapped + raw_mapped
            if node_type == "list_item" or (
                collapse_pdf_glyphs
                and _LEADING_PRIVATE_USE.fullmatch(text or raw_text)
            ):
                text, text_stripped = self._strip_private_use_bullet(text)
                raw_text, raw_stripped = self._strip_private_use_bullet(raw_text)
                stripped_pua_bullets += text_stripped or raw_stripped
            content = text or raw_text
            if not content:
                dropped[label] += 1
                warnings.append(f"empty_node: dropped {label}")
                continue
            if node_type == "formula":
                raw_text = content
                formula_id = hashlib.sha256(normalize_text(content).encode("utf-8")).hexdigest()
                text = FORMULA_TEXT
            else:
                text = content
            if label == "caption":
                warnings.append(f"orphan_caption: {text}")
            context_prefix = None
            if node_type != "figure":
                context_prefix, context_mapped = self._clean_text(
                    self._caption(item, document) or "",
                    collapse_pdf_glyphs=collapse_pdf_glyphs,
                )
                symbol_characters_mapped += context_mapped
            nodes.append(
                DocumentNode(
                    node_type=node_type,
                    text=text,
                    reading_order=len(nodes),
                    level=int(level) if level is not None else None,
                    page=self._page(item),
                    bbox=self._bbox(item),
                    table_rows=table_rows,
                    table_id=table_id,
                    context_prefix=context_prefix or None,
                    image_id=image_id,
                    tree_depth=int(tree_level),
                    raw_text=raw_text or None,
                    formula_id=formula_id,
                )
            )

        pages_reordered = 0
        page_breaks_stitched = 0
        if collapse_pdf_glyphs:
            nodes, pages_reordered = self._repair_pdf_order(nodes)
            page_breaks_stitched = self._stitch_pdf_page_breaks(nodes)
        runs_stitched = self._stitch_unpositioned_runs(nodes)
        for reading_order, node in enumerate(nodes):
            if node.node_type == "caption":
                node.node_type = "text"
            node.reading_order = reading_order

        remaining_private_use = sum(self._private_use_count(node) for node in nodes)
        if collapse_pdf_glyphs and remaining_private_use:
            warnings.append(f"remaining_private_use: {remaining_private_use}")

        return ParsedDocument(
            tree=DocumentTree(
                nodes=nodes,
                structure_warnings=warnings,
                parse_stats={
                    "page_count": len(document.pages) if getattr(document, "pages", None) is not None else None,
                    "items_total": len(items),
                    "nodes_kept": len(nodes),
                    "dropped": dict(sorted(dropped.items())),
                    "captions": {
                        "total": captions_recovered + captions_orphaned,
                        "recovered": captions_recovered,
                        "orphaned": captions_orphaned,
                    },
                    "images_extracted": len(images),
                    "pages_reordered": pages_reordered,
                    "page_breaks_stitched": page_breaks_stitched,
                    "runs_stitched": runs_stitched,
                    "symbol_characters_mapped": symbol_characters_mapped,
                    "stripped_pua_bullets": stripped_pua_bullets,
                },
            ),
            images=images,
        )

    def parse(self, source: bytes, filename: str) -> ParsedDocument:
        suffix = Path(filename).suffix.lower()
        if suffix not in {".pdf", ".docx"}:
            raise ValueError("DoclingParser chỉ hỗ trợ PDF và DOCX trong pha B0")
        temporary_name = ""
        try:
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temporary:
                temporary.write(source)
                temporary_name = temporary.name
            document = self._get_converter().convert(temporary_name).document
            parsed = self.adapt(document, filename)
            if suffix == ".docx" and self._has_drawingml_shape(source):
                parsed.tree.structure_warnings.append(
                    "missing_image: DOCX DrawingML shape bytes unavailable; "
                    "install LibreOffice to render it"
                )
            return parsed
        finally:
            if temporary_name:
                Path(temporary_name).unlink(missing_ok=True)
