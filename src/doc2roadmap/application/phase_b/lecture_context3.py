"""`lecture-context-3`: the book passages a lecture is written from, and the user message sent with them."""
from __future__ import annotations

import unicodedata
from collections.abc import Mapping
from typing import Any

from doc2roadmap.domain.phase_b_limits import BSettings

ELIGIBLE_ROLES = ("noi_dung", "bai_tap")
MIN_NAME_CHARS = 3
PREREQUISITE_DEFINITION_CHARS = 400
FORMULA_MARK = "[formula]"


def _norm(value: Any) -> str:
    return " ".join(unicodedata.normalize("NFC", str(value)).casefold().split())


def _get(value: Any, key: str, default: Any = None) -> Any:
    return value.get(key, default) if isinstance(value, Mapping) else getattr(value, key, default)


def concept_names(node: Mapping[str, Any]) -> list[str]:
    """Normalised name and aliases of a concept; names shorter than three characters are too ambiguous to match."""
    raw = [node.get("display_name"), node.get("name")]
    raw += [alias.get("name") if isinstance(alias, Mapping) else alias for alias in node.get("aliases") or []]
    names: list[str] = []
    for value in raw:
        name = _norm(value) if value else ""
        if len(name) >= MIN_NAME_CHARS and name not in names:
            names.append(name)
    return names


def gather_chunks(graph: Any, node: Mapping[str, Any], definition_chunk_id: str | None,
                  settings: BSettings) -> list[Any]:
    """Passages in reading order, picked by priority until `lecture_context_chars` is reached."""
    chunks = sorted(graph.chunks.values(), key=lambda chunk: (_get(chunk, "order_index", 0), str(_get(chunk, "chunk_id"))))
    position = {str(_get(chunk, "chunk_id")): index for index, chunk in enumerate(chunks)}
    names = concept_names(node)

    def eligible(index: int) -> bool:
        return 0 <= index < len(chunks) and _get(chunks[index], "role") in ELIGIBLE_ROLES

    def chapter(index: int) -> str:
        return (_get(chunks[index], "section_path") or [""])[0]

    def neighbour(index: int, step: int) -> int | None:
        other = index + step
        return other if eligible(other) and chapter(other) == chapter(index) else None

    text = {index: _norm(_get(chunk, "text", "")) for index, chunk in enumerate(chunks) if eligible(index)}
    hits = {index: sum(value.count(name) for name in names) for index, value in text.items()}
    heading = {index for index in text
               if any(name in _norm(" ".join(_get(chunks[index], "section_path") or [])) for name in names)}

    anchor = position.get(str(definition_chunk_id)) if definition_chunk_id else None
    if anchor is None or not eligible(anchor):
        anchor = next((index for index in sorted(text) if hits[index]), None)

    order: list[int] = []

    def add(index: int | None) -> None:
        if index is not None and index not in order:
            order.append(index)

    if anchor is not None:
        add(anchor)
        add(neighbour(anchor, 1))
    for index in sorted(heading, key=lambda value: (-hits[value], value)):
        add(index)
        add(neighbour(index, 1))
    for index in sorted((value for value in text if hits[value]), key=lambda value: (-hits[value], value)):
        add(index)
    if anchor is not None:
        for step in (-1, 2, 3):
            add(neighbour(anchor, step))

    picked: list[int] = []
    total = 0
    for index in order:
        size = len(str(_get(chunks[index], "text", "")).strip())
        if picked and total + size > settings.lecture_context_chars:
            break
        picked.append(index)
        total += size
    return [chunks[index] for index in sorted(picked)]


def formula_pages(chunks: list[Any], limit: int | None = None) -> list[int]:
    """Pages of the passages that lost a formula to PDF extraction, in reading order, at most `limit` (all if None)."""
    pages: list[int] = []
    for chunk in chunks:
        page = _get(chunk, "page")
        if FORMULA_MARK in str(_get(chunk, "text", "")) and page and page not in pages:
            pages.append(int(page))
    return pages if limit is None else pages[:limit]


def formula_raw_texts(graph: Any) -> dict[str, str]:
    """formula_id -> the PDF text layer of that formula, whitespace collapsed; formulas without text are left out."""
    tree = getattr(graph, "tree", None)
    cached = getattr(graph, "_formula_raw_texts", None)
    if cached and cached[0] is tree:
        return cached[1]
    rows = {}
    for node in getattr(tree, "nodes", None) or []:
        formula_id, raw = getattr(node, "formula_id", None), " ".join(str(getattr(node, "raw_text", None) or "").split())
        if formula_id and raw:
            rows[formula_id] = raw
    try:
        graph._formula_raw_texts = (tree, rows)
    except AttributeError:
        pass
    return rows


def formula_text(chunk: Any, raw_texts: Mapping[str, str], text: str | None = None) -> str:
    """Chunk text with each `[formula]` turned into `[formula: <raw text>]`, in the order of the chunk's `formula_refs`.

    A mark with no ref, or whose formula has no raw text, stays `[formula]`. Only the text sent to the model changes.
    """
    text = str(_get(chunk, "text", "")) if text is None else text
    refs = list(_get(chunk, "formula_refs") or [])
    if not refs or not raw_texts:
        return text
    pieces = text.split(FORMULA_MARK)
    out = [pieces[0]]
    for number, piece in enumerate(pieces[1:]):
        raw = raw_texts.get(_get(refs[number], "formula_id")) if number < len(refs) else None
        out += [f"[formula: {raw}]" if raw else FORMULA_MARK, piece]
    return "".join(out)


def source_rows(chunks: list[Any]) -> list[dict[str, Any]]:
    return [{"label": f"S{number}", "chunk_id": _get(chunk, "chunk_id"), "page": _get(chunk, "page"),
             "section_path": list(_get(chunk, "section_path") or [])}
            for number, chunk in enumerate(chunks, 1)]


def source_texts(chunks: list[Any]) -> dict[str, str]:
    return {f"S{number}": str(_get(chunk, "text", "")) for number, chunk in enumerate(chunks, 1)}


def user_message(node: Mapping[str, Any], module: Mapping[str, Any], chunks: list[Any],
                 prerequisites: list[Mapping[str, Any]], next_up: list[str],
                 raw_texts: Mapping[str, str] | None = None) -> str:
    aliases = [alias.get("name") if isinstance(alias, Mapping) else str(alias) for alias in node.get("aliases") or []]
    aliases = [alias for alias in aliases if alias]
    index = module.get("index")
    lines = [f"Khái niệm: {node.get('display_name') or node.get('name')}"
             + (f" (còn gọi: {', '.join(aliases)})" if aliases else ""),
             f"Thuộc module {index + 1 if isinstance(index, int) else '?'}: "
             f"{module.get('display_name') or module.get('title') or ''}", ""]
    if prerequisites:
        lines.append("Khái niệm tiên quyết:")
        lines += [f"- {row['name']} (module {row['module_number']}): {row['definition']}" for row in prerequisites]
        lines.append("")
    if next_up:
        lines += ["Khái niệm tiếp theo dùng tới khái niệm này: " + ", ".join(next_up), ""]
    lines.append("Tư liệu từ sách:")
    for number, chunk in enumerate(chunks, 1):
        section = " > ".join(_get(chunk, "section_path") or [])
        lines += [f"[S{number}] (trang {_get(chunk, 'page')}, mục {section})",
                  formula_text(chunk, raw_texts or {}).strip(), ""]
    return "\n".join(lines)


def prerequisite_rows(skeleton: Mapping[str, Any], context: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Name, module number and a definition cut to 400 characters for each prerequisite."""
    rows = []
    for item in skeleton.get("prerequisites", []):
        recall = item.get("recall") or {}
        definition = str((recall.get("definition") or {}).get("quote") or "")
        if not definition:
            source = context["sources"].get(next((row.get("N") for row in context.get("prerequisites", [])
                                                  if row.get("node_id") == recall.get("node_id")), None) or "", {})
            definition = str(source.get("text") or "")
        index = recall.get("module_index")
        rows.append({"name": recall.get("name"), "module_number": index + 1 if isinstance(index, int) else "?",
                     "definition": definition[:PREREQUISITE_DEFINITION_CHARS]})
    return rows
