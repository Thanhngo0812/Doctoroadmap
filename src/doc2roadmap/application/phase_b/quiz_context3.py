"""`quiz-context-3`: the book passages a concept's quiz is written from, the prompts, and the checks on what the model returns.

Spec: doc/quiz-3-spec.md. The two prompts are the spec's text word for word.
"""
from __future__ import annotations

import hashlib
import json
import unicodedata
from dataclasses import dataclass
from typing import Any

from doc2roadmap.application.phase_b.lecture3 import FORMULA_RULE_TEXT_ONLY, FORMULA_RULE_WITH_IMAGES
from doc2roadmap.application.phase_b.lecture_context3 import (
    formula_pages, formula_raw_texts, formula_text, gather_chunks, source_rows,
)
from doc2roadmap.domain.phase_b_limits import BSettings

GENERATION_TEMPERATURE = 1.0
SOLVER_TEMPERATURE = 0.0
MAX_SIBLINGS = 12
OPTION_COUNT = 4
BLOOMS = ("nho", "hieu", "van_dung")

SYSTEM_GENERATION = """Bạn là một giảng viên đại học giỏi, ra câu hỏi trắc nghiệm tiếng Việt để sinh viên tự kiểm tra mức hiểu một khái niệm trong cuốn sách họ đang học.

Ra đúng 3 câu cho khái niệm được nêu:
- Câu 1 kiểm tra nắm định nghĩa hay tính chất cốt lõi. Câu 2 kiểm tra hiểu: giải thích, phân biệt với khái niệm gần, nhận ra ví dụ đúng. Câu 3 kiểm tra vận dụng: một tình huống hay một bài tính ngắn.
- Mỗi câu có 4 phương án, đúng một phương án đúng. Ba phương án sai phải hợp lý với người học chưa nắm chắc: hiểu nhầm thường gặp, khái niệm gần, đảo điều kiện hay đảo chiều phát biểu. Không có phương án vô lý.
- Không để lộ đáp án qua độ dài, cách viết, hay chữ lặp lại từ câu hỏi. Không dùng "tất cả đều đúng", "không có đáp án nào".
- Câu hỏi đọc độc lập được: không viết "theo đoạn trên", "trong tài liệu", không nhắc nhãn nguồn.
- Được dùng công thức LaTeX trong $...$ ở câu hỏi và phương án. Bài tính thì chọn số đơn giản và tính lại cẩn thận.
- Lời giải thích ngắn: vì sao phương án đúng là đúng, mỗi phương án sai sai ở đâu.
- Bám sách: đáp án phải đúng theo sách; dùng đúng ký hiệu và thuật ngữ của sách; giữ đúng chiều và điều kiện của phát biểu trong sách.
- {formula_rule}"""

SYSTEM_SOLVER = """Bạn là người giải đề cẩn thận. Đọc tư liệu sách và từng câu trắc nghiệm, rồi tự giải: câu tính toán thì tự tính lại từng bước, không đoán. Chọn phương án đúng theo sách và kiến thức chuẩn. Kiểm cả các phương án còn lại: nếu có phương án khác cũng đúng (kể cả đúng trong điều kiện câu hỏi cho phép), hoặc không phương án nào đúng, đánh dấu ambiguous và nói lý do ngắn."""

GENERATION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"items": {"type": "array", "items": {"type": "object", "properties": {
        "bloom": {"type": "string", "enum": list(BLOOMS)},
        "stem": {"type": "string"},
        "options": {"type": "array", "minItems": OPTION_COUNT, "maxItems": OPTION_COUNT, "items": {
            "type": "object", "properties": {"text": {"type": "string"}, "why_wrong": {"type": "string"}},
            "required": ["text", "why_wrong"]}},
        "correct_index": {"type": "integer", "minimum": 0, "maximum": OPTION_COUNT - 1},
        "explanation": {"type": "string"},
        "source_labels": {"type": "array", "items": {"type": "string"}}},
        "required": ["bloom", "stem", "options", "correct_index", "explanation", "source_labels"]}}},
    "required": ["items"],
}
SOLVER_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"answers": {"type": "array", "items": {"type": "object", "properties": {
        "q": {"type": "integer"},
        "chosen": {"type": "integer", "minimum": 0, "maximum": OPTION_COUNT - 1},
        "ambiguous": {"type": "boolean"},
        "reason": {"type": "string"}},
        "required": ["q", "chosen", "ambiguous", "reason"]}}},
    "required": ["answers"],
}


def generation_system(with_images: bool) -> str:
    return SYSTEM_GENERATION.replace("{formula_rule}", FORMULA_RULE_WITH_IMAGES if with_images else FORMULA_RULE_TEXT_ONLY)


def _norm(value: Any) -> str:
    return " ".join(unicodedata.normalize("NFC", str(value)).casefold().split())


def _name(node: Any) -> str:
    return str(node.get("display_name") or node.get("name") or "")


@dataclass
class Material:
    user: str
    chunks: list[Any]
    sources: list[dict[str, Any]]    # label, chunk_id, page of each passage sent
    pages: list[int]                 # pages with a formula that get a picture (limit applied)
    pages_wanted: int                # every page with a formula in the material, before the limit

    def fingerprint(self) -> str:
        return hashlib.sha256(json.dumps({"user": self.user, "pages": self.pages}, ensure_ascii=False).encode()).hexdigest()


def build_material(graph: Any, concept: Any, settings: BSettings) -> Material:
    """Passages as the lecture gathers them, formulas as raw text, the other concepts of the module as distractor sources."""
    anchor = (concept.get("anchor") or {}).get("chunk_id")
    teaching = [chunk_id for chunk_id in concept.get("teaching_chunk_ids") or [] if chunk_id in graph.chunks]
    definition = anchor if anchor in graph.chunks else teaching[0] if teaching else None
    chunks = gather_chunks(graph, concept, definition, settings)
    raw_texts = formula_raw_texts(graph)
    module = graph.modules.get(concept.get("module_id"), {})
    siblings = [_name(graph.nodes[node_id]) for node_id in module.get("node_ids", [])
                if node_id != concept.get("node_id") and node_id in graph.nodes]
    lines = [f"Khái niệm: {_name(concept)}", "Các khái niệm khác cùng module: " + ", ".join(siblings[:MAX_SIBLINGS]), "",
             "Tư liệu từ sách:"]
    for number, chunk in enumerate(chunks, 1):
        section = " > ".join(getattr(chunk, "section_path", None) or [])
        lines += [f"[S{number}] (trang {getattr(chunk, 'page', None)}, mục {section})",
                  formula_text(chunk, raw_texts).strip(), ""]
    pages = formula_pages(chunks)
    sources = [{"label": row["label"], "chunk_id": row["chunk_id"], "page": row["page"]} for row in source_rows(chunks)]
    return Material("\n".join(lines), chunks, sources, pages[:settings.lecture_max_page_images], len(pages))


def build_item(concept: Any, material: Material, raw: Any) -> tuple[dict[str, Any] | None, str | None]:
    """A candidate in the shape the bank keeps, or the reason it is not well formed. Only structure is checked here."""
    if not isinstance(raw, dict):
        return None, "local.malformed"
    stem = str(raw.get("stem") or "").strip()
    if not stem:
        return None, "local.empty_stem"
    options = raw.get("options")
    if (not isinstance(options, list) or len(options) != OPTION_COUNT
            or not all(isinstance(option, dict) and str(option.get("text") or "").strip() for option in options)):
        return None, "local.option_count"
    texts = [str(option["text"]).strip() for option in options]
    if len({_norm(text) for text in texts}) != OPTION_COUNT:
        return None, "local.duplicate_options"
    correct = raw.get("correct_index")
    if type(correct) is not int or not 0 <= correct < OPTION_COUNT:
        return None, "local.correct_index"
    by_label = {row["label"]: row for row in material.sources}
    labels = [label for label in dict.fromkeys(raw.get("source_labels") or []) if label in by_label]
    evidence = [dict(by_label[label]) for label in labels]
    bloom = raw.get("bloom")
    return {
        "item_id": "qi_" + hashlib.sha256((concept["node_id"] + stem + "|".join(texts)).encode()).hexdigest()[:24],
        "concept_id": concept["node_id"], "module_id": concept.get("module_id"), "generator": "llm",
        "bloom": bloom if bloom in BLOOMS else "hieu", "stem": stem,
        "options": [{"text": text, "is_correct": index == correct,
                     "why_wrong": "" if index == correct else str(options[index].get("why_wrong") or "").strip(),
                     **({"evidence": evidence} if index == correct else {})}
                    for index, text in enumerate(texts)],
        "explanation": str(raw.get("explanation") or "").strip(), "evidence": evidence,
    }, None


def solver_message(material: Material, shown: list[dict[str, Any]]) -> str:
    """The material, then each question with its options already shuffled; nothing about the answer."""
    questions = [{"q": row["q"], "stem": row["stem"], "options": row["options"]} for row in shown]
    return (material.user + "\n\nCác câu trắc nghiệm (phương án đánh số từ 0):\n"
            + json.dumps(questions, ensure_ascii=False))


def verdicts(payload: Any, shown: list[dict[str, Any]], items: list[dict[str, Any]]) -> list[tuple[bool, str | None, str]]:
    """Per question: kept?, rejection code, and the solver's own reason. `order[k]` is the original index of shown option k."""
    answers = {}
    for answer in (payload.get("answers") if isinstance(payload, dict) else None) or []:
        if isinstance(answer, dict) and type(answer.get("q")) is int:
            answers.setdefault(answer["q"], answer)
    result = []
    for row, item in zip(shown, items):
        answer = answers.get(row["q"])
        if answer is None:
            result.append((False, "solver.missing_answer", ""))
            continue
        reason = str(answer.get("reason") or "")
        chosen = answer.get("chosen")
        if type(chosen) is not int or not 0 <= chosen < len(row["order"]):
            result.append((False, "solver.invalid_choice", reason))
        elif answer.get("ambiguous") is not False:
            result.append((False, "solver.ambiguous", reason))
        elif not item["options"][row["order"][chosen]]["is_correct"]:
            result.append((False, "solver.wrong_choice", reason))
        else:
            result.append((True, None, reason))
    return result
