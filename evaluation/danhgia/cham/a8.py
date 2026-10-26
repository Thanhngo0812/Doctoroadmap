"""A8: P/R/F1 cạnh trực tiếp và bao đóng, tính bằng số đếm tp/fp/fn trong không gian vàng (xem `can`).

Hai hồ sơ, mỗi hồ sơ khớp một bộ chấm cũ để đối chiếu:
- `spec` (mặc định, **số báo cáo**, theo spec mục 8): bao đóng tính **trước** khi lọc phạm vi; phạm vi chỉ lọc theo **đích**;
  như `score_edges` của `domain/gold_scoring.py`;
- `giu_lai_v3` (**hồ sơ lịch sử**, chỉ để so với số v3 và T-01 đã báo, không dùng làm số báo cáo): máy rút gọn bắc cầu,
  lọc **hai đầu** thuộc đích vàng, **rồi** mới đóng; như `grade` của bộ chấm tập giữ lại v3.
"""
from __future__ import annotations

from .do_thi import dong_bao

HO_SO = ("spec", "giu_lai_v3")
MEM = ("cung", "ca_hai")


def canh_may(hd, *, mem, bo_qua=False):
    """Cặp node `(nguon, dich)` của máy theo cạnh cứng (hoặc cả mềm), qua bản đồ danh tính, bỏ tự nối."""
    danh_tinh = hd["ban_do_danh_tinh"]
    ket_qua = set()
    for canh in hd["canh"]:
        if canh["mem"] and mem == "cung":
            continue
        if canh["bo_qua"] and not bo_qua:
            continue
        a, b = danh_tinh.get(canh["nguon"], canh["nguon"]), danh_tinh.get(canh["dich"], canh["dich"])
        if a != b:
            ket_qua.add((a, b))
    return ket_qua


def _dem(du_doan, vang):
    tp = len(du_doan & vang)
    return tp, len(du_doan - vang), len(vang - du_doan)


def f1_theo_chuong(du_doan, du_doan_rut_gon, vang_toan_cuon, dich_chuong, *, ho_so="spec", hien_dien=None):
    """Trả về `{"truc_tiep": (tp,fp,fn), "bao_dong": (tp,fp,fn)}` cho một chương.

    Mọi tập cạnh đều là cặp khái niệm vàng. `du_doan` là cạnh cứng của máy đã ánh xạ; `du_doan_rut_gon` là cạnh cứng đã rút
    gọn bắc cầu trong không gian node rồi mới ánh xạ (chỉ hồ sơ `giu_lai_v3` dùng).
    """
    if ho_so == "spec":
        pham_vi = set(dich_chuong)
        loc = lambda canh: {(a, b) for a, b in canh if b in pham_vi}  # noqa: E731
        return {
            "truc_tiep": _dem(loc(du_doan), loc(vang_toan_cuon)),
            "bao_dong": _dem(loc(dong_bao(du_doan)), loc(dong_bao(vang_toan_cuon))),
        }
    if ho_so == "giu_lai_v3":
        pham_vi = set(dich_chuong) & set(hien_dien)
        loc = lambda canh: {(a, b) for a, b in canh if a in pham_vi and b in pham_vi}  # noqa: E731
        may, vang = loc(du_doan_rut_gon), loc(vang_toan_cuon)
        return {"truc_tiep": _dem(may, vang), "bao_dong": _dem(dong_bao(may), dong_bao(vang))}
    raise ValueError(f"hồ sơ phải là một trong {HO_SO}, không phải {ho_so!r}")
