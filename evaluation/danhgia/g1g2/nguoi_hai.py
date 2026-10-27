"""Người duyệt thứ hai: mẫu khoảng 30% số mục theo seed, đồng thuận với người thứ nhất (Cohen κ kèm % đồng ý)."""
from danhgia.thong_ke.dong_thuan import cohen_kappa
from danhgia.thong_ke.lcg import Lcg


def chon_mau(khoa, *, seed, ti_le=0.30, loai_tru=()):
    """`round(ti_le · N')` mục (ít nhất 1), N' = số mục không nằm trong `loai_tru` (mục bị cài lỗi). Bốc không hoàn lại bằng LCG
    theo seed; trả theo thứ tự đọc ban đầu. Mẫu không bao giờ chứa mục bị cài nên người hai không thấy giá trị bị cài."""
    loai_tru = set(loai_tru)
    khoa = [k for k in khoa if k not in loai_tru]
    n = len(khoa)
    if not n:
        raise ValueError("không có mục nào để bốc")
    so_mau = min(n, max(1, int(ti_le * n + 0.5)))
    rng, chi_so = Lcg(seed), list(range(n))
    for i in range(so_mau):
        j = i + rng.chi_so(n - i)
        chi_so[i], chi_so[j] = chi_so[j], chi_so[i]
    return [khoa[i] for i in sorted(chi_so[:so_mau])]


def dong_thuan(doc1, doc2):
    """κ và % đồng ý cho vai trò G2 và cho cấp, chỉ trên phần chung: mục trong phiếu hai mà cả hai người đều giữ.
    Mục một trong hai người xoá nằm ngoài phần chung và được đếm ở `so_loai_vi_xoa`. Dùng nhãn thô của từng người,
    không phải vàng cuối (vàng đã gỡ lỗi cài)."""
    a = {h["khoa"]: h for h in doc1["hang"]}
    b = {h["khoa"]: h for h in doc2["hang"]}
    chung = [k for k in b if k in a and not a[k]["xoa"] and not b[k]["xoa"]]
    if not chung:
        raise ValueError("hai người không có mục chung nào còn giữ")
    return {"so_mau": len(b), "so_chung": len(chung),
            "so_loai_vi_xoa": sum(1 for k in b if k in a and (a[k]["xoa"] or b[k]["xoa"])),
            "so_ngoai_phieu_1": sum(1 for k in b if k not in a),
            "vai_tro": cohen_kappa([a[k]["vai_tro"] for k in chung], [b[k]["vai_tro"] for k in chung]),
            "cap": cohen_kappa([a[k]["cap"] for k in chung], [b[k]["cap"] for k in chung])}
