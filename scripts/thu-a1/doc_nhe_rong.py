"""Kiểm rộng bộ đọc nhẹ trên 16 cuốn học của D-01, 8 lĩnh vực (vé v4-10 bước 2b). 0 USD, tại máy.

Mỗi cuốn (chỉ `split == "train"`; **không mở sách `test/`**):
- bộ đọc nhẹ (`doc_nhe.parse`): thời gian, số nút theo loại;
- tín hiệu chọn bộ đọc: tỉ lệ ký tự font toán, tỉ lệ trang có ít nhất 10 ký tự toán;
- chất lượng chữ: ký tự vùng riêng (U+E000–F8FF), "ƣ"/"Ƣ" (glyph sai thay "ư" mà README D-01 đã ghi), tỉ lệ mảnh âm tiết một chữ cái;
- nếu đã có cây docling của cuốn đó trong kho (`ingest_d01.py`): so mức cây (`doc_nhe.compare`) và mức chunk (`so_chunk_doc_nhe`), cùng
  tham số chunk của manifest; thời gian parse docling lấy từ manifest chunk (`parse_runtime_seconds`).
Ghi `tmp/thu-a1/doc-nhe-rong/bang.json` và in bảng theo cuốn. Chạy từ gốc repo:
  .venv/Scripts/python.exe scripts/thu-a1/doc_nhe_rong.py [--chi=d01-01,d01-02]
"""
import ctypes
import json
import re
import sys
import time
import unicodedata
from collections import Counter
from pathlib import Path

import pypdfium2 as pdfium
import pypdfium2.raw as raw

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from doc_nhe import MATH_FONT, compare, parse  # noqa: E402
from so_chunk_doc_nhe import chunks_of, compare as compare_chunks, light_tree  # noqa: E402
from doc2roadmap.domain.models import DocumentNode, DocumentTree  # noqa: E402
from doc2roadmap.infrastructure.text import SentencePieceTokenCounter  # noqa: E402


def router_signal(path):
    pdf = pdfium.PdfDocument(path)
    buffer, flags = ctypes.create_string_buffer(256), ctypes.c_int()
    total = math = math_pages = 0
    for index in range(len(pdf)):
        textpage, count = pdf[index].get_textpage(), 0
        for i in range(textpage.count_chars()):
            if raw.FPDFText_GetUnicode(textpage.raw, i) in (10, 13, 32):
                continue
            raw.FPDFText_GetFontInfo(textpage.raw, i, buffer, 256, ctypes.byref(flags))
            total += 1
            if MATH_FONT.search(buffer.value.decode("utf-8", "replace")):
                math += 1
                count += 1
        math_pages += count >= 10
    return {"ky_tu_font_toan": round(math / max(total, 1), 4), "trang_toan": round(math_pages / max(len(pdf), 1), 3)}


def text_quality(texts):
    joined = "".join(texts)
    tokens = re.findall(r"[^\W\d_]+", unicodedata.normalize("NFC", joined).casefold())
    single = sum(len(token) == 1 for token in tokens)
    return {"vung_rieng": sum(bool(re.match(r"[-]", ch)) for ch in joined),
            "u_sai": joined.count("ƣ") + joined.count("Ƣ"),
            "manh_mot_chu": round(single / max(len(tokens), 1), 4)}


def latest(folder):
    versions = sorted((p for p in folder.iterdir() if p.name.startswith("v")), key=lambda p: int(p.name[1:])) if folder.exists() else []
    return versions[-1] if versions else None


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    options = dict(arg[2:].split("=", 1) for arg in sys.argv[1:] if arg.startswith("--") and "=" in arg)
    manifest = json.loads((ROOT / "document-data/manifest.json").read_text(encoding="utf-8"))
    books = [book for book in manifest["books"] if book["split"] == "train"]
    if "chi" in options:
        books = [book for book in books if book["id"] in set(options["chi"].split(","))]
    counter = SentencePieceTokenCounter(ROOT / "vendor/gemma/tokenizer.model", "google-gemma-sentencepiece-v1")
    out = ROOT / "tmp/thu-a1/doc-nhe-rong"
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for book in books:
        path = ROOT / "document-data" / book["file"]
        assert "/test/" not in path.as_posix() and book["split"] == "train"
        began = time.perf_counter()
        nodes, stats = parse(path)
        seconds = time.perf_counter() - began
        row = {"id": book["id"], "linh_vuc": book["field"], "trang": stats["pages"], "nhe_giay_trang": round(seconds / stats["pages"], 4),
               "nut_nhe": dict(Counter(node["node_type"] for node in nodes).most_common()), **router_signal(path),
               "chu_nhe": text_quality([node["text"] for node in nodes])}
        tree_dir = latest(ROOT / "artifacts/parse_tree" / book["id"])
        chunk_dir = latest(ROOT / "artifacts/chunks" / book["id"])
        if tree_dir and chunk_dir:
            reference = json.loads((tree_dir / "tree.json").read_text(encoding="utf-8"))
            chunk_manifest = json.loads((chunk_dir / "manifest.json").read_text(encoding="utf-8"))
            settings = {name: value for name, value in chunk_manifest["config"]["chunk"].items()
                        if name in ("max_tokens", "max_table_tokens", "hard_cap_tokens", "target_tokens", "sentence_overlap",
                                    "result_min_count", "result_max_body_chars", "heading_scheme")}
            settings.setdefault("heading_scheme", None)
            tree = DocumentTree(nodes=[DocumentNode.from_dict(node) for node in reference["nodes"]])
            ref_chunks = chunks_of(tree, book["id"], counter, settings)
            light_chunks = chunks_of(light_tree(nodes), book["id"], counter, settings)
            pages_with = Counter()
            heavy = {}
            for node in reference["nodes"]:
                if node.get("page") is not None and node["node_type"] in ("formula", "table", "figure"):
                    heavy.setdefault(node["node_type"], set()).add(int(node["page"]))
            row.update({"docling_giay_trang": round(chunk_manifest.get("parse_runtime_seconds", 0) / max(stats["pages"], 1), 3)
                        if chunk_manifest.get("parse_runtime_seconds") else None,
                        "trang_cong_thuc_bang_hinh": round(len(set().union(*heavy.values())) / stats["pages"], 3) if heavy else 0.0,
                        "chu_docling": text_quality([node.get("text") or "" for node in reference["nodes"]]),
                        **{f"cay_{key}": value for key, value in compare(nodes, reference).items()},
                        **{f"chunk_{key}": value for key, value in compare_chunks(ref_chunks, light_chunks).items()}})
        rows.append(row)
        print(json.dumps(row, ensure_ascii=False), flush=True)
    (out / "bang.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
