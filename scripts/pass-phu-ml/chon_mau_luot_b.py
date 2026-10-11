"""Chọn mẫu phiếu cho lượt B của D-01 (Claude chạy; cần khoa.jsonl, không giao script này cho agentic).

Mẫu gồm:
- khoảng TI_LE phiếu thật của mỗi sách, chọn ngẫu nhiên theo seed;
- mọi phiếu kiểm, để chấm lượt B trên vàng;
- phiếu lặp có phiếu gốc nằm trong mẫu, để đo độ tự nhất quán của lượt B.
Thứ tự được xáo. Mỗi dòng ra là dòng nguyên văn của phiếu gốc.

Chạy:  python chon_mau_luot_b.py --phieu tmp/d01-phieu/phieu.jsonl --khoa tmp/d01-phieu/khoa.jsonl --ra <thư mục gói>/phieu.jsonl
       [--ds-ra tmp/d01-luot-B/chon.json] [--ti-le 0.15] [--seed 20261010]
"""
import argparse
import json
import random
import sys
from collections import Counter, defaultdict


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phieu", required=True)
    ap.add_argument("--khoa", required=True)
    ap.add_argument("--ra", required=True)
    ap.add_argument("--ds-ra")
    ap.add_argument("--ti-le", type=float, default=0.15)
    ap.add_argument("--seed", type=int, default=20261010)
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    lines, pairs = {}, {}
    with open(args.phieu, encoding="utf-8") as f:
        for line in f:
            sheet = json.loads(line)
            lines[sheet["phieu_id"]] = line if line.endswith("\n") else line + "\n"
            pairs[sheet["phieu_id"]] = len(sheet["ung_vien"])
    with open(args.khoa, encoding="utf-8") as f:
        keys = {k["phieu_id"]: k for k in map(json.loads, f)}

    rng = random.Random(args.seed)
    by_book = defaultdict(list)
    for pid, k in keys.items():
        if k["loai"] == "thuc":
            by_book[k["doc_id"]].append(pid)
    chosen = []
    for book in sorted(by_book):
        ids = sorted(by_book[book])
        chosen += rng.sample(ids, round(args.ti_le * len(ids)))
    picked = set(chosen)
    checks = sorted(pid for pid, k in keys.items() if k["loai"] == "kiem")
    repeats = sorted(pid for pid, k in keys.items() if k["loai"] == "lap" and k["lap_cua"] in picked)
    sample = chosen + checks + repeats
    rng.shuffle(sample)

    with open(args.ra, "w", encoding="utf-8", newline="\n") as f:
        f.writelines(lines[pid] for pid in sample)
    if args.ds_ra:
        with open(args.ds_ra, "w", encoding="utf-8") as f:
            json.dump({"seed": args.seed, "ti_le": args.ti_le, "phieu_id": sample}, f, ensure_ascii=False)

    kinds = Counter(keys[pid]["loai"] for pid in sample)
    print(f"{len(sample)} phiếu, {sum(pairs[pid] for pid in sample)} cặp; theo loại: {dict(kinds)}")
    for book in sorted(by_book):
        n = sum(1 for pid in chosen if keys[pid]["doc_id"] == book)
        print(f"  {book}: {n}/{len(by_book[book])} phiếu thật")


if __name__ == "__main__":
    main()
