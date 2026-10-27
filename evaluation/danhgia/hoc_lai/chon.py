"""Luật một sai số chuẩn chọn số lá, khai trước: chọn cấu hình ÍT LÁ NHẤT có AP trung bình ≥ AP(tốt nhất) − SE."""
import math
import statistics

SO_CUON = 16
EPS = 1e-12


def _trung_binh(ap):
    return {la: statistics.fmean(v) for la, v in ap.items()}


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
    """`ap`: {số lá: AP của từng trong 16 cuốn để ra}. SE = độ lệch chuẩn mẫu (n−1) của AP theo cuốn của cấu hình tốt nhất chia √16."""
    _kiem_tra(ap)
    tb = _trung_binh(ap)
    tot = _tot_nhat(tb)
    se = statistics.stdev(ap[tot]) / math.sqrt(SO_CUON)
    nguong = tb[tot] - se
    chon = min(la for la in tb if tb[la] >= nguong - EPS)
    return {"chon": chon, "tot_nhat": tot, "ap_tot_nhat": tb[tot], "se": se, "nguong": nguong, "ap_trung_binh": tb}
