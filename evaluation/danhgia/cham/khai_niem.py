"""Thước khâu khái niệm (A3, A4, A5), truy nguyên, thước phụ so với B5 và trần người (vé DG-10; spec mục 8). Thuần: không đọc kho, không
gọi mô hình, không nhập `doc2roadmap`. Văn bản sách vào dưới dạng dữ liệu `{trang: chữ}`.

Đầu ra là dòng số đếm theo chương (`dong`), mỗi thước hai mức căn `nghiem` (chỉ `khop`) và `noi` (cộng `may_rong_hon`, `may_hep_hon`):
- `a3.do_phu.*`: khái niệm G3 dạy ở đây hoặc qua ví dụ có node (hiện diện) căn; `dau_cuoi.do_phu_day_hoc.*`: như vậy nhưng node phải trong dãy học.
- `a4.ti_le_tach.*`: khái niệm vàng có >= 1 node trong dãy học căn; tử là khái niệm có >= 2 node trong dãy học.
  `a4.ti_le_gop_nham.*`: node trong dãy học căn >= 1 khái niệm G3 (tính vào chương của khái niệm G3 đứng đầu theo thứ tự G3); tử là node căn >= 2 khái niệm vàng.
  `a4.bcubed_p.*`, `a4.bcubed_r.*`: B-cubed trên các liên kết (khái niệm G3, node trong dãy học) đã căn: P của liên kết = 1/số khái niệm vàng của node, R = 1/số node
  trong dãy của khái niệm vàng; trung bình theo liên kết.
- `a5.cau_neo_dung.*`: cặp (khái niệm vàng, node hiện diện) căn mà khái niệm vàng có câu định nghĩa; tử là câu neo trùng câu vàng (cùng trang, độ giống >= ngưỡng).
  `a5.cau_neo_cung_trang.*` (mức nới): hoặc câu neo ở cùng trang với câu định nghĩa. Hợp đồng chỉ mang trang và mã chunk của câu neo, không mang khoảng chunk
  của câu vàng, nên "cùng chunk" của spec được xấp xỉ bằng cùng trang.
  `a5.trang_thai_chinh_xac.*` (trên phần không `uncertain`), `a5.trang_thai_phu.*` (độ phủ), `a5.nham.<vàng>.<máy>.*` (ma trận bốn trạng thái vàng x sáu trạng thái máy).
  Ánh xạ sáu máy sang bốn vàng đọc từ tệp giao thức (`doc_anh_xa`): giá trị `null` là không quyết định (ra khỏi mẫu số độ chính xác), danh sách là các
  trạng thái vàng được coi là đúng (danh sách rỗng: không bao giờ đúng).
- `truy_nguyen.*` (chương `toan_sach`; mức `nghiem`/`noi` là hai ngưỡng khớp mờ, không phải mức căn): câu neo và câu bằng chứng của cạnh khớp mờ trong văn bản trang; câu
  được khớp trên trang ghi kèm, trang đó nối với trang liền sau, và trang liền trước nối với nó, như nhau cho mọi hệ (câu vắt hai trang không bị tính là bịa).
  `truy_nguyen.khai_niem_bia` (tên và mọi tên khác đều không có trong văn bản sách), `truy_nguyen.khai_niem_co_bang_chung`, `truy_nguyen.canh_co_bang_chung`.
- `tran_nguoi.<người>.a8.*`: F1 của hệ so với vàng thô của từng người, mỗi người một lần chấm.
"""
from __future__ import annotations

import json
from pathlib import Path

from danhgia.phieu.kiem import do_khop_cau
from danhgia.ten import am_tiet, do_giong

from . import bang, dong
from .can import MUC_CAN, bang_node

TRANG_THAI_DAY = ("day_o_day", "day_qua_vi_du")
TRANG_THAI_VANG = (*TRANG_THAI_DAY, "chi_nhac", "kien_thuc_nen")
TRANG_THAI_MAY = ("taught", "uncertain", "mentioned_only", "unchecked", "prior_knowledge", "not_subject_matter")
NGUONG_CAU_NEO = 0.9
NGUONG_TRUY_NGUYEN = {"nghiem": 0.9, "noi": 0.75}   # nháp; Claude chốt vào giao thức ở DG-18


def kiem_anh_xa(anh_xa):
    ax = anh_xa["may_sang_vang"]
    thieu = [t for t in TRANG_THAI_MAY if t not in ax]
    if thieu:
        raise ValueError(f"ánh xạ trạng thái thiếu giá trị máy {thieu}")
    for may, vang in ax.items():
        if may not in TRANG_THAI_MAY:
            raise ValueError(f"ánh xạ trạng thái có giá trị máy lạ {may!r}")
        if vang is not None:
            la = [v for v in vang if v not in TRANG_THAI_VANG]
            if la:
                raise ValueError(f"ánh xạ trạng thái: {may} -> {la} không phải trạng thái vàng")


def doc_anh_xa(duong):
    anh_xa = json.loads(Path(duong).read_text(encoding="utf-8"))
    kiem_anh_xa(anh_xa)
    return anh_xa


def _hien_dien(hd):
    return {k["ma"]: k for k in hd["khai_niem"] if not k["bi_loai"] and not k["da_gop"]}


def _chuan_van_ban(van_ban):
    return {int(k): v for k, v in van_ban.items()}


def cham_khai_niem(hd, g3, g4, can, van_ban, anh_xa, *, ma_sach=None, nguong_cau_neo=NGUONG_CAU_NEO,
                   nguong_truy_nguyen=None):
    """Dòng số đếm A3, A4, A5 (và truy nguyên nếu có `van_ban`). `g4` chỉ để kiểm cùng sách và để căn nguồn "ngoài" nếu cần."""
    kiem_anh_xa(anh_xa)
    ma_sach = ma_sach or g3["ma_sach"]
    for ten, tep in (("G3", g3), ("G4", g4), ("bảng căn", can)):
        if tep["ma_sach"] != ma_sach:
            raise ValueError(f"{ten} thuộc sách {tep['ma_sach']!r}, không phải {ma_sach!r}")
    he = hd["dinh_danh"]["he"]
    hien = _hien_dien(hd)
    trong_day = {ma for ma, k in hien.items() if k["trong_day_hoc"]}
    vang = {k["ma"]: k for k in g3["khai_niem"]}
    chuong_co = list(dict.fromkeys(k["chuong"] for k in g3["khai_niem"]))
    thu_tu = {ma: i for i, ma in enumerate(vang)}
    ax = anh_xa["may_sang_vang"]
    la = sorted({k["trang_thai_day"] for k in hien.values()} - set(ax))
    if la:
        raise ValueError(f"trạng thái dạy của máy {la} không có trong ánh xạ giao thức")
    rows = []
    for muc in MUC_CAN:
        nut_cua_vang, vang_cua_nut = bang_node(can, muc, hd["ban_do_danh_tinh"])
        nut_h = {g: {n for n in ns if n in hien} for g, ns in nut_cua_vang.items()}
        nut_d = {g: ns & trong_day for g, ns in nut_h.items()}
        vang_cua_nut_d = {}
        for g, ns in nut_d.items():
            for n in ns:
                vang_cua_nut_d.setdefault(n, set()).add(g)
        chuong_nut = {n: min((g for g in gs if g in vang), key=thu_tu.get, default=None) for n, gs in vang_cua_nut_d.items()}
        for chuong in chuong_co:
            ma_c = [m for m, k in vang.items() if k["chuong"] == chuong]
            day = [m for m in ma_c if vang[m]["trang_thai"] in TRANG_THAI_DAY]
            rows.append(dong.ti_le(he, ma_sach, chuong, f"a3.do_phu.{muc}", sum(bool(nut_h.get(m)) for m in day), len(day)))
            rows.append(dong.ti_le(he, ma_sach, chuong, f"dau_cuoi.do_phu_day_hoc.{muc}", sum(bool(nut_d.get(m)) for m in day), len(day)))
            co_node = [m for m in ma_c if nut_d.get(m)]
            rows.append(dong.ti_le(he, ma_sach, chuong, f"a4.ti_le_tach.{muc}", sum(len(nut_d[m]) >= 2 for m in co_node), len(co_node)))
            nut_chuong = [n for n, c in chuong_nut.items() if c is not None and vang[c]["chuong"] == chuong]
            rows.append(dong.ti_le(he, ma_sach, chuong, f"a4.ti_le_gop_nham.{muc}",
                                   sum(len(vang_cua_nut_d[n]) >= 2 for n in nut_chuong), len(nut_chuong)))
            lien_ket = [(g, n) for g in co_node for n in nut_d[g]]
            rows.append(dong.trung_binh(he, ma_sach, chuong, f"a4.bcubed_p.{muc}",
                                        sum(1 / len(vang_cua_nut_d[n]) for _, n in lien_ket), len(lien_ket)))
            rows.append(dong.trung_binh(he, ma_sach, chuong, f"a4.bcubed_r.{muc}",
                                        sum(1 / len(nut_d[g]) for g, _ in lien_ket), len(lien_ket)))
            cap = [(m, n) for m in ma_c for n in sorted(nut_h.get(m, ()))]
            co_cau = [(m, n) for m, n in cap if am_tiet(vang[m]["dinh_nghia"]["cau"])]
            dung = cung_trang = 0
            for m, n in co_cau:
                neo, dn = hien[n]["cau_neo"], vang[m]["dinh_nghia"]
                if neo is None:
                    continue
                cung = neo["trang"] == dn["trang"]
                khop = cung and am_tiet(neo["cau"]) and do_giong(neo["cau"], dn["cau"]) >= nguong_cau_neo
                dung += bool(khop)
                cung_trang += bool(khop or cung)
            rows.append(dong.ti_le(he, ma_sach, chuong, f"a5.cau_neo_dung.{muc}", dung, len(co_cau)))
            rows.append(dong.ti_le(he, ma_sach, chuong, f"a5.cau_neo_cung_trang.{muc}", cung_trang, len(co_cau)))
            quyet = [(m, n) for m, n in cap if ax[hien[n]["trang_thai_day"]] is not None]
            rows.append(dong.ti_le(he, ma_sach, chuong, f"a5.trang_thai_chinh_xac.{muc}",
                                   sum(vang[m]["trang_thai"] in ax[hien[n]["trang_thai_day"]] for m, n in quyet), len(quyet)))
            rows.append(dong.ti_le(he, ma_sach, chuong, f"a5.trang_thai_phu.{muc}", len(quyet), len(cap)))
            dem_nham = {}
            for m, n in cap:
                khoa = (vang[m]["trang_thai"], hien[n]["trang_thai_day"])
                dem_nham[khoa] = dem_nham.get(khoa, 0) + 1
            for tv in TRANG_THAI_VANG:
                for tm in TRANG_THAI_MAY:
                    rows.append(dong.dem(he, ma_sach, chuong, f"a5.nham.{tv}.{tm}.{muc}", dem_nham.get((tv, tm), 0)))
    if van_ban:
        rows += truy_nguyen(hd, van_ban, ma_sach=ma_sach, nguong=nguong_truy_nguyen)
    return rows


# ---------------------------------------------------------------- truy nguyên


def diem_cau(cau, trang, van_ban):
    """Độ khớp mờ lớn nhất của `cau` với văn bản trang `trang`, trang đó nối trang liền sau, và trang liền trước nối với nó."""
    if trang is None:
        return 0.0
    cu = lambda t: van_ban.get(t, "")  # noqa: E731
    bien = [cu(trang), f"{cu(trang - 1)} {cu(trang)}", f"{cu(trang)} {cu(trang + 1)}"]
    return max((do_khop_cau(cau, t) for t in bien if t.strip()), default=0.0)


def _cau_co_that(hd, van_ban):
    """Danh sách (loại, mã, trang, câu, điểm) của mọi câu neo (node hiện diện) và câu bằng chứng (cạnh không bỏ qua) có chữ."""
    ket = []
    for ma, k in _hien_dien(hd).items():
        neo = k["cau_neo"]
        if neo is not None and am_tiet(neo["cau"]):
            ket.append(("cau_neo", ma, neo["trang"], neo["cau"], diem_cau(neo["cau"], neo["trang"], van_ban)))
    for c in hd["canh"]:
        bc = c["bang_chung"]
        if not c["bo_qua"] and bc is not None and am_tiet(bc["cau"]):
            ket.append(("cau_canh", f"{c['nguon']}>{c['dich']}", bc["trang"], bc["cau"], diem_cau(bc["cau"], bc["trang"], van_ban)))
    return ket


def truy_nguyen(hd, van_ban, *, ma_sach=None, nguong=None):
    nguong = nguong or NGUONG_TRUY_NGUYEN
    van_ban = _chuan_van_ban(van_ban)
    he, ma_sach = hd["dinh_danh"]["he"], ma_sach or hd["dinh_danh"]["doc_id"]
    hien = _hien_dien(hd)
    cau = _cau_co_that(hd, van_ban)
    rows = []
    for muc, nguong_muc in nguong.items():
        theo_loai = {loai: [d for l, _, _, _, d in cau if l == loai] for loai in ("cau_neo", "cau_canh")}
        for loai, ten in (("cau_neo", "cau_neo_co_that"), ("cau_canh", "cau_canh_co_that")):
            rows.append(dong.ti_le(he, ma_sach, "toan_sach", f"truy_nguyen.{ten}.{muc}",
                                   sum(d >= nguong_muc for d in theo_loai[loai]), len(theo_loai[loai])))
        tat_ca = theo_loai["cau_neo"] + theo_loai["cau_canh"]
        rows.append(dong.ti_le(he, ma_sach, "toan_sach", f"truy_nguyen.bang_chung_co_that.{muc}",
                               sum(d >= nguong_muc for d in tat_ca), len(tat_ca)))
    van = " ".join(" ".join(am_tiet(van_ban[t])) for t in sorted(van_ban))
    van = f" {van} "
    bia = sum(not any((ten_ := " ".join(am_tiet(t))) and f" {ten_} " in van for t in [k["ten"], *(k["ten_khac"] or [])])
              for k in hien.values())
    rows.append(dong.ti_le(he, ma_sach, "toan_sach", "truy_nguyen.khai_niem_bia", bia, len(hien)))
    rows.append(dong.ti_le(he, ma_sach, "toan_sach", "truy_nguyen.khai_niem_co_bang_chung",
                           sum(k["cau_neo"] is not None and bool(am_tiet(k["cau_neo"]["cau"])) for k in hien.values()), len(hien)))
    canh = [c for c in hd["canh"] if not c["bo_qua"]]
    rows.append(dong.ti_le(he, ma_sach, "toan_sach", "truy_nguyen.canh_co_bang_chung",
                           sum(c["bang_chung"] is not None for c in canh), len(canh)))
    return rows


def ca_truot(hd, van_ban, *, nguong=None):
    """Mọi câu neo hay câu bằng chứng có chữ mà độ khớp dưới ngưỡng (mặc định ngưỡng nghiêm), để người đọc xem lỗi của bộ khớp."""
    nguong = NGUONG_TRUY_NGUYEN["nghiem"] if nguong is None else nguong
    van_ban = _chuan_van_ban(van_ban)
    return [{"loai": l, "ma": m, "trang": t, "cau": c, "diem": round(d, 3)} for l, m, t, c, d in _cau_co_that(hd, van_ban) if d < nguong]


# ---------------------------------------------------------------- thước phụ so với B5, trần người


def bang_theo_vi_tri_chuong(rows, g3, *, muc="nghiem"):
    """Độ phủ và tỉ lệ tách theo vị trí chương (thứ tự chương trong G3), cho thước phụ so với B5 (Q38)."""
    ket = []
    for vi_tri, chuong in enumerate(dict.fromkeys(k["chuong"] for k in g3["khai_niem"])):
        gia = {r["thuoc"]: dong.gia_tri(r) for r in rows if r["chuong"] == chuong}
        ket.append({"chuong": chuong, "vi_tri": vi_tri, "do_phu": gia[f"a3.do_phu.{muc}"], "ti_le_tach": gia[f"a4.ti_le_tach.{muc}"]})
    return ket


def tran_nguoi(hd, vang_theo_nguoi, *, ma_sach=None, vang="chinh"):
    """F1 của hệ (trực tiếp và bao đóng) so với vàng thô của từng người: mỗi người `(g3, g4, can)` là một lần chấm riêng với
    đúng vàng của người đó (chưa hội ý). Thước `tran_nguoi.<người>.a8.*`; gói thống kê chỉ gộp số đếm."""
    if not vang_theo_nguoi:
        raise ValueError("cần ít nhất một người")
    rows = []
    for nguoi, (g3, g4, can) in vang_theo_nguoi.items():
        for r in bang.cham(hd, g3, g4, can, ma_sach=ma_sach, vang=vang):
            if r["thuoc"].startswith(("a8.f1_truc_tiep", "a8.f1_bao_dong")):
                rows.append({**r, "thuoc": f"tran_nguoi.{nguoi}.{r['thuoc']}"})
    return rows
