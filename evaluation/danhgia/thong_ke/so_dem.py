"""Bảng số đếm theo chương → thước theo cuốn và trung bình macro.

Mỗi dòng: `{he, ma_sach, chuong, thuoc, kieu}`, với `kieu = "ti_le"` thêm `tu`, `mau`; với `kieu = "f1"` thêm `tp`, `fp`, `fn`.
Thước của một cuốn tính lại từ tổng số đếm các chương, không lấy trung bình các chương. Mẫu số 0 cho `None`: chưa đo được, không phải 0.
"""
from collections import defaultdict

_TRUONG = {"ti_le": ("tu", "mau"), "f1": ("tp", "fp", "fn")}


def kieu_cua(rows, thuoc):
    kieu = {row["kieu"] for row in rows if row["thuoc"] == thuoc}
    if len(kieu) != 1:
        raise ValueError(f"thước {thuoc!r} phải có đúng một kiểu, đang có {sorted(kieu)}")
    (ket,) = kieu
    if ket not in _TRUONG:
        raise ValueError(f"kiểu không biết: {ket!r}")
    return ket


def gia_tri(kieu, dem):
    if kieu == "ti_le":
        tu, mau = dem
        return tu / mau if mau else None
    tp, fp, fn = dem
    mau = 2 * tp + fp + fn
    return 2 * tp / mau if mau else None


def cong(dem_a, dem_b):
    return tuple(x + y for x, y in zip(dem_a, dem_b))


def dem_theo_chuong(rows, he, thuoc):
    """`{ma_sach: {chuong: số đếm}}` của một hệ, một thước."""
    kieu = kieu_cua(rows, thuoc)
    ket = defaultdict(dict)
    for row in rows:
        if row["he"] != he or row["thuoc"] != thuoc:
            continue
        if row["chuong"] in ket[row["ma_sach"]]:
            raise ValueError(f"trùng dòng: {he}, {row['ma_sach']}, {row['chuong']}, {thuoc}")
        ket[row["ma_sach"]][row["chuong"]] = tuple(row[truong] for truong in _TRUONG[kieu])
    return kieu, dict(ket)


def gia_tri_cuon(kieu, cac_chuong):
    tong = None
    for dem in cac_chuong:
        tong = dem if tong is None else cong(tong, dem)
    return gia_tri(kieu, tong) if tong is not None else None


def trung_binh_macro(cac_gia_tri):
    co = [g for g in cac_gia_tri if g is not None]
    return sum(co) / len(co) if co else None


def thuoc_theo_cuon(rows, *, he, thuoc):
    kieu, theo_sach = dem_theo_chuong(rows, he, thuoc)
    theo_cuon = {sach: gia_tri_cuon(kieu, chuong.values()) for sach, chuong in sorted(theo_sach.items())}
    return {"kieu": kieu, "theo_cuon": theo_cuon, "macro": trung_binh_macro(theo_cuon.values())}
