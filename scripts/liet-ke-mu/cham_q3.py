"""Chấm Q3 (không sót khái niệm trọng yếu, ≥ 90%) từ danh sách liệt kê mù T7.

Hai bước, vì so tên mờ không được để máy tự quyết:
1. `cham_q3.py`: đọc `artifacts/a8-gold/liet-ke-mu.md`; khái niệm khớp đúng tên hoặc alias của khái niệm máy (sau chuẩn
   hoá NFKC, chữ thường, bỏ khoảng trắng thừa) là khớp tự động; còn lại ghi vào `liet-ke-mu-doi-chieu.xlsx` kèm ba khái
   niệm máy gần nhất để người xác nhận.
2. Người điền cột «Xác nhận» (tên khái niệm máy tương ứng, hoặc «Không có»), rồi chạy lại: Q3 = khớp / tổng.

Khái niệm máy là khái niệm `learnable` của bản canonical mới nhất của tài liệu — lộ trình dựng trên đúng danh sách này.
Chạy từ gốc repo:  .venv/Scripts/python.exe scripts/liet-ke-mu/cham_q3.py
"""
import difflib
import math
import re
import sys
import unicodedata
from pathlib import Path

import openpyxl
from openpyxl.styles import Alignment, Font

sys.path.insert(0, "src")
from doc2roadmap.composition import build_learning_graph  # noqa: E402

LIST = Path("artifacts/a8-gold/liet-ke-mu.md")
SHEET = Path("artifacts/a8-gold/liet-ke-mu-doi-chieu.xlsx")
NONE = "Không có"


def norm(text):
    return " ".join(unicodedata.normalize("NFKC", str(text)).casefold().replace("(?)", "").split()).strip(" .;:")


def parse(text):
    """{(doc_id, tiêu đề phần): [(tên, không chắc)]} — chỉ các tiêu đề `## doc-…`."""
    sections, current = {}, None
    for line in text.splitlines():
        heading = re.match(r"^##\s+(doc-\d+)\s+—\s+(.+?)\s*$", line)
        if heading:
            current = (heading.group(1), heading.group(2))
            sections[current] = []
        elif current and line.startswith("- ") and line[2:].strip():
            name = line[2:].strip()
            sections[current].append((name.replace("(?)", "").strip(), "(?)" in name))
    return sections


def wilson(k, n, z=1.96):
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return centre - half, centre + half


def machine_names(store, doc):
    artifact = store.load_latest_canonical(doc)
    names = {}
    for node in artifact.payload["nodes"]:
        if node.get("learnable"):
            for value in [node["name"], *(a["name"] if isinstance(a, dict) else a for a in node.get("aliases", []))]:
                names.setdefault(norm(value), node["name"])
    return artifact.version, names


def confirmations():
    if not SHEET.exists():
        return {}
    rows = list(openpyxl.load_workbook(SHEET, read_only=True)["Đối chiếu"].iter_rows(values_only=True))[1:]
    return {(r[1], r[2], r[3]): r[7] for r in rows if r and r[0] is not None and r[7]}


def main():
    sections = parse(LIST.read_text(encoding="utf-8"))
    empty = [key for key, items in sections.items() if not items]
    if not sections or len(empty) == len(sections):
        raise SystemExit(f"{LIST}: chưa có khái niệm nào được liệt kê")
    store = build_learning_graph()[0].teaching.store
    machine = {doc: machine_names(store, doc) for doc in sorted({doc for doc, _ in sections})}
    confirmed = confirmations()
    pending, totals = [], {}
    for (doc, part), items in sections.items():
        version, names = machine[doc]
        hit = 0
        for name, unsure in items:
            key = (doc, part, name)
            if norm(name) in names:
                hit += 1
                continue
            answer = confirmed.get(key)
            if answer and answer != NONE:
                hit += 1
            elif answer is None:
                close = difflib.get_close_matches(norm(name), list(names), n=3, cutoff=0.5)
                pending.append([doc, part, name, "có" if unsure else ""] + [names[c] for c in close] + [""] * (3 - len(close)))
        totals[(doc, part)] = (hit, len(items))
    print(f"canonical: " + ", ".join(f"{doc} v{version}" for doc, (version, _) in machine.items()))
    for (doc, part), (hit, total) in totals.items():
        print(f"  {doc} — {part}: {hit}/{total}" if total else f"  {doc} — {part}: (trống)")
    hits = sum(h for h, _ in totals.values())
    total = sum(t for _, t in totals.values())
    if pending:
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = "Đối chiếu"
        sheet.append(["STT", "Tài liệu", "Phần", "Khái niệm người liệt kê", "Người ghi (?)", "Gần nhất 1", "Gần nhất 2",
                      "Xác nhận (tên khái niệm máy tương ứng, hoặc «Không có»)"])
        for index, row in enumerate(pending, 1):
            sheet.append([index, row[0], row[1], row[2], row[3], row[4], row[5], None])
        for cell in sheet[1]:
            cell.font = Font(bold=True)
        for column, width in zip("ABCDEFGH", (6, 9, 34, 36, 10, 34, 34, 44)):
            sheet.column_dimensions[column].width = width
        for line in sheet.iter_rows(min_row=2):
            for cell in line:
                cell.alignment = Alignment(wrap_text=True, vertical="top")
        workbook.save(SHEET)
        print(f"{len(pending)} khái niệm chưa khớp đúng tên → {SHEET}: điền cột H rồi chạy lại. Q3 chưa tính.")
        return
    low, high = wilson(hits, total)
    print(f"Q3 = {hits}/{total} = {hits / total:.0%} (Wilson 95% {low:.0%}–{high:.0%}); ngưỡng ≥ 90%")


if __name__ == "__main__":
    main()
