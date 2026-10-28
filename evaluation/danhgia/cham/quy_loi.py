"""Quy lỗi theo khâu (vé DG-15; spec mục 10, Bảng 8 và Hình 4 của bản hội đồng). Thuần: không đọc kho, không gọi mô hình, không nhập `doc2roadmap`.

Mỗi cạnh vàng trong phạm vi (cạnh G4 "văn bản thể hiện" có đích trong chương bốc) mà lộ trình làm sai, tức hỏng Q6 (đặt ngược, hoặc có đầu không có trong dãy
học, đúng định nghĩa `a10.q6`), được gán vào **lý do đầu tiên** trong bảy lý do, theo đúng thứ tự spec và chỉ một lý do:
1. câu định nghĩa của một đầu nằm trong mục hệ cắt sai hoặc gán vai trò khác `noi_dung` (A1, A2); đầu vào `muc_loi` là tập khái niệm vàng thuộc diện đó, `None` là
   cờ "không áp" (chưa có G2): cạnh rơi sang lý do kế;
2. một đầu không có node hiện diện căn `khop` (A3; nguồn ngoài sách luôn thuộc lý do này);
3. một đầu bị tách (>= 2 node trong dãy học) hoặc gộp nhầm (node trong dãy căn >= 2 khái niệm vàng, kể cả hai đầu dồn vào một node) (A4);
4. một đầu có node nhưng không node nào trong dãy học (trạng thái làm nó ra khỏi dãy, A5);
5. không có cạnh máy đúng chiều giữa các node của hai đầu, cặp không nằm trong tập cặp đã xét và nguồn không nằm trong cửa sổ định nghĩa của đích (A6/A7);
6. không có cạnh máy đúng chiều (A8 không đề xuất), dù cặp có trong tập cặp đã xét hay trong cửa sổ;
7. có cạnh máy đúng chiều (kể cả cạnh mềm, R17) nhưng dãy học vẫn đặt ngược (A9/A10).

Diễn giải cần Claude duyệt (ghi ở báo cáo): lý do 5 và 6 chỉ xét khi **chưa có cạnh máy đúng chiều**, vì cạnh do pass chính tạo ra không cần nằm trong tập cặp
ứng viên. Hệ không có `cap_ung_vien` (B5, baseline) không phân biệt được 5 và 6: mọi cạnh như vậy vào lý do 6 và `meta.ly_do_5_khong_ap` là true.
`cua_so_dinh_nghia` của hợp đồng có dạng `{node đích: [node nguồn có tên trong cửa sổ]}`; bộ xuất hiện để `None`, khi đó chỉ cặp ứng viên được xét và
`meta.cua_so_thieu` là true.

Cạnh máy ngoài vàng (đích trong phạm vi) được xếp loại theo thứ tự: `dung_g5b` (G5(b) đã phán đúng), `nguoc_chieu` (cạnh ngược có trong vàng), `bac_cau` (nằm
trong bao đóng bắc cầu của vàng), `sai_han`; cạnh có trong vàng là `trong_vang`.

Danh sách cạnh theo lý do (`danh_sach`) chỉ có khi `tap == "phat_trien"` và `co_danh_sach`; tập thử không bao giờ trả danh sách (ném lỗi nếu hỏi).
"""
from __future__ import annotations

from . import a8, a10, dong
from .can import anh_xa_canh, doc_vang
from .do_thi import dong_bao

LY_DO = (1, 2, 3, 4, 5, 6, 7)
TEN_LY_DO = {1: "muc_cat_sai_hoac_vai_tro", 2: "khong_trich_duoc_khai_niem", 3: "gop_nham_hoac_tach", 4: "ra_khoi_day_hoc",
             5: "cap_khong_duoc_xet", 6: "a8_khong_de_xuat", 7: "bi_lam_mem_hoac_xep_sai"}
LOAI_MAY = ("trong_vang", "dung_g5b", "nguoc_chieu", "bac_cau", "sai_han")
TAP = ("phat_trien", "thu")


def _hien_dien(hd):
    return {k["ma"] for k in hd["khai_niem"] if not k["bi_loai"] and not k["da_gop"]}


def _cap_ung_vien(hd):
    """(tập cặp node đã xét, cửa sổ {đích: tập nguồn}, có thông tin ứng viên không, có cửa sổ không)."""
    cuv = hd["cap_ung_vien"]
    if cuv is None:
        return set(), {}, False, False
    danh_tinh = hd["ban_do_danh_tinh"]
    chuan = lambda n: danh_tinh.get(n, n)  # noqa: E731
    cap = {frozenset((chuan(c["trai"]), chuan(c["phai"]))) for c in cuv["cap"]}
    cua_so = cuv["cua_so_dinh_nghia"]
    if cua_so is None:
        return cap, {}, True, False
    if not isinstance(cua_so, dict) or any(not isinstance(v, list) for v in cua_so.values()):
        raise ValueError("cua_so_dinh_nghia phải có dạng {node đích: [node nguồn]}")
    return cap, {chuan(d): {chuan(n) for n in ns} for d, ns in cua_so.items()}, True, True


def _ly_do(a, b, *, muc_loi, hien_nut, hang, vang_cua_nut_day, canh_may, cap_xet, cua_so, co_ung_vien):
    """Lý do đầu tiên (1..7) của cạnh vàng `(a, b)` đã hỏng Q6. Một chuỗi if: một cạnh chỉ có một lý do."""
    if muc_loi is not None and (a in muc_loi or b in muc_loi):
        return 1
    na, nb = hien_nut(a), hien_nut(b)
    if not na or not nb:
        return 2
    da, db = na & hang, nb & hang
    if len(da) >= 2 or len(db) >= 2 or any(len(vang_cua_nut_day[n]) >= 2 for n in da | db):
        return 3
    if not da or not db:
        return 4
    if any((u, v) in canh_may for u in na for v in nb):
        return 7
    if not co_ung_vien:
        return 6
    da_xet = any(frozenset((u, v)) in cap_xet or u in cua_so.get(v, ()) for u in na for v in nb)
    return 6 if da_xet else 5


def quy_loi(hd, g3, g4, can, *, tap, muc="nghiem", vang="chinh", mem="cung", muc_loi=None, g5b=None, co_danh_sach=False, ma_sach=None):
    """Trả `{"rows": [...], "danh_sach": [...] hoặc None, "meta": {...}}`; `rows` là dòng `dong.dem` theo chương (xem `kiem_tong`)."""
    if tap not in TAP:
        raise ValueError(f"tap phải là một trong {TAP}, không phải {tap!r}")
    if co_danh_sach and tap != "phat_trien":
        raise ValueError("tập thử không in danh sách cạnh theo lý do: chỉ in số")
    if hd["lo_trinh"] is None:
        raise ValueError("hệ không có lộ trình (lo_trinh null): không có Q6 nên không quy lỗi")
    ma_sach = ma_sach or g3["ma_sach"]
    for ten, tep in (("G3", g3), ("G4", g4), ("bảng căn", can)):
        if tep["ma_sach"] != ma_sach:
            raise ValueError(f"{ten} thuộc sách {tep['ma_sach']!r}, không phải {ma_sach!r}")
    he = hd["dinh_danh"]["he"]
    chuong_co = list(dict.fromkeys(k["chuong"] for k in g3["khai_niem"]))
    cua = {k["ma"]: k["chuong"] for k in g3["khai_niem"]}
    ten_vang = {k["ma"]: k["ten"] for k in g3["khai_niem"]}
    v = doc_vang(g3, g4, can, muc, hd["ban_do_danh_tinh"], vang=vang)
    cap_vang, nut_cua_vang, vang_cua_nut = v["cap"], v["nut_cua_vang"], v["vang_cua_nut"]
    hien = _hien_dien(hd)
    hang_thu_tu = a10.hang_nut(hd["lo_trinh"]["day_hoc"])
    hang = set(hang_thu_tu)
    vi_tri = a10.vi_tri_vang(hang_thu_tu, nut_cua_vang)
    hien_nut = lambda g: {n for n in nut_cua_vang.get(g, ()) if n in hien}  # noqa: E731
    vang_cua_nut_day = {}
    for g_, ns in nut_cua_vang.items():
        for n in ns:
            if n in hien and n in hang:
                vang_cua_nut_day.setdefault(n, set()).add(g_)
    cap_xet, cua_so, co_ung_vien, co_cua_so = _cap_ung_vien(hd)
    canh_ca_mem = a8.canh_may(hd, mem="ca_hai")
    tham_so = dict(muc_loi=muc_loi, hien_nut=hien_nut, hang=hang, vang_cua_nut_day=vang_cua_nut_day, canh_may=canh_ca_mem,
                   cap_xet=cap_xet, cua_so=cua_so, co_ung_vien=co_ung_vien)

    dem = {c: {"vang": 0, "dung": 0, **{i: 0 for i in LY_DO}, **{m: 0 for m in LOAI_MAY}} for c in chuong_co}
    danh_sach = [] if co_danh_sach else None
    for a, b in sorted(cap_vang):
        c = cua[b]
        dem[c]["vang"] += 1
        if a in vi_tri and b in vi_tri and vi_tri[a] < vi_tri[b]:    # đúng: phủ định của điều kiện lỗi trong a10.q6
            dem[c]["dung"] += 1
            continue
        ly_do = _ly_do(a, b, **tham_so)
        dem[c][ly_do] += 1
        if danh_sach is not None:
            danh_sach.append({"chuong": c, "nguon": a, "dich": b, "ten_nguon": ten_vang.get(a, a), "ten_dich": ten_vang.get(b, b),
                              "ly_do": ly_do, "ten_ly_do": TEN_LY_DO[ly_do]})

    phan = {} if g5b is None else dict(g5b)
    dong_bao_vang = dong_bao(cap_vang)
    may = anh_xa_canh(a8.canh_may(hd, mem=mem), vang_cua_nut)
    for a, b in sorted(may):
        if b not in cua:
            continue    # đích ngoài phạm vi (kể cả đích ảo của node chưa căn): không thuộc mẫu số A8
        loai = ("trong_vang" if (a, b) in cap_vang else "dung_g5b" if phan.get((a, b)) == "dung" else
                "nguoc_chieu" if (b, a) in cap_vang else "bac_cau" if (a, b) in dong_bao_vang else "sai_han")
        dem[cua[b]][loai] += 1

    rows = []
    for c in chuong_co:
        rows.append(dong.dem(he, ma_sach, c, f"quy_loi.vang_pham_vi.{muc}", dem[c]["vang"]))
        rows.append(dong.dem(he, ma_sach, c, f"quy_loi.dung.{muc}", dem[c]["dung"]))
        for i in LY_DO:
            rows.append(dong.dem(he, ma_sach, c, f"quy_loi.ly_do_{i}.{muc}", dem[c][i]))
        for m in LOAI_MAY:
            rows.append(dong.dem(he, ma_sach, c, f"quy_loi.may.{m}.{muc}", dem[c][m]))
    kiem_tong(rows)
    meta = {"khong_ap": [1] if muc_loi is None else [], "ly_do_5_khong_ap": not co_ung_vien,
            "cua_so_thieu": co_ung_vien and not co_cua_so, "so_canh_vang": len(cap_vang)}
    return {"rows": rows, "danh_sach": danh_sach, "meta": meta}


def kiem_tong(rows):
    """Mỗi chương: cạnh đúng cộng tổng bảy lý do bằng tổng cạnh vàng trong phạm vi (không cạnh nào bị mất hay đếm hai lần)."""
    theo = {}
    for r in rows:
        if r["thuoc"].startswith("quy_loi.") and not r["thuoc"].startswith("quy_loi.may."):
            ten, muc = r["thuoc"].rsplit(".", 1)
            theo.setdefault((r["chuong"], muc), {})[ten] = r["gia_tri"]
    for (chuong, muc), gia in theo.items():
        tong = gia["quy_loi.dung"] + sum(gia[f"quy_loi.ly_do_{i}"] for i in LY_DO)
        if tong != gia["quy_loi.vang_pham_vi"]:
            raise ValueError(f"tổng đúng + lý do = {tong} khác tổng cạnh vàng {gia['quy_loi.vang_pham_vi']} ở chương {chuong}, mức {muc}")


def muc_loi_tu_a1a2(g3_khai_niem, vang_g1, du_doan, bang_dong, *, nguong_cau=None):
    """Tập khái niệm vàng có câu định nghĩa nằm trong mục mà hệ cắt sai (lá của hệ không khớp lá vàng) hoặc gán vai trò khác `noi_dung`.
    Định vị câu như `a1a2.cham` (lỗi có hại); khái niệm không có câu hay không định vị được không bị tính là lỗi (đếm ở `khong_dinh_vi`).
    Trả `(tập khái niệm, số khái niệm không định vị được)`."""
    from . import a1a2

    nguong = a1a2.NGUONG_DINH_VI if nguong_cau is None else nguong_cau
    tieu_de = du_doan["headings"]
    khop = a1a2.khop_tieu_de(vang_g1, tieu_de, {d["id"]: d["trang"] for d in bang_dong})
    la_vang = a1a2.la_theo_vi_tri(vang_g1, bang_dong)
    if du_doan.get("lines") is not None:
        la_he = {x: v.get("leaf") for x, v in du_doan["lines"].items()}
    else:
        la_he = a1a2.la_theo_vi_tri([p for p in tieu_de if p["dong"]], bang_dong)
    hdoc = {p["id"]: p for p in tieu_de}
    theo_trang = {}
    for d in bang_dong:
        theo_trang.setdefault(d["trang"], []).append(d)
    loi, khong = set(), 0
    for kn in g3_khai_niem:
        dn = kn["dinh_nghia"]
        if not dn.get("cau") or dn.get("trang") is None:
            continue
        x = a1a2._dinh_vi_cau(dn["cau"], dn["trang"], theo_trang.get(dn["trang"], []), nguong)
        if x is None:
            khong += 1
            continue
        hl = la_he.get(x)
        vai_tro = hdoc[hl].get("vai_tro") if hl in hdoc else None
        cat_sai = khop.get(hl) != la_vang.get(x)
        if cat_sai or vai_tro != "noi_dung":
            loi.add(kn["ma"])
    return loi, khong
