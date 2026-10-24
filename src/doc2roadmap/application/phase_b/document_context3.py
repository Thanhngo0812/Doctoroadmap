"""`document-context-3`: the book passages a document is written from, the prompt, and the admin log (spec: doc/tai-lieu-3-spec.md)."""
from __future__ import annotations

import re
from dataclasses import dataclass, replace
from typing import Any

from doc2roadmap.application.phase_b.assistant_context import build_validation as answer_validation
from doc2roadmap.application.phase_b.assistant_context import module_number
from doc2roadmap.application.phase_b.lecture3 import FORMULA_RULE_TEXT_ONLY, FORMULA_RULE_WITH_IMAGES
from doc2roadmap.application.phase_b.lecture_context3 import (
    FORMULA_MARK, _get, formula_pages, formula_raw_texts, formula_text, gather_chunks, source_rows,
)
from doc2roadmap.application.phase_b.lectures import _assemble
from doc2roadmap.domain.phase_b_limits import BSettings

DEFAULT_REQUEST = "Tóm tắt các ý chính của phạm vi này để ôn tập, có ví dụ."
DEFAULT_TITLE = "Tài liệu học tập"
SYSTEM_TEMPLATE = """Bạn là một giảng viên đại học giỏi và tận tâm. Bạn soạn tài liệu học tập bằng tiếng Việt cho sinh viên đang tự học từ một cuốn sách, theo đúng yêu cầu của sinh viên.

Cách viết:
- Làm đúng thứ sinh viên yêu cầu: đề cương ôn tập, tóm tắt công thức, bảng so sánh, hướng dẫn từng bước, tổng quan… Chọn hình thức hợp nhất với yêu cầu: văn xuôi, danh sách, bảng Markdown, hay kết hợp.
- Bao quát các khái niệm trong phạm vi đã chọn, dành nhiều chỗ hơn cho những gì yêu cầu nhắc tới. Sắp theo trình tự dễ học, thường theo thứ tự module.
- Giải thích đủ để hiểu, không chỉ chép định nghĩa. Có ví dụ khi giúp hiểu: ưu tiên ví dụ trong sách; ví dụ tự nghĩ phải đúng: ví dụ số thì chọn số đơn giản, dễ tính, và soát lại từng phép tính, từng bước suy luận trước khi viết.
- Dòng đầu là một tiêu đề "# …" ngắn, nói rõ tài liệu này là gì.

Trung thực với sách:
- Sách là chuẩn. Không viết điều mâu thuẫn với sách. Dùng đúng ký hiệu và thuật ngữ của sách.
- Giữ đúng chiều và phạm vi của phát biểu trong sách: sách nói "nếu A thì B" thì đừng viết thành "nếu B thì A"; điều sách gán cho đối tượng hay vai trò nào thì giữ đúng đối tượng, vai trò đó. Khi tóm tắt thành gạch đầu dòng hay bảng cũng vậy: giữ đúng điều kiện và chiều của phát biểu.
- Viết công thức bằng LaTeX trong $...$ hoặc $$...$$.
- {formula_rule}
- Đoạn nào dựa vào sách thì gắn nhãn nguồn như [S2] ở cuối đoạn hay cuối dòng bảng. Phần giải thích hay ví dụ tự nghĩ thì không cần nhãn.
- Nếu sách nói ít về điều được hỏi, vẫn viết đầy đủ bằng hiểu biết chung, nhưng không mâu thuẫn với sách.

Định dạng: Markdown. Độ dài tuỳ yêu cầu và phạm vi, thường 600–1.500 từ. Không chào hỏi, không nói về bản thân, không nhắc tới "tư liệu" hay "đoạn trích"."""

_TITLE = re.compile(r"^#[ \t]+(.+?)[ \t#]*$", re.MULTILINE)
_GROUP = re.compile(r"\[(S\d+(?:\s*[,;]\s*S\d+)*)\]")


def system_prompt(with_images: bool) -> str:
    return SYSTEM_TEMPLATE.replace("{formula_rule}", FORMULA_RULE_WITH_IMAGES if with_images else FORMULA_RULE_TEXT_ONLY)


def title_of(markdown: str) -> str:
    found = _TITLE.search(markdown)
    return found.group(1).strip() if found and found.group(1).strip() else DEFAULT_TITLE


def split_group_labels(text: str) -> str:
    """`[S1, S2]` -> `[S1][S2]`, so one rule reads single and grouped labels."""
    return _GROUP.sub(lambda m: "".join(f"[{part.strip()}]" for part in re.split(r"[,;]", m.group(1))), text)


@dataclass
class Material:
    chunks: list[Any]
    user: str
    pages: list[int]            # pages with a formula that get a picture (limit applied)
    pages_wanted: int           # every page with a formula in the material, before the limit
    search_error: bool = False


def _ordered_nodes(graph: Any, node_ids: list[str]) -> list[str]:
    modules = list(graph.modules)

    def key(node_id: str) -> tuple[int, int]:
        module_id = graph.nodes[node_id].get("module_id")
        if module_id not in graph.modules:
            return len(modules), 0
        members = list(graph.modules[module_id].get("node_ids", []))
        return modules.index(module_id), members.index(node_id) if node_id in members else len(members)
    return sorted(dict.fromkeys(node_ids), key=key)


def gather(graph: Any, node_ids: list[str], request: str, settings: BSettings, search: Any) -> Material:
    """Per concept (module order, then order in the module) its definition first; then the passages found for the
    request; then the rest of each concept's passages, until `document_context_chars`. Shown in reading order."""
    raw_texts = formula_raw_texts(graph)
    concepts, firsts, rests = [], [], []
    for node_id in _ordered_nodes(graph, node_ids):
        node = graph.nodes[node_id]
        module = graph.modules.get(node.get("module_id"), {})
        concepts.append((node.get("display_name") or node.get("name"), module_number(module) if module else "?"))
        _, base, _ = _assemble(graph, node_id, settings)
        definition = base["definition"].get("chunk_id")
        # The per-concept limit counts what comes after the definition passage, which is always taken whole:
        # a long definition must not push out the example that follows it (see the report, "Câu hỏi").
        defined = graph.chunks.get(definition)
        room = settings.document_per_concept_chars + len(str(_get(defined, "text", "")).strip() if defined else "")
        picked = gather_chunks(graph, node, definition, replace(settings, lecture_context_chars=room))
        first = next((chunk for chunk in picked if _get(chunk, "chunk_id") == definition), picked[0] if picked else None)
        firsts += [first] if first is not None else []
        rests.append([chunk for chunk in picked if chunk is not first])
    hits, search_error = [], False
    try:
        hits = [graph.chunks[row["chunk_id"]] for row in search(request, scope="all", k=6)
                if row.get("chunk_id") in graph.chunks] if search is not None else []
    except Exception:  # noqa: BLE001 - a failed search only narrows the material
        search_error = True
    # The remaining passages go round the concepts (every concept's next passage before any concept's third), so the
    # concepts at the end of the scope are not starved by the first ones.
    rest = [rows[rank] for rank in range(max((len(rows) for rows in rests), default=0)) for rows in rests if rank < len(rows)]
    chosen: dict[str, Any] = {}
    total = 0
    for chunk in [*firsts, *hits, *rest]:
        chunk_id = str(_get(chunk, "chunk_id"))
        size = len(formula_text(chunk, raw_texts).strip())
        if chunk_id in chosen or total + size > settings.document_context_chars:
            continue
        chosen[chunk_id] = chunk
        total += size
    chunks = sorted(chosen.values(), key=lambda c: (_get(c, "order_index", 0), str(_get(c, "chunk_id"))))
    pages = formula_pages(chunks)
    module_ids = list(dict.fromkeys(graph.nodes[n].get("module_id") for n in _ordered_nodes(graph, node_ids)
                                    if graph.nodes[n].get("module_id") in graph.modules))
    scope_line = "; ".join(
        f"module {module_number(graph.modules[m])}: {graph.modules[m].get('display_name') or graph.modules[m].get('title') or ''}"
        for m in module_ids)
    lines = [f"Yêu cầu của sinh viên: {request}", "", f"Phạm vi đã chọn: {scope_line}", "",
             "Các khái niệm trong phạm vi:"]
    lines += [f"- {name} (module {number})" for name, number in concepts]
    lines += ["", "Tư liệu từ sách:"]
    for number, chunk in enumerate(chunks, 1):
        section = " > ".join(_get(chunk, "section_path") or [])
        lines += [f"[S{number}] (trang {_get(chunk, 'page')}, mục {section})", formula_text(chunk, raw_texts).strip(), ""]
    return Material(chunks, "\n".join(lines), pages[:settings.document_max_page_images], len(pages), search_error)


def build_validation(text: str, labels: list[str], *, finish_reason: str | None, images_sent: int, pages_wanted: int,
                     search_error: bool, seconds_to_first_text: float | None, seconds_total: float,
                     cost_usd: float) -> dict[str, Any]:
    """Admin log of one document. Nothing here changes or blocks the document."""
    log = answer_validation(split_group_labels(text), labels)
    return {**log, "formula_left": FORMULA_MARK[:-1] in text, "pages_with_formula": pages_wanted,
            "images_sent": images_sent, "thieu_anh_trang": images_sent < pages_wanted, "finish_reason": finish_reason,
            "search_error": search_error, "seconds_to_first_text": seconds_to_first_text,
            "seconds_total": seconds_total, "cost_usd": cost_usd}


__all__ = ["DEFAULT_REQUEST", "DEFAULT_TITLE", "Material", "build_validation", "gather", "source_rows", "split_group_labels",
           "system_prompt", "title_of"]
