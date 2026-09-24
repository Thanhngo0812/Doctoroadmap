"""Chấm bảng kiểm câu neo đã điền (T4; Q9 của vé 04: câu neo đúng nơi dạy ≥ 90%).

Chạy từ gốc repo:  .venv/Scripts/python.exe scripts/cham-neo/cham_bang.py artifacts/a8-gold/kiem-cau-neo-output.xlsx
"""
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import openpyxl

CHOICES = ("Đúng nơi dạy", "Sai — chỉ nhắc qua", "Sai — nói về nghĩa khác", "Không chắc")


def wilson(k, n, z=1.96):
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return centre - half, centre + half


def line(label, rows):
    judged = [r for r in rows if r["answer"] != "Không chắc"]
    good = sum(r["answer"] == "Đúng nơi dạy" for r in judged)
    if not judged:
        return f"  {label}: —"
    low, high = wilson(good, len(judged))
    return f"  {label}: đúng {good}/{len(judged)} = {good / len(judged):.0%} (Wilson 95% {low:.0%}–{high:.0%}), không chắc {len(rows) - len(judged)}"


def main(path):
    key = json.loads(Path("artifacts/a8-gold/kiem-cau-neo-khoa.json").read_text(encoding="utf-8"))
    sheet = openpyxl.load_workbook(path, read_only=True)["Câu neo"]
    answers, notes = {}, {}
    for row in list(sheet.iter_rows(values_only=True))[1:]:
        if row and row[0] is not None:
            if row[7] is not None and row[7] not in CHOICES:
                raise ValueError(f"dòng {row[0]}: đánh giá {row[7]!r} ngoài bốn lựa chọn")
            answers[int(row[0])], notes[int(row[0])] = row[7], row[8]
    graphs = {doc: json.loads(Path(value["path"]).read_text(encoding="utf-8")) for doc, value in key["inputs"].items()}
    rows = []
    for item in key["items"]:
        node = next(n for n in graphs[item["doc_id"]]["nodes"] if n["node_id"] == item["node_id"])
        rows.append({**item, "answer": answers.get(item["item"]), "note": notes.get(item["item"]), "name": node["name"],
                     "multiline": "\n" in node["anchor"]["sentence"]})
    missing = [r["item"] for r in rows if r["answer"] is None]
    print(f"{path}: {len(rows)} dòng, bỏ trống {len(missing)} {missing[:10]}")
    print(f"  phân bố: {dict(Counter(r['answer'] for r in rows))}")
    print(line("Q9 toàn bộ (ngưỡng ≥ 90%)", [r for r in rows if r["answer"]]))
    groups = defaultdict(list)
    for r in rows:
        if r["answer"]:
            groups[("tài liệu", r["doc_id"])].append(r)
            groups[("trạng thái", r["status"])].append(r)
            groups[("câu neo", "nhiều dòng" if r["multiline"] else "một dòng")].append(r)
    for (kind, value), members in sorted(groups.items()):
        print(line(f"{kind} {value}", members))
    print("  các dòng không đúng:")
    for r in rows:
        if r["answer"] and r["answer"] != "Đúng nơi dạy":
            print(f"    {r['item']:>2} {r['doc_id']:<13} {r['name'][:40]!r:<44} {r['answer']:<24} {str(r['note'] or '')[:90]}")
    first_note = notes.get(1)
    print(f"  ghi chú dòng 1: {first_note!r}")


if __name__ == "__main__":
    main(sys.argv[1])
