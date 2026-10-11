"""Frozen PDFium row extraction and R2 classification primitives."""
import ctypes
import re
import unicodedata
from collections import Counter, defaultdict

import pypdfium2 as pdfium
import pypdfium2.raw as raw

MATH_FONT = re.compile(r"CMMI|CMSY|CMEX|CMBSY|MSBM|MSAM|EUFM|RSFS|STMARY|WASY|Symbol|Euclid|MT ?Extra|Math|LMMath|STIX", re.I)
BOLD_FONT = re.compile(r"bold|black|heavy|semibold|demi|[-,+](bd|b)\b|VNBX|BX\d|CMBX", re.I)
ITALIC_FONT = re.compile(r"italic|oblique|slant|CMTI|CMSL", re.I)
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
# Riêng tiếng Việt (đồ án chỉ làm tiếng Việt): âm tiết có dấu, dùng để tách tiêu đề với công thức Word và dòng mã lệnh.
VIET_LETTER = re.compile(r"[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]")
MATH_WORDS = {"sin", "cos", "tan", "tg", "cot", "cotg", "lim", "log", "ln", "lg", "exp", "max", "min", "dx", "dy", "dz", "dt",
              "arcsin", "arccos", "arctg", "arctan", "det", "rank", "sup", "inf", "mod"}
MONO_FONT = re.compile(r"courier|consola|mono|lucida console|menlo", re.I)
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
    textpage.close()
    for line in lines:
        # Keep PDFium's line segmentation and geometry; only repair UTF-16 text.
        for index, char in enumerate(line):
            if char.ch and 0xD800 <= ord(char.ch) <= 0xDBFF:
                following = line[index + 1] if index + 1 < len(line) else None
                if following and following.ch and 0xDC00 <= ord(following.ch) <= 0xDFFF:
                    char.ch = chr(0x10000 + ((ord(char.ch) - 0xD800) << 10) + ord(following.ch) - 0xDC00)
                    following.ch = ''
                else:
                    char.ch = '\ufffd'
            elif char.ch and 0xDC00 <= ord(char.ch) <= 0xDFFF:
                char.ch = '\ufffd'
    return lines


def describe(chars, page_no, height, width=None):
    visible = [c for c in chars if c.ch.strip()]
    if not visible:
        return None
    text = re.sub(r"\s+", " ", "".join(c.ch for c in chars)).strip()
    sizes = sorted(round(c.top - c.bottom, 1) for c in visible)
    non_bullet = [c for c in visible if c.ch not in BULLET]
    math = sum(bool(MATH_FONT.search(c.font)) for c in non_bullet) / max(len(non_bullet), 1)
    letters = sum(c.ch.isalpha() and c.ch not in SYMBOLS and not PRIVATE_USE.match(c.ch) for c in visible)
    text_letters = sum(c.ch.isalpha() and not MATH_FONT.search(c.font) and not PRIVATE_USE.match(c.ch) for c in visible)
    tokens = re.findall(r"[^\W\d_]+", text)
    return {"page": page_no, "text": text, "x0": min(c.left for c in visible), "x1": max(c.right for c in visible),
            "letters": letters, "text_letters": text_letters, "tokens": len(tokens),
            "viet": sum(bool(VIET_LETTER.search(token.lower())) for token in tokens),
            "single": sum(len(token) == 1 for token in tokens) / max(len(tokens), 1),
            "math_words": sum(token.lower() in MATH_WORDS for token in tokens),
            "mono": sum(bool(MONO_FONT.search(c.font)) for c in visible) / len(visible),
            "top": max(c.top for c in visible), "bottom": min(c.bottom for c in visible), "size": sizes[len(sizes) // 2],
            "bold": sum(c.weight >= 600 or bool(BOLD_FONT.search(c.font)) for c in visible) / len(visible) >= 0.6,
            "math": math, "symbol_share": 1 - letters / len(visible), "height": height,
            "chars": len(visible), "width": width,
            "italic": sum(bool(ITALIC_FONT.search(c.font)) for c in visible) / len(visible),
            "font": Counter(c.font for c in visible).most_common(1)[0][0],
            "weight": sorted(c.weight for c in visible)[len(visible) // 2],
            "font_bold": sum(bool(BOLD_FONT.search(c.font)) for c in visible) / len(visible)}


def norm_repeat(text):
    return re.sub(r"\d+", "#", " ".join(unicodedata.normalize("NFC", text).casefold().split()))


def extract_rows(path):
    """Đọc dòng thô một lần; các trường bố cục thêm chỉ dành cho thí nghiệm v4-14."""
    pdf = pdfium.PdfDocument(path)
    rows, figures = [], []
    for page_index in range(len(pdf)):
        page = pdf[page_index]
        width, height = page.get_size()
        for chars in page_lines(page):
            row = describe(chars, page_index + 1, height, width)
            if row:
                rows.append(row)
        for obj in page.get_objects(max_depth=2):
            if obj.type == raw.FPDF_PAGEOBJ_IMAGE:
                left, bottom, right, top = obj.get_bounds()
                if (right - left) * (top - bottom) >= 0.03 * width * height:
                    figures.append({"page": page_index + 1, "top": top, "bbox": (left, bottom, right, top)})
    pages = len(pdf)
    pdf.close()
    return rows, figures, pages


def prepare_rows(rows):
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
    return body_rows, body


def classify_row(r, standalone, body, *, headings=True):
    words = len(r["text"].split())
    mathy = r["math"] >= 0.5 or any(ch in STRONG_MATH or PRIVATE_USE.match(ch) for ch in r["text"] if not PUA_BULLET.match(ch + " "))
    if r["letters"] == 0:
        return "formula" if mathy else "text"
    if (r["math"] >= 0.6 and r["text_letters"] <= 4) or (r["symbol_share"] >= 0.7 and words <= 12 and mathy):
        return "formula"
    if r["viet"] == 0 and r["tokens"] >= 2 and r["mono"] < 0.6 and (r["single"] >= 0.4 or r["math_words"] > 0):
        return "formula"  # công thức Word (Times nghiêng): không có âm tiết tiếng Việt, nhiều biến một chữ hoặc tên hàm
    if r["mono"] >= 0.6:
        return "text"  # dòng mã lệnh (font đơn cách)
    bare = PUA_BULLET.sub("", LIST_START.sub("", r["text"])) if (PUA_BULLET.match(r["text"]) or LIST_START.match(r["text"])) else r["text"]
    if CAPTION.match(r["text"]) and words <= 40:
        return "caption"
    wordy = r["letters"] >= 3 and not TABLE_ROW_END.search(r["text"]) and r["single"] < 0.4
    vietnamese = r["viet"] >= 1 and r["single"] < 0.3  # tiêu đề không đánh số phải có âm tiết tiếng Việt
    if headings and wordy and words <= 20 and HEADING_NUMBER.match(r["text"]) and (r["bold"] or r["size"] >= 1.1 * body) \
            and not r["text"].endswith(","):
        return "section_header"
    if headings and wordy and vietnamese and words <= 15 and ENUMERATOR.match(r["text"]) and r["bold"]:
        return "section_header"
    if headings and wordy and vietnamese and words <= 15 and r["size"] >= 1.2 * body and not r["text"].endswith((".", ",", ";")):
        return "section_header"
    if headings and wordy and vietnamese and words <= 15 and r["bold"] and bare != r["text"] and bare[:1].isupper() \
            and not r["text"].endswith((",", ";", ".")):
        return "section_header"  # tiêu đề in đậm mở đầu bằng dấu đầu dòng (xstk: "• Mẫu tổng quát và mẫu cụ thể")
    if headings and wordy and vietnamese and standalone and words <= 12 and r["bold"] and r["size"] >= 0.98 * body and bare[:1].isupper() \
            and not r["text"].endswith((",", ";")):
        return "section_header"
    if LIST_START.match(r["text"]):
        return "list_item"
    if r["bottom"] < 0.15 * r["height"] and r["size"] < 0.85 * body:
        return "footnote"
    return "text"


def standalone_flags(rows):
    previous = None
    flags = []
    for row in rows:
        gap = previous["bottom"] - row["top"] if previous and previous["page"] == row["page"] else None
        flags.append(gap is None or gap > 0.5 * max(row["size"], 1.0) or previous["text"].endswith((".", ":", "?", "!")))
        previous = row
    return flags


def heading_level(text):
    text = text.strip()
    if re.match(r"^(chương|phần|chapter|part)\b", text, re.I):
        return 1
    match = re.match(r"^(\d{1,2}(?:\.\d{1,2}){0,3})", text)
    if match:
        return min(4, match.group(1).count(".") + 2)
    return 2
