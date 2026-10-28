"""Thước A1 (cấu trúc) và A2 (vai trò vùng), vé DG-13. Thuần: không đọc kho, không nhập `doc2roadmap`.

Định nghĩa M1, M2, M3 viết lại gọn từ `scripts/a1-d02/cham_d02.py` (test đối chiếu chạy chính bộ chấm đó bằng tiến trình con):
- M1: hai tiêu đề khớp khi dòng chung với tiêu đề vàng chiếm từ nửa số dòng của tiêu đề vàng trở lên (mã dòng mang số trang nên
  "cùng trang" nằm sẵn trong mã), ghép một-một cực đại. `a1.m1` là F1 (tp/fp/fn); `a1.complete_entry`: khớp thêm cùng cấp và cùng trang đầu.
- M2: trên tiêu đề khớp, cha của tiêu đề hệ ánh xạ về đúng cha của tiêu đề vàng; mẫu số là số tiêu đề khớp (`a1.m2`).
- M3 (`a1.m3`): tỉ lệ ký tự thân bài (không tính khoảng trắng) có mục sâu nhất (lá) trùng vàng. Thân bài: nếu có nhãn trang mẫu (L2)
  thì các dòng `than_bai`/`danh_sach` của chúng; nếu không (G1 không có L2) thì mọi dòng trừ `evaluation_excluded` (đầu trang, chân trang, số trang).
- A2 theo mục vàng (G2 = `vai_tro` của tiêu đề vàng): `a2.recall_noi_dung_muc` và `a2.recall_noi_dung_ky_tu`; `a2.f1_vai_tro.<vai trò>` (macro-F1 bằng
  `macro_f1_vai_tro` trên số đếm cuốn); `a2.nham.<vàng>.<hệ>` (hệ là một trong sáu vai trò, `khong_co` nếu hệ không khai vai trò, `khong_khop` nếu mục
  vàng không có tiêu đề hệ khớp); lỗi có hại `a2.loi_co_hai`: khái niệm G3 **có câu định nghĩa và trang**, câu được định vị vào dòng trên trang đó (khớp mờ),
  mà mục hệ chứa dòng ấy không phải `noi_dung`; khái niệm không có câu không đếm, câu không định vị được đếm riêng ở `a2.khong_dinh_vi_cau`.
Dự đoán của hệ (`du_doan`): `headings` (id, dong, cap, cha, text, vai_tro), tùy chọn `lines` ({mã dòng: {leaf}}) và `evaluation_excluded`. Không có `lines` thì
lá của dòng lấy theo vị trí: tiêu đề gần nhất đứng trước. Hợp đồng `danh-gia-xuat-1` mang `cau_truc` chưa có mã dòng nên `du_doan_tu_hop_dong` định vị
tiêu đề bằng chữ và trang (xem câu hỏi trong báo cáo).
"""
from __future__ import annotations

import difflib
from collections import Counter

from danhgia.g1g2.phieu import tim_dong
from danhgia.phieu.kiem import do_khop_cau

from . import dong

VAI_TRO = ("noi_dung", "bai_tap", "de_cuong", "mo_dau", "hanh_chinh", "cuoi_sach")
THAN_BAI = {"than_bai", "danh_sach"}
NGUONG_DINH_VI = 0.75


def _trang(ma_dong):
    return int(ma_dong.split("-")[0][1:])


def _nhom(trang, chuong):
    if not chuong:
        return "toan_sach"
    for c in chuong:
        if c["trang_dau"] <= trang <= c["trang_cuoi"]:
            return c["ma"]
    return "ngoai_chuong"


def khop_tieu_de(vang, du_doan, trang_cua):
    """{id tiêu đề hệ: id tiêu đề vàng}, ghép một-một cực đại; khớp khi dòng chung trên một trang chiếm từ nửa số dòng vàng."""
    canh = {}
    for i, g in enumerate(vang):
        gs = set(g["dong"])
        ung = []
        for j, p in enumerate(du_doan):
            chung = gs & set(p["dong"])
            trang = Counter(trang_cua[x] for x in chung if x in trang_cua)
            if trang and max(trang.values()) * 2 >= len(gs):
                ung.append((len(chung), j))
        canh[i] = [j for _, j in sorted(ung, key=lambda t: (-t[0], t[1]))]
    chu = {}

    def them(i, da_xet):
        for j in canh[i]:
            if j in da_xet:
                continue
            da_xet.add(j)
            if j not in chu or them(chu[j], da_xet):
                chu[j] = i
                return True
        return False

    for i in canh:
        them(i, set())
    return {du_doan[j]["id"]: vang[i]["id"] for j, i in chu.items()}


def la_theo_vi_tri(tieu_de, bang):
    """{mã dòng: id tiêu đề gần nhất đứng trước (hoặc None)}; như `gold_leaves` của D-02."""
    mo = {x: h["id"] for h in tieu_de for x in h["dong"]}
    la, ket = None, {}
    for d in bang:
        la = mo.get(d["id"], la)
        ket[d["id"]] = la
    return ket


def _ky_tu(chuoi):
    return sum(not c.isspace() for c in chuoi)


def _dinh_vi_cau(cau, trang, dong_trang, nguong):
    """Mã dòng chứa chỗ bắt đầu của câu trên trang (khớp mờ >= nguong, rồi khối khớp dài nhất), hoặc None."""
    if not dong_trang or do_khop_cau(cau, " ".join(d["text"] for d in dong_trang)) < nguong:
        return None
    ranh, van = [], ""
    for d in dong_trang:
        ranh.append((len(van), d["id"]))
        van += d["text"].lower() + " "
    cau_n = " ".join(cau.lower().split())
    khoi = difflib.SequenceMatcher(None, van, cau_n, autojunk=False).find_longest_match(0, len(van), 0, len(cau_n))
    if khoi.size < 4:
        return None
    return [ma for bat_dau, ma in ranh if bat_dau <= khoi.a][-1]


def cham(vang, du_doan, bang_dong, *, he, ma_sach, chuong=None, trang_mau=None, g3_khai_niem=None, nguong_cau=NGUONG_DINH_VI):
    """Dòng số đếm A1 và A2. `vang`: tiêu đề G1 (có `vai_tro` cho A2). `bang_dong`: [{id, trang, text}]. `chuong`: [{ma, trang_dau, trang_cuoi}] hoặc None
    (một nhóm `toan_sach`); trang ngoài mọi chương vào nhóm `ngoai_chuong`, nên tổng các chương bằng số cả cuốn."""
    tieu_de = du_doan["headings"]
    trang_cua = {d["id"]: d["trang"] for d in bang_dong}
    theo_id = {d["id"]: d for d in bang_dong}
    nhom_ma = [c["ma"] for c in chuong] + ["ngoai_chuong"] if chuong else ["toan_sach"]
    nhom = lambda ma_dong: _nhom(trang_cua[ma_dong], chuong)  # noqa: E731
    khop = khop_tieu_de(vang, tieu_de, trang_cua)
    ngoc = {g["id"]: g for g in vang}
    hdoc = {p["id"]: p for p in tieu_de}
    dau = lambda h: h["dong"][0] if h["dong"] else None  # noqa: E731
    dem = {}

    def cong(ma_nhom, thuoc, **gia):
        d = dem.setdefault((ma_nhom, thuoc), {})
        for k, v in gia.items():
            d[k] = d.get(k, 0) + v

    # ------------------------------------------------ A1
    for g in vang:
        n = nhom(dau(g))
        co = g["id"] in khop.values()
        cong(n, "a1.m1", tp=co, fn=not co)
    for p in tieu_de:
        if p["id"] not in khop and dau(p) is not None:
            cong(nhom(dau(p)), "a1.m1", fp=1)
        elif p["id"] not in khop:
            cong(nhom_ma[-1], "a1.m1", fp=1)
    nguoc = {v: k for k, v in khop.items()}
    for g in vang:
        n = nhom(dau(g))
        p = hdoc.get(nguoc.get(g["id"]))
        tron = p is not None and p["cap"] == g["cap"] and _trang(dau(p)) == _trang(dau(g))
        cong(n, "a1.complete_entry", tp=tron, fn=not tron)
    for p in tieu_de:
        gid = khop.get(p["id"])
        g = ngoc.get(gid)
        tron = g is not None and p["cap"] == g["cap"] and _trang(dau(p)) == _trang(dau(g))
        if not tron:
            cong(nhom(dau(p)) if dau(p) is not None else nhom_ma[-1], "a1.complete_entry", fp=1)
    for p in tieu_de:
        if p["id"] not in khop:
            continue
        g = ngoc[khop[p["id"]]]
        cha = p.get("cha")
        thuc = None if cha is None else khop.get(cha, "<unmatched>")
        cong(nhom(dau(g)), "a1.m2", tu=thuc == g.get("cha"), mau=1)
    la_vang = la_theo_vi_tri(vang, bang_dong)
    if du_doan.get("lines") is not None:
        la_he = {x: v.get("leaf") for x, v in du_doan["lines"].items()}
        co_la = set(la_he)
    else:
        la_he, co_la = la_theo_vi_tri([p for p in tieu_de if p["dong"]], bang_dong), set(theo_id)
    loai = set(du_doan.get("evaluation_excluded", ()))
    if trang_mau is not None:
        vai_tro_dong = {x: r for t in trang_mau for x, r in t["dong"].items()}
        than = {x for x, r in vai_tro_dong.items() if r in THAN_BAI}
    else:
        than = set(theo_id) - loai
    for x in sorted(than):
        if x not in co_la:
            cong(nhom(x), "a1.m3_dong_thieu_trong_du_doan", gia_tri=1)   # tính sai ở M3 và đếm riêng, không bỏ lặng lẽ
        la = la_he.get(x) if x in co_la else None
        thuc = None if la is None else khop.get(la, "<unmatched>")
        cong(nhom(x), "a1.m3", tu=_ky_tu(theo_id[x]["text"]) * (x in co_la and thuc == la_vang[x]), mau=_ky_tu(theo_id[x]["text"]))
    # ------------------------------------------------ A2
    vai_tro_he = lambda gid: ("khong_khop" if gid not in nguoc else (hdoc[nguoc[gid]].get("vai_tro") or "khong_co"))  # noqa: E731
    for g in vang:
        if g.get("vai_tro") is None:
            continue
        n = nhom(dau(g))
        h = vai_tro_he(g["id"])
        if g["vai_tro"] == "noi_dung":
            cong(n, "a2.recall_noi_dung_muc", tu=h == "noi_dung", mau=1)
        cong(n, f"a2.nham.{g['vai_tro']}.{h}", gia_tri=1)
        for v in VAI_TRO:
            cong(n, f"a2.f1_vai_tro.{v}", tp=g["vai_tro"] == v == h, fn=g["vai_tro"] == v != h, fp=h == v != g["vai_tro"])
    for x in sorted(set(theo_id) - loai):
        gl = la_vang[x]
        if gl is None or ngoc[gl].get("vai_tro") != "noi_dung":
            continue
        hl = la_he.get(x) if x in co_la else None
        hv = hdoc[hl].get("vai_tro") if hl in hdoc else None
        cong(nhom(x), "a2.recall_noi_dung_ky_tu", tu=_ky_tu(theo_id[x]["text"]) * (hv == "noi_dung"), mau=_ky_tu(theo_id[x]["text"]))
    theo_trang = {}
    for d in bang_dong:
        theo_trang.setdefault(d["trang"], []).append(d)
    for kn in g3_khai_niem or ():
        dn = kn["dinh_nghia"]
        if not dn.get("cau") or dn.get("trang") is None:
            continue
        n = _nhom(dn["trang"], chuong)
        x = _dinh_vi_cau(dn["cau"], dn["trang"], theo_trang.get(dn["trang"], []), nguong_cau)
        if x is None:
            cong(n, "a2.khong_dinh_vi_cau", gia_tri=1)
            continue
        hl = la_he.get(x) if x in co_la else None
        hv = hdoc[hl].get("vai_tro") if hl in hdoc else None
        cong(n, "a2.loi_co_hai", tu=hv != "noi_dung", mau=1)
    # ------------------------------------------------ đổ ra dòng đủ mọi thước, mọi nhóm (số 0 vẫn có dòng)
    ky = {"a1.m1": "f1", "a1.complete_entry": "f1", "a1.m2": "ti_le", "a1.m3": "ti_le", "a2.recall_noi_dung_muc": "ti_le",
          "a2.recall_noi_dung_ky_tu": "ti_le", "a2.loi_co_hai": "ti_le", "a2.khong_dinh_vi_cau": "dem",
          "a1.m3_dong_thieu_trong_du_doan": "dem"}
    ky.update({f"a2.f1_vai_tro.{v}": "f1" for v in VAI_TRO})
    ky.update({f"a2.nham.{a}.{b}": "dem" for a in VAI_TRO for b in (*VAI_TRO, "khong_co", "khong_khop")})
    rows = []
    for n in nhom_ma:
        for thuoc, kieu in ky.items():
            d = dem.get((n, thuoc), {})
            if kieu == "f1":
                rows.append(dong.f1(he, ma_sach, n, thuoc, int(d.get("tp", 0)), int(d.get("fp", 0)), int(d.get("fn", 0))))
            elif kieu == "ti_le":
                rows.append(dong.ti_le(he, ma_sach, n, thuoc, int(d.get("tu", 0)), int(d.get("mau", 0))))
            else:
                rows.append(dong.dem(he, ma_sach, n, thuoc, int(d.get("gia_tri", 0))))
    return rows


def macro_f1_vai_tro(rows_cuon):
    """Macro-F1 sáu vai trò trên số đếm cuốn; vai trò không có mục vàng nào (F1 None) ra khỏi trung bình và được đếm riêng."""
    gia = [dong.gia_tri(r) for r in rows_cuon if r["thuoc"].startswith("a2.f1_vai_tro.")]
    co = [g for g in gia if g is not None]
    return {"gia_tri": sum(co) / len(co) if co else None, "so_vai_tro_co_so": len(co), "so_vai_tro": len(gia)}


def du_doan_tu_hop_dong(hd, bang_dong):
    """Dự đoán của hệ từ khối `cau_truc` của hợp đồng. Hợp đồng chưa có mã dòng, nên tiêu đề được định vị bằng chữ trên trang ghi kèm
    (rồi trang liền trước, vì `trang` của tiêu đề là trang nhỏ nhất của các chunk dưới nó); không định vị được thì `dong` rỗng và ghi vào `khong_dinh_vi`."""
    ct = hd["cau_truc"]
    if ct is None:
        raise ValueError("hợp đồng không có khối cau_truc")
    vai_tro = {m["ma"]: m["vai_tro"] for m in ct["muc"]}
    if ct["tieu_de"] and all(t["ma_dong"] is not None for t in ct["tieu_de"]) and "dong_thuoc_muc" in ct:
        # hợp đồng đã căn dòng ở seam xuất: dùng thẳng mã dòng và lá của từng dòng; dòng không căn được không có trong `lines` (tính sai ở M3, đếm riêng)
        tieu_de = [{"id": t["ma"], "dong": list(t["ma_dong"]), "cap": t["cap"], "cha": t["cha"], "text": t["chu"],
                    "vai_tro": vai_tro.get(t["ma"])} for t in ct["tieu_de"] if t["cap"] != 0]      # cấp 0 là gốc tài liệu, không phải tiêu đề
        return {"headings": tieu_de, "khong_dinh_vi": [t["id"] for t in tieu_de if not t["dong"]],
                "lines": {x: {"leaf": la} for x, la in ct["dong_thuoc_muc"].items()},
                "dong_khong_can": list(ct.get("dong_khong_can", [])), "evaluation_excluded": []}
    theo_trang = {}
    for d in bang_dong:
        theo_trang.setdefault(d["trang"], []).append(d)
    tieu_de, khong = [], []
    for t in (t for t in ct["tieu_de"] if t["cap"] != 0):
        ma_dong = []
        for trang in (t["trang"], None if t["trang"] is None else t["trang"] - 1):
            if trang is not None:
                ma_dong = tim_dong(theo_trang.get(trang, []), t["chu"]) or []
            if ma_dong:
                break
        if not ma_dong:
            khong.append(t["ma"])
        tieu_de.append({"id": t["ma"], "dong": ma_dong, "cap": t["cap"], "cha": t["cha"], "text": t["chu"], "vai_tro": vai_tro.get(t["ma"])})
    return {"headings": tieu_de, "khong_dinh_vi": khong, "evaluation_excluded": []}
