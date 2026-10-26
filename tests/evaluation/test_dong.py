"""Gộp số đếm theo chương lên cuốn, rồi trung bình macro theo cuốn."""
import pytest

from danhgia.cham import dong


def test_thuoc_theo_cuon_tinh_lai_tu_tong_so_dem_khong_trung_binh_ti_le():
    c1 = dong.ti_le("h", "A", "c1", "q6", 1, 2)
    c2 = dong.ti_le("h", "A", "c2", "q6", 3, 4)
    cuon = dong.gop_cuon([c1, c2])
    assert len(cuon) == 1 and (cuon[0]["tu"], cuon[0]["mau"], cuon[0]["chuong"]) == (4, 6)[:2] + ("cuon",)
    assert dong.gia_tri(cuon[0]) == pytest.approx(4 / 6)  # không phải (0,5 + 0,75) / 2 = 0,625


def test_f1_theo_cuon_cong_tp_fp_fn():
    cuon = dong.gop_cuon([dong.f1("h", "A", "c1", "f1", 2, 1, 1), dong.f1("h", "A", "c2", "f1", 1, 1, 1)])[0]
    assert (cuon["tp"], cuon["fp"], cuon["fn"]) == (3, 2, 2)
    p, r, f = dong.chi_so_f1(cuon)
    assert (p, r) == (pytest.approx(0.6), pytest.approx(0.6)) and f == pytest.approx(0.6)


def test_f1_tp_bang_0_co_vang_thi_f1_la_0_khong_phai_none():
    # khác bộ chấm cũ CÓ CHỦ Ý: cũ cho None khi P+R=0, làm cuốn sai hết bị loại khỏi trung bình macro
    assert dong.chi_so_f1(dong.f1("h", "A", "c1", "f1", 0, 2, 3)) == (0.0, 0.0, 0.0)


def test_f1_khong_co_canh_vang_thi_f1_va_recall_la_none():
    p, r, f = dong.chi_so_f1(dong.f1("h", "A", "c1", "f1", 0, 2, 0))
    assert (p, r, f) == (0.0, None, None)
    assert dong.gia_tri(dong.f1("h", "A", "c1", "f1", 0, 0, 0)) is None


def test_f1_khong_du_doan_nhung_co_vang_thi_f1_la_0_precision_none():
    p, r, f = dong.chi_so_f1(dong.f1("h", "A", "c1", "f1", 0, 0, 3))
    assert (p, r, f) == (None, 0.0, 0.0)


def test_f1_binh_thuong_khong_doi():
    assert dong.gia_tri(dong.f1("h", "A", "c1", "f1", 3, 1, 1)) == pytest.approx(0.75)


def test_cuon_sai_het_van_vao_trung_binh_macro_voi_0():
    rows = [dong.f1("h", "A", "cuon", "f1", 3, 1, 1), dong.f1("h", "B", "cuon", "f1", 0, 4, 4)]
    macro = dong.trung_binh_macro(rows)[("h", "f1")]
    assert macro["gia_tri"] == pytest.approx(0.375) and macro["so_cuon_co_so"] == 2


def test_ti_le_mau_so_khong_la_none():
    assert dong.gia_tri(dong.ti_le("h", "A", "c1", "q6", 0, 0)) is None


def test_trung_binh_macro_theo_cuon_bo_cuon_none_va_dem_rieng():
    rows = [dong.ti_le("h", "A", "cuon", "q6", 1, 2), dong.ti_le("h", "B", "cuon", "q6", 3, 4),
            dong.ti_le("h", "C", "cuon", "q6", 0, 0)]
    macro = dong.trung_binh_macro(rows)[("h", "q6")]
    assert macro["gia_tri"] == pytest.approx(0.625) and macro["so_cuon_co_so"] == 2 and macro["so_cuon"] == 3


def test_macro_khong_co_cuon_nao_xac_dinh_la_none():
    macro = dong.trung_binh_macro([dong.ti_le("h", "A", "cuon", "q6", 0, 0)])[("h", "q6")]
    assert macro["gia_tri"] is None
