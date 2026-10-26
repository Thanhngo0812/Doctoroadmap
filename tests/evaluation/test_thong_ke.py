"""DG-05: thống kê và đồng thuận. Số đáp án tính tay hoặc lấy từ nguồn gốc ghi ở từng test."""
import ast
from pathlib import Path

import pytest

from danhgia.thong_ke import (
    bootstrap_phan_cap,
    cohen_kappa,
    hoan_vi_ghep_cap,
    holm,
    krippendorff_alpha,
    mo_phong_cong_suat,
    psa,
    sign_test,
    thuoc_theo_cuon,
)


def _f1(he, sach, chuong, tp, fp, fn, thuoc="f1_quan_he"):
    return {"he": he, "ma_sach": sach, "chuong": chuong, "thuoc": thuoc, "kieu": "f1", "tp": tp, "fp": fp, "fn": fn}


def _ti_le(he, sach, chuong, tu, mau, thuoc="q6"):
    return {"he": he, "ma_sach": sach, "chuong": chuong, "thuoc": thuoc, "kieu": "ti_le", "tu": tu, "mau": mau}


# --- thước theo cuốn ---------------------------------------------------------------------------------------------

def test_thuoc_theo_cuon_cong_so_dem_cac_chuong_roi_moi_tinh_va_trung_binh_macro():
    rows = [
        _f1("he", "s1", "c1", tp=2, fp=0, fn=2),   # cộng hai chương: tp 3, fp 1, fn 2 → F1 = 6/9
        _f1("he", "s1", "c2", tp=1, fp=1, fn=0),
        _f1("he", "s2", "c1", tp=1, fp=1, fn=1),   # F1 = 2/4
    ]
    ket_qua = thuoc_theo_cuon(rows, he="he", thuoc="f1_quan_he")
    assert ket_qua["theo_cuon"] == {"s1": pytest.approx(6 / 9), "s2": pytest.approx(0.5)}
    assert ket_qua["macro"] == pytest.approx((6 / 9 + 0.5) / 2)


def test_mau_so_0_tra_none_va_khong_keo_trung_binh_ve_0():
    rows = [_ti_le("he", "s1", "c1", tu=1, mau=4), _ti_le("he", "s2", "c1", tu=0, mau=0)]
    ket_qua = thuoc_theo_cuon(rows, he="he", thuoc="q6")
    assert ket_qua["theo_cuon"] == {"s1": pytest.approx(0.25), "s2": None}
    assert ket_qua["macro"] == pytest.approx(0.25)


def test_dong_khac_kieu_trong_cung_thuoc_bi_tu_choi():
    rows = [_f1("he", "s1", "c1", 1, 0, 0, thuoc="x"), _ti_le("he", "s1", "c2", 1, 1, thuoc="x")]
    with pytest.raises(ValueError):
        thuoc_theo_cuon(rows, he="he", thuoc="x")


# --- bootstrap phân cấp -------------------------------------------------------------------------------------------

def _hai_cuon_lech():
    # s1 luôn F1 = 1, s2 luôn F1 = 0: khoảng phải trải từ 0 tới 1 vì có vòng lấy toàn s1 hoặc toàn s2.
    return [_f1("he", "s1", f"c{i}", 3, 0, 0) for i in range(3)] + [_f1("he", "s2", f"c{i}", 0, 3, 3) for i in range(3)]


def test_bootstrap_tat_dinh_theo_seed():
    rows = _hai_cuon_lech()
    lan_1 = bootstrap_phan_cap(rows, he="he", thuoc="f1_quan_he", so_vong=500, seed=7)
    lan_2 = bootstrap_phan_cap(rows, he="he", thuoc="f1_quan_he", so_vong=500, seed=7)
    assert lan_1 == lan_2


def test_bootstrap_lay_lai_theo_cuon_khong_theo_chuong():
    # Nếu lấy lại theo chương gộp chung (sai), cực trị 0 và 1 gần như không xuất hiện với 6 chương; lấy theo cuốn thì
    # mỗi vòng có xác suất 1/4 rơi vào toàn s1 hoặc toàn s2.
    ket_qua = bootstrap_phan_cap(_hai_cuon_lech(), he="he", thuoc="f1_quan_he", so_vong=2000, seed=1)
    assert ket_qua["macro"] == pytest.approx(0.5)
    assert ket_qua["thap"] == pytest.approx(0.0)
    assert ket_qua["cao"] == pytest.approx(1.0)


def test_bootstrap_lay_lai_chuong_ben_trong_cuon():
    # Một cuốn duy nhất: lấy lại cuốn không đổi gì, nên mọi biến thiên phải đến từ tầng chương.
    rows = [_f1("he", "s1", "c1", 4, 0, 0), _f1("he", "s1", "c2", 0, 4, 4)]
    ket_qua = bootstrap_phan_cap(rows, he="he", thuoc="f1_quan_he", so_vong=2000, seed=3)
    assert ket_qua["thap"] == pytest.approx(0.0)
    assert ket_qua["cao"] == pytest.approx(1.0)


# --- hoán vị ghép cặp ---------------------------------------------------------------------------------------------

def _hai_he(hieu):
    rows = []
    for sach in ("s1", "s2", "s3", "s4"):
        for chuong in ("c1", "c2", "c3"):
            rows.append(_f1("A", sach, chuong, 5 + hieu, 5 - hieu, 5 - hieu))
            rows.append(_f1("B", sach, chuong, 5, 5, 5))
    return rows


def test_hoan_vi_hai_he_giong_het_cho_p_bang_1():
    ket_qua = hoan_vi_ghep_cap(_hai_he(0), "A", "B", thuoc="f1_quan_he", so_lan=500, seed=2)
    assert ket_qua["hieu"] == pytest.approx(0.0)
    assert ket_qua["p"] == pytest.approx(1.0)


def test_hoan_vi_hai_he_khac_xa_o_moi_chuong_cho_p_rat_nho():
    ket_qua = hoan_vi_ghep_cap(_hai_he(4), "A", "B", thuoc="f1_quan_he", so_lan=2000, seed=2)
    assert ket_qua["hieu"] > 0.3
    assert ket_qua["p"] < 0.001


def test_hoan_vi_phan_tang_nhan_ra_loi_the_nho_nhung_deu_giua_cac_cuon_rat_khac_nhau():
    # Mỗi chương A hơn B đúng một tp, trong khi mức F1 giữa các cuốn chênh rất lớn. Ghép cặp trong chương thì phương sai
    # giữa cuốn triệt tiêu và p rất nhỏ; nếu hoán vị phá ghép cặp (trộn A của chương này với B của chương khác) thì
    # phương sai giữa cuốn nuốt mất lợi thế và p lớn.
    rows = []
    for i, muc in enumerate((1, 3, 6, 10, 15, 21, 28, 36)):
        for chuong in ("c1", "c2", "c3"):
            rows.append(_f1("A", f"s{i}", chuong, muc + 1, 40 - muc, 40 - muc))
            rows.append(_f1("B", f"s{i}", chuong, muc, 40 - muc, 40 - muc))
    ket_qua = hoan_vi_ghep_cap(rows, "A", "B", thuoc="f1_quan_he", so_lan=2000, seed=4)
    assert ket_qua["p"] < 0.01


def test_hoan_vi_chi_doi_nhan_trong_cung_chuong():
    # A hơn B ở s1, kém B ở s2 đúng bằng nhau: hiệu macro 0, p = 1. Nếu hoán vị trộn chương giữa các cuốn (sai) thì
    # vẫn ra p = 1 ở đây, nên test kèm kiểm tra: mỗi chương phải có đủ hai hệ, thiếu thì báo lỗi.
    rows = [_f1("A", "s1", "c1", 4, 0, 0), _f1("B", "s1", "c1", 0, 4, 4)]
    with pytest.raises(ValueError):
        hoan_vi_ghep_cap(rows + [_f1("A", "s2", "c1", 1, 0, 0)], "A", "B", thuoc="f1_quan_he", so_lan=10, seed=1)


# --- sign test, Holm --------------------------------------------------------------------------------------------

def test_sign_test_khop_bang_nhi_thuc():
    assert sign_test(8, 0) == pytest.approx(2 / 256)
    assert sign_test(7, 1) == pytest.approx(18 / 256)
    assert sign_test(4, 4) == pytest.approx(1.0)
    assert sign_test(0, 0) is None


def test_holm_vi_du_sach_giao_khoa():
    # Holm (1979): p sắp tăng dần nhân với (m - i + 1), rồi lấy cực đại tích luỹ; m = 3.
    ket_qua = holm({"a": 0.01, "b": 0.04, "c": 0.03})
    assert ket_qua["a"] == pytest.approx(0.03)
    assert ket_qua["c"] == pytest.approx(0.06)
    assert ket_qua["b"] == pytest.approx(0.06)   # 0,04 × 1 = 0,04 nhưng không được nhỏ hơn bước trước (0,06)


def test_holm_khong_vuot_1():
    assert holm({"a": 0.6, "b": 0.7})["b"] == pytest.approx(1.0)


# --- đồng thuận -------------------------------------------------------------------------------------------------

def test_psa_bang_f1_giua_hai_nguoi():
    # Hripcsak & Rothschild 2005: PSA = 2a / (2a + b + c), bằng F1 khi lấy một người làm chuẩn.
    assert psa(20, 33, 34) == pytest.approx(40 / 107)
    assert psa(0, 0, 0) is None


def test_cohen_kappa_vi_du_tinh_tay():
    a = ["x", "x", "y", "y", "x", "y", "x", "x", "y", "x"]
    b = ["x", "y", "y", "y", "x", "y", "x", "x", "x", "x"]
    # po = 8/10; biên: A có 6x/4y, B có 6x/4y → pe = 0,36 + 0,16 = 0,52; κ = (0,8 - 0,52) / 0,48.
    ket_qua = cohen_kappa(a, b)
    assert ket_qua["dong_y"] == pytest.approx(0.8)
    assert ket_qua["kappa"] == pytest.approx(0.28 / 0.48)


def test_cohen_kappa_mot_lop_duy_nhat_tra_none():
    assert cohen_kappa(["x", "x"], ["x", "x"])["kappa"] is None


# Krippendorff (2011), "Computing Krippendorff's Alpha-Reliability", ví dụ 4 người × 12 đơn vị có dữ liệu thiếu.
_KRIPPENDORFF_2011 = [
    [1, 2, 3, 3, 2, 1, 4, 1, 2, None, None, None],
    [1, 2, 3, 3, 2, 2, 4, 1, 2, 5, None, 3],
    [None, 3, 3, 3, 2, 3, 4, 2, 2, 5, 1, None],
    [1, 2, 3, 3, 2, 4, 4, 1, 2, 5, 1, None],
]


@pytest.mark.parametrize("muc_do, ky_vong", [("danh_nghia", 0.743), ("thu_bac", 0.815), ("khoang", 0.849)])
def test_krippendorff_alpha_khop_vi_du_goc(muc_do, ky_vong):
    assert krippendorff_alpha(_KRIPPENDORFF_2011, muc_do=muc_do) == pytest.approx(ky_vong, abs=5e-4)


def test_krippendorff_alpha_dong_y_hoan_toan_bang_1():
    assert krippendorff_alpha([[1, 2, 3, 4], [1, 2, 3, 4]], muc_do="thu_bac") == pytest.approx(1.0)


# --- công suất ----------------------------------------------------------------------------------------------------

def test_mo_phong_cong_suat_tang_theo_hieu_ung_va_tat_dinh():
    hieu_chuong = [0.1, -0.05, 0.2, 0.0, -0.1, 0.15, 0.05, -0.02, 0.08]
    nho = mo_phong_cong_suat(hieu_chuong, hieu_ung=0.0, so_cuon=8, so_chuong=3, so_mo_phong=200, so_hoan_vi=200, seed=5)
    lon = mo_phong_cong_suat(hieu_chuong, hieu_ung=0.3, so_cuon=8, so_chuong=3, so_mo_phong=200, so_hoan_vi=200, seed=5)
    assert nho["cong_suat"] < 0.2          # hiệu ứng 0: tỉ lệ bác bỏ gần alpha
    assert lon["cong_suat"] > 0.9
    assert mo_phong_cong_suat(hieu_chuong, hieu_ung=0.3, so_cuon=8, so_chuong=3, so_mo_phong=200, so_hoan_vi=200,
                              seed=5) == lon


# --- kiến trúc ----------------------------------------------------------------------------------------------------

def test_thong_ke_khong_nhap_doc2roadmap():
    goc = Path(__file__).resolve().parents[2] / "evaluation" / "danhgia" / "thong_ke"
    for tep in goc.rglob("*.py"):
        cay = ast.parse(tep.read_text(encoding="utf-8"))
        for nut in ast.walk(cay):
            ten = []
            if isinstance(nut, ast.Import):
                ten = [a.name for a in nut.names]
            elif isinstance(nut, ast.ImportFrom) and nut.module:
                ten = [nut.module]
            assert not any(t.split(".")[0] == "doc2roadmap" for t in ten), tep
