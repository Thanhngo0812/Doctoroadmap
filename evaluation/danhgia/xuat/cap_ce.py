"""Văn bản đầu vào cross-encoder cho một cặp ứng viên pass phụ (vé DG-21), đúng khuôn lúc học (`scripts/pass-phu-ml/dung_du_lieu_e6.py: make_row`).

Mỗi dòng là một chiều X -> Y: tên Y, câu của cửa sổ định nghĩa của Y với tên X bọc `@ … @` và tên Y bọc `# … #`, câu định nghĩa của X.
Câu tách từ bằng bộ tách từ của sản phẩm (cùng underthesea với lúc học). Việc cắt theo độ dài 256 làm ở `ce_hoc.Encoder`, không ở đây.
Seam xuất: nhập `doc2roadmap`.
"""
from __future__ import annotations

from collections import defaultdict

from doc2roadmap.domain.canonical import alias_kind
from doc2roadmap.domain.mentions import _mention_normalize, _names


def _am_tiet(tu):
    ket_qua = []
    for chi_so, tu_don in enumerate(tu):
        phan = tu_don.split()
        for k, p in enumerate(phan):
            ket_qua.append((_mention_normalize(p), chi_so, k == 0, k == len(phan) - 1))
    return ket_qua


def _day_am_tiet(ten_cac, tach_tu):
    ket_qua = []
    for gia_tri in ten_cac:
        gia_tri = " ".join((gia_tri or "").split())
        if gia_tri and alias_kind(gia_tri) != "symbol":
            day = [a for a, *_ in _am_tiet(tach_tu(gia_tri))]
            if day and day not in ket_qua:
                ket_qua.append(day)
    return ket_qua


def _doan(am_tiet, cac_day):
    thay = set()
    for day in cac_day:
        co = len(day)
        for i in range(len(am_tiet) - co + 1):
            if am_tiet[i][2] and am_tiet[i + co - 1][3] and all(am_tiet[i + k][0] == day[k] for k in range(co)):
                thay.add((am_tiet[i][1], am_tiet[i + co - 1][1]))
    return thay


def _chen_dau(tu, doan_x, doan_y):
    mo, dong = defaultdict(list), defaultdict(list)
    for (dau, cuoi), dau_hieu in [(s, "@") for s in doan_x] + [(s, "#") for s in doan_y]:
        mo[dau].append((dau - cuoi, dau_hieu == "@", dau_hieu))
        dong[cuoi].append((cuoi - dau, dau_hieu == "#", dau_hieu))
    ra = []
    for chi_so, tu_don in enumerate(tu):
        ra += [d for *_, d in sorted(mo[chi_so])]
        ra.append(tu_don)
        ra += [d for *_, d in sorted(dong[chi_so])]
    return " ".join(ra)


def phan_van_ban(cac_cau, neo, trung, ten_x, ten_y, dinh_nghia_x, tach_tu):
    """Phần văn bản của một dòng (`cau` âm tiết cách nhau). `trung`: chỉ số câu có tên X theo ranh giới từ."""
    day_x, day_y = _day_am_tiet(ten_x, tach_tu), _day_am_tiet(ten_y, tach_tu)
    da_danh_dau = []
    for cau in cac_cau:
        tu = list(tach_tu(cau))
        am_tiet = _am_tiet(tu)
        da_danh_dau.append(_chen_dau(tu, _doan(am_tiet, day_x), _doan(am_tiet, day_y)))
    thuan = lambda van: " ".join(tach_tu(" ".join((van or "").split())))  # noqa: E731
    return {"y_ten": thuan(ten_y[0]), "x_ten": thuan(ten_x[0]), "x_dinh_nghia": thuan(dinh_nghia_x),
            "cau": da_danh_dau, "cau_neo": neo, "cau_co_x": sorted(trung)}


def hang_cap(ctx, tach_tu, ma_cap, x, y, ma_sach):
    """Dòng văn bản cho chiều x -> y, dùng `SecondaryFeatureContext` của sản phẩm (cửa sổ và bộ khớp tên cùng với luồng chấm)."""
    cac_cau, neo = ctx.window_cache[y]
    trung = {i for i, cau in enumerate(cac_cau) if ctx.found(ctx.pattern_cache[x], cau) and ctx.found_words(ctx.word_cache[x], cau)}
    nut_x, nut_y = ctx.node_by_id[x], ctx.node_by_id[y]
    dinh_nghia = (nut_x.get("anchor") or {}).get("sentence") or ""
    phan = phan_van_ban([" ".join(c.split()) for c in cac_cau], neo, trung, _names(nut_x), _names(nut_y), dinh_nghia, tach_tu)
    return {"id": f"{ma_cap}|{x}|{y}", "nguon": ma_sach, "nhom": ma_sach, "pair_id": ma_cap, "x": x, "y": y, **phan}
