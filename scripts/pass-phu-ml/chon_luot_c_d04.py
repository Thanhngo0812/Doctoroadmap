"""D-04c: chọn phiếu cho lượt C phân xử, rồi xuất gói giao chỉ gồm các phiếu đó (không kèm nhãn A, B hay khoá).

Phiếu cần phân xử: A và B lệch nhau ở nhị phân `can_hoc_truoc` hay không (phép đo D-04d chỉ dùng nhị phân này), hoặc một lượt chỉ có nhãn
giữ chỗ. Lượt B (script gọi Gemini) gán `khong_tien_quyet` với lý do cố định khi mô hình không trả nhãn cho phiếu; dòng đó không phải phán xét.
Lệch giữa các nhãn khác (`du_tai_cho` hay `kien_thuc_nen`…) không đổi nhị phân, nên không gửi C.

Chạy:  python chon_luot_c_d04.py <phieu.jsonl> <nhan-A.jsonl> <nhan-B.jsonl> <thư mục gói C> <hướng dẫn.md> <kiem_nhan_d04.py>
"""
import json
import shutil
import sys
from pathlib import Path

PLACEHOLDER_REASONS = {"đoạn Y không cho thấy quan hệ"}


def _is_prereq(row):
    return row["nhan"] == "can_hoc_truoc"


def _is_placeholder(row):
    return row["ly_do"] in PLACEHOLDER_REASONS


def needs_arbitration(row_a, row_b):
    return _is_prereq(row_a) != _is_prereq(row_b) or _is_placeholder(row_a) or _is_placeholder(row_b)


def _read(path):
    with open(path, encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) != 7:
        print(__doc__)
        return 2
    cards_path, a_path, b_path, out_dir, guide, checker = sys.argv[1:]
    run_a = {row["phieu_id"]: row for row in _read(a_path)}
    run_b = {row["phieu_id"]: row for row in _read(b_path)}
    cards = [card for card in _read(cards_path) if needs_arbitration(run_a[card["phieu_id"]], run_b[card["phieu_id"]])]
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=False)
    with open(out / "phieu.jsonl", "w", encoding="utf-8") as handle:
        for card in cards:
            handle.write(json.dumps(card, ensure_ascii=False) + "\n")
    shutil.copy(guide, out)
    shutil.copy(checker, out)
    placeholders = sum(_is_placeholder(run_a[c["phieu_id"]]) or _is_placeholder(run_b[c["phieu_id"]]) for c in cards)
    print(f"{len(cards)} phiếu cho lượt C ({placeholders} có nhãn giữ chỗ) -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
