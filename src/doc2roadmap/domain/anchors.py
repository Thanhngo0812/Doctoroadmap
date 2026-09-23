from __future__ import annotations

import re
import unicodedata

from .provenance import DEFAULT_DEFINITION_SIGNALS

# Neo định nghĩa (spec v2, W11–W12): mỗi khái niệm có một câu nguyên văn nơi tài liệu dạy nó; trạng thái là thuộc tính
# của khái niệm, quyết trên mọi ứng viên cùng lúc — khắc phục lỗi gộp theo từng đoạn của C8 v2.
STATUSES = ("defined_here", "introduced_by_example", "mentioned_only", "prior_knowledge", "not_subject_matter",
            "uncertain")
ANCHORED = {"defined_here", "introduced_by_example"}
TO_TEACHING = {"defined_here": "taught", "introduced_by_example": "taught", "mentioned_only": "mentioned_only",
               "prior_knowledge": "prior_knowledge", "not_subject_matter": "not_subject_matter", "uncertain": "uncertain"}
# `prior_knowledge` chỉ hợp lệ khi câu trích tự nói người đọc phải biết trước. v2 kích nhầm bởi giả thiết định lý
# ("Suppose V is a complex inner product space") — dùng một khái niệm không có nghĩa là đòi biết trước nó.
PRIOR_SIGNALS = ("recall", "previous course", "familiar", "prerequisite", "assume the reader", "you should know",
                 "đã học", "đã biết", "nhắc lại", "kiến thức cần có", "yêu cầu kiến thức", "cần biết trước")
_SENTENCE = re.compile(r"\S.*?(?:[.!?](?=\s|$)|$)", re.S)


def _norm(text):
    return " ".join(unicodedata.normalize("NFC", str(text)).casefold().split())


def _compact(text):
    # NFKC gộp chữ nghiêng toán học về chữ thường (𝑉 → V); bỏ khoảng trắng vì PDF toán hay chèn khoảng lạc (𝑉 𝑚).
    return "".join(unicodedata.normalize("NFKC", str(text)).casefold().split())


def _sentences(text):
    return [(match.start(), match.group(0).strip()) for match in _SENTENCE.finditer(text) if match.group(0).strip()]


def _names(node):
    values = {node["name"], *(alias["name"] if isinstance(alias, dict) else alias for alias in node.get("aliases", []))}
    return {_compact(value) for value in values if len(_compact(value)) >= 2}


def candidate_sentences(node, chunks, *, limit=6):
    """Câu nhắc tên hoặc alias của khái niệm, hoặc chứa căn cứ A3 của nó; câu có tín hiệu định nghĩa hay căn cứ A3 đứng
    trước, rồi theo vị trí trong tài liệu.

    Câu căn cứ A3 luôn là ứng viên: tên do mô hình đặt ("Hàng hoặc cột tỷ lệ") thường không có nguyên văn trong sách,
    còn căn cứ thì đã được kiểm là có. Ưu tiên mỗi chunk một câu trước khi lấy câu thứ hai của cùng chunk.
    """
    names = _names(node)
    signals = tuple(_norm(signal) for signal in DEFAULT_DEFINITION_SIGNALS)
    # Khớp theo câu trích chứ không theo offset: offset căn cứ tính trên toàn văn bản, không trên chunk.
    evidence = {}
    for span in node.get("evidence", []):
        if isinstance(span, dict) and "chunk_id" in span and _compact(span.get("quote", "")):
            evidence.setdefault(span["chunk_id"], []).append(_compact(span["quote"]))
    found = []
    for chunk in sorted(chunks, key=lambda value: (value.order_index, value.chunk_id)):
        sentences = _sentences(chunk.text)
        for index, (start, sentence) in enumerate(sentences):
            flat = _norm(sentence)
            compact = _compact(sentence)
            # Câu chứa đầu câu trích, hoặc nằm trọn trong câu trích dài nhiều câu.
            cited = any(quote[:40] in compact or (len(compact) >= 8 and compact in quote)
                        for quote in evidence.get(chunk.chunk_id, []))
            if not cited and not any(name in compact for name in names):
                continue
            context = " ".join(text for _, text in sentences[max(0, index - 1): index + 2])
            found.append({"chunk_id": chunk.chunk_id, "order_index": chunk.order_index, "char_start": start,
                          "sentence": sentence, "context": context,
                          "signal": cited or any(signal in flat for signal in signals)})
    seen, ranked = set(), []
    for row in sorted(found, key=lambda r: (not r["signal"], r["order_index"], r["char_start"])):
        ranked.append((row["chunk_id"] in seen, row))
        seen.add(row["chunk_id"])
    picked = [row for _, row in sorted(ranked, key=lambda pair: pair[0])][:limit]
    picked.sort(key=lambda r: (not r["signal"], r["order_index"], r["char_start"]))
    return [{"cand_id": f"k{index}", **{k: v for k, v in row.items() if k != "signal"}}
            for index, row in enumerate(picked, 1)]


def validate_anchor_response(value, *, node_id, candidates):
    if not isinstance(value, dict) or value.get("node_id") != node_id:
        raise ValueError("phán quyết sai node_id")
    if value.get("status") not in STATUSES:
        raise ValueError("status ngoài sáu giá trị cho phép")
    if "confidence" in value:
        raise ValueError("mô hình không được trả confidence")
    if not isinstance(value.get("reason"), str) or not value["reason"].strip():
        raise ValueError("phán quyết thiếu reason")
    status = value["status"]
    by_id = {candidate["cand_id"]: candidate for candidate in candidates}
    if status in ANCHORED and not value.get("anchor"):
        raise ValueError(f"status {status} cần anchor")
    if value.get("anchor") is not None and value["anchor"] not in by_id:
        raise ValueError("anchor không phải mã ứng viên nào")
    if status in ANCHORED | {"prior_knowledge", "not_subject_matter"}:
        quote = value.get("quote")
        if not isinstance(quote, str) or not _norm(quote):
            raise ValueError(f"status {status} cần quote")
        scope = [by_id[value["anchor"]]] if status in ANCHORED else candidates
        if not any(_norm(quote) in _norm(candidate["context"]) for candidate in scope):
            raise ValueError("quote không có trong ứng viên")
        if status == "prior_knowledge" and not any(signal in _norm(quote) for signal in PRIOR_SIGNALS):
            raise ValueError("prior_knowledge cần câu trích có tín hiệu tường minh")


def anchor_fields(value, candidates):
    """Trường ghi lên node: trạng thái dạy, chunk dạy và vị trí dạy lấy từ câu neo; không có neo thì để trống."""
    by_id = {candidate["cand_id"]: candidate for candidate in candidates}
    anchor = by_id.get(value.get("anchor")) if value["status"] in ANCHORED else None
    return {
        "teaching_status": TO_TEACHING[value["status"]],
        "teaching_chunk_ids": [anchor["chunk_id"]] if anchor else [],
        "teaching_order_index": anchor["order_index"] if anchor else None,
        "teaching_conflict": False,
        "anchor": ({"chunk_id": anchor["chunk_id"], "char_start": anchor["char_start"], "sentence": anchor["sentence"]}
                   if anchor else None),
    }
