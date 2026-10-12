"""E0' (vòng 2): bảng đặc trưng × nhãn cho các cặp (phiếu, X) của D-01. 0 USD, không gọi mô hình.

Mỗi dòng là một ứng viên X của một phiếu về Y, đọc là "X là tiên quyết của Y". Đặc trưng dùng đúng `pair_features` của vòng 1
(`dung_bang_cap.py`), tính trên artifact danh tính (A9'') mà vé 12 đã dùng để xuất phiếu. 16 cuốn D-01 chưa chạy A8, nên bỏ nhóm `main_*`.
Nhãn ghép theo `(phieu_id, x_id)`: lượt A (bản gộp), và tuỳ chọn nhãn A cũ (trước khi gán lại 1–240) và lượt B.
Phiếu kiểm không vào bảng (chúng thuộc doc-1, xstk, doc-4). Phiếu lặp vào bảng với `loai = lap` để bộ học tự bỏ.

`trong_cua_so` tính lại bằng `x_trong_ywin_tu > 0` (bộ khớp hiện tại); cờ lúc xuất phiếu giữ ở `trong_cua_so_phieu`. Hai cờ lệch nhau ở các
tên có âm tiết giữa từ ghép tận cùng bằng "y" ("quy luật"), vì bộ khớp lúc xuất phiếu có lỗi y→i (sửa 2026-10-12). In số dòng lệch theo
từng chiều: phiếu nói ngoài mà nay trong cửa sổ (do sửa lỗi), và ngược lại (phải bằng 0).

Cần `khoa.jsonl` (mã sách thật), nên chỉ Claude chạy. Ghi vào `tmp/` vì dòng có tên khái niệm. Chạy bằng `tmp/venv-ml` (underthesea):
  tmp/venv-ml/Scripts/python.exe scripts/pass-phu-ml/dung_bang_d01.py --phieu tmp/d01-phieu/phieu.jsonl --khoa tmp/d01-phieu/khoa.jsonl \
      --nhan tmp/d01-gan-nhan/nhan-A-gop.jsonl [--nhan-cu tmp/d01-gan-nhan/nhan-A.jsonl] [--nhan-b <nhan-B.jsonl>] [--ra tmp/pass-phu-ml/bang-d01]
"""
import argparse
import csv
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import dung_bang_cap as dbc  # noqa: E402
from xuat_phieu import chunks_for, latest_identity  # noqa: E402

dbc.WORDS = True  # khớp tên theo ranh giới từ, như lúc xuất phiếu


def read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def labels(path):
    return {(r["phieu_id"], r["x_id"]): r["nhan"] for r in read_jsonl(path)} if path else {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phieu", required=True)
    ap.add_argument("--khoa", required=True)
    ap.add_argument("--nhan", required=True)
    ap.add_argument("--nhan-cu")
    ap.add_argument("--nhan-b")
    ap.add_argument("--ra", default="tmp/pass-phu-ml/bang-d01")
    ap.add_argument("--chi", help="chỉ các sách này, phân cách bằng dấu phẩy")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    out = Path(args.ra)
    out.mkdir(parents=True, exist_ok=True)

    key = {k["phieu_id"]: k for k in read_jsonl(args.khoa)}
    label_a, label_old, label_b = labels(args.nhan), labels(args.nhan_cu), labels(args.nhan_b)
    by_doc = defaultdict(list)
    for sheet in read_jsonl(args.phieu):
        k = key[sheet["phieu_id"]]
        if k["loai"] != "kiem":
            by_doc[k["doc_id"]].append(sheet)
    docs = args.chi.split(",") if args.chi else sorted(by_doc)

    for doc in docs:
        started = time.time()
        artifact = latest_identity(ROOT / "artifacts", doc)
        payload = artifact.payload
        ctx = dbc.Context(payload, chunks_for(doc, artifact), 4, 2)
        pair_by_nodes = {frozenset((p["left"], p["right"])): p for p in payload.get("suspected_pairs", [])}
        rows, now_inside, now_outside = [], 0, 0
        for sheet in by_doc[doc]:
            y = sheet["y_id"]
            for cand in sheet["ung_vien"]:
                x = cand["x_id"]
                features = dbc.pair_features(ctx, x, y, pair_by_nodes.get(frozenset((x, y))))
                features = {name: value for name, value in features.items() if not name.startswith("main_")}
                inside = features["x_trong_ywin_tu"] > 0
                now_inside += int(inside and not cand["trong_cua_so"])
                now_outside += int(cand["trong_cua_so"] and not inside)
                rows.append({"doc": doc, "linh_vuc": sheet["linh_vuc"], "phieu_id": sheet["phieu_id"], "loai": key[sheet["phieu_id"]]["loai"],
                             "x": x, "y": y, "ten_x": cand["x_ten"], "ten_y": sheet["y_ten"],
                             "trong_cua_so": int(inside), "trong_cua_so_phieu": int(cand["trong_cua_so"]), "so_cau_co_ten": len(cand["cau_co_ten"]),
                             "nhan_a": label_a.get((sheet["phieu_id"], x), ""), "nhan_a_cu": label_old.get((sheet["phieu_id"], x), ""),
                             "nhan_b": label_b.get((sheet["phieu_id"], x), ""), **features})
        with (out / f"{doc}.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        print(json.dumps({"doc": doc, "phieu": len(by_doc[doc]), "dong": len(rows), "thieu_nhan_a": sum(1 for r in rows if not r["nhan_a"]),
                          "phieu_ngoai_nay_trong": now_inside, "phieu_trong_nay_ngoai": now_outside, "giay": round(time.time() - started)},
                         ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
