"""So sánh cặp theo cuốn: hiệu AP, khoảng tin cậy bootstrap theo cuốn (LCG tất định), kiểm định dấu."""
import statistics

from danhgia.thong_ke.kiem_dinh import sign_test
from danhgia.thong_ke.lcg import Lcg

EPS = 1e-12


def hieu_theo_cuon(a, b):
    if set(a) != set(b):
        raise ValueError("hai hệ phải có cùng tập cuốn")
    return {c: a[c] - b[c] for c in sorted(a)}


def _phan_vi(sap_xep, q):
    vi_tri = q * (len(sap_xep) - 1)
    duoi = int(vi_tri)
    tren = min(duoi + 1, len(sap_xep) - 1)
    return sap_xep[duoi] + (sap_xep[tren] - sap_xep[duoi]) * (vi_tri - duoi)


def so_sanh_cap(a, b, *, so_vong=10000, seed=20261027, muc=0.95):
    """Hiệu a − b theo cuốn: trung bình, khoảng bootstrap theo cuốn, số cuốn thắng/thua/hoà, p của kiểm định dấu (hoà loại)."""
    hieu = list(hieu_theo_cuon(a, b).values())
    thang = sum(1 for v in hieu if v > EPS)
    thua = sum(1 for v in hieu if v < -EPS)
    sinh = Lcg(seed)
    mau = sorted(statistics.fmean(hieu[sinh.chi_so(len(hieu))] for _ in hieu) for _ in range(so_vong))
    duoi = (1 - muc) / 2
    return {"trung_binh": statistics.fmean(hieu), "khoang_thap": _phan_vi(mau, duoi), "khoang_cao": _phan_vi(mau, 1 - duoi),
            "thang": thang, "thua": thua, "hoa": len(hieu) - thang - thua, "p_dau": sign_test(thang, thua), "so_cuon": len(hieu)}
