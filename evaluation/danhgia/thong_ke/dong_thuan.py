"""Đồng thuận người gán (spec mục 8; VL §6.2, §8).

- `psa`: đồng thuận dương đặc hiệu = F1 giữa hai người, dùng khi chỉ ghi ca dương nên không có ca âm để tính κ (Hripcsak & Rothschild 2005).
- `cohen_kappa`: hai người, nhãn danh nghĩa, kèm % đồng ý.
- `krippendorff_alpha`: nhiều người, cho phép thiếu, mức danh nghĩa, thứ bậc, khoảng (Krippendorff 2011, ma trận trùng hợp).
"""
from collections import Counter, defaultdict
from itertools import permutations


def psa(a, b, c):
    """a: mục cả hai cùng ghi; b, c: mục chỉ một người ghi."""
    mau = 2 * a + b + c
    return 2 * a / mau if mau else None


def cohen_kappa(nhan_a, nhan_b):
    if len(nhan_a) != len(nhan_b) or not nhan_a:
        raise ValueError("hai danh sách nhãn phải cùng độ dài, khác rỗng")
    n = len(nhan_a)
    dong_y = sum(x == y for x, y in zip(nhan_a, nhan_b)) / n
    bien_a, bien_b = Counter(nhan_a), Counter(nhan_b)
    ky_vong = sum(bien_a[k] * bien_b[k] for k in bien_a) / n ** 2
    kappa = (dong_y - ky_vong) / (1 - ky_vong) if ky_vong < 1 else None
    return {"dong_y": dong_y, "kappa": kappa, "so_muc": n}


def _ma_tran_trung_hop(du_lieu):
    """`du_lieu[người][đơn vị]`, `None` là thiếu. Chỉ đơn vị có từ hai giá trị trở lên mới vào ma trận."""
    so_don_vi = len(du_lieu[0])
    o = defaultdict(float)
    for j in range(so_don_vi):
        gia = [hang[j] for hang in du_lieu if hang[j] is not None]
        m = len(gia)
        if m < 2:
            continue
        for x, y in permutations(range(m), 2):
            o[(gia[x], gia[y])] += 1 / (m - 1)
    return o


def krippendorff_alpha(du_lieu, *, muc_do="danh_nghia"):
    """α của Krippendorff. Trả `None` khi kỳ vọng bất đồng bằng 0, tức mọi giá trị quan sát là một giá trị duy nhất: đồng ý
    tuyệt đối nhưng không có biến thiên để đo độ tin cậy; nơi gọi phải báo riêng ca này, không đọc `None` là "chưa đo".
    Mức `thu_bac` và `khoang` cần nhãn là số có thứ tự tự nhiên; nhãn chữ sẽ bị sắp theo từ điển và cho số sai (soát S-07)."""
    if muc_do in ("thu_bac", "khoang") and any(isinstance(v, str) for hang in du_lieu for v in hang):
        raise ValueError("mức thứ bậc và khoảng cần nhãn số")
    o = _ma_tran_trung_hop(du_lieu)
    gia_tri = sorted({c for c, _ in o} | {k for _, k in o})
    n_c = {c: sum(v for (x, _), v in o.items() if x == c) for c in gia_tri}
    n = sum(n_c.values())
    if n <= 1:
        return None

    def khoang_cach(c, k):
        if c == k:
            return 0.0
        if muc_do == "danh_nghia":
            return 1.0
        if muc_do == "khoang":
            return float(c - k) ** 2
        if muc_do == "thu_bac":
            thap, cao = sorted((c, k))
            giua = sum(n_c[g] for g in gia_tri if thap <= g <= cao)
            return (giua - (n_c[c] + n_c[k]) / 2) ** 2
        raise ValueError(f"mức đo không biết: {muc_do!r}")

    quan_sat = sum(v * khoang_cach(c, k) for (c, k), v in o.items())
    ky_vong = sum(n_c[c] * n_c[k] * khoang_cach(c, k) for c in gia_tri for k in gia_tri) / (n - 1)
    if ky_vong == 0:
        return None
    return 1 - quan_sat / ky_vong
