"""Luật một sai số chuẩn chọn số lá, khai trước: chọn cấu hình ÍT LÁ NHẤT có AP trung bình ≥ AP(tốt nhất) − SE."""
import math
import statistics

SO_CUON = 16
EPS = 1e-12


def _co_nghia(v):
    """Cuốn không có dòng dương thì AP không xác định (None hay NaN) và không vào trung bình hay SE."""
    return [x for x in v if x is not None and not math.isnan(x)]


def _trung_binh(ap):
    return {la: statistics.fmean(_co_nghia(v)) for la, v in ap.items()}


def _kiem_tra(ap):
    for la, v in ap.items():
        if len(v) != SO_CUON:
            raise ValueError(f"cấu hình {la} lá có {len(v)} giá trị AP, cần đủ {SO_CUON} cuốn")


def _tot_nhat(tb):
    # trùng điểm trung bình: lấy cấu hình ít lá hơn
    return min(tb, key=lambda la: (-tb[la], la))


def chon_ap_cao_nhat(ap):
    """Phép phá: chọn thẳng cấu hình AP trung bình cao nhất, bỏ luật một SE."""
    _kiem_tra(ap)
    tb = _trung_binh(ap)
    tot = _tot_nhat(tb)
    return {"chon": tot, "tot_nhat": tot, "ap_trung_binh": tb}


def chon_mot_se(ap):
    """`ap`: {số lá: AP của từng trong 16 cuốn để ra}. SE = độ lệch chuẩn mẫu (n−1) của AP theo cuốn của cấu hình tốt nhất chia √n,
    n = số cuốn có AP xác định (16 khi mọi cuốn có dòng dương)."""
    _kiem_tra(ap)
    tb = _trung_binh(ap)
    tot = _tot_nhat(tb)
    hop_le = _co_nghia(ap[tot])
    se = statistics.stdev(hop_le) / math.sqrt(len(hop_le))
    nguong = tb[tot] - se
    chon = min(la for la in tb if tb[la] >= nguong - EPS)
    return {"chon": chon, "tot_nhat": tot, "ap_tot_nhat": tb[tot], "se": se, "so_cuon_hop_le": len(hop_le), "nguong": nguong, "ap_trung_binh": tb}


def chon_c_nhieu_nhat(c_theo_lan):
    """Vé DG-21: `C` được chọn **nhiều nhất** qua các lần chia LOBO; hoà thì lấy `C` nhỏ hơn.

    `c_theo_lan`: dãy `C` mà từng lần chia đã chọn. Trả {"chon", "dem": {C: số lần}, "hoa": các C cùng số lần cao nhất}.
    """
    dem = {}
    for c in c_theo_lan:
        dem[float(c)] = dem.get(float(c), 0) + 1
    if not dem:
        raise ValueError("không có lần chia nào để chọn C")
    cao = max(dem.values())
    hoa = sorted(c for c, n in dem.items() if n == cao)
    return {"chon": hoa[0], "dem": dict(sorted(dem.items())), "hoa": hoa}
