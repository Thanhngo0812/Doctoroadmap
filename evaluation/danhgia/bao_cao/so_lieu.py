"""Tính mọi con số của Bảng 9–12 và Hình 3–4 từ dòng số đếm theo chương. Làm tròn chỉ xảy ra lúc hiển thị (`bang.py`), không bao giờ ở đây.

Đầu vào là các dòng `dong.ti_le` / `dong.f1` của mọi hệ và mọi cuốn. Hai thước không nằm trong dòng của bộ chấm được dựng thành dòng cùng dạng:
- chi phí (phút, USD) từ khối `chi_phi` của hợp đồng, một dòng `toan_sach` mỗi cuốn, `ti_le(giá trị, 1)`;
- trần người từ tệp đồng thuận G4 (`vang.g4.dem_g4`): F1 giữa hai người = 2a / (2a + b + c), chương nào cũng một dòng `f1`.
"""
from __future__ import annotations

from danhgia.bao_cao import thuoc as T
from danhgia.cham import dong
from danhgia.thong_ke import bootstrap_phan_cap, hoan_vi_ghep_cap, holm, sign_test, thuoc_theo_cuon, wilson
from danhgia.thong_ke.bootstrap import _phan_vi
from danhgia.thong_ke.kiem_dinh import _hieu_macro
from danhgia.thong_ke.lcg import Lcg
from danhgia.thong_ke.so_dem import dem_theo_chuong, gia_tri_cuon

SEED = 20261114
SO_VONG = 10000
TRUONG_DONG = ("he", "ma_sach", "chuong", "thuoc", "kieu")


def kiem_dong(rows):
    for r in rows:
        thieu = [t for t in TRUONG_DONG if t not in r]
        if thieu:
            raise ValueError(f"dòng thiếu trường {thieu}")
    return rows


def chuan_he_b5(rows, he_b5=None):
    """Tên hệ B5 trong dữ liệu (b5a hay b5b tuỳ chế độ giao thức chốt) và bảng đổi về `b5`. Có nhiều hệ B5 mà không chỉ định thì lỗi."""
    co = sorted({r["he"] for r in rows} & set(T.HE_B5_CO_THE))
    if he_b5 is None:
        if len(co) > 1:
            raise ValueError(f"có nhiều hệ B5 trong dữ liệu ({co}): chỉ định bằng --he-b5")
        he_b5 = co[0] if co else None
    return he_b5, ({he_b5: "b5"} if he_b5 not in (None, "b5") else {})


def doi_ten_he(rows, doi):
    if not doi:
        return rows
    return [{**r, "he": doi.get(r["he"], r["he"])} for r in rows]


def dong_chi_phi(hop_dong):
    """Danh sách `(ma_sach, hợp đồng)` -> dòng phút, phút không tính chờ embedding, USD. Giá trị null trong hợp đồng thì không có dòng (ô hiện —)."""
    rows = []
    for ma_sach, hd in hop_dong:
        cp = hd.get("chi_phi")
        tong = cp.get("tong") if cp else None
        if not tong:
            continue
        he = hd["dinh_danh"]["he"]
        giay, cho = tong.get("giay_chay"), tong.get("giay_cho_embedding")
        if giay is not None:
            rows.append(dong.ti_le(he, ma_sach, "toan_sach", T.THUOC_PHUT, giay / 60, 1))
            if cho is not None:
                rows.append(dong.ti_le(he, ma_sach, "toan_sach", T.THUOC_PHUT_KHONG_CHO, (giay - cho) / 60, 1))
        if tong.get("usd") is not None:
            rows.append(dong.ti_le(he, ma_sach, "toan_sach", T.THUOC_USD, tong["usd"], 1))
    return rows


def dong_tran_nguoi(dong_thuan_theo_sach):
    """`{ma_sach: kết quả dem_g4}` -> dòng F1 giữa hai người (PSA) của hệ `tran_nguoi`, mức không bắc cầu."""
    rows = []
    for ma_sach, kq in sorted(dong_thuan_theo_sach.items()):
        for chuong, theo in sorted(kq["khong_bac_cau"]["theo_chuong"].items()):
            t = theo["tong"]
            # tp = a; b và c đối xứng nên đặt fp = c, fn = b: 2tp / (2tp + fp + fn) đúng bằng PSA
            rows.append(dong.f1(T.HE_TRAN_NGUOI, ma_sach, chuong, T.THUOC_F1, t["a"], t["c"], t["b"]))
    return rows


def _loc(rows, he, thuoc):
    return [r for r in rows if r["he"] == he and r["thuoc"] == thuoc]


class Tinh:
    """Tính một lần, nhớ kết quả: cùng (hệ, thước) được hỏi ở nhiều bảng."""

    def __init__(self, rows, *, so_vong=SO_VONG, seed=SEED):
        self.rows, self.so_vong, self.seed = kiem_dong(rows), so_vong, seed
        self.sach = sorted({r["ma_sach"] for r in rows})
        self._nho, self._hieu = {}, {}

    def tat_ca(self):
        """Mọi ô và mọi hiệu đã tính, khoá `hệ|thước` hay `hệ|thước|hệ chính`: nguồn của `so-lieu.json`."""
        return ({f"{he}|{thuoc}": v for (he, thuoc), v in sorted(self._nho.items()) if v is not None},
                {f"{he}|{thuoc}|chinh": v for (he, thuoc), v in sorted(self._hieu.items()) if v is not None})

    def o(self, he, thuoc):
        """`{macro, thap, cao, theo_cuon, so_cuon_co_so, so_cuon, mau_so}`, hoặc `None` khi hệ không có dòng nào cho thước này."""
        khoa = (he, thuoc)
        if khoa not in self._nho:
            self._nho[khoa] = self._tinh_o(he, thuoc)
        return self._nho[khoa]

    def _tinh_o(self, he, thuoc):
        sub = _loc(self.rows, he, thuoc)
        if not sub:
            return None
        tl = thuoc_theo_cuon(sub, he=he, thuoc=thuoc)
        ci = bootstrap_phan_cap(sub, he=he, thuoc=thuoc, so_vong=self.so_vong, seed=self.seed)
        truong = ("mau",) if tl["kieu"] == "ti_le" else ("tp", "fn")
        return {"macro": tl["macro"], "thap": ci["thap"], "cao": ci["cao"], "theo_cuon": tl["theo_cuon"],
                "so_cuon_co_so": sum(v is not None for v in tl["theo_cuon"].values()), "so_cuon": len(tl["theo_cuon"]),
                "mau_so": sum(sum(r[t] for t in truong) for r in sub)}

    def hieu(self, he_a, he_b, thuoc):
        khoa = (he_a, thuoc)
        if he_b != "chinh":
            return self._tinh_hieu(he_a, he_b, thuoc)
        if khoa not in self._hieu:
            self._hieu[khoa] = self._tinh_hieu(he_a, he_b, thuoc)
        return self._hieu[khoa]

    def _tinh_hieu(self, he_a, he_b, thuoc):
        """Hiệu macro `a − b` trên các cuốn có ở cả hai hệ, kèm CI bootstrap phân cấp ghép cặp (cùng cuốn, cùng chương được lấy cho cả hai hệ)."""
        sub = [r for r in self.rows if r["thuoc"] == thuoc and r["he"] in (he_a, he_b)]
        if not _loc(sub, he_a, thuoc) or not _loc(sub, he_b, thuoc):
            return None
        kieu, da = dem_theo_chuong(sub, he_a, thuoc)
        _, db = dem_theo_chuong(sub, he_b, thuoc)
        chung = sorted(set(da) & set(db))
        if not chung:
            return None
        for s in chung:
            if set(da[s]) != set(db[s]):
                raise ValueError("chương lệch giữa hai hệ trong cùng một cuốn")
        cap = {s: [(da[s][c], db[s][c]) for c in sorted(da[s])] for s in chung}
        goc = _hieu_macro(kieu, cap)
        sinh, mau = Lcg(self.seed), []
        for _ in range(self.so_vong):
            moi = {}
            for i in range(len(chung)):
                s = chung[sinh.chi_so(len(chung))]
                ch = cap[s]
                moi[i] = [ch[sinh.chi_so(len(ch))] for _ in ch]
            h = _hieu_macro(kieu, moi)
            if h is not None:
                mau.append(h)
        mau.sort()
        thap = cao = None
        if mau:
            thap, cao = _phan_vi(mau, 0.025), _phan_vi(mau, 0.975)
        return {"hieu": goc, "thap": thap, "cao": cao, "so_cuon_chung": len(chung)}

    def ci_cuon(self, he, thuoc, ma_sach):
        """Giá trị của một cuốn kèm CI bootstrap chương trong cuốn: lấy lại chương có hoàn lại, tính lại từ tổng số đếm."""
        sub = _loc(self.rows, he, thuoc)
        if not sub:
            return None
        kieu, theo = dem_theo_chuong(sub, he, thuoc)
        if ma_sach not in theo:
            return None
        chuong = [theo[ma_sach][c] for c in sorted(theo[ma_sach])]
        sinh, mau = Lcg(self.seed), []
        for _ in range(self.so_vong):
            g = gia_tri_cuon(kieu, [chuong[sinh.chi_so(len(chuong))] for _ in chuong])
            if g is not None:
                mau.append(g)
        mau.sort()
        return {"gia_tri": gia_tri_cuon(kieu, chuong), "thap": _phan_vi(mau, 0.025) if mau else None,
                "cao": _phan_vi(mau, 0.975) if mau else None, "so_chuong": len(chuong)}

    def kiem_dinh_chinh_thuc(self):
        """Ba phép kiểm định chính thức: hoán vị ghép cặp, p sau Holm trên cả ba, sign test theo cuốn. Phép không tính được thì `p = None`."""
        ket, p_tho = {}, {}
        for ten, thuoc, a, b, thap_la_tot in T.KIEM_DINH:
            muc = {"hieu": None, "p": None, "so_lan": self.so_vong, "loi": None, "thang": 0, "thua": 0, "hoa": 0, "p_sign": None}
            sa, sb = _loc(self.rows, a, thuoc), _loc(self.rows, b, thuoc)
            if sa and sb:
                try:
                    hv = hoan_vi_ghep_cap(sa + sb, a, b, thuoc=thuoc, so_lan=self.so_vong, seed=self.seed)
                    muc.update(hieu=hv["hieu"], p=hv["p"])
                except ValueError:
                    muc["loi"] = "hai hệ không cùng tập chương"
                ca, cb = self.o(a, thuoc)["theo_cuon"], self.o(b, thuoc)["theo_cuon"]
                for s in sorted(set(ca) & set(cb)):
                    x, y = ca[s], cb[s]
                    if x is None or y is None:
                        continue
                    if abs(x - y) < 1e-12:
                        muc["hoa"] += 1
                    elif (x < y) == thap_la_tot:
                        muc["thang"] += 1
                    else:
                        muc["thua"] += 1
                muc["p_sign"] = sign_test(muc["thang"], muc["thua"])
            else:
                muc["loi"] = "thiếu hệ"
            ket[ten] = muc
            # phép không tính được vẫn chiếm một chỗ trong họ ba phép: p = 1 giữ hệ số Holm (3, 2, 1) cho các phép còn lại
            p_tho[ten] = muc["p"] if muc["p"] is not None else 1.0
        sau = holm(p_tho)
        for ten, muc in ket.items():
            muc["p_holm"] = sau[ten] if muc["p"] is not None else None
        return ket


def dai_nhieu(tinh_chinh, tinh_nhieu):
    """Dải min–max của macro hệ chính qua lượt chính cộng các lượt nhiễu, mỗi thước chất lượng. `tinh_nhieu`: các `Tinh` của lượt nhiễu (hệ đã đổi thành chinh)."""
    ket = {}
    for thuoc in T.THUOC_CHAT_LUONG:
        gia = []
        for t in (tinh_chinh, *tinh_nhieu):
            o = t.o("chinh", thuoc)
            if o is not None and o["macro"] is not None:
                gia.append(o["macro"])
        ket[thuoc] = {"min": min(gia), "max": max(gia), "so_luot": len(gia)} if len(gia) >= 2 else None
    return ket


def trong_dai_nhieu(macro_he, macro_chinh, dai):
    """Chênh với hệ chính nhỏ hơn bề rộng dải nhiễu K lượt thì không được tuyên bố hơn (giao thức mục 9)."""
    if dai is None or macro_he is None or macro_chinh is None:
        return False
    return abs(macro_he - macro_chinh) < dai["max"] - dai["min"]


def thac_nuoc(rows, he, meta_theo_sach, muc=T.MUC):
    """Tổng hợp quy lỗi qua mọi cuốn: tổng cạnh vàng trong phạm vi, bảy lý do, số đúng. Lý do "không áp" thì `None`, không phải 0."""
    def tong(ten):
        return sum(r["gia_tri"] for r in rows if r["he"] == he and r["thuoc"] == ten)

    sach = sorted({r["ma_sach"] for r in rows if r["he"] == he and r["thuoc"] == f"quy_loi.vang_pham_vi.{muc}"})
    if not sach:
        return None
    khong_ap = set()
    for s in sach:
        khong_ap |= set(meta_theo_sach.get(s, {}).get("khong_ap", ()))
    ly_do = {}
    for i in T.LY_DO:
        v = tong(f"quy_loi.ly_do_{i}.{muc}")
        if i in khong_ap:
            if v:
                raise ValueError(f"lý do {i} được khai không áp nhưng có {v} cạnh")
            ly_do[i] = None
        else:
            ly_do[i] = v
    ket = {"he": he, "so_cuon": len(sach), "tong": tong(f"quy_loi.vang_pham_vi.{muc}"), "dung": tong(f"quy_loi.dung.{muc}"),
           "ly_do": ly_do, "khong_ap": sorted(khong_ap)}
    if ket["dung"] + sum(v for v in ly_do.values() if v) != ket["tong"]:
        raise ValueError("tổng đúng + bảy lý do khác tổng cạnh vàng: dữ liệu quy lỗi không khép kín")
    return ket


def g5_tong(g5, doi_he):
    """Rubric trung bình theo hệ (trọng số số mục mỗi người) và tỉ lệ thắng theo hệ và theo cặp trong vòng tròn so sánh. Thăm dò, không kiểm định."""
    ten = lambda h: doi_he.get(h, h)  # noqa: E731
    tong, so, cap = {}, {}, {}
    for k in g5["theo_nguoi"].values():
        for he, r in k["rubric"].items():
            if r["trung_binh"] is not None:
                tong[ten(he)] = tong.get(ten(he), 0.0) + r["trung_binh"] * r["n"]
                so[ten(he)] = so.get(ten(he), 0) + r["n"]
        for ten_cap, d in k["so_sanh"].items():
            goc_a, goc_b = ten_cap.split("~")
            a, b = ten(goc_a), ten(goc_b)
            ben = sorted((a, b), key=lambda h: (T.thu_tu_he(h), h))
            c = cap.setdefault("~".join(ben), {"he": ben, "thang": {a: 0, b: 0}, "hoa": 0})
            c["thang"][a] += d[goc_a]
            c["thang"][b] += d[goc_b]
            c["hoa"] += d["hoa"]
    rubric = {he: {"trung_binh": tong[he] / so[he], "n": so[he]} for he in tong}
    theo_he = {}
    for c in cap.values():
        n = sum(c["thang"].values()) + c["hoa"]
        for h in c["he"]:
            t = theo_he.setdefault(h, {"thang": 0, "n": 0})
            t["thang"] += c["thang"][h]
            t["n"] += n
    for t in theo_he.values():
        t["ti_le"] = t["thang"] / t["n"] if t["n"] else None
        t["wilson"] = wilson(t["thang"], t["n"]) if t["n"] else None
    return {"rubric": rubric, "ti_le_thang": theo_he, "cap": cap}
