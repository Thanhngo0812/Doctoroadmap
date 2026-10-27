"""Khoảng tin cậy bootstrap phân cấp: lấy lại cuốn có hoàn lại, rồi lấy lại chương trong mỗi cuốn đã lấy (spec mục 9).

Cạnh trong cùng cuốn không độc lập (cùng văn phong, cùng người gán, cùng một lần chạy), nên đơn vị lấy mẫu là cuốn; tầng chương giữ phần biến thiên
bên trong cuốn (Saravanan và cộng sự 2020, VL §9).
"""
from danhgia.thong_ke.lcg import Lcg
from danhgia.thong_ke.so_dem import dem_theo_chuong, gia_tri_cuon, trung_binh_macro


def _phan_vi(sap_xep, q):
    """Phân vị theo nội suy tuyến tính giữa hai điểm kề (cách mặc định của numpy)."""
    vi_tri = q * (len(sap_xep) - 1)
    duoi = int(vi_tri)
    tren = min(duoi + 1, len(sap_xep) - 1)
    return sap_xep[duoi] + (sap_xep[tren] - sap_xep[duoi]) * (vi_tri - duoi)


def bootstrap_phan_cap(rows, *, he, thuoc, so_vong=10000, seed=20261114, muc=0.95):
    kieu, theo_sach = dem_theo_chuong(rows, he, thuoc)
    sach = sorted(theo_sach)
    chuong = {s: [theo_sach[s][c] for c in sorted(theo_sach[s])] for s in sach}
    goc = trung_binh_macro(gia_tri_cuon(kieu, chuong[s]) for s in sach)
    sinh = Lcg(seed)
    mau = []
    for _ in range(so_vong):
        cac_cuon = []
        for _ in sach:
            chon = sach[sinh.chi_so(len(sach))]
            dem = chuong[chon]
            cac_cuon.append(gia_tri_cuon(kieu, [dem[sinh.chi_so(len(dem))] for _ in dem]))
        gia = trung_binh_macro(cac_cuon)
        if gia is not None:
            mau.append(gia)
    if not mau:
        return {"macro": goc, "thap": None, "cao": None, "so_vong_hop_le": 0}
    mau.sort()
    duoi = (1 - muc) / 2
    return {"macro": goc, "thap": _phan_vi(mau, duoi), "cao": _phan_vi(mau, 1 - duoi), "so_vong_hop_le": len(mau)}
