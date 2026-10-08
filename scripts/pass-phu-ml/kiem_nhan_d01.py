"""Kiểm định dạng tệp nhãn D-01 so với tệp phiếu. Chỉ dùng thư viện chuẩn; không cần tệp khoá.

Chạy:  python kiem_nhan_d01.py --phieu phieu.jsonl --nhan nhan-A.jsonl [--mot-phan]
--mot-phan: đang gán dở, không báo lỗi các cặp chưa gán (vẫn in tiến độ).
Thoát mã 1 nếu có lỗi định dạng; mã 0 nếu đạt.
"""
import argparse
import json
import sys
from collections import Counter

NHAN = {"can_de_hieu", "cong_cu", "khong", "nguoc", "khop_nham", "khong_ro"}
TRUONG = ("phieu_id", "doc_id", "y_id", "x_id", "nhan", "cau", "trung_gian", "ly_do", "nguoi_gan", "luot")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phieu", required=True)
    ap.add_argument("--nhan", required=True)
    ap.add_argument("--mot-phan", action="store_true")
    args = ap.parse_args()
    sheets = {}
    with open(args.phieu, encoding="utf-8") as f:
        for line in f:
            s = json.loads(line)
            sheets[s["phieu_id"]] = (s["doc_id"], s["y_id"], {c["i"] for c in s["cau"]},
                                     {c["x_id"]: c["trong_cua_so"] for c in s["ung_vien"]})
    errors, seen, labels = [], set(), Counter()

    def err(no, msg):
        errors.append(f"dòng {no}: {msg}")

    with open(args.nhan, encoding="utf-8") as f:
        for no, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError as e:
                err(no, f"JSON hỏng ({e.msg})")
                continue
            if not isinstance(r, dict) or any(k not in r for k in TRUONG):
                err(no, "thiếu trường; cần đủ " + ", ".join(TRUONG))
                continue
            s = sheets.get(r["phieu_id"])
            if s is None:
                err(no, f"phieu_id không có trong tệp phiếu: {r['phieu_id']}")
                continue
            doc_id, y_id, cau_ids, cands = s
            if r["doc_id"] != doc_id or r["y_id"] != y_id:
                err(no, "doc_id/y_id không khớp phiếu")
            if r["x_id"] not in cands:
                err(no, "x_id không phải ứng viên của phiếu")
                continue
            nhan, cau, tg = r["nhan"], r["cau"], r["trung_gian"]
            if nhan not in NHAN:
                err(no, f"nhãn lạ: {nhan}")
                continue
            hop_le = cau is None or (type(cau) is int and cau in cau_ids)
            if not hop_le:
                err(no, f"cau={cau!r} không phải chỉ số câu của phiếu")
            elif nhan in ("can_de_hieu", "cong_cu") and cau is None:
                err(no, f"{nhan} phải có cau")
            elif nhan in ("khong", "khong_ro") and cau is not None:
                err(no, f"{nhan} phải để cau = null")
            if nhan == "khop_nham" and not cands[r["x_id"]]:
                err(no, "khop_nham chỉ dùng cho ứng viên trong_cua_so = true")
            if tg is not None and (nhan != "khong" or tg not in cands or tg == r["x_id"]):
                err(no, "trung_gian chỉ dùng với nhãn khong và phải là x_id của ứng viên khác cùng phiếu")
            if not isinstance(r["ly_do"], str) or not 1 <= len(r["ly_do"].split()) <= 30:
                err(no, "ly_do phải có từ 1 đến 30 từ")
            if not isinstance(r["nguoi_gan"], str) or not r["nguoi_gan"].strip():
                err(no, "nguoi_gan rỗng")
            if r["luot"] not in ("A", "B", "C"):
                err(no, "luot phải là A, B hoặc C")
            key = (r["phieu_id"], r["x_id"], r["luot"])
            if key in seen:
                err(no, "cặp đã gán ở dòng trước (trùng phieu_id, x_id, luot)")
            seen.add(key)
            labels[nhan] += 1
    total = sum(len(s[3]) for s in sheets.values())
    for luot in sorted({k[2] for k in seen}) or ["A"]:
        done = {(p, x) for p, x, lt in seen if lt == luot}
        missing = total - len(done)
        print(f"lượt {luot}: đã gán {len(done)}/{total} cặp; còn thiếu {missing}")
        if missing and not args.mot_phan:
            errors.append(f"lượt {luot}: còn {missing} cặp chưa gán (dùng --mot-phan nếu đang làm dở)")
    print("phân bố nhãn:", dict(labels))
    for e in errors[:30]:
        print("LỖI", e)
    if len(errors) > 30:
        print(f"... và {len(errors) - 30} lỗi nữa")
    print("ĐẠT" if not errors else f"KHÔNG ĐẠT: {len(errors)} lỗi")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
