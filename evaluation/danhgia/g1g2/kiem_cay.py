"""Kiểm cây mục G1 và vai trò vùng G2. Định dạng D-02 (`cay-muc/<sách>.jsonl`, mỗi tiêu đề trỏ mã dòng) cộng trường `vai_tro`.

Chỉ dùng thư viện chuẩn và không nhập gì từ gói `danhgia`: tệp này được chép nguyên vào gói nháp giao cho người làm nháp.
Chạy: `python kiem_cay.py --sach <mã> --thu-muc <thư mục gói>`; in `ĐẠT` hoặc danh sách lỗi.

Trường mỗi tiêu đề: sach, id (`h` + số, tăng dần), dong (mã dòng, theo thứ tự đọc), text, cap (1–6), cha, vung, vai_tro, ghi_chu.
`vai_tro` có ở mọi tiêu đề; `vung` chỉ ở cấp 1 và bằng `vai_tro` (D-02), cấp khác `vung` là null.
"""
import argparse
import copy
import json
import re
import sys
from pathlib import Path

VAI_TRO = ("mo_dau", "noi_dung", "bai_tap", "de_cuong", "hanh_chinh", "cuoi_sach")
NHANH_DAU = ("mo_dau", "hanh_chinh")  # nhánh riêng, không đóng nhánh nội dung đang mở (luật cha D-02)
BAT_BUOC = ("sach", "id", "dong", "text", "cap", "cha", "vung", "vai_tro", "ghi_chu")


def doc_jsonl(duong):
    return [json.loads(x) for x in Path(duong).read_text(encoding="utf-8-sig").splitlines() if x.strip()]


def tinh_cha(muc):
    """Bản sao có `cha` hợp lệ theo luật D-02. Giữ `cha` đã khai khi còn là tiêu đề đang mở ở cấp liền trên;
    nếu không thì lấy tiêu đề đang mở ở nhánh của tiêu đề liền trước, rồi mới tới nhánh kia; không có thì `cha` = None (validator sẽ báo)."""
    muc = copy.deepcopy(muc)
    ngan = {"dau": {}, "noi": {}}
    truoc = "noi"
    for h in muc:
        cap = h["cap"]
        if cap == 1:
            nhanh = "dau" if h["vai_tro"] in NHANH_DAU else "noi"
            h["cha"] = None
        else:
            ung = [(n, ngan[n][cap - 1]) for n in (truoc, "noi" if truoc == "dau" else "dau") if cap - 1 in ngan[n]]
            chon = next((u for u in ung if u[1] == h.get("cha")), ung[0] if ung else None)
            nhanh, h["cha"] = chon if chon else (truoc, None)
        ngan[nhanh] = {d: v for d, v in ngan[nhanh].items() if d < cap}
        ngan[nhanh][cap] = h["id"]
        truoc = nhanh
    return muc


def doi_so(muc):
    """Đánh lại id h001… theo thứ tự hiện có, cập nhật cha."""
    anh_xa = {h["id"]: f"h{i:03d}" for i, h in enumerate(muc, start=1)}
    ra = copy.deepcopy(muc)
    for h in ra:
        h["id"] = anh_xa[h["id"]]
        h["cha"] = anh_xa.get(h["cha"])
    return ra


def kiem_dong(dong):
    """(danh sách lỗi, {mã dòng: thứ tự}, {trang: tập mã dòng})."""
    loi, vi_tri, theo_trang = [], {}, {}
    for i, d in enumerate(dong):
        if not isinstance(d, dict):
            loi.append(f"dong {i + 1}: cần object")
            continue
        khoa, trang = d.get("id"), d.get("trang")
        if not isinstance(khoa, str) or not re.fullmatch(r"p\d{4,}-l\d{3,}", khoa):
            loi.append(f"dong {i + 1}: id sai")
            continue
        if type(trang) is not int or trang < 1 or int(khoa.split("-")[0][1:]) != trang:
            loi.append(f"{khoa}: trang không khớp id")
            continue
        if khoa in vi_tri:
            loi.append(f"{khoa}: mã dòng trùng")
        if not isinstance(d.get("text"), str) or not d["text"].strip():
            loi.append(f"{khoa}: text rỗng/sai")
        vi_tri[khoa] = i
        theo_trang.setdefault(trang, set()).add(khoa)
    return loi, vi_tri, theo_trang


def kiem_cay(sach, muc, dong):
    """Danh sách lỗi (rỗng là hợp lệ). `dong` là bảng dòng đọc từ `dong/<sách>.jsonl`."""
    loi, vi_tri, _ = kiem_dong(dong)
    da_dung, ngan, nhanh_cua = set(), {"front": {}, "content": {}}, {}
    truoc_so, truoc_vi_tri = -1, -1
    for i, h in enumerate(muc):
        if not isinstance(h, dict):
            loi.append(f"cay-muc {i + 1}: cần object")
            continue
        khoa, cap, ids = h.get("id"), h.get("cap"), h.get("dong")
        if not set(BAT_BUOC) <= h.keys():
            loi.append(f"{khoa}: thiếu trường bắt buộc")
        if h.get("sach") != sach:
            loi.append(f"{khoa}: sach sai")
        if not isinstance(khoa, str) or not re.fullmatch(r"h\d+", khoa):
            loi.append(f"{khoa}: id tiêu đề sai")
        else:
            so = int(khoa[1:])
            if so <= truoc_so:
                loi.append(f"{khoa}: id trùng/không tăng")
            truoc_so = so
        if not isinstance(ids, list) or not ids or any(not isinstance(x, str) for x in ids):
            loi.append(f"{khoa}: dong phải là danh sách không rỗng")
            ids = []
        if len(ids) != len(set(ids)) or da_dung.intersection(ids):
            loi.append(f"{khoa}: mã dòng thuộc nhiều tiêu đề")
        da_dung.update(ids)
        if any(x not in vi_tri for x in ids):
            loi.append(f"{khoa}: mã dòng không tồn tại")
        elif ids:
            thu_tu = [vi_tri[x] for x in ids]
            if thu_tu != sorted(thu_tu) or thu_tu[0] <= truoc_vi_tri:
                loi.append(f"{khoa}: sai thứ tự đọc")
            truoc_vi_tri = thu_tu[-1]
        if not isinstance(h.get("text"), str) or not h["text"].strip():
            loi.append(f"{khoa}: text rỗng/sai")
        if not isinstance(h.get("ghi_chu"), str):
            loi.append(f"{khoa}: ghi_chu phải là chữ")
        vai_tro = h.get("vai_tro")
        if vai_tro not in VAI_TRO:
            loi.append(f"{khoa}: vai_tro phải thuộc {list(VAI_TRO)}")
        if type(cap) is not int or not 1 <= cap <= 6:
            loi.append(f"{khoa}: cap ngoài 1–6")
            continue
        if cap == 1:
            nhanh = "front" if vai_tro in NHANH_DAU else "content"
            if h.get("vung") != vai_tro:
                loi.append(f"{khoa}: vung cấp 1 phải bằng vai_tro")
        else:
            nhanh = nhanh_cua.get(h.get("cha"), "content")
            if h.get("vung") is not None:
                loi.append(f"{khoa}: vung cấp con phải null")
        mong = None if cap == 1 else ngan[nhanh].get(cap - 1)
        if (cap > 1 and mong is None) or h.get("cha") != mong:
            loi.append(f"{khoa}: cha phải là tiêu đề đang mở cấp {cap - 1} trong nhánh logic")
        ngan[nhanh] = {d: v for d, v in ngan[nhanh].items() if d < cap}
        ngan[nhanh][cap] = khoa
        if isinstance(khoa, str):
            nhanh_cua[khoa] = nhanh
    return loi


def kiem_thu_muc(sach, thu_muc):
    thu_muc = Path(thu_muc)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", sach):
        return ["sach: mã sách không hợp lệ"]
    try:
        dong = doc_jsonl(thu_muc / "dong" / f"{sach}.jsonl")
        muc = doc_jsonl(thu_muc / "cay-muc" / f"{sach}.jsonl")
    except (OSError, ValueError) as e:
        return [f"Không đọc được tệp: {e}"]
    return kiem_cay(sach, muc, dong) or []


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--sach", required=True)
    p.add_argument("--thu-muc", type=Path, required=True)
    a = p.parse_args()
    ds = kiem_thu_muc(a.sach, a.thu_muc)
    print("\n".join(ds) if ds else "ĐẠT")
    raise SystemExit(1 if ds else 0)
