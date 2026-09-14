from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass

from .models import (
    Chunk,
    ChunkingResult,
    DocumentNode,
    DocumentTree,
    FormulaRef,
    ImageRef,
    Section,
    TableRef,
)
from .normalization import normalize_text
from .ports import SentenceSplitter, TextSpan, TokenCounter


HEADING_TYPES = {"title", "section_header"}
MERGEABLE_TYPES = {"text", "paragraph", "list_item", "figure", "table", "formula"}
TEXT_BLOCK_TYPES = {"text", "paragraph", "list_item"}
CHUNK_ALGORITHM_ID = "section-id-v8"
OVERSIZE_TABLE_ROW = "table_row_exceeds_max_tokens"
OVERSIZE_TABLE_PRESERVED = "table_kept_whole_above_text_limit"
OVERSIZE_SENTENCE_BOUNDARY = "sentence_splitter_no_boundary"
OVERSIZE_HARD_CAP = "hard_cap_forced_split"
_NUMBERED_HEADING = re.compile(r"^(\d+(?:\.\d+)*)(?:[.)])?\s+")
_LETTER_HEADING = re.compile(r"^[^\W\d_][.)]\s+")
_ARABIC_NUMBER = re.compile(r"\d+")
_ROMAN_NUMBER = re.compile(r"(?<![^\W\d_])[IVXLCDM]+(?![^\W\d_])", re.IGNORECASE)
_TRAILING_PAGE_NUMBER = re.compile(r"\s+\d+\s*$")
_LEADING_BULLETS = frozenset("•▪▫◦‣⁃∙●○■□-–—")


@dataclass(slots=True)
class _LeafBlock:
    node: DocumentNode
    block_type: str
    text: str
    char_start: int
    char_end: int
    owner: Section
    oversize_reason: str | None = None


def _stable_id(prefix: str, *parts: object) -> str:
    payload = json.dumps(parts, ensure_ascii=False, separators=(",", ":"))
    digest = hashlib.blake2b(payload.encode("utf-8"), digest_size=12).hexdigest()
    return f"{prefix}_{digest}"


def _section_id(doc_id: str, path: list[str], occurrence: int) -> str:
    return _stable_id("s", doc_id, path, occurrence)


def _chunk_id(
    doc_id: str,
    section_id: str,
    text: str,
    split_index: int,
    occurrence: int,
) -> str:
    return _stable_id("c", doc_id, section_id, text, split_index, occurrence)


def _table_markdown(node: DocumentNode) -> str:
    if not node.table_rows:
        return node.text
    rows = [[str(cell).replace("|", "\\|") for cell in row] for row in node.table_rows]
    width = max(len(row) for row in rows)
    rows = [row + [""] * (width - len(row)) for row in rows]
    header = rows[0]
    body = rows[1:]
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join(["---"] * width) + " |"]
    lines.extend("| " + " | ".join(row) + " |" for row in body)
    return "\n".join(lines)


def _heading_number_level(title: str) -> int | None:
    match = _NUMBERED_HEADING.match(title)
    return match.group(1).count(".") + 1 if match else None


def _is_numbered_heading(title: str) -> bool:
    return _heading_number_level(title) is not None or bool(_LETTER_HEADING.match(title))


def _false_heading_reason(
    title: str, body_texts: list[str], *, sequence_member: bool = False
) -> str | None:
    if _is_numbered_heading(title) or sequence_member:
        return None
    if title[0] in _LEADING_BULLETS or unicodedata.category(title[0]) == "Pd":
        return "bullet"
    if sum(text.count(title) for text in body_texts) >= 2:
        return "repeated"
    if (title.endswith(":") and title[0].islower()) or len(title.split()) > 15:
        return "heuristic"
    return None


def _roman_value(value: str) -> int:
    digits = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    result = 0
    previous = 0
    for character in reversed(value.upper()):
        digit = digits[character]
        result += -digit if digit < previous else digit
        previous = max(previous, digit)
    return result


def _chapter_sequences(nodes: list[DocumentNode]) -> tuple[set[int], dict[int, int]]:
    headings = [
        (index, normalize_text(node.text))
        for index, node in enumerate(nodes)
        if node.node_type in HEADING_TYPES and normalize_text(node.text)
    ]
    groups: dict[str, list[tuple[int, int, int]]] = defaultdict(list)
    for heading_position, (node_index, title) in enumerate(headings):
        matches = sorted(
            [*_ARABIC_NUMBER.finditer(title), *_ROMAN_NUMBER.finditer(title)],
            key=lambda match: match.start(),
        )
        for match in matches:
            prefix = title[: match.start()].casefold()
            if not any(character.isalpha() for character in prefix):
                continue
            value = int(match.group()) if match.group().isdigit() else _roman_value(match.group())
            groups[prefix].append((heading_position, node_index, value))

    sequence_members: set[int] = set()
    covering: list[tuple[int, int, list[tuple[int, int, int]]]] = []
    for members in groups.values():
        if len({value for _, _, value in members}) < 2:
            continue
        sequence_members.update(node_index for _, node_index, _ in members)
        positions = sorted({position for position, _, _ in members})
        if any(second > first + 1 for first, second in zip(positions, positions[1:])):
            covering.append((positions[0], positions[-1], members))

    levels: dict[int, int] = {}
    for start, end, members in covering:
        level = 1 + sum(
            outer_start < start and end < outer_end
            for outer_start, outer_end, _ in covering
        )
        for _, node_index, _ in members:
            levels[node_index] = max(levels.get(node_index, 0), level)
    return sequence_members, levels


def _group_warnings(warnings: list[str]) -> list[str]:
    counts = Counter(warnings)
    emitted: set[str] = set()
    grouped = []
    for warning in warnings:
        if warning not in emitted:
            count = counts[warning]
            grouped.append(f"{warning} ×{count}" if count > 1 else warning)
            emitted.add(warning)
    return grouped


def _is_non_linguistic(text: str) -> bool:
    return len(text) >= 100 and sum(character.isalpha() for character in text) / len(text) < 0.1


def _toc_candidate(text: str, headings: set[str]) -> bool:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines or not any(_TRAILING_PAGE_NUMBER.search(line) for line in lines):
        return False
    matches = sum(_TRAILING_PAGE_NUMBER.sub("", line).strip() in headings for line in lines)
    return matches * 2 > len(lines)


def _toc_runs(nodes: list[DocumentNode], headings: set[str]) -> tuple[set[int], dict[int, str]]:
    candidates = {
        index
        for index, node in enumerate(nodes)
        if node.node_type in TEXT_BLOCK_TYPES
        and _toc_candidate(normalize_text(node.text), headings)
    }
    excluded: set[int] = set()
    warnings: dict[int, str] = {}
    index = 0
    while index < len(nodes):
        if index not in candidates:
            index += 1
            continue
        end = index + 1
        while end in candidates:
            end += 1
        first_text = normalize_text(nodes[index].text)
        if end - index > 1 or "\n" in first_text:
            excluded.update(range(index, end))
            excerpt = " | ".join(
                normalize_text(nodes[item].text).replace("\n", " | ")
                for item in range(index, min(end, index + 2))
            )
            warnings[index] = f"toc_block: {excerpt[:120]}"
        index = end
    return excluded, warnings


def _table_parts(
    text: str, max_tokens: int, counter: TokenCounter
) -> list[tuple[str, str | None]]:
    if counter.count(text) <= max_tokens:
        return [(text, None)]
    lines = text.splitlines()
    if len(lines) < 3 or not re.match(r"^\|?\s*:?-{3,}", lines[1]):
        return [(text, OVERSIZE_TABLE_ROW)]

    header = lines[:2]
    parts: list[tuple[str, str | None]] = []
    rows: list[str] = []
    for row in lines[2:]:
        candidate = "\n".join([*header, *rows, row])
        if rows and counter.count(candidate) > max_tokens:
            parts.append(("\n".join([*header, *rows]), None))
            rows = []
        single = "\n".join([*header, row])
        if not rows and counter.count(single) > max_tokens:
            parts.append((single, OVERSIZE_TABLE_ROW))
        else:
            rows.append(row)
    if rows:
        parts.append(("\n".join([*header, *rows]), None))
    return parts


def _sentence_groups(
    text: str,
    max_tokens: int,
    overlap: int,
    counter: TokenCounter,
    splitter: SentenceSplitter,
) -> tuple[list[TextSpan], bool]:
    if counter.count(text) <= max_tokens:
        return [TextSpan(0, len(text))], False
    sentences = splitter.split(text) or [TextSpan(0, len(text))]
    splitter_failed = len(sentences) == 1 and sentences[0] == TextSpan(0, len(text))
    groups: list[TextSpan] = []
    start = 0
    while start < len(sentences):
        end = start + 1
        while end < len(sentences):
            candidate = text[sentences[start].start : sentences[end].end]
            if counter.count(candidate) > max_tokens:
                break
            end += 1
        groups.append(TextSpan(sentences[start].start, sentences[end - 1].end))
        if end == len(sentences):
            break
        start = max(start + 1, end - overlap)
    return groups, splitter_failed


def _hard_cap_spans(
    text: str,
    span: TextSpan,
    hard_cap_tokens: int,
    counter: TokenCounter,
) -> list[TextSpan]:
    if counter.count(text[span.start : span.end]) <= hard_cap_tokens:
        return [span]

    parts: list[TextSpan] = []
    start = span.start
    # ponytail: hard-cap splitting is exceptional; cache boundaries only if giant blocks make this hot.
    while start < span.end:
        boundaries = [
            start,
            *(
                index
                for index in range(start + 1, span.end)
                if not unicodedata.combining(text[index])
            ),
            span.end,
        ]
        if counter.count(text[start : span.end]) <= hard_cap_tokens:
            parts.append(TextSpan(start, span.end))
            break

        low, high, best = 1, len(boundaries) - 1, 0
        while low <= high:
            middle = (low + high) // 2
            if counter.count(text[start : boundaries[middle]]) <= hard_cap_tokens:
                best = middle
                low = middle + 1
            else:
                high = middle - 1
        if best == 0:
            raise ValueError("một cụm ký tự đơn lẻ vượt hard_cap_tokens")

        safe_end = boundaries[best]
        floor_tokens = hard_cap_tokens - max(1, hard_cap_tokens // 10)
        low, high, window_start = 1, best, safe_end
        while low <= high:
            middle = (low + high) // 2
            if counter.count(text[start : boundaries[middle]]) >= floor_tokens:
                window_start = boundaries[middle]
                high = middle - 1
            else:
                low = middle + 1
        spaces = [
            boundary
            for boundary in boundaries[1 : best + 1]
            if boundary >= window_start and text[boundary - 1].isspace()
        ]
        end = spaces[-1] if spaces else safe_end
        parts.append(TextSpan(start, end))
        start = end
    return parts


def chunk_document(
    tree: DocumentTree,
    doc_id: str,
    counter: TokenCounter,
    splitter: SentenceSplitter,
    *,
    max_tokens: int = 512,
    max_table_tokens: int = 2048,
    hard_cap_tokens: int = 6000,
    target_tokens: int = 256,
    sentence_overlap: int = 1,
) -> ChunkingResult:
    if not 0 < target_tokens <= max_tokens:
        raise ValueError("target_tokens phải lớn hơn 0 và không vượt max_tokens")
    if max_table_tokens <= 0 or hard_cap_tokens <= 0:
        raise ValueError("max_table_tokens và hard_cap_tokens phải lớn hơn 0")
    if sentence_overlap < 0:
        raise ValueError("sentence_overlap không được âm")

    nodes = sorted(tree.nodes, key=lambda node: node.reading_order)
    sequence_members, sequence_levels = _chapter_sequences(nodes)
    known_headings = {
        title
        for node in nodes
        if node.node_type in HEADING_TYPES
        for title in [normalize_text(node.text)]
        if title
    }
    toc_indexes, toc_warnings = _toc_runs(nodes, known_headings)
    declared_levels = {
        int(node.level)
        for node in nodes
        if node.node_type in HEADING_TYPES and node.level is not None
    }
    declared_hierarchy = len(declared_levels) >= 2
    body_texts = [
        text
        for node in nodes
        if node.node_type not in HEADING_TYPES
        for text in [normalize_text(node.text)]
        if text
    ]
    root = Section(
        section_id=_section_id(doc_id, [], 0),
        doc_id=doc_id,
        title="<document>",
        level=0,
        heading_level_raw=None,
        parent_section_id=None,
        section_path=[],
        order_index=-1,
    )
    sections = [root]
    stack = [root]
    heading_depth: dict[str, int | None] = {root.section_id: -1}
    section_occurrences: dict[tuple[str, ...], int] = defaultdict(int)
    chunk_occurrences: dict[tuple[str, str, int], int] = defaultdict(int)
    chunks: list[Chunk] = []
    full_parts: list[str] = []
    full_length = 0
    result_order = 0
    structure_warnings = list(tree.structure_warnings)
    heading_levels: list[int] = []
    numbered_heading_seen = False
    numbered_level: int | None = None
    pending: list[_LeafBlock] = []

    def emit(blocks: list[_LeafBlock]) -> None:
        nonlocal result_order
        first = blocks[0]
        text = "\n".join(block.text for block in blocks)
        semantic_spans, splitter_failed = (
            _sentence_groups(text, max_tokens, sentence_overlap, counter, splitter)
            if len(blocks) == 1 and first.block_type != "table"
            else ([TextSpan(0, len(text))], False)
        )
        if splitter_failed:
            location = (
                f"page {first.node.page}"
                if first.node.page is not None
                else f"section {' > '.join(first.owner.section_path) or '<document>'}"
            )
            structure_warnings.append(f"{OVERSIZE_SENTENCE_BOUNDARY}: {location}")
        spans = [
            (part, len(parts) > 1)
            for semantic_span in semantic_spans
            for parts in [_hard_cap_spans(text, semantic_span, hard_cap_tokens, counter)]
            for part in parts
        ]
        for split_index, (span, forced) in enumerate(spans):
            chunk_text = text[span.start : span.end]
            char_start = first.char_start + span.start
            char_end = first.char_start + span.end
            span_blocks = [
                block
                for block in blocks
                if block.char_start < char_end and char_start < block.char_end
            ]
            chunk_first = span_blocks[0]
            occurrence_key = (first.owner.section_id, chunk_text, split_index)
            occurrence = chunk_occurrences[occurrence_key]
            chunk_occurrences[occurrence_key] += 1
            token_count = counter.count(chunk_text)
            chunks.append(
                Chunk(
                    chunk_id=_chunk_id(
                        doc_id,
                        first.owner.section_id,
                        chunk_text,
                        split_index,
                        occurrence,
                    ),
                    doc_id=doc_id,
                    order_index=result_order,
                    split_index=split_index,
                    page=chunk_first.node.page,
                    char_start=char_start,
                    char_end=char_end,
                    parent_section_id=first.owner.section_id,
                    section_path=list(first.owner.section_path),
                    heading_level=first.owner.level,
                    block_types=list(dict.fromkeys(block.block_type for block in span_blocks)),
                    text=chunk_text,
                    context_prefix=(
                        normalize_text(chunk_first.node.context_prefix)
                        if chunk_first.node.context_prefix
                        else None
                    ),
                    image_refs=[
                        ImageRef(block.node.image_id, block.char_start)
                        for block in span_blocks
                        if block.node.image_id is not None
                        and char_start <= block.char_start < char_end
                    ],
                    token_count=token_count,
                    tokenizer_id=counter.identifier,
                    table_refs=[
                        TableRef(block.node.table_id, max(block.char_start, char_start))
                        for block in span_blocks
                        if block.node.table_id is not None
                    ],
                    formula_refs=[
                        FormulaRef(block.node.formula_id, max(block.char_start, char_start))
                        for block in span_blocks
                        if block.node.formula_id is not None
                    ],
                    oversize_reason=(
                        OVERSIZE_HARD_CAP
                        if forced
                        else (
                            next(
                                (
                                    block.oversize_reason
                                    for block in span_blocks
                                    if block.oversize_reason is not None
                                ),
                                None,
                            )
                            or (
                                OVERSIZE_TABLE_PRESERVED
                                if token_count > max_tokens
                                and any(
                                    block.block_type == "table" for block in span_blocks
                                )
                                else (
                                    OVERSIZE_SENTENCE_BOUNDARY
                                    if token_count > max_tokens
                                    else None
                                )
                            )
                        )
                    ),
                )
            )
            result_order += 1

    def flush() -> None:
        if pending:
            emit(pending)
            pending.clear()

    def queue(block: _LeafBlock) -> None:
        if block.block_type not in MERGEABLE_TYPES:
            flush()
            emit([block])
            return
        if pending:
            candidate = "\n".join([item.text for item in pending] + [block.text])
            merge_limit = (
                max_table_tokens
                if block.block_type == "table"
                or any(item.block_type == "table" for item in pending)
                else max_tokens
            )
            if (
                pending[0].owner.section_id != block.owner.section_id
                or counter.count(candidate) > merge_limit
            ):
                flush()
        pending.append(block)
        if counter.count("\n".join(item.text for item in pending)) >= target_tokens:
            flush()

    for node_index, node in enumerate(nodes):
        node_type = node.node_type
        if node.node_type in HEADING_TYPES:
            title = normalize_text(node.text)
            if not title:
                continue
            false_heading_reason = _false_heading_reason(
                title,
                body_texts,
                sequence_member=node_index in sequence_members,
            )
            if false_heading_reason:
                warning_type = (
                    "rejected_heading"
                    if false_heading_reason == "heuristic"
                    else f"rejected_heading_{false_heading_reason}"
                )
                structure_warnings.append(f"{warning_type}: {title}")
                node_type = "text"
            else:
                flush()
                explicit_level = _heading_number_level(title)
                if explicit_level is not None:
                    level = explicit_level
                    numbered_level = level
                    numbered_heading_seen = True
                elif _LETTER_HEADING.match(title):
                    level = (numbered_level or 1) + 1
                    numbered_heading_seen = True
                elif node_index in sequence_levels:
                    level = numbered_level = sequence_levels[node_index]
                    numbered_heading_seen = True
                elif declared_hierarchy and node.level is not None:
                    level = max(1, int(node.level))
                elif not numbered_heading_seen:
                    level = 1
                else:
                    level = (numbered_level or 1) + 1

                parent_depth = heading_depth[stack[-1].section_id]
                if (
                    node.tree_depth is not None
                    and parent_depth is not None
                    and node.tree_depth > parent_depth
                    and level <= stack[-1].level
                ):
                    level = stack[-1].level + 1
                    structure_warnings.append(f"clamped_heading_level: {title} -> {level}")
                while len(stack) > 1 and stack[-1].level >= level:
                    stack.pop()
                path = [*stack[-1].section_path, title]
                path_key = tuple(path)
                occurrence = section_occurrences[path_key]
                section_occurrences[path_key] += 1
                section = Section(
                    section_id=_section_id(doc_id, path, occurrence),
                    doc_id=doc_id,
                    title=title,
                    level=level,
                    heading_level_raw=node.level,
                    parent_section_id=stack[-1].section_id,
                    section_path=path,
                    order_index=result_order,
                )
                sections.append(section)
                stack.append(section)
                heading_depth[section.section_id] = node.tree_depth
                heading_levels.append(level)
                result_order += 1
                continue

        raw_text = _table_markdown(node) if node_type == "table" else node.text
        text = normalize_text(raw_text)
        if not text:
            continue
        if node_index in toc_indexes:
            if node_index in toc_warnings:
                structure_warnings.append(toc_warnings[node_index])
            continue
        if node_type in TEXT_BLOCK_TYPES and _is_non_linguistic(text):
            excerpt = text[:80].replace("\n", " ")
            structure_warnings.append(
                f"non_linguistic_block: {len(text)} chars: {excerpt}"
            )
            continue
        owner = stack[-1]
        owner.has_direct_content = True
        parts = (
            _table_parts(text, max_table_tokens, counter)
            if node_type == "table"
            else [(text, None)]
        )
        for part, oversize_reason in parts:
            if full_parts:
                full_parts.append("\n")
                full_length += 1
            block_start = full_length
            full_parts.append(part)
            full_length += len(part)
            queue(
                _LeafBlock(
                    node=node,
                    block_type=node_type,
                    text=part,
                    char_start=block_start,
                    char_end=full_length,
                    owner=owner,
                    oversize_reason=oversize_reason,
                )
            )

    flush()
    if len(heading_levels) >= 4 and len(set(heading_levels)) == 1:
        structure_warnings.append(
            f"flat_heading_tree: {len(heading_levels)} headings at level {heading_levels[0]}"
        )

    return ChunkingResult(
        doc_id=doc_id,
        sections=sections,
        chunks=chunks,
        normalized_full_text="".join(full_parts),
        structure_warnings=_group_warnings(structure_warnings),
    )
