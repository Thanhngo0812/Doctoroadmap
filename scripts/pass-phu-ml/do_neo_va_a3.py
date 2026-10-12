"""Gộp khâu (2026-10-12): câu neo của C8 có sẵn trong bằng chứng A3 hay chunk định nghĩa A5 không, và danh tính gộp nhờ tín hiệu nào. 0 USD.

Trả lời đề xuất "A5 kiêm neo và trạng thái dạy, danh tính gộp vào A4": nếu câu neo gần như luôn là một câu bằng chứng A3 của chính khái niệm,
thì một lời gọi A5 chọn neo trong các câu đó thay được lời gọi C8 riêng. Đếm trên khái niệm `taught` có neo:
- `trung_cau_a3`: câu neo trùng một câu bằng chứng A3 theo đúng luật hạng 0 của C8 (câu neo chứa 40 ký tự đầu của câu trích, hoặc nằm trọn
  trong câu trích);
- `chunk_a3`: chunk neo là chunk có bằng chứng A3;
- `chunk_a5`: chunk neo thuộc chunk định nghĩa mà A5 chọn (trừ chunk do provenance thêm);
- `chi_nho_provenance`: chunk neo do provenance thêm và không có bằng chứng A3: neo mất nếu bỏ provenance mà không có luật thay;
- `khac`: còn lại (neo từ chunk nhắc tên, khối tiêu đề, ký hiệu do C8 tự tìm).
Danh tính: với các cặp được gộp, đếm nguồn đề cử (`reasons` trong `identity_log`).
Chạy từ gốc repo:  .venv/Scripts/python.exe scripts/pass-phu-ml/do_neo_va_a3.py [doc ...]
"""
import json
import sys
import unicodedata
from collections import Counter
from pathlib import Path

DEV = {"doc-1": ("artifacts/v3-r12-final-evaluation", 2), "xstk-ch3-1": ("artifacts", 42), "doc-4": ("artifacts", 8)}


def norm(text):
    return " ".join(unicodedata.normalize("NFC", text or "").casefold().split())


def payload_for(doc):
    if doc in DEV:
        root, version = DEV[doc]
        return json.loads((Path(root) / "graph" / doc / f"v{version}" / "graph.json").read_text(encoding="utf-8"))
    base = Path("artifacts/graph") / doc
    for path in sorted(base.glob("v*"), key=lambda p: -int(p.name[1:])):
        if json.loads((path / "manifest.json").read_text(encoding="utf-8")).get("stage") == "identity":
            return json.loads((path / "graph.json").read_text(encoding="utf-8"))
    raise SystemExit(f"{doc}: không có artifact identity")


def measure(doc):
    payload = payload_for(doc)
    added = {(row["node_id"], row["chunk_id"]) for row in payload.get("provenance_log", []) if row.get("status") == "added"}
    counts, statuses = Counter(), Counter()
    for node in payload["nodes"]:
        if not node.get("learnable"):
            continue
        statuses[node.get("teaching_status")] += 1
        anchor = node.get("anchor") or {}
        if node.get("teaching_status") != "taught" or not anchor.get("sentence"):
            continue
        counts["taught"] += 1
        sentence, chunk = norm(anchor["sentence"]), anchor.get("chunk_id")
        evidence = node.get("evidence") or []
        quotes = [norm(row.get("quote")) for row in evidence if row.get("quote")]
        a3_chunks = {row.get("chunk_id") for row in evidence}
        a5_chunks = {c for c in node.get("defining_chunk_ids") or [] if (node["node_id"], c) not in added}
        same_sentence = any(q and (q[:40] in sentence or sentence in q) for q in quotes)
        counts["trung_cau_a3"] += same_sentence
        counts["chunk_a3"] += chunk in a3_chunks
        counts["chunk_a5"] += chunk in a5_chunks
        only_provenance = (node["node_id"], chunk) in added and chunk not in a3_chunks
        counts["chi_nho_provenance"] += only_provenance
        counts["khac"] += not same_sentence and chunk not in a3_chunks and chunk not in a5_chunks and not only_provenance
    merged = Counter()
    for row in payload.get("identity_log", []):
        if row.get("verdict") == "same":
            merged["+".join(sorted(row.get("reasons") or [])) or "?"] += 1
    return {"doc": doc, "trang_thai": dict(statuses), **counts, "gop_theo_nguon": dict(merged),
            "nut_bi_gop": len(payload.get("identity_map", {})), "cap_danh_tinh_da_phan": len(payload.get("identity_log", []))}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    docs = [a for a in sys.argv[1:] if not a.startswith("--")] or [*DEV, *(f"d01-{i:02d}" for i in range(1, 17))]
    total = Counter()
    rows = []
    for doc in docs:
        row = measure(doc)
        rows.append(row)
        for key in ("taught", "trung_cau_a3", "chunk_a3", "chunk_a5", "chi_nho_provenance", "khac", "nut_bi_gop", "cap_danh_tinh_da_phan"):
            total[key] += row.get(key, 0)
        print(json.dumps(row, ensure_ascii=False))
    print(json.dumps({"tong": dict(total)}, ensure_ascii=False))
    Path("tmp/pass-phu-ml/ket-qua/neo-va-a3.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
