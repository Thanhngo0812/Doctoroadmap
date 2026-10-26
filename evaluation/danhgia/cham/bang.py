"""Lõi chấm A8 và A10: hợp đồng + G3 + G4 + bảng căn -> bảng số đếm theo chương. Thuần, không đọc kho, không gọi mô hình."""
from __future__ import annotations

from . import a8, a10, dong
from .can import MUC_CAN, doc_vang

__all__ = ["cham", "MUC_CAN"]


def _hien_dien(hd):
    return {k["ma"] for k in hd["khai_niem"] if not k["bi_loai"]}


def cham(hd, g3, g4, can, *, ma_sach=None, ho_so="spec", mem="cung", vang="chinh"):
    """Trả danh sách dòng số đếm (xem `dong`).

    Với mỗi mức căn (`nghiem`, `noi`) và mỗi chương của G3: F1 trực tiếp và bao đóng, Q6, Q7 (cạnh cứng), Q7 tính cả
    cạnh mềm, Q7b, tỉ lệ đích trọn, và số cạnh vàng bị tự nối. Cộng, cho cả cuốn: số chu trình và số thành phần liên thông.
    Hệ không có lộ trình (`lo_trinh` là null) thì không có dòng A9/A10.
    """
    if ho_so not in a8.HO_SO:
        raise ValueError(f"hồ sơ phải là một trong {a8.HO_SO}, không phải {ho_so!r}")
    if mem not in a8.MEM:
        raise ValueError(f"mem phải là một trong {a8.MEM}, không phải {mem!r}")
    ma_sach = ma_sach or g3["ma_sach"]
    for ten, tep in (("G3", g3), ("G4", g4), ("bảng căn", can)):
        if tep["ma_sach"] != ma_sach:
            raise ValueError(f"{ten} thuộc sách {tep['ma_sach']!r}, không phải {ma_sach!r}")
    he = hd["dinh_danh"]["he"]
    chuong_co = list(dict.fromkeys(k["chuong"] for k in g3["khai_niem"]))
    lo_trinh = hd["lo_trinh"]
    hang = a10.hang_vi_tri(lo_trinh["day_hoc"]) if lo_trinh is not None else None
    mem_f1 = "cung" if ho_so == "giu_lai_v3" else mem
    du_doan_f1 = a8.canh_may(hd, mem=mem_f1)
    may_cung, may_ca = a8.canh_may(hd, mem="cung", bo_qua=True), a8.canh_may(hd, mem="ca_hai", bo_qua=True)
    hien_dien = _hien_dien(hd)
    rows = []
    for muc in MUC_CAN:
        v = doc_vang(g3, g4, can, muc, hd["ban_do_danh_tinh"], vang=vang)
        vang_cuon = set().union(*v["cap"].values()) if v["cap"] else set()
        for chuong in chuong_co:
            dich = v["dich_theo_chuong"][chuong]
            ket_qua = a8.f1_theo_chuong(du_doan_f1, vang_cuon, dich, ho_so=ho_so, hien_dien=hien_dien)
            rows.append(dong.f1(he, ma_sach, chuong, f"a8.f1_truc_tiep.{muc}", *ket_qua["truc_tiep"]))
            rows.append(dong.f1(he, ma_sach, chuong, f"a8.f1_bao_dong.{muc}", *ket_qua["bao_dong"]))
            rows.append(dong.dem(he, ma_sach, chuong, f"can.tu_noi.{muc}", v["tu_noi"][chuong]))
            if hang is None:
                continue
            cap_chuong = {(a, b) for a, b in vang_cuon if b in dich}
            rows.append(dong.ti_le(he, ma_sach, chuong, f"a10.q6.{muc}", *a10.q6(cap_chuong, hang)))
            tong, n, tron = a10.q7(vang_cuon, may_cung, dich, hang)
            rows.append(dong.trung_binh(he, ma_sach, chuong, f"a10.q7.{muc}", tong, n))
            rows.append(dong.ti_le(he, ma_sach, chuong, f"a10.q7_tron.{muc}", tron, n))
            tong, n, _ = a10.q7(vang_cuon, may_ca, dich, hang)
            rows.append(dong.trung_binh(he, ma_sach, chuong, f"a10.q7_ca_mem.{muc}", tong, n))
            tong, n = a10.q7b(vang_cuon, may_cung, dich, hang)
            rows.append(dong.trung_binh(he, ma_sach, chuong, f"a10.q7b.{muc}", tong, n))
    if hang is not None:
        chu_trinh, thanh_phan = a10.cau_truc_do_thi(may_cung, lo_trinh["day_hoc"])
        rows.append(dong.dem(he, ma_sach, "toan_sach", "a10.so_chu_trinh", chu_trinh))
        rows.append(dong.dem(he, ma_sach, "toan_sach", "a10.so_thanh_phan", thanh_phan))
    return rows
