"""Bảng duyệt danh tính (vé v2-10, T5; cổng 2 của vé 05).

Mọi cặp mà bước phán danh tính không phán `different`: các gộp (bắt buộc duyệt những gộp chạm khái niệm vàng) và các
cặp `sense_split` (hệ thống giữ tách). Không cần mù: đây là duyệt đề xuất, người duyệt được thấy hệ thống đề xuất gì.

Chạy từ gốc repo:  .venv/Scripts/python.exe scripts/duyet-danh-tinh/tao_bang.py [doc phiên-bản-identity tệp-vàng]
Có tham số thì sinh bảng riêng cho tài liệu đó (`duyet-danh-tinh-<doc>.xlsx`), ví dụ cho tập giữ lại ở vé 07.
"""
import hashlib
import json
import sys
from pathlib import Path

import openpyxl
from openpyxl.styles import Alignment, Font
from openpyxl.worksheet.datavalidation import DataValidation

# bản `identity` của lượt 1 (nhật ký vé 05); tài liệu không có cặp nào khác `different` thì không cần liệt kê
IDENTITY = {"doc-1": 24, "doc-2": 18}
GOLD = {"doc-1": "artifacts/a8-gold/doc-1-10-12-vang.json", "doc-2": "artifacts/a8-gold/doc-2-98-115-vang.json"}
CHOICES = "Đồng ý gộp,Không gộp,Là hai nghĩa khác nhau,Không chắc"
GUIDE = [
    "Duyệt gộp khái niệm",
    "",
    "Mỗi dòng là một cặp khái niệm cùng tài liệu, kèm câu tài liệu dùng để dạy từng khái niệm (câu neo) và đề xuất của hệ thống.",
    "• «Gộp»: hệ thống cho rằng hai khái niệm là MỘT ý người học chỉ học một lần (đồng nghĩa, ký hiệu, cách gọi khác).",
    "• «Giữ tách — hai nghĩa»: hệ thống cho rằng cùng một tên được dùng cho hai nghĩa khác nhau.",
    "Chọn một:",
    "• Đồng ý gộp — đúng là một khái niệm.",
    "• Không gộp — hai khái niệm khác nhau (ví dụ khái niệm chung và trường hợp riêng, đối tượng và tính chất của nó).",
    "• Là hai nghĩa khác nhau — cùng tên nhưng tài liệu dùng cho hai nghĩa.",
    "• Không chắc — ghi lý do vào ghi chú.",
    "",
    "Cột «Chạm vàng» = Có: cặp này đụng khái niệm của bộ vàng, bắt buộc duyệt trước khi bật bước gộp.",
    "Ghi giờ bắt đầu và giờ xong vào ô ghi chú của dòng đầu tiên.",
]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    global IDENTITY, GOLD
    suffix = ""
    if len(sys.argv) == 4:
        IDENTITY, GOLD, suffix = {sys.argv[1]: int(sys.argv[2])}, {sys.argv[1]: sys.argv[3]}, f"-{sys.argv[1]}"
    rows = []
    for doc, version in IDENTITY.items():
        path = Path(f"artifacts/graph/{doc}/v{version}/graph.json")
        payload = json.loads(path.read_text(encoding="utf-8"))
        by_id = {n["node_id"]: n for n in [*payload["nodes"], *payload["merged_nodes"]]}
        gold = json.loads(Path(GOLD[doc]).read_text(encoding="utf-8"))
        concepts = {n for e in gold["edges"] for n in (e["prerequisite"], e["target"])} | set(gold["targets"])
        for row in payload["identity_log"]:
            if row["verdict"] == "different":
                continue
            left, right = by_id[row["left"]], by_id[row["right"]]
            rows.append({"doc_id": doc, "pair_id": row["pair_id"], "left": left, "right": right,
                         "proposal": "Gộp" if row["verdict"] == "same" else "Giữ tách — hai nghĩa",
                         "gold": bool({row["left"], row["right"]} & concepts), "reason": row["reason"]})
    rows.sort(key=lambda r: (not r["gold"], r["doc_id"], r["pair_id"]))

    def anchor(node):
        sentence = (node.get("anchor") or {}).get("sentence")
        return sentence if sentence else f"(không có câu neo) mô tả: {node.get('description', '')}"

    workbook = openpyxl.Workbook()
    guide = workbook.active
    guide.title = "Hướng dẫn"
    for line in GUIDE:
        guide.append([line])
    guide["A1"].font = Font(bold=True, size=13)
    guide.column_dimensions["A"].width = 120
    sheet = workbook.create_sheet("Cặp")
    sheet.append(["STT", "Tài liệu", "Chạm vàng", "Khái niệm 1", "Câu neo 1", "Khái niệm 2", "Câu neo 2",
                  "Hệ thống đề xuất", "Lý do của hệ thống", "Quyết định", "Ghi chú"])
    for index, row in enumerate(rows, 1):
        row["item"] = index
        sheet.append([index, row["doc_id"], "Có" if row["gold"] else "", row["left"]["name"], anchor(row["left"]),
                      row["right"]["name"], anchor(row["right"]), row["proposal"], row["reason"], None, None])
    for cell in sheet[1]:
        cell.font = Font(bold=True)
    for column, width in zip("ABCDEFGHIJK", (6, 10, 10, 26, 55, 26, 55, 18, 45, 20, 30)):
        sheet.column_dimensions[column].width = width
    for line in sheet.iter_rows(min_row=2):
        for cell in line:
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    choice = DataValidation(type="list", formula1=f'"{CHOICES}"', allow_blank=True)
    sheet.add_data_validation(choice)
    choice.add(f"J2:J{len(rows) + 1}")
    out = Path(f"artifacts/a8-gold/duyet-danh-tinh{suffix}.xlsx")
    workbook.save(out)
    key = {"inputs": {doc: {"version": v, "sha256": sha256(f"artifacts/graph/{doc}/v{v}/graph.json")}
                      for doc, v in IDENTITY.items()},
           "sheet": {"path": str(out), "sha256": sha256(out)},
           "items": [{"item": r["item"], "doc_id": r["doc_id"], "pair_id": r["pair_id"], "left": r["left"]["node_id"],
                      "right": r["right"]["node_id"], "proposal": r["proposal"], "gold": r["gold"]} for r in rows]}
    Path(f"artifacts/a8-gold/duyet-danh-tinh{suffix}-khoa.json").write_text(json.dumps(key, ensure_ascii=False, indent=2) + "\n",
                                                                   encoding="utf-8")
    print(f"{out}: {len(rows)} cặp, {sum(r['gold'] for r in rows)} chạm vàng")


if __name__ == "__main__":
    main()
