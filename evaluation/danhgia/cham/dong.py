"""Dòng số đếm theo chương (định dạng DG-05 dùng) và phép gộp lên cuốn, lên trung bình macro.

Mỗi dòng có `{he, ma_sach, chuong, thuoc, kieu}` cộng:
- `ti_le`: `tu`, `mau`;
- `f1`: `tp`, `fp`, `fn`;
- `trung_binh`: `tong`, `n` (trung bình của các tỉ lệ theo từng đích, ví dụ Q7);
- `dem`: `gia_tri`.
Mẫu số 0 cho `None`, không bao giờ cho 0.
"""
from __future__ import annotations


def _goc(he, ma_sach, chuong, thuoc, kieu):
    return {"he": he, "ma_sach": ma_sach, "chuong": chuong, "thuoc": thuoc, "kieu": kieu}


def ti_le(he, ma_sach, chuong, thuoc, tu, mau):
    return {**_goc(he, ma_sach, chuong, thuoc, "ti_le"), "tu": tu, "mau": mau}


def f1(he, ma_sach, chuong, thuoc, tp, fp, fn):
    return {**_goc(he, ma_sach, chuong, thuoc, "f1"), "tp": tp, "fp": fp, "fn": fn}


def trung_binh(he, ma_sach, chuong, thuoc, tong, n):
    return {**_goc(he, ma_sach, chuong, thuoc, "trung_binh"), "tong": tong, "n": n}


def dem(he, ma_sach, chuong, thuoc, gia_tri):
    return {**_goc(he, ma_sach, chuong, thuoc, "dem"), "gia_tri": gia_tri}


def _chia(tu, mau):
    return tu / mau if mau else None


def chi_so_f1(row):
    """(precision, recall, f1); phần nào có mẫu số 0 hoặc P+R=0 thì None."""
    p, r = _chia(row["tp"], row["tp"] + row["fp"]), _chia(row["tp"], row["tp"] + row["fn"])
    if p is None or r is None or p + r == 0:
        return p, r, None
    return p, r, 2 * p * r / (p + r)


def gia_tri(row):
    kieu = row["kieu"]
    if kieu == "ti_le":
        return _chia(row["tu"], row["mau"])
    if kieu == "f1":
        return chi_so_f1(row)[2]
    if kieu == "trung_binh":
        return _chia(row["tong"], row["n"])
    return row["gia_tri"]


_TRUONG_CONG = {"ti_le": ("tu", "mau"), "f1": ("tp", "fp", "fn"), "trung_binh": ("tong", "n"), "dem": ("gia_tri",)}


def gop_cuon(rows):
    """Thước theo cuốn = cộng số đếm của các chương, tính lại từ tổng (không lấy trung bình các tỉ lệ)."""
    nhom = {}
    for row in rows:
        khoa = (row["he"], row["ma_sach"], row["thuoc"], row["kieu"])
        if khoa not in nhom:
            nhom[khoa] = {**_goc(*khoa[:3], "cuon", khoa[3]), **dict.fromkeys(_TRUONG_CONG[row["kieu"]], 0)}
        for truong in _TRUONG_CONG[row["kieu"]]:
            nhom[khoa][truong] += row[truong]
    return list(nhom.values())


def trung_binh_macro(rows_cuon):
    """Trung bình macro theo cuốn của từng thước; cuốn có giá trị None (mẫu số 0) bị bỏ khỏi trung bình và được đếm riêng."""
    nhom = {}
    for row in rows_cuon:
        nhom.setdefault((row["he"], row["thuoc"]), []).append(gia_tri(row))
    ket_qua = {}
    for (he, thuoc), gia in nhom.items():
        co = [g for g in gia if g is not None]
        ket_qua[(he, thuoc)] = {"gia_tri": sum(co) / len(co) if co else None, "so_cuon_co_so": len(co),
                                "so_cuon": len(gia)}
    return ket_qua
