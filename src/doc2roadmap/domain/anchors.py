from __future__ import annotations

import unicodedata
import re

from .sentence_splitter import UnicodeSentenceSplitter

# Neo định nghĩa (spec v2, W11–W12): mỗi khái niệm có một câu nguyên văn nơi tài liệu dạy nó; trạng thái là thuộc tính
# của khái niệm, quyết trên mọi ứng viên cùng lúc — khắc phục lỗi gộp theo từng đoạn của C8 v2.
STATUSES = ("defined_here", "introduced_by_example", "mentioned_only", "prior_knowledge", "not_subject_matter",
            "uncertain")
ANCHORED = {"defined_here", "introduced_by_example"}
TO_TEACHING = {"defined_here": "taught", "introduced_by_example": "taught", "mentioned_only": "mentioned_only",
               "prior_knowledge": "prior_knowledge", "not_subject_matter": "not_subject_matter", "uncertain": "uncertain"}


def numbered_label(text):
    match = re.fullmatch(r"(.+?)\s*(\d+(?:[.]\d+)*)(?:[.:])?", unicodedata.normalize("NFC", text).strip())
    if not match:
        return None
    prefix, number = match.group(1).strip(), match.group(2)
    words = prefix.split()
    if len(words) > 2 or not words:
        return None
    if len(words) == 1 and not any(char.isspace() for char in text[:match.start(2)]):
        # Chữ viết không cách từ: chỉ một–hai ký tự, ví dụ 定理2.
        if len(prefix) > 2:
            return None
    if not all(all(char.isalpha() or unicodedata.category(char).startswith("M") for char in word)
               for word in words):
        return None
    return _norm(prefix), number


def label_families(nodes, chunks):
    """Tiền tố có ít nhất hai số khác nhau trong tên hoặc tiêu đề cùng tài liệu."""
    numbers = {}
    titles = [node.get("name", "") for node in nodes]
    titles += [part for chunk in chunks for part in (getattr(chunk, "section_path", None) or [])]
    for title in titles:
        match = numbered_label(str(title))
        if match:
            prefix, number = match
            numbers.setdefault(prefix, set()).add(number)
    return {prefix for prefix, seen in numbers.items() if len(seen) >= 2}


def validate_display_name(value, *, node_id, label, sentence):
    if not isinstance(value, dict) or value.get("node_id") != node_id:
        raise ValueError("display_name sai node_id")
    name = value.get("display_name")
    if not isinstance(name, str) or not name.strip() or len(name) > 100:
        raise ValueError("display_name rỗng hoặc quá dài")
    prefix = (numbered_label(label) or ("",))[0]
    if _norm(name) in {_norm(label), prefix} or any(char.isdigit() for char in name):
        raise ValueError("display_name vẫn là nhãn đánh số")
    words = re.findall(r"\w+", unicodedata.normalize("NFC", name).casefold())
    source = re.findall(r"\w+", unicodedata.normalize("NFC", sentence).casefold())
    if len(words) > 10:
        raise ValueError("display_name quá dài")
    if (len(words) == 1 and len(words[0]) > 2 and " " not in sentence
            and words[0] in unicodedata.normalize("NFC", sentence).casefold()):
        return
    if not words or not all(word in source for word in words):
        raise ValueError("từ trong display_name không nằm trong câu neo")


def _norm(text):
    return " ".join(unicodedata.normalize("NFC", str(text)).casefold().split())


# Tên do mô hình viết hay mang dấu LaTeX (`𝐅^{m,n}`, `null T^k`) mà văn bản PDF không có (`𝐅 𝑚 , 𝑛`); gạch nối có nhiều
# biến thể (– — −). Bỏ dấu LaTeX và gộp gạch nối trước khi so, cả tên lẫn câu.
_LATEX_MARKUP = {ord(char): None for char in "^_{}\\"}
_DASHES = {ord(char): "-" for char in "‐‑‒–—−"}


def _compact(text):
    # NFKC gộp chữ nghiêng toán học về chữ thường (𝑉 → V); bỏ khoảng trắng vì PDF toán hay chèn khoảng lạc (𝑉 𝑚).
    folded = unicodedata.normalize("NFKC", str(text)).casefold().translate(_LATEX_MARKUP).translate(_DASHES)
    return "".join(folded.split())


def _symbolic(name):
    # Tên viết bằng ký hiệu toán: có chữ số, dấu LaTeX/phân cách, hoặc ký tự đổi khi NFKC (𝐅, 𝑇, ℒ).
    return any(char.isdigit() or char in "^_{},()" or unicodedata.normalize("NFKC", char) != char for char in name)


def symbolic_name_chunks(node, chunks, *, normalize=_compact):
    """Chunk nào nhắc tên ký hiệu của khái niệm, tìm trên toàn tài liệu sau khi bỏ khoảng trắng.

    Mention map (A6) khớp tên theo ranh giới từ nên bỏ sót `𝐅 𝑚 , 𝑛` của tên `𝐅^{m,n}`; tên chữ thường thì không cần — và
    so sau khi bỏ khoảng trắng sẽ khớp nhầm ("Addition" trong "additional").
    """
    values = [node["name"], *(alias["name"] if isinstance(alias, dict) else alias for alias in node.get("aliases", []))]
    names = {normalize(value) for value in values if _symbolic(value) and len(normalize(value)) >= 3}
    return {chunk.chunk_id for chunk in chunks if names and any(name in normalize(chunk.text) for name in names)}


def _sentences(text):
    return [(span.start, text[span.start:span.end].strip()) for span in UnicodeSentenceSplitter().split(text)]


def _names(node, normalize=_compact):
    values = {node["name"], *(alias["name"] if isinstance(alias, dict) else alias for alias in node.get("aliases", []))}
    return {normalize(value) for value in values if len(normalize(value)) >= 2}


def heading_chunks(node, chunks, *, normalize=_compact):
    """First chunk of a named section, or a chunk opening with a named block title."""
    names = _names(node, normalize)
    found, previous_path = {}, ()
    for chunk in sorted(chunks, key=lambda value: (value.order_index, value.chunk_id)):
        if getattr(chunk, "role", "noi_dung") != "noi_dung":
            continue
        path = tuple(getattr(chunk, "section_path", None) or ())
        if path != previous_path and path and any(name in normalize(path[-1]) for name in names):
            found[chunk.chunk_id] = (path[-1], 0)
        previous_path = path
        offset = 0
        for line in chunk.text.splitlines(keepends=True)[:3]:
            title = line.strip()
            offset += len(line)
            if (title and len(title) <= 140 and not title.endswith((".", "。", "!", "?", "؟"))
                    and any(name in normalize(title) for name in names)):
                found[chunk.chunk_id] = (title, offset)
                break
    return found


def candidate_sentences(node, chunks, *, limit=6, headings=None, normalize=_compact, split_sentences=_sentences):
    """Căn cứ A3, rồi khối mang tên khái niệm, rồi câu nhắc tên theo vị trí.

    Câu căn cứ A3 luôn là ứng viên: tên do mô hình đặt ("Hàng hoặc cột tỷ lệ") thường không có nguyên văn trong sách,
    còn căn cứ thì đã được kiểm là có. Ưu tiên mỗi chunk một câu trước khi lấy câu thứ hai của cùng chunk.
    """
    names = _names(node, normalize)
    headings = heading_chunks(node, chunks, normalize=normalize) if headings is None else headings
    # Khớp theo câu trích chứ không theo offset: offset căn cứ tính trên toàn văn bản, không trên chunk.
    evidence = {}
    for span in node.get("evidence", []):
        if isinstance(span, dict) and "chunk_id" in span and normalize(span.get("quote", "")):
            evidence.setdefault(span["chunk_id"], []).append(normalize(span["quote"]))
    found = []
    for chunk in sorted(chunks, key=lambda value: (value.order_index, value.chunk_id)):
        if getattr(chunk, "role", "noi_dung") != "noi_dung":
            continue
        title = headings.get(chunk.chunk_id)
        if title:
            body = split_sentences(chunk.text[title[1]:])
            if body:
                start, sentence = body[0]
                found.append({"chunk_id": chunk.chunk_id, "order_index": chunk.order_index,
                              "char_start": title[1] + start, "sentence": sentence,
                              "context": " ".join([title[0], *(text for _, text in body[:2])]), "rank": 1})
        sentences = split_sentences(chunk.text)
        for index, (start, sentence) in enumerate(sentences):
            compact = normalize(sentence)
            # Câu chứa đầu câu trích, hoặc nằm trọn trong câu trích dài nhiều câu.
            cited = any(quote[:40] in compact or (len(compact) >= 8 and compact in quote)
                        for quote in evidence.get(chunk.chunk_id, []))
            if not cited and not any(name in compact for name in names):
                continue
            context = " ".join(text for _, text in sentences[max(0, index - 1): index + 2])
            found.append({"chunk_id": chunk.chunk_id, "order_index": chunk.order_index, "char_start": start,
                          "sentence": sentence, "context": context,
                          "rank": 0 if cited else 2})
    seen, ranked = set(), []
    for row in sorted(found, key=lambda r: (r["rank"], r["order_index"], r["char_start"])):
        ranked.append((row["chunk_id"] in seen, row))
        seen.add(row["chunk_id"])
    picked = [row for _, row in sorted(ranked, key=lambda pair: pair[0])][:limit]
    if limit and not any(row["rank"] == 1 for row in picked):
        first_heading = next((row for row in found if row["rank"] == 1), None)
        if first_heading is not None:
            picked[-1:] = [first_heading]
    picked.sort(key=lambda r: (r["rank"], r["order_index"], r["char_start"]))
    return [{"cand_id": f"k{index}", **{k: v for k, v in row.items() if k != "rank"}}
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
