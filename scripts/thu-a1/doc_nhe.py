"""Bộ đọc PDF nhẹ thay docling (thí nghiệm, vé v4-10 bước 2): pypdfium2 cộng luật, không mô hình học. 0 USD, tại máy.

Câu hỏi: với PDF sạch có lớp chữ, một bộ đọc chỉ dùng lớp chữ (font, cỡ, vị trí) có cho cây tài liệu đủ gần docling mà nhanh hơn nhiều không?
Bộ đọc v0 làm theo thứ tự:
- **Ký tự:** đọc từng ký tự của lớp chữ: mã, hộp lỏng (chiều cao hộp thay cho cỡ chữ, vì có PDF ghi cỡ 1 và phóng bằng ma trận),
  tên font, độ đậm.
- **Dòng:** theo ngắt dòng của pdfium.
- **Đầu trang, chân trang:** dòng ở 8% trên hoặc dưới của trang, chuỗi chuẩn hoá (số thay bằng #) lặp ở ít nhất 3 trang, hoặc chỉ là số
  trang, thì bỏ.
- **Loại dòng:**
  - công thức: ít nhất 40% ký tự thuộc font toán (CM* của LaTeX, Symbol, Euclid, MT Extra…), hoặc gần như toàn ký hiệu;
  - tiêu đề: (mẫu đánh số tiếng Việt và chữ đậm hoặc to hơn thân bài) hoặc (to hơn thân bài 20% và ngắn);
  - mục danh sách: ký hiệu đầu dòng hoặc a), 1), (i);
  - chú thích hình/bảng: "Hình …", "Bảng …";
  - chú thích cuối trang: chữ nhỏ ở đáy trang;
  - còn lại là văn bản.
- **Gom khối:** dòng văn bản liền nhau thành đoạn (ngắt khi cách dòng lớn, thụt đầu dòng sau câu kết thúc, đổi cỡ chữ); dòng công thức liền
  nhau thành một công thức; dòng tiếp nối của mục danh sách nhập vào mục.
- **Hình:** đối tượng ảnh phủ từ 3% trang.
- Chưa nhận bảng (v0): bảng ra thành dòng chữ.
Đầu ra là danh sách nút cùng kiểu với adapter docling (`node_type`, `text`, `page`, `level`, `bbox`), để so với cây docling đã lưu.
Riêng tiếng Việt: mẫu đánh số "Chương", "Phần", "Bài", "§" — đồ án chỉ làm tiếng Việt (chủ dự án chốt 2026-10-05).
Chạy từ gốc repo:  .venv/Scripts/python.exe scripts/thu-a1/doc_nhe.py [--tai-lieu=doc-1,doc-4,xstk] [--ra=tmp/thu-a1/doc-nhe]
"""
import ctypes
import difflib
import json
import re
import sys
import time
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import pypdfium2 as pdfium
import pypdfium2.raw as raw

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
# tài liệu: (tệp PDF, cây docling của luồng dùng làm mốc)
DOCS = {"doc-1": ("doc-1.pdf", "artifacts/parse_tree/doc-1/v5/tree.json"),
        "doc-4": ("doc-4.pdf", "artifacts/parse_tree/doc-4/v2/tree.json"),
        "xstk": ("xstk-ch3-1.pdf", "artifacts/parse_tree/xstk-ch3-1/v2/tree.json")}
MATH_FONT = re.compile(r"CMMI|CMSY|CMEX|CMBSY|MSBM|MSAM|EUFM|RSFS|STMARY|WASY|Symbol|Euclid|MT ?Extra|Math|LMMath|STIX", re.I)
BOLD_FONT = re.compile(r"bold|black|heavy|semibold|demi|[-,+](bd|b)\b|VNBX|BX\d|CMBX", re.I)
BULLET = "•●◦▪■□♦◆✓✔➢►‣⁃∙·-–—+*"
LIST_START = re.compile(r"^\s*(?:[" + re.escape(BULLET) + r"\uf000-\uf0ff]\s+|\(?[a-zđ]\)\s+|\(?[ivx]{1,4}\)\s+|\d{1,2}\)\s+)")
HEADING_NUMBER = re.compile(r"^\s*(?:(?:chương|phần|bài|mục|chapter|part)\s+[\divxlc]+\b|§\s*\d+|\d{1,2}(?:\.\d{1,2}){0,3}\.?\s+\S|"
                            r"[IVXLC]{1,5}\s*[-–.]\s*\S|[A-ZĐ]\.\s+\S)", re.I)
ENUMERATOR = re.compile(r"^\s*\(?(?:[a-zđ]|[ivx]{1,4}|\d{1,2})\)\s+\S")
TABLE_ROW_END = re.compile(r"\d+(?:[.,]\d+)?(?:\s+\d+(?:[.,]\d+)?){1,}\s*$")
PRIVATE_USE = re.compile(r"[\ue000-\uf8ff]")
# Dấu đầu dòng của font Symbol/Wingdings mà PDF ghi vào vùng ký tự riêng (U+F0B7 "•", U+F0A7 "§", U+F076 "v", U+F0D8, U+F0FC…).
PUA_BULLET = re.compile(r"^\s*[\uf000-\uf0ff]\s+")
STRONG_MATH = set("=+−×÷∑∫∏√≤≥≠≈∈∉⊂⊆∪∩→⇒⇔∀∃∞∂∇±^")
CHAPTER_LABEL = re.compile(r"(?:chương|phần|chapter|part)\s+[\divxlc]+\.?", re.I)
CAPTION = re.compile(r"^\s*(hình|bảng|sơ đồ|biểu đồ|figure|table)\s+\d", re.I)
SYMBOLS = set("=+−-×÷∑∫∏√≤≥≠≈∈∉⊂⊆⊃∪∩→←⇒⇔↔∀∃∞∂∇±·°()[]{}|,.^_/<>′'αβγδεζηθλμνξπρστφχψωΓΔΘΛΞΠΣΦΨΩ")


class Char:
    __slots__ = ("ch", "left", "bottom", "right", "top", "font", "weight")

    def __init__(self, ch, left, bottom, right, top, font, weight):
        self.ch, self.left, self.bottom, self.right, self.top, self.font, self.weight = ch, left, bottom, right, top, font, weight


def page_lines(page):
    """Dòng của một trang: danh sách ký tự theo thứ tự của pdfium, cắt ở ngắt dòng pdfium sinh ra."""
    textpage = page.get_textpage()
    buffer, flags, rect = ctypes.create_string_buffer(256), ctypes.c_int(), raw.FS_RECTF()
    lines, current = [], []
    for index in range(textpage.count_chars()):
        code = raw.FPDFText_GetUnicode(textpage.raw, index)
        if code in (10, 13):
            if current:
                lines.append(current)
                current = []
            continue
        raw.FPDFText_GetLooseCharBox(textpage.raw, index, ctypes.byref(rect))
        raw.FPDFText_GetFontInfo(textpage.raw, index, buffer, 256, ctypes.byref(flags))
        char = Char(chr(code) if code else "", rect.left, rect.bottom, rect.right, rect.top, buffer.value.decode("utf-8", "replace"),
                    raw.FPDFText_GetFontWeight(textpage.raw, index))
        if current and char.ch.strip() and current[-1].ch.strip() and char.left < current[-1].left - 2 and \
                abs(char.bottom - current[-1].bottom) > 0.6 * max(current[-1].top - current[-1].bottom, 1):
            lines.append(current)  # pdfium quên ngắt dòng: x lùi và đổi đường chân chữ
            current = []
        current.append(char)
    if current:
        lines.append(current)
    return lines


def describe(chars, page_no, height):
    visible = [c for c in chars if c.ch.strip()]
    if not visible:
        return None
    text = re.sub(r"\s+", " ", "".join(c.ch for c in chars)).strip()
    sizes = sorted(round(c.top - c.bottom, 1) for c in visible)
    non_bullet = [c for c in visible if c.ch not in BULLET]
    math = sum(bool(MATH_FONT.search(c.font)) for c in non_bullet) / max(len(non_bullet), 1)
    letters = sum(c.ch.isalpha() and c.ch not in SYMBOLS and not PRIVATE_USE.match(c.ch) for c in visible)
    text_letters = sum(c.ch.isalpha() and not MATH_FONT.search(c.font) and not PRIVATE_USE.match(c.ch) for c in visible)
    return {"page": page_no, "text": text, "x0": min(c.left for c in visible), "x1": max(c.right for c in visible),
            "letters": letters, "text_letters": text_letters,
            "top": max(c.top for c in visible), "bottom": min(c.bottom for c in visible), "size": sizes[len(sizes) // 2],
            "bold": sum(c.weight >= 600 or bool(BOLD_FONT.search(c.font)) for c in visible) / len(visible) >= 0.6,
            "math": math, "symbol_share": 1 - letters / len(visible), "height": height,
            "chars": len(visible)}


def norm_repeat(text):
    return re.sub(r"\d+", "#", " ".join(unicodedata.normalize("NFC", text).casefold().split()))


def parse(path):
    pdf = pdfium.PdfDocument(path)
    rows, figures = [], []
    for page_index in range(len(pdf)):
        page = pdf[page_index]
        width, height = page.get_size()
        for chars in page_lines(page):
            row = describe(chars, page_index + 1, height)
            if row:
                rows.append(row)
        for obj in page.get_objects(max_depth=2):
            if obj.type == raw.FPDF_PAGEOBJ_IMAGE:
                left, bottom, right, top = obj.get_bounds()
                if (right - left) * (top - bottom) >= 0.03 * width * height:
                    figures.append({"page": page_index + 1, "top": top, "bbox": (left, bottom, right, top)})
    pages = len(pdf)
    # Đầu trang, chân trang: chuỗi lặp ở vùng 8% trên/dưới, hoặc chỉ là số trang.
    zone = lambda r: r["top"] > 0.92 * r["height"] or r["bottom"] < 0.08 * r["height"]  # noqa: E731
    seen = defaultdict(set)
    for r in rows:
        if zone(r):
            seen[norm_repeat(r["text"])].add(r["page"])
    repeated = {key for key, value in seen.items() if len(value) >= 3}
    body_rows = [r for r in rows if not (zone(r) and (norm_repeat(r["text"]) in repeated or re.fullmatch(r"[\W\d#ivxlcIVXLC]{1,8}", r["text"])))]
    weights = Counter()
    for r in body_rows:
        weights[r["size"]] += r["chars"]
    body = weights.most_common(1)[0][0] if weights else 10.0

    def kind(r, standalone):
        words = len(r["text"].split())
        mathy = r["math"] >= 0.5 or any(ch in STRONG_MATH or PRIVATE_USE.match(ch) for ch in r["text"] if not PUA_BULLET.match(ch + " "))
        if r["letters"] == 0:
            return "formula" if mathy else "text"
        if (r["math"] >= 0.6 and r["text_letters"] <= 4) or (r["symbol_share"] >= 0.7 and words <= 12 and mathy):
            return "formula"
        bare = PUA_BULLET.sub("", LIST_START.sub("", r["text"])) if (PUA_BULLET.match(r["text"]) or LIST_START.match(r["text"])) else r["text"]
        if CAPTION.match(r["text"]) and words <= 40:
            return "caption"
        wordy = r["letters"] >= 3 and not TABLE_ROW_END.search(r["text"])
        if wordy and words <= 20 and HEADING_NUMBER.match(r["text"]) and (r["bold"] or r["size"] >= 1.1 * body) \
                and not r["text"].endswith(","):
            return "section_header"
        if wordy and words <= 15 and ENUMERATOR.match(r["text"]) and r["bold"]:
            return "section_header"
        if wordy and words <= 15 and r["size"] >= 1.2 * body and not r["text"].endswith((".", ",", ";")):
            return "section_header"
        if wordy and words <= 15 and r["bold"] and bare != r["text"] and bare[:1].isupper() and not r["text"].endswith((",", ";", ".")):
            return "section_header"  # tiêu đề in đậm mở đầu bằng dấu đầu dòng (xstk: "• Mẫu tổng quát và mẫu cụ thể")
        if wordy and standalone and words <= 12 and r["bold"] and r["size"] >= 0.98 * body and bare[:1].isupper() \
                and not r["text"].endswith((",", ";")):
            return "section_header"
        if LIST_START.match(r["text"]):
            return "list_item"
        if r["bottom"] < 0.15 * r["height"] and r["size"] < 0.85 * body:
            return "footnote"
        return "text"

    margins = {}
    for page in {r["page"] for r in body_rows}:
        lefts = sorted(r["x0"] for r in body_rows if r["page"] == page and r["letters"] >= 3)
        rights = sorted(r["x1"] for r in body_rows if r["page"] == page and r["letters"] >= 3)
        margins[page] = (lefts[len(lefts) // 5] if lefts else 0.0, rights[-(len(rights) // 5) - 1] if rights else 0.0)
    nodes = []
    previous = None
    for r in body_rows:
        gap = (previous["bottom"] - r["top"]) if previous and previous["page"] == r["page"] else None
        line_height = max(r["size"], 1.0)
        standalone = gap is None or gap > 0.5 * line_height or previous["text"].endswith((".", ":", "?", "!"))
        current = kind(r, standalone)
        joinable = previous is not None and nodes and previous["page"] == r["page"] and gap is not None and -line_height < gap < 1.2 * line_height
        last = nodes[-1] if nodes else None
        left, right = margins[r["page"]]
        ended = last is not None and last["text"].endswith((".", ":", "?", "!"))
        new_paragraph = ended and (r["x0"] > left + 0.8 * line_height or (previous is not None and previous["x1"] < right - 3 * line_height))
        if joinable and current == "text" and last["node_type"] in {"text", "list_item", "footnote"} and \
                abs(r["size"] - previous["size"]) <= 0.15 * line_height and not new_paragraph:
            last["text"] += " " + r["text"]
        elif current == "formula" and last is not None and last["node_type"] == "formula" and last["page"] == r["page"] \
                and gap is not None and -line_height < gap < 2.5 * line_height:
            last["text"] += " " + r["text"]
        elif joinable and current == "section_header" and last["node_type"] == "section_header" and not HEADING_NUMBER.match(r["text"]) \
                and not CHAPTER_LABEL.fullmatch(last["text"].strip()):
            last["text"] += " " + r["text"]  # tiêu đề dài xuống dòng; dòng nhãn chương ("Chương I") thì để riêng như docling
        else:
            nodes.append({"node_type": current, "text": r["text"], "page": r["page"], "x0": r["x0"],
                          "level": heading_level(r["text"]) if current == "section_header" else None})
        previous = r
    for figure in figures:
        nodes.append({"node_type": "figure", "text": "", "page": figure["page"], "x0": figure["bbox"][0], "level": None})
    from doc2roadmap.infrastructure.parsing.docling_parser import DoclingParser
    for node in nodes:  # cùng bước làm sạch chữ của adapter dự án (ánh xạ ký tự Symbol vùng riêng, gộp glyph PDF)
        node["text"], _ = DoclingParser._clean_text(node["text"], collapse_pdf_glyphs=True)
    return nodes, {"pages": pages, "body_size": body, "repeated_lines_removed": len(rows) - len(body_rows)}


def heading_level(text):
    text = text.strip()
    if re.match(r"^(chương|phần|chapter|part)\b", text, re.I):
        return 1
    match = re.match(r"^(\d{1,2}(?:\.\d{1,2}){0,3})", text)
    if match:
        return min(4, match.group(1).count(".") + 2)
    return 2


def words(text):
    """Tách chuỗi chữ và chuỗi số riêng ("x1" thành "x", "1"), vì hai bộ đọc đặt khoảng trắng quanh chỉ số khác nhau."""
    return re.findall(r"[^\W\d_]+|\d+", unicodedata.normalize("NFC", text).casefold())


def compare(nodes, reference):
    """So với cây docling: phủ từ (túi từ), thứ tự (theo trang), tiêu đề, công thức, số nút theo loại."""
    ref_nodes = reference["nodes"]
    def content(node):
        if node.get("node_type") == "formula":
            return node.get("raw_text") or ""
        if node.get("node_type") == "table":
            return " ".join(" ".join(row) for row in (node.get("table_rows") or []))
        return node.get("text") or ""
    ref_words, light_words = Counter(), Counter()
    ref_pages, light_pages = defaultdict(list), defaultdict(list)
    for node in ref_nodes:
        found = words(content(node))
        ref_words.update(found)
        if node.get("page") is not None:
            ref_pages[int(node["page"])].extend(found)
    for node in nodes:
        found = words(node["text"])
        light_words.update(found)
        light_pages[node["page"]].extend(found)
    common = sum((ref_words & light_words).values())
    ratios = []
    for page in sorted(set(ref_pages) | set(light_pages)):
        a, b = ref_pages.get(page, []), light_pages.get(page, [])
        if a or b:
            ratios.append((len(a) + len(b), difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()))
    def heading_key(text):
        return " ".join(words(text))
    ref_headings = [heading_key(n["text"]) for n in ref_nodes if n.get("node_type") in {"section_header", "title"}]
    light_headings = [heading_key(n["text"]) for n in nodes if n["node_type"] == "section_header"]
    def matched(source, target):
        """Khớp khi giống ít nhất 0,85, hoặc chuỗi này nằm trọn trong chuỗi kia (một bên gộp "Chương I" với tên chương, bên kia tách)."""
        hits = 0
        for value in source:
            if value and any(value in other or (other and other in value)
                             or difflib.SequenceMatcher(None, value, other).ratio() >= 0.85 for other in target):
                hits += 1
        return hits
    ref_formula = Counter(w for n in ref_nodes if n.get("node_type") == "formula" for w in words(n.get("raw_text") or ""))
    light_formula = Counter(w for n in nodes if n["node_type"] == "formula" for w in words(n["text"]))
    return {
        "nut_docling": dict(Counter(n.get("node_type") for n in ref_nodes).most_common()),
        "nut_nhe": dict(Counter(n["node_type"] for n in nodes).most_common()),
        "phu_tu_R": round(common / max(sum(ref_words.values()), 1), 3),
        "phu_tu_P": round(common / max(sum(light_words.values()), 1), 3),
        "thu_tu_theo_trang": round(sum(w * r for w, r in ratios) / max(sum(w for w, _ in ratios), 1), 3),
        "tieu_de_R": round(matched(ref_headings, light_headings) / max(len(ref_headings), 1), 3),
        "tieu_de_P": round(matched(light_headings, ref_headings) / max(len(light_headings), 1), 3),
        "so_tieu_de": [len(ref_headings), len(light_headings)],
        "cong_thuc_phu_tu": round(sum((ref_formula & light_formula).values()) / max(sum(ref_formula.values()), 1), 3),
    }


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    options = dict(arg[2:].split("=", 1) for arg in sys.argv[1:] if arg.startswith("--") and "=" in arg)
    out = Path(options.get("ra", "tmp/thu-a1/doc-nhe"))
    out.mkdir(parents=True, exist_ok=True)
    report = {}
    for key in options.get("tai-lieu", "doc-1,doc-4,xstk").split(","):
        pdf, tree = DOCS[key]
        began = time.perf_counter()
        nodes, stats = parse(ROOT / pdf)
        seconds = time.perf_counter() - began
        reference = json.loads((ROOT / tree).read_text(encoding="utf-8"))
        result = {"giay": round(seconds, 2), "giay_moi_trang": round(seconds / stats["pages"], 4), **stats, **compare(nodes, reference)}
        report[key] = result
        (out / f"{key}-nut.json").write_text(json.dumps(nodes, ensure_ascii=False, indent=0), encoding="utf-8")
        print(json.dumps({key: result}, ensure_ascii=False), flush=True)
    (out / "so-sanh.json").write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
