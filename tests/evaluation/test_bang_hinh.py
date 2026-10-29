"""Vé DG-17: lệnh `bang-hinh` (Bảng 9–12). Số trong ô khớp số tính tay trên fixture 3 cuốn × 2 chương (xem `bang_hinh_ho_tro`)."""
import json
import re

import numpy as np
import pytest

from danhgia.__main__ import main
from danhgia.bao_cao import cong
from tests.evaluation import bang_hinh_ho_tro as H

SO_VONG = 400
SEED = 20261114


class RefLcg:
    """LCG 64 bit của spec mục 9, viết lại độc lập với `danhgia.thong_ke.lcg`."""

    def __init__(self, seed):
        self.s = seed & (2 ** 64 - 1)

    def chi_so(self, n):
        self.s = (self.s * 6364136223846793005 + 1442695040888963407) & (2 ** 64 - 1)
        return (self.s >> 33) % n


def ref_ci_f1(theo_sach, so_vong=SO_VONG, seed=SEED):
    """CI bootstrap phân cấp của macro F1 theo định nghĩa spec mục 9: cuốn có hoàn lại, rồi chương trong cuốn đã lấy."""
    sach = sorted(theo_sach)

    def f1(ds):
        tp, fp, fn = (sum(d[i] for d in ds) for i in range(3))
        return None if tp + fn == 0 else 2 * tp / (2 * tp + fp + fn)

    rng, mau = RefLcg(seed), []
    for _ in range(so_vong):
        cuon = []
        for _ in sach:
            ds = theo_sach[sach[rng.chi_so(len(sach))]]
            cuon.append(f1([ds[rng.chi_so(len(ds))] for _ in ds]))
        co = [x for x in cuon if x is not None]
        mau.append(sum(co) / len(co))
    return np.percentile(mau, [2.5, 97.5])


def fmt(x, n=3):
    return f"{x:.{n}f}".replace(".", ",")


def chay(tmp_path, capsys, *them, tap="phat_trien", them_manifest=None, ra="ra", co_b5=True):
    argv = H.dung_thu_muc(tmp_path, tap=tap, them_manifest=them_manifest, co_b5=co_b5) + ["--so-vong", str(SO_VONG), "--ra", str(tmp_path / ra), *them]
    ma = main(argv)
    out = capsys.readouterr()
    assert ma == 0, out.err
    return tmp_path / ra, out


def hang(text, nhan):
    for dong in text.splitlines():
        cot = [c.strip() for c in dong.strip().strip("|").split("|")]
        if cot and cot[0] == nhan:
            return cot
    raise AssertionError(f"không có hàng {nhan!r}")


def doc(ra, ten):
    return (ra / ten).read_text(encoding="utf-8")


def so_lieu(ra):
    return json.loads((ra / "so-lieu.json").read_text(encoding="utf-8"))


# ------------------------------------------------------------------------------------------------ Bảng 9


def test_bang_9_o_f1_khop_so_tinh_tay_kem_ci(tmp_path, capsys):
    ra, _ = chay(tmp_path, capsys)
    o = hang(doc(ra, "bang-9.md"), "Hệ chính")
    thap, cao = ref_ci_f1(H.F1_CHINH)
    # macro tay: (0,7 + 0,5 + 0,9) / 3 = 0,7
    assert o[3] == f"0,700 [{fmt(thap)}; {fmt(cao)}]"


def test_bang_9_ci_cua_hieu_cuoi_cung_khop_so_lieu(tmp_path, capsys):
    ra, _ = chay(tmp_path, capsys)
    o = so_lieu(ra)["o"]["chinh|a8.f1_truc_tiep.nghiem"]
    thap, cao = ref_ci_f1(H.F1_CHINH)
    assert o["macro"] == pytest.approx(0.7, abs=1e-12)
    assert (o["thap"], o["cao"]) == pytest.approx((thap, cao), abs=1e-12)


def test_bang_9_cac_cot_con_lai_khop_so_tinh_tay(tmp_path, capsys):
    ra, _ = chay(tmp_path, capsys)
    o = hang(doc(ra, "bang-9.md"), "Hệ chính")
    assert o[1].startswith("0,850 [")          # độ phủ: (0,85 + 0,7 + 1) / 3
    assert o[2].startswith("0,167 [")          # Q6: (0,15 + 0,25 + 0,1) / 3
    assert o[4].startswith("0,883 [")          # bằng chứng: (0,95 + 0,9 + 0,8) / 3
    assert o[5].startswith("20,0 [")           # phút: (10 + 20 + 30) / 3
    assert o[6].startswith("0,01 [")           # USD: (0,004 + 0,004 + 0,008) / 3 = 0,00533


def test_seed_thong_ke_quyet_dinh_ci(tmp_path, capsys):
    # tiền đề: với 30 vòng, seed mặc định và seed 1 cho hai CI khác nhau, nên test này nhạy với việc seed bị bỏ qua
    mac_dinh, khac = ref_ci_f1(H.F1_CHINH, so_vong=30, seed=SEED), ref_ci_f1(H.F1_CHINH, so_vong=30, seed=1)
    assert tuple(mac_dinh) != tuple(khac)
    ra, _ = chay(tmp_path, capsys, "--so-vong", "30")
    o = so_lieu(ra)["o"]["chinh|a8.f1_truc_tiep.nghiem"]
    assert (o["thap"], o["cao"]) == pytest.approx(tuple(mac_dinh), abs=1e-12)
    ra, _ = chay(tmp_path, capsys, "--so-vong", "30", "--seed", "1", ra="ra-seed1")
    o = so_lieu(ra)["o"]["chinh|a8.f1_truc_tiep.nghiem"]
    assert (o["thap"], o["cao"]) == pytest.approx(tuple(khac), abs=1e-12)


def test_chi_lam_tron_luc_hien_thi_khong_lam_tron_tung_cuon_truoc_khi_lay_trung_binh(tmp_path, capsys):
    ra, _ = chay(tmp_path, capsys)
    macro = so_lieu(ra)["o"]["chinh|chi_phi.usd"]["macro"]
    assert macro == pytest.approx(0.016 / 3, abs=1e-15)          # 0,00533, không phải 0,00333 của (0 + 0 + 0,01) / 3
    assert hang(doc(ra, "bang-9.md"), "Hệ chính")[6].startswith("0,01 ")


def test_o_thieu_hien_gach_ngang_khong_bao_gio_0(tmp_path, capsys):
    ra, _ = chay(tmp_path, capsys)
    b5 = hang(doc(ra, "bang-9.md"), "B5 mô hình đọc thẳng")
    assert b5[1] == "—" and b5[2] == "—" and b5[5] == "—" and b5[6] == "—"      # B5 không có dòng độ phủ, Q6 hay chi phí
    b1 = hang(doc(ra, "bang-9.md"), "B1 mục lục")
    assert b1[5] == "—"                                                           # B1 không đo thời gian: null, không phải 0 phút
    assert b1[6].startswith("0,00 ")                                              # nhưng USD là số 0,0 có thật
    for cot in (*b5[1:], *b1[1:]):
        assert cot != "0" and not re.fullmatch(r"0([.,]0+)?", cot)


def test_cuon_mau_so_0_bi_bo_khoi_trung_binh_va_duoc_ghi(tmp_path, capsys):
    ra, _ = chay(tmp_path, capsys)
    b1 = hang(doc(ra, "bang-9.md"), "B1 mục lục")
    assert b1[2].startswith("0,625 [") and "(2/3 cuốn có số)" in b1[2]            # (0,55 + 0,7) / 2
    o = so_lieu(ra)["o"]["b1|a10.q6.nghiem"]
    assert (o["so_cuon_co_so"], o["so_cuon"], o["mau_so"]) == (2, 3, 40)


def test_tran_nguoi_la_f1_giua_hai_sinh_vien_va_cot_khac_khong_ap_dung(tmp_path, capsys):
    ra, _ = chay(tmp_path, capsys)
    t = hang(doc(ra, "bang-9.md"), "Trần người (F1 giữa hai sinh viên)")
    assert t[3].startswith("0,737 [")                                              # (32/36 + 24/32 + 16/28) / 3
    assert [t[1], t[2], t[4], t[5], t[6]] == ["—"] * 5


def test_dai_nhieu_danh_dau_o_co_chenh_nho_hon_dai(tmp_path, capsys):
    ra, _ = chay(tmp_path, capsys)
    text = doc(ra, "bang-9.md")
    sl = so_lieu(ra)["dai_nhieu"]["a8.f1_truc_tiep.nghiem"]
    assert (sl["min"], sl["max"]) == pytest.approx((0.6, 0.8))                    # hệ chính 0,7; nhiễu 0,6 và 0,8
    assert "(trong dải nhiễu)" in hang(text, "B5 mô hình đọc thẳng")[3]            # |0,6 - 0,7| = 0,1 < 0,2
    assert "(trong dải nhiễu)" not in hang(text, "B1 mục lục")[3]                  # |0,1 - 0,7| = 0,6
    assert "(trong dải nhiễu)" not in hang(text, "Hệ chính")[3]
    assert "Dải nhiễu của hệ chính qua 3 lượt" in text


def test_ba_phep_kiem_dinh_va_holm(tmp_path, capsys):
    ra, _ = chay(tmp_path, capsys)
    kd = so_lieu(ra)["kiem_dinh"]
    assert set(kd) == {"q6_chinh_so_b1", "f1_chinh_so_b5", "bang_chung_chinh_so_b5"}
    p = {k: v["p"] for k, v in kd.items()}
    assert all(0 < x <= 1 for x in p.values())
    # Holm tính tay: thứ tự tăng, nhân (3, 2, 1), lấy cực đại tích luỹ, chặn ở 1
    thu_tu = sorted(p, key=lambda k: (p[k], k))
    dung, cuc_dai = {}, 0.0
    for i, k in enumerate(thu_tu):
        cuc_dai = max(cuc_dai, min(1.0, (3 - i) * p[k]))
        dung[k] = cuc_dai
    assert {k: v["p_holm"] for k, v in kd.items()} == pytest.approx(dung)
    assert any(kd[k]["p_holm"] > kd[k]["p"] + 1e-9 for k in kd)                   # Holm có tác dụng: không phải p thô
    text = doc(ra, "bang-9.md")
    assert "p sau Holm" in text


def test_sign_test_theo_cuon_dem_dung_chieu_va_bo_cuon_khong_do_duoc(tmp_path, capsys):
    ra, _ = chay(tmp_path, capsys)
    kd = so_lieu(ra)["kiem_dinh"]
    q6 = kd["q6_chinh_so_b1"]
    assert (q6["thang"], q6["thua"], q6["hoa"]) == (2, 0, 0)                        # Q6 thấp là tốt; cuốn C của B1 không đo được
    assert q6["p_sign"] == pytest.approx(0.5)
    f1 = kd["f1_chinh_so_b5"]
    assert (f1["thang"], f1["thua"]) == (3, 0) and f1["p_sign"] == pytest.approx(0.25)


# ------------------------------------------------------------------------------------------------ Bảng 10, 11, 12


def test_bang_10_hang_a8_co_tran_nguoi_hang_a1_chua_co_so(tmp_path, capsys):
    ra, _ = chay(tmp_path, capsys)
    text = doc(ra, "bang-10.md")
    a8 = hang(text, "A8")
    assert a8[2].startswith("0,700 [") and a8[3].startswith("0,737 [")
    a1 = hang(text, "A1")
    assert a1[2] == "—" and a1[3] == "—"
    a3 = hang(text, "A3")
    assert a3[3] == "—"


def test_bang_11_hieu_ci_suy_bien_hang_khong_chay_va_nhom_oracle(tmp_path, capsys):
    ra, _ = chay(tmp_path, capsys)
    text = doc(ra, "bang-11.md")
    r17 = hang(text, "tắt R17")
    assert r17[1] == "Q6 +0,100 [+0,100; +0,100]"                                   # mọi chương hơn hệ chính đúng 0,1
    assert hang(text, "docling thay bộ đọc nhẹ (3–4 cuốn)")[1] == "— (không chạy)"
    assert hang(text, "hồi quy logistic thay LightGBM (A1 và bước phụ A8)")[1] == "— (không chạy)"
    assert text.index("Thiết lập oracle") < text.index("oracle A8 (khái niệm vàng)") < text.index("oracle A10 (quan hệ vàng)")
    assert text.index("cross-encoder thay LightGBM") < text.index("Thiết lập oracle")
    assert hang(text, "oracle A10 (quan hệ vàng)")[1] == "— (không chạy)"


def _g5():
    def nguoi(n_chinh, tb_chinh, so_sanh):
        return {"rubric": {"chinh": {"n": n_chinh, "trung_binh": tb_chinh}, "b1": {"n": 10, "trung_binh": 3.0}, "b5": {"n": 10, "trung_binh": 4.0}},
                "so_sanh": so_sanh}
    return {"theo_nguoi": {
        "S1": nguoi(10, 5.0, {"chinh~b1": {"chinh": 6, "b1": 2, "hoa": 2}, "chinh~b5": {"chinh": 5, "b5": 3, "hoa": 2}, "b1~b5": {"b1": 2, "b5": 6, "hoa": 2}}),
        "S2": nguoi(30, 6.0, {"chinh~b1": {"chinh": 4, "b1": 4, "hoa": 2}, "chinh~b5": {"chinh": 4, "b5": 4, "hoa": 2}, "b1~b5": {"b1": 3, "b5": 5, "hoa": 2}}),
    }}


def test_bang_12_rubric_theo_trong_so_va_ti_le_thang_theo_cap(tmp_path, capsys):
    ra, _ = chay(tmp_path, capsys, "--g5", H.ghi_json(tmp_path / "g5.json", _g5()))
    text = doc(ra, "bang-12.md")
    rb = hang(text, "Điểm rubric trung bình (thang 7)")
    assert rb[1] == "5,75"                                                          # (10 × 5 + 30 × 6) / 40, không phải trung bình hai người 5,5
    th = hang(text, "Tỉ lệ thắng khi so cặp (tính trên các cặp có hệ đó)")
    assert th[1].startswith("0,475 [") and th[1].endswith("(19/40)")                # chinh thắng 6 + 5 + 4 + 4 trên 40 lượt có chinh
    assert th[2].startswith("0,275 [") and th[2].endswith("(11/40)")
    assert th[3].startswith("0,450 [") and th[3].endswith("(18/40)")
    assert "thăm dò" in text.lower()
    # Từng cặp: chinh~b1 gộp hai người, thắng 10, b1 thắng 6, hoà 4, tỉ lệ 10/20
    cap = hang(text, "Hệ chính ~ B1 mục lục")
    assert cap[1:] == ["10", "6", "4", "0,500"]


def test_bang_12_khong_co_g5_thi_gach_ngang(tmp_path, capsys):
    ra, _ = chay(tmp_path, capsys)
    text = doc(ra, "bang-12.md")
    assert hang(text, "Điểm rubric trung bình (thang 7)")[1:] == ["—", "—", "—"]


def test_ten_bang_nam_tren_bang(tmp_path, capsys):
    ra, _ = chay(tmp_path, capsys)
    for so_bang, nhan in ((9, "Bảng 9. Kết quả đầu-cuối trên 3 giáo trình"), (10, "Bảng 10. Kết quả từng khâu"),
                          (11, "Bảng 11. Thí nghiệm bỏ hoặc thay bộ phận"), (12, "Bảng 12. Đánh giá của người học")):
        dong = doc(ra, f"bang-{so_bang}.md").splitlines()
        assert dong[0].startswith(nhan) and dong[2].startswith("|")


def test_b5a_duoc_doi_ten_thanh_b5_va_nhieu_he_b5_phai_chi_dinh(tmp_path, capsys):
    rows = [{**r, "he": "b5a"} for r in H.dong_b5()]
    duong = H.ghi_json(tmp_path / "b5a.json", rows)
    ra, _ = chay(tmp_path, capsys, "--dong", H.ghi_json(tmp_path / "dong2.json", H.dong_he_chinh() + H.dong_b1()), duong, ra="ra5", co_b5=False)
    assert hang(doc(ra, "bang-9.md"), "B5 mô hình đọc thẳng")[3].startswith("0,600 [")
    rows_b = [{**r, "he": "b5b"} for r in H.dong_b5()]
    with pytest.raises(ValueError, match="nhiều hệ B5"):
        main(H.dung_thu_muc(tmp_path, co_b5=False) + ["--dong", H.ghi_json(tmp_path / "hai.json", rows + rows_b), "--ra", str(tmp_path / "x")])


# ------------------------------------------------------------------------------------------------ Cổng allowlist


def test_man_hinh_chi_in_khoa_allowlist_voi_gia_tri_so_bool_null(tmp_path, capsys):
    _, out = chay(tmp_path, capsys)
    dong = out.out.strip().splitlines()
    assert dong
    for d in dong:
        assert re.fullmatch(r"[a-z0-9_]+ (true|false|null|-?[0-9.]+(e-?[0-9]+)?)", d), d
    assert "tap_thu false" in dong and "so_cuon 3" in dong


def test_cong_chan_khoa_la_gia_tri_chuoi_dict_va_khong_in_gi(capsys):
    for xau in ({"x": 1}, {"tap_thu": SECRET_CHUOI}, {"tap_thu": {"a": SECRET_CHUOI}}, {"tap_thu": [1]}, {"tap_thu": float("nan")}):
        with pytest.raises(ValueError) as e:
            cong.in_allowlist(xau, ("tap_thu",))
        assert SECRET_CHUOI not in str(e.value)
    # khoá lạ: đừng in cả khoá hợp lệ đứng trước nó
    with pytest.raises(ValueError):
        cong.in_allowlist({"tap_thu": True, SECRET_CHUOI: 1}, ("tap_thu",))
    assert capsys.readouterr().out == ""


SECRET_CHUOI = H.SECRET


def test_cong_in_so_bool_null_theo_thu_tu():
    dong = cong.dong_allowlist({"a": 1, "b": 0.5, "c": True, "d": None}, ("a", "b", "c", "d"))
    assert dong == ["a 1", "b 0.5", "c true", "d null"]
