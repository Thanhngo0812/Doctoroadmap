"""Chuyển bảng duyệt danh tính đã điền thành JSON cho `roadmap --identity-review`.

Chạy từ gốc repo:
    .venv/Scripts/python.exe scripts/duyet-danh-tinh/doi_json.py <bảng đã điền .xlsx> <khoá .json> <doc_id> <tệp ra .json>
"""
import json
import sys
from pathlib import Path

import openpyxl


def main(sheet, key_path, doc_id, out):
    key = json.loads(Path(key_path).read_text(encoding="utf-8"))
    by_item = {row["item"]: row for row in key["items"] if row["doc_id"] == doc_id}
    decisions = []
    for row in list(openpyxl.load_workbook(sheet, read_only=True)["Cặp"].iter_rows(values_only=True))[1:]:
        if row and row[0] is not None and row[9] and int(row[0]) in by_item:
            item = by_item[int(row[0])]
            decisions.append({"left": item["left"], "right": item["right"], "decision": row[9]})
    Path(out).write_text(json.dumps({"doc_id": doc_id, "decisions": decisions}, ensure_ascii=False, indent=2) + "\n",
                         encoding="utf-8")
    print(f"{out}: {len(decisions)} quyết định cho {doc_id}")


if __name__ == "__main__":
    main(*sys.argv[1:5])
