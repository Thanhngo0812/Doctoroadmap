"""DG-20: phần thuần của việc chọn lại siêu tham số (chia LOBO, dừng sớm theo seed, luật một sai số chuẩn, so sánh cặp)."""
import math
import statistics

import pytest

from danhgia.hoc_lai.chia import chia_dong, chon_dung_som, lobo, vong_ngoai
from danhgia.hoc_lai.chon import chon_ap_cao_nhat, chon_mot_se
from danhgia.hoc_lai.so_sanh import hieu_theo_cuon, so_sanh_cap

CUON = [f"d01-{i:02d}" for i in range(1, 17)]


def test_lobo_moi_cuon_de_ra_dung_mot_lan():
    chia = lobo(CUON)
    assert [de_ra for de_ra, _ in chia] == sorted(CUON)
    for de_ra, hoc in chia:
        assert de_ra not in hoc and len(hoc) == 15 and sorted(hoc + [de_ra]) == sorted(CUON)


def test_dung_som_ba_cuon_khong_chua_cuon_de_ra_va_tat_dinh():
    for de_ra in CUON:
        dung, hoc = chon_dung_som(CUON, de_ra, seed=20261027)
        assert len(dung) == 3 and len(hoc) == 12
        assert de_ra not in dung and de_ra not in hoc
        assert not set(dung) & set(hoc) and set(dung) | set(hoc) | {de_ra} == set(CUON)
        assert (dung, hoc) == chon_dung_som(list(reversed(CUON)), de_ra, seed=20261027)  # không phụ thuộc thứ tự đầu vào


def test_dung_som_doi_theo_seed_va_theo_cuon_de_ra():
    a = chon_dung_som(CUON, "d01-01", seed=20261027)[0]
    assert a != chon_dung_som(CUON, "d01-01", seed=1)[0] or a != chon_dung_som(CUON, "d01-01", seed=2)[0]
    tap = {tuple(chon_dung_som(CUON, de_ra, seed=20261027)[0]) for de_ra in CUON}
    assert len(tap) > 8  # mỗi cuốn để ra một tập dừng sớm riêng, không dùng chung một tập cố định


GOLD_DUNG_SOM = ["d01-09", "d01-10", "d01-14"]


def test_dung_som_gia_tri_co_dinh():
    # Khoá giá trị để seed hay thuật toán đổi sẽ bị bắt; giá trị ghi từ lần chạy đầu của chia.py (không phải so tay), nên chỉ giữ cho seed và thuật toán không đổi ngầm.
    assert chon_dung_som(CUON, "d01-01", seed=20261027)[0] == GOLD_DUNG_SOM


def test_vong_ngoai_khong_ro_ri_cuon_de_ra():
    """Mỗi cuốn để ra mang nhãn ngược hoàn toàn với mọi cuốn khác (toàn 1, còn lại toàn 0). Mô hình giả nhớ từng dòng đã thấy và đoán
    số đa số cho dòng lạ. Nếu cuốn để ra lọt vào học hay dừng sớm, độ chính xác ngoài mẫu tăng vọt từ 0."""
    dac_trung = {c: [(c, k) for k in range(6)] for c in CUON}

    def nhan(c, de_ra):
        return 1 if c == de_ra else 0

    def hoc_va_cham(hoc, dung, de_ra):
        nho = {f: nhan(c, de_ra) for c in list(hoc) + list(dung) for f in dac_trung[c]}
        da_so = round(sum(nho.values()) / len(nho))
        doan = [nho.get(f, da_so) for f in dac_trung[de_ra]]
        return sum(1 for d in doan if d == 1) / len(doan)

    assert max(vong_ngoai(CUON, hoc_va_cham, seed=20261027).values()) == 0.0

    def hoc_ro_ri(hoc, dung, de_ra):
        return hoc_va_cham(list(hoc) + [de_ra], dung, de_ra)
    assert min(vong_ngoai(CUON, hoc_ro_ri, seed=20261027, kiem_tra=False).values()) == 1.0  # chứng tỏ bài kiểm có răng


def test_vong_ngoai_bat_chia_ro_ri():
    def chia_hong(cuon, de_ra, *, seed):
        dung, hoc = chon_dung_som(cuon, de_ra, seed=seed)
        return dung, hoc + [de_ra]
    with pytest.raises(ValueError, match="rò rỉ"):
        vong_ngoai(CUON, lambda *a: 0.0, seed=1, chia=chia_hong)

    def chia_dung_som_ro(cuon, de_ra, *, seed):
        dung, hoc = chon_dung_som(cuon, de_ra, seed=seed)
        return [de_ra] + dung[1:], hoc
    with pytest.raises(ValueError, match="rò rỉ"):
        vong_ngoai(CUON, lambda *a: 0.0, seed=1, chia=chia_dung_som_ro)


def test_chia_dong_ro_ri_theo_cuon_la_bat_buoc_khac_chia_cuon():
    cuon_cua_dong = [c for c in CUON for _ in range(10)]
    de_ra, hoc = chia_dong(len(cuon_cua_dong), 0.2, seed=7)
    assert len(de_ra) == 32 and not set(de_ra) & set(hoc)
    assert len({cuon_cua_dong[i] for i in hoc} & {cuon_cua_dong[i] for i in de_ra}) > 10  # chia theo dòng: cuốn lọt cả hai bên


# --- luật một sai số chuẩn: tính tay -----------------------------------------------------------------------------------

def ap_16(trung_binh, lech):
    """16 giá trị có trung bình đúng `trung_binh` và độ lệch chuẩn mẫu đúng `lech`: nửa cộng, nửa trừ cùng một độ lệch."""
    d = lech * math.sqrt(15 / 16)
    return [trung_binh + d if i % 2 == 0 else trung_binh - d for i in range(16)]


def test_mot_se_tinh_tay():
    # best = 255 lá, trung bình 0,80, độ lệch mẫu 0,08 => SE = 0,08/4 = 0,02, ngưỡng 0,78
    ap = {7: ap_16(0.70, 0.08), 15: ap_16(0.77, 0.08), 31: ap_16(0.7801, 0.08), 63: ap_16(0.79, 0.08), 127: ap_16(0.795, 0.08), 255: ap_16(0.80, 0.08)}
    kq = chon_mot_se(ap)
    assert kq["tot_nhat"] == 255 and kq["chon"] == 31
    assert kq["se"] == pytest.approx(0.02) and kq["nguong"] == pytest.approx(0.78)


def test_mot_se_ca_hoa_diem_lay_it_la_nhat():
    # hai cấu hình trùng đỉnh: best là cấu hình ít lá hơn; cả hai trong ngưỡng thì chọn ít lá nhất
    ap = {7: ap_16(0.60, 0.05), 15: ap_16(0.80, 0.05), 31: ap_16(0.80, 0.05), 63: ap_16(0.70, 0.05), 127: ap_16(0.70, 0.05), 255: ap_16(0.70, 0.05)}
    kq = chon_mot_se(ap)
    assert kq["tot_nhat"] == 15 and kq["chon"] == 15


def test_mot_se_ca_cham_nguong_duoc_chon():
    # đúng bằng ngưỡng thì vẫn được chọn (≥)
    ap = {7: ap_16(0.78, 0.08), 15: ap_16(0.70, 0.08), 31: ap_16(0.70, 0.08), 63: ap_16(0.70, 0.08), 127: ap_16(0.70, 0.08), 255: ap_16(0.80, 0.08)}
    assert chon_mot_se(ap)["chon"] == 7


def test_mot_se_khong_phai_cau_hinh_cao_nhat_khi_co_cau_hinh_it_la_trong_nguong():
    ap = {7: ap_16(0.795, 0.08), 15: ap_16(0.79, 0.08), 31: ap_16(0.8, 0.08), 63: ap_16(0.7, 0.08), 127: ap_16(0.7, 0.08), 255: ap_16(0.7, 0.08)}
    assert chon_mot_se(ap)["chon"] == 7 != chon_ap_cao_nhat(ap)["chon"]


def test_mot_se_bo_cuon_khong_co_ap_khoi_trung_binh_va_se():
    # 14 cuốn có AP (None ở 2 cuốn không có dòng dương): SE = sd / √14, không phải √16
    co = ap_16(0.80, 0.08)[:14]
    ap = {7: co + [None, float("nan")], 15: [x - 0.1 for x in co] + [None, None]}
    kq = chon_mot_se(ap)
    assert kq["so_cuon_hop_le"] == 14
    assert kq["se"] == pytest.approx(statistics.stdev(co) / math.sqrt(14))
    assert kq["ap_trung_binh"][7] == pytest.approx(statistics.fmean(co))


def test_mot_se_doi_hoi_du_16_cuon():
    with pytest.raises(ValueError):
        chon_mot_se({7: [0.5] * 15, 15: [0.5] * 15})


# --- so sánh cặp ---------------------------------------------------------------------------------------------------------

def test_hieu_theo_cuon_va_sign_test_tinh_tay():
    a = {c: 0.9 for c in CUON[:12]} | {c: 0.5 for c in CUON[12:14]} | {c: 0.7 for c in CUON[14:]}
    b = {c: 0.8 for c in CUON[:12]} | {c: 0.6 for c in CUON[12:14]} | {c: 0.7 for c in CUON[14:]}
    hieu = hieu_theo_cuon(a, b)
    assert sum(1 for v in hieu.values() if v > 1e-12) == 12 and sum(1 for v in hieu.values() if v < -1e-12) == 2
    kq = so_sanh_cap(a, b, so_vong=2000, seed=20261027)
    assert kq["thang"] == 12 and kq["thua"] == 2 and kq["hoa"] == 2
    assert kq["trung_binh"] == pytest.approx((12 * 0.1 - 2 * 0.1) / 16)
    # sign test hai phía n=14, k=2: 2 * P(X<=2) = 2*(1+14+91)/16384
    assert kq["p_dau"] == pytest.approx(2 * 106 / 16384)
    assert kq["khoang_thap"] <= kq["trung_binh"] <= kq["khoang_cao"]
    assert so_sanh_cap(a, b, so_vong=2000, seed=20261027) == kq  # tất định


def test_so_sanh_cap_khoang_tin_cay_tat_ca_dong_deu():
    a = {c: 0.8 for c in CUON}
    b = {c: 0.6 for c in CUON}
    kq = so_sanh_cap(a, b, so_vong=500, seed=1)
    assert kq["khoang_thap"] == pytest.approx(0.2) and kq["khoang_cao"] == pytest.approx(0.2)


def test_hoc_lai_la_phan_thuan_khong_nhap_thu_vien_hoc_may():
    import ast
    from pathlib import Path
    goc = Path(__file__).resolve().parents[2] / "evaluation" / "danhgia" / "hoc_lai"
    tep = sorted(goc.glob("*.py"))
    assert len(tep) >= 4
    for duong in tep:
        for nut in ast.walk(ast.parse(duong.read_text(encoding="utf-8"))):
            ten = [x.name for x in nut.names] if isinstance(nut, ast.Import) else [nut.module or ""] if isinstance(nut, ast.ImportFrom) and nut.level == 0 else []
            for t in ten:
                assert t.split(".")[0] not in {"lightgbm", "sklearn", "numpy", "pandas", "doc2roadmap"}, f"{duong.name}: {t}"
