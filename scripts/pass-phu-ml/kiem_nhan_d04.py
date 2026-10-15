"""D-04: kiểm định dạng tệp nhãn cạnh ngược trước khi trả. Chỉ cần Python chuẩn; không đọc khoá.

Báo từng lỗi kèm `phieu_id`: dòng không đọc được hay thiếu trường; nhãn ngoài bảy giá trị; phiếu lạ, thiếu nhãn, hoặc nhiều hơn một nhãn trong
một lượt; `cau_y` thiếu hoặc ngoài danh sách câu của Y; `cau_giai_thich` có mặt khi và chỉ khi nhãn là `du_tai_cho`, và nằm trong danh sách câu.
Chạy:  python kiem_nhan_d04.py <phieu.jsonl> <nhan.jsonl>
"""
import json
import sys

LABELS = {"can_hoc_truoc", "du_tai_cho", "kien_thuc_nen", "nghia_khac", "khong_tien_quyet", "nguoc", "khong_ro"}
NEEDS_SENTENCE = {"can_hoc_truoc", "du_tai_cho", "kien_thuc_nen", "nghia_khac"}
REQUIRED = ("phieu_id", "nhan", "ly_do", "nguoi_gan", "luot")


def check(cards, lines):
    """`cards`: các phiếu đã đọc; `lines`: các dòng văn bản của tệp nhãn. Trả danh sách lỗi (chuỗi)."""
    sentences = {card["phieu_id"]: {row["i"] for row in card["y"]["cau"]} for card in cards}
    errors, seen = [], {}
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            errors.append(f"dòng {number}: không đọc được JSON")
            continue
        if not isinstance(row, dict):
            errors.append(f"dòng {number}: không phải đối tượng JSON")
            continue
        pid = row.get("phieu_id")
        missing = [field for field in REQUIRED if field not in row]
        if missing:
            errors.append(f"dòng {number} ({pid}): thiếu trường {', '.join(missing)}")
            continue
        if pid not in sentences:
            errors.append(f"dòng {number} ({pid}): phiếu không có trong tệp phiếu")
            continue
        seen[(pid, row["luot"])] = seen.get((pid, row["luot"]), 0) + 1
        label = row["nhan"]
        if label not in LABELS:
            errors.append(f"{pid}: nhãn lạ {label!r}")
            continue
        valid = sentences[pid]
        if label in NEEDS_SENTENCE:
            if row.get("cau_y") not in valid:
                errors.append(f"{pid}: `cau_y` = {row.get('cau_y')!r} không nằm trong danh sách câu của Y")
        elif row.get("cau_y") is not None and row.get("cau_y") not in valid:
            errors.append(f"{pid}: `cau_y` = {row.get('cau_y')!r} không nằm trong danh sách câu của Y")
        if label == "du_tai_cho":
            if row.get("cau_giai_thich") not in valid:
                errors.append(f"{pid}: nhãn du_tai_cho cần `cau_giai_thich` là chỉ số câu của Y")
        elif row.get("cau_giai_thich") is not None:
            errors.append(f"{pid}: `cau_giai_thich` chỉ dùng cho nhãn du_tai_cho")
    for (pid, run), count in sorted(seen.items()):
        if count > 1:
            errors.append(f"{pid}: {count} nhãn trong lượt {run}")
    for run in sorted({run for _, run in seen}):
        absent = sorted(pid for pid in sentences if (pid, run) not in seen)
        errors += [f"{pid}: thiếu nhãn trong lượt {run}" for pid in absent]
    if not seen:
        errors.append("tệp nhãn không có dòng hợp lệ nào")
    return errors


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    with open(sys.argv[1], encoding="utf-8") as handle:
        cards = [json.loads(line) for line in handle if line.strip()]
    with open(sys.argv[2], encoding="utf-8") as handle:
        errors = check(cards, handle.read().splitlines())
    for error in errors:
        print(error)
    print(f"{len(errors)} lỗi" if errors else "HỢP LỆ")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
