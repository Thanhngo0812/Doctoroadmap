"""Phiếu kiểm căn: bốc 20% số ca phán tay theo seed (làm tròn lên), đọc lại, tính % đồng ý và Cohen κ."""
import math
from fractions import Fraction

from danhgia.thong_ke.dong_thuan import cohen_kappa
from danhgia.thong_ke.lcg import Lcg

TI_LE_MAC_DINH = 0.2


def chon_kiem(ma_phan, *, seed, ti_le=TI_LE_MAC_DINH):
    """`ceil(ti_le · n)` mã dòng phán (tính bằng phân số để 0,2 × 15 không thành 3,0000000000000004), bốc không hoàn lại bằng LCG
    theo seed; trả theo thứ tự ban đầu."""
    n = len(ma_phan)
    if not n:
        raise ValueError("không có ca phán tay nào để kiểm")
    k = min(n, max(1, math.ceil(Fraction(str(ti_le)) * n)))
    rng, chi_so = Lcg(seed), list(range(n))
    for i in range(k):
        j = i + rng.chi_so(n - i)
        chi_so[i], chi_so[j] = chi_so[j], chi_so[i]
    return [ma_phan[i] for i in sorted(chi_so[:k])]


def dong_thuan(phan_goc, phan_kiem):
    """% đồng ý và κ trên các ca mà phiếu kiểm có; ca ngoài mẫu không vào mẫu số."""
    chung = [m for m in phan_kiem if m in phan_goc]
    if not chung:
        raise ValueError("phiếu kiểm không có ca nào trùng phán gốc")
    return cohen_kappa([phan_goc[m]["quan_he"] for m in chung], [phan_kiem[m]["quan_he"] for m in chung])
