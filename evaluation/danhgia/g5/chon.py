"""Chọn mẫu và dựng hàng cho phiếu G5 (spec mục 5; vé DG-16). Thuần: không đọc kho, không nhập `doc2roadmap`.

- (a) khái niệm máy không căn được vào vàng: gộp mọi hệ, khử trùng theo chữ chuẩn hoá, tối đa 60 mục mỗi cuốn.
- (b) cạnh máy ngoài vàng (không ánh xạ được vào cạnh G4 chính qua bảng căn): tối đa 100 mục mỗi hệ mỗi cuốn. Mọi hàng, kể cả câu đối chứng, có đúng sáu trường:
  tên X, câu định nghĩa của X, trang X, tên Y, câu định nghĩa của Y, trang Y (không có câu bằng chứng của cạnh: nó là dấu hiệu phân biệt cạnh máy với đối chứng).
  Câu định nghĩa lấy theo một nguồn: câu của kho chốt G3 khi khái niệm đã căn được, nếu không thì câu neo của node. Hàng thiếu một trong sáu trường không vào phiếu. Mỗi người phán có thêm
  câu đối chứng, mỗi loại khoảng 10% tổng số hàng: cạnh vàng **thô của chính người đó** (G4 trước hội ý) và cặp ngẫu nhiên
  (hai khái niệm vàng cùng chương, không có cạnh nào trong G4 chính theo cả hai chiều). Câu đối chứng có cùng cột, cùng định dạng và bị xáo vào hàng của máy.
- (c) rubric Likert 7 mức cho từng module và so sánh cặp mù (hệ chính với từng hệ so sánh), trái phải xáo tất định.
Mã dòng và mã module do LCG theo seed, không chứa tên hệ.
"""
from __future__ import annotations

import zlib

from danhgia.can.mu import _sinh_ma, _xao
from danhgia.cham import a8
from danhgia.cham.can import MUC_CAN, anh_xa_canh, doc_vang
from danhgia.ten import chuan_hoa
from danhgia.thong_ke.lcg import Lcg

TOI_DA_A, TOI_DA_B = 60, 100
TI_LE_DOI_CHUNG = 0.10
PHAN_A = ("day", "chi_nhac", "khong_phai_khai_niem", "rac")
PHAN_B = ("can", "khong_can", "nguoc_chieu")
PHAN_SO_SANH = ("trai", "phai", "hoa")
DIEM_RUBRIC = tuple(range(1, 8))


def _ra(seed, *them):
    """LCG đã bỏ vài số đầu (seed liền nhau cho số đầu tương quan), trộn thêm các số nguyên `them`."""
    so = [v if isinstance(v, int) else zlib.crc32(str(v).encode("utf-8")) for v in them]
    g = Lcg(seed * 1000003 + sum((i + 1) * 7919 * v for i, v in enumerate(so)))
    for _ in range(4):
        g.chi_so(2)
    return g


def boc(ds, k, seed, *them):
    """k phần tử không hoàn lại bằng LCG, trả theo thứ tự ban đầu."""
    n = len(ds)
    k = min(k, n)
    g, chi_so = _ra(seed, *them), list(range(n))
    for i in range(k):
        j = i + g.chi_so(n - i)
        chi_so[i], chi_so[j] = chi_so[j], chi_so[i]
    return [ds[i] for i in sorted(chi_so[:k])]


def khoa_hien_thi(*chuoi):
    return tuple(chuan_hoa(c) for c in chuoi)


TRUONG_HANG_B = ("nguon", "dn_nguon", "trang_nguon", "dich", "dn_dich", "trang_dich")


def khoa_hang(h):
    return khoa_hien_thi(h["nguon"], h["dn_nguon"], h["dich"], h["dn_dich"]) + (h["trang_nguon"], h["trang_dich"])


def _hang_g3(a, b):
    """Hàng (b) từ hai khái niệm kho chốt G3; None nếu một trong hai thiếu câu định nghĩa hoặc trang."""
    da, db = a["dinh_nghia"], b["dinh_nghia"]
    if not all(d.get("cau") and d.get("trang") is not None for d in (da, db)):
        return None
    return {"nguon": a["ten"], "dn_nguon": da["cau"], "trang_nguon": da["trang"], "dich": b["ten"], "dn_dich": db["cau"], "trang_dich": db["trang"]}


def hien_dien(hd):
    return {k["ma"]: k for k in hd["khai_niem"] if not k["bi_loai"] and not k["da_gop"]}


# ---------------------------------------------------------------- (a)


def mau_a(hop_dong_theo_he, can_gop, *, seed, toi_da=TOI_DA_A):
    """Khái niệm máy hiện diện không có dòng căn nào (mọi mức) với khái niệm vàng, gộp mọi hệ và khử trùng."""
    da_can = {h["may"] for h in can_gop["hang"] if h["quan_he"] in MUC_CAN["noi"]}
    nhom = {}
    for he, hd in hop_dong_theo_he.items():
        for ma, k in hien_dien(hd).items():
            if f"{he}:{ma}" in da_can:
                continue
            neo = k["cau_neo"] or {}
            khoa = khoa_hien_thi(k["ten"], neo.get("cau") or "") + (neo.get("trang"),)
            hang = nhom.setdefault(khoa, {"ten": k["ten"], "ten_khac": list(k["ten_khac"] or []), "cau": neo.get("cau"),
                                          "trang": neo.get("trang"), "id_goc": []})
            hang["id_goc"].append(f"{he}:{ma}")
    ds = [dict(h, id_goc=sorted(h["id_goc"])) for h in nhom.values()]
    return boc(ds, toi_da, seed, 1), len(ds)


# ---------------------------------------------------------------- (b)


def canh_ngoai_vang(hd, g3, g4, can_he, *, muc="nghiem"):
    """Cạnh máy (cứng, không bỏ qua) của một hệ, chia thành khớp vàng và ngoài vàng. Một cạnh khớp vàng khi có cặp khái niệm vàng nó ánh xạ tới
    nằm trong cạnh vàng chính của G4; cạnh có đầu không căn được (node ảo) hay đặt ngược là ngoài vàng. Trả `{tong, khop, du: [...]}`."""
    nut = {k["ma"]: k for k in hd["khai_niem"]}
    v = doc_vang(g3, g4, can_he, muc, hd["ban_do_danh_tinh"])
    cap_vang, vcn = v["cap"], v["vang_cua_nut"]
    dn_g3 = {k["ma"]: (k["dinh_nghia"].get("cau"), k["dinh_nghia"].get("trang")) for k in g3["khai_niem"]}
    thu_tu = {k["ma"]: i for i, k in enumerate(g3["khai_niem"])}

    def dinh_nghia(n):
        """Câu định nghĩa G3 của khái niệm vàng đã căn với node, nếu không thì câu neo của node."""
        for g in sorted((g for g in vcn.get(n, ()) if g in dn_g3), key=thu_tu.get):
            if dn_g3[g][0] and dn_g3[g][1] is not None:
                return dn_g3[g]
        neo = nut[n]["cau_neo"] or {}
        return (neo["cau"], neo["trang"]) if neo.get("cau") and neo.get("trang") is not None else None

    canh = sorted(a8.canh_may(hd, mem="cung"))
    khop, so_du, du = 0, 0, []
    for a, b in canh:
        if anh_xa_canh({(a, b)}, vcn) & cap_vang:
            khop += 1
            continue
        so_du += 1
        da, db = dinh_nghia(a), dinh_nghia(b)
        if da is None or db is None:
            continue        # thiếu câu định nghĩa ở một đầu: không đưa vào phiếu (đếm ở `khong_du_truong`)
        du.append({"nguon": nut[a]["ten"], "dn_nguon": da[0], "trang_nguon": da[1], "dich": nut[b]["ten"], "dn_dich": db[0],
                   "trang_dich": db[1], "id": f"{a}>{b}"})
    return {"tong": len(canh), "khop": khop, "so_du": so_du, "du": du, "khong_du_truong": so_du - len(du)}


def mau_b(canh_theo_he, *, seed, toi_da=TOI_DA_B):
    """Mẫu cạnh ngoài vàng: tối đa `toi_da` mỗi hệ; hàng hiển thị giống hệt nhau giữa các hệ gộp thành một hàng.
    Trả `(hàng, thống kê mỗi hệ)`; hàng có `canh` = {hệ: số cạnh mẫu của hệ}."""
    nhom, thong_ke = {}, {}
    for i, (he, d) in enumerate(sorted(canh_theo_he.items())):
        mau = boc(d["du"], toi_da, seed, 2, i)
        thong_ke[he] = {"tong": d["tong"], "khop": d["khop"], "du": d.get("so_du", len(d["du"])), "du_du_truong": len(d["du"]), "mau": len(mau)}
        for e in mau:
            hang = nhom.setdefault(khoa_hang(e), {**{t: e[t] for t in TRUONG_HANG_B}, "canh": {}})
            hang["canh"][he] = hang["canh"].get(he, 0) + 1
    return list(nhom.values()), thong_ke


def doi_chung_vang(g4_tho, g3, k, seed, nguoi, *, tru=()):
    """k cạnh vàng thô của chính người phán (quan hệ `van_ban`), hiển thị như cạnh máy."""
    kn = {x["ma"]: x for x in g3["khai_niem"]}
    ds = []
    for q in g4_tho["quan_he"]:
        if q["loai"] != "van_ban" or not isinstance(q["nguon"], str):     # nguồn "ngoài" không có câu định nghĩa trong kho chốt
            continue
        h = _hang_g3(kn[q["nguon"]], kn[q["dich"]])
        if h is not None and khoa_hang(h) not in tru:
            ds.append(h)
    return boc(ds, k, seed, 3, nguoi)


def doi_chung_ngau(g3, g4_chinh, k, seed, nguoi, *, tru=()):
    """k cặp ngẫu nhiên: hai khái niệm vàng cùng chương, không có cạnh nào trong G4 chính theo cả hai chiều; câu kèm theo là câu định nghĩa của đích."""
    co_canh = set()
    for q in g4_chinh["vang_chinh"]:
        if isinstance(q["nguon"], str):
            co_canh |= {(q["nguon"], q["dich"]), (q["dich"], q["nguon"])}
    theo_chuong = {}
    for x in g3["khai_niem"]:
        theo_chuong.setdefault(x["chuong"], []).append(x)
    ung = [(a, b) for ds in theo_chuong.values() for a in ds for b in ds if a["ma"] != b["ma"] and (a["ma"], b["ma"]) not in co_canh]
    chon, thay = [], set(tru)
    for i in _xao(len(ung), _ra(seed, 4, nguoi)):            # xáo toàn bộ rồi lấy k cặp đầu không trùng hiển thị
        a, b = ung[i]
        h = _hang_g3(a, b)
        if h is not None and khoa_hang(h) not in thay:
            thay.add(khoa_hang(h))
            chon.append(h)
        if len(chon) == k:
            break
    return chon


def so_dong_doi_chung(so_hang_may):
    """Mỗi loại ~10% tổng số hàng: k = N/8 làm k/(N + 2k) = 10%."""
    return round(so_hang_may * TI_LE_DOI_CHUNG / (1 - 2 * TI_LE_DOI_CHUNG))


def dung_phieu_b(hang_may, g3, g4_chinh, g4_tho, *, seed, nguoi, cam=()):
    """Hàng (b) của một người: hàng máy + câu đối chứng, xáo tất định, mã ngẫu nhiên không chứa `cam` (tên hệ)."""
    k = so_dong_doi_chung(len(hang_may))
    tru = {khoa_hang(h) for h in hang_may}
    dv = doi_chung_vang(g4_tho, g3, k, seed, nguoi, tru=tru)
    tru |= {khoa_hang(h) for h in dv}
    dn = doi_chung_ngau(g3, g4_chinh, k, seed, nguoi, tru=tru)
    hang = [dict(h, loai="may") for h in hang_may] + [dict(h, loai="doi_chung_vang", canh={}) for h in dv] \
        + [dict(h, loai="doi_chung_ngau", canh={}) for h in dn]
    xep = _xao(len(hang), _ra(seed, 5, nguoi))
    ma = _sinh_ma("b", len(hang), {c.lower() for c in cam})
    return [dict(hang[i], ma=m) for m, i in zip(ma, xep)]


# ---------------------------------------------------------------- (c)


def mau_module(hop_dong_theo_he):
    """Module của mọi hệ có lộ trình, khử trùng theo (tên module, tên các khái niệm); `he` ghi các hệ có module đó."""
    nhom = {}
    for he, hd in hop_dong_theo_he.items():
        if hd["lo_trinh"] is None:
            continue
        ten = {k["ma"]: k["ten"] for k in hd["khai_niem"]}
        for m in hd["lo_trinh"]["module"]:
            tv = [ten[x] for x in m["thanh_vien"]]
            hang = nhom.setdefault(khoa_hien_thi(m["ten"], *tv), {"ten": m["ten"], "thanh_vien": tv, "he": []})
            hang["he"].append(he)
    return [dict(h, he=sorted(h["he"])) for h in nhom.values()]


def van_ban_lo_trinh(hd):
    ten = {k["ma"]: k["ten"] for k in hd["khai_niem"]}
    return "\n".join(f"{i}. {m['ten']}: " + "; ".join(ten[x] for x in m["thanh_vien"]) for i, m in enumerate(hd["lo_trinh"]["module"], start=1))


def cap_so_sanh(hop_dong_theo_he, *, chinh="chinh", seed, nguoi):
    """Cặp (hệ chính, hệ khác) cho mọi hệ khác có lộ trình; trái phải xáo tất định theo seed và người phán."""
    ket = []
    for i, he in enumerate(sorted(h for h, hd in hop_dong_theo_he.items() if h != chinh and hd["lo_trinh"] is not None)):
        chinh_trai = _ra(seed, 6, nguoi, i).dong_xu()
        trai, phai = (chinh, he) if chinh_trai else (he, chinh)
        ket.append({"cap": f"{chinh}~{he}", "trai_la": trai, "phai_la": phai, "trai": van_ban_lo_trinh(hop_dong_theo_he[trai]),
                    "phai": van_ban_lo_trinh(hop_dong_theo_he[phai])})
    return ket
