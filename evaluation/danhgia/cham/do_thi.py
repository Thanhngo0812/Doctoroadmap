"""Phép đồ thị thuần cho lõi chấm: bao đóng, rút gọn bắc cầu, chu trình, thành phần liên thông.

Cạnh luôn là cặp có hướng `(tiên quyết, đích)`.
"""
from __future__ import annotations

from collections import defaultdict, deque


def dong_bao(canh):
    """Bao đóng bắc cầu, bỏ cạnh tự nối. Đồ thị có chu trình vẫn chạy được."""
    ke = defaultdict(set)
    for nguon, dich in canh:
        ke[nguon].add(dich)
    ket_qua = set()
    for dau in sorted(ke):
        hang, thay = deque(sorted(ke[dau])), set()
        while hang:
            nut = hang.popleft()
            if nut in thay:
                continue
            thay.add(nut)
            if nut != dau:
                ket_qua.add((dau, nut))
            hang.extend(sorted(ke.get(nut, ())))
    return ket_qua


def rut_gon(canh):
    """Chỉ giữ cạnh trực tiếp của DAG: cạnh (s,t) bị bỏ nếu còn đường s tới t qua cạnh khác."""
    cap = {(a, b) for a, b in canh if a != b}
    con = defaultdict(set)
    for nguon, dich in cap:
        con[nguon].add(dich)
    giu = set()
    for nguon, dich in cap:
        ngan_xep = list(con.get(nguon, set()) - {dich})
        thay = set()
        while ngan_xep:
            nut = ngan_xep.pop()
            if nut == dich:
                break
            if nut not in thay:
                thay.add(nut)
                ngan_xep.extend(con.get(nut, ()))
        else:
            giu.add((nguon, dich))
    return giu


def to_tien(canh):
    """tổ tiên[đích] = tập nguồn tới được đích qua bao đóng."""
    ket_qua = {}
    for nguon, dich in dong_bao(canh):
        ket_qua.setdefault(dich, set()).add(nguon)
    return ket_qua


def so_chu_trinh(nut, canh):
    """Số thành phần liên thông mạnh có chu trình (cỡ ≥ 2, hoặc có cạnh tự nối). Tarjan lặp, không đệ quy."""
    ke = defaultdict(list)
    tu_noi = set()
    for nguon, dich in canh:
        if nguon == dich:
            tu_noi.add(nguon)
        else:
            ke[nguon].append(dich)
    chi_so, thap, tren_ngan, ngan, dem = {}, {}, set(), [], 0
    so = 0
    for goc in sorted(set(nut) | set(ke) | {d for ds in ke.values() for d in ds}):
        if goc in chi_so:
            continue
        lam = [(goc, iter(sorted(ke.get(goc, ()))))]
        chi_so[goc] = thap[goc] = dem
        dem += 1
        ngan.append(goc)
        tren_ngan.add(goc)
        while lam:
            nut_, it = lam[-1]
            tiep = next(it, None)
            if tiep is not None:
                if tiep not in chi_so:
                    chi_so[tiep] = thap[tiep] = dem
                    dem += 1
                    ngan.append(tiep)
                    tren_ngan.add(tiep)
                    lam.append((tiep, iter(sorted(ke.get(tiep, ())))))
                elif tiep in tren_ngan:
                    thap[nut_] = min(thap[nut_], chi_so[tiep])
                continue
            lam.pop()
            if lam:
                cha = lam[-1][0]
                thap[cha] = min(thap[cha], thap[nut_])
            if thap[nut_] == chi_so[nut_]:
                thanh_phan = []
                while True:
                    x = ngan.pop()
                    tren_ngan.discard(x)
                    thanh_phan.append(x)
                    if x == nut_:
                        break
                if len(thanh_phan) > 1 or (len(thanh_phan) == 1 and thanh_phan[0] in tu_noi):
                    so += 1
    return so


def so_thanh_phan(nut, canh):
    """Số thành phần liên thông (bỏ hướng) trên đúng tập `nut`; nút lẻ loi tính một thành phần."""
    nut = set(nut)
    cha = {x: x for x in nut}

    def tim(x):
        while cha[x] != x:
            cha[x] = cha[cha[x]]
            x = cha[x]
        return x

    for nguon, dich in canh:
        if nguon in nut and dich in nut:
            cha[tim(nguon)] = tim(dich)
    return len({tim(x) for x in nut})
