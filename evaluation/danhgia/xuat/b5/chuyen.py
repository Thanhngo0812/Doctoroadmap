"""Chuyển đầu ra B5 sang hợp đồng `danh-gia-xuat-1` (spec mục 2 và 11). Không nhập mã pipeline.

Luật của lời nhắc b5-1 (mục "Ghi chú cho bộ chuyển đổi"):
- khái niệm B5 luôn là `taught` (hợp đồng không có giá trị `defined_here`); câu neo là `cau_dinh_nghia` kèm trang;
- hợp nhất khái niệm (giữa các chương ở B5b, và trong một lời gọi) chỉ khi tên trùng sau `chuan_hoa`; không so tên khác, không gộp mờ;
- quan hệ trỏ tới tên không có trong `khai_niem`: không vá (không thêm khái niệm). Hợp đồng không chứa cạnh có đầu lạ,
  nên các quan hệ này đi vào báo cáo kèm số đếm `quan_he_tro_khai_niem_la`;
- câu trích được kiểm có thật trong sách và được đếm, nhưng không bị loại: thước truy nguyên của bộ chấm tự đếm câu bịa.
"""
from __future__ import annotations

from dataclasses import dataclass

from danhgia.hop_dong import kiem_hoac_loi
from danhgia.hop_dong.luoc_do import TEN_LUOC_DO
from danhgia.ten import chuan_hoa

PHIEN_BAN_LOI_NHAC = "b5-1"
KHAU = "b5"


class KhongCoLuotNaoThanhCong(ValueError):
    """Mọi lượt đều thất bại: không có gì để chuyển."""


@dataclass
class LuotCuaChuong:
    nhan: str      # "cuon" ở B5a, mã chương ở B5b
    dau: int
    cuoi: int
    luot: object   # goi.Luot


class _KiemCau:
    """Phân loại câu trích: đúng trang đã khai, trang khác trong phạm vi lời gọi, hoặc không có."""

    def __init__(self, doc_trang):
        self._doc, self._dem = doc_trang, {}

    def _trang(self, n):
        if n not in self._dem:
            self._dem[n] = chuan_hoa(self._doc(n))
        return self._dem[n]

    def phan_loai(self, cau, trang, dau, cuoi):
        chuan = chuan_hoa(cau)
        if not chuan:
            return "khong_co"
        if isinstance(trang, int) and chuan in self._trang(trang):
            return "dung_trang"
        if any(chuan in self._trang(n) for n in range(dau, cuoi + 1)):
            return "trang_khac"
        return "khong_co"


def _cong(a, b):
    return None if a is None and b is None else (a or 0) + (b or 0)


def _chi_phi(luots, that_bai):
    tong = {"giay_chay": None, "giay_cho_embedding": None, "so_loi_goi_mo_hinh": len(luots), "token_vao": None,
            "token_ra": None, "so_loi_goi_embedding": None, "usd": None}
    for l in luots:
        tong["giay_chay"] = _cong(tong["giay_chay"], l.luot.giay)
        tong["token_vao"] = _cong(tong["token_vao"], l.luot.token_vao)
        tong["token_ra"] = _cong(tong["token_ra"], l.luot.token_ra)
        tong["usd"] = _cong(tong["usd"], l.luot.usd)
    ghi_chu = None
    if that_bai:
        ghi_chu = "lượt thất bại: " + "; ".join(
            f"{t['nhan']}{' (cat_vi_tran)' if t['cat_vi_tran'] else ''}" for t in that_bai)
    return {"theo_khau": {KHAU: dict(tong)}, "tong": tong, "ghi_chu": ghi_chu}


def chuyen(luots, *, manifest, doc_trang, che_do, k, commit, ngay_chay, transport, mo_hinh, hash_cau_hinh):
    """Trả (hợp đồng, báo cáo). `luots`: danh sách `LuotCuaChuong` theo thứ tự sách."""
    tot = [l for l in luots if l.luot.ok]
    that_bai = [{"nhan": l.nhan, "cat_vi_tran": l.luot.cat_vi_tran, "loi": l.luot.loi} for l in luots if not l.luot.ok]
    if not tot:
        raise KhongCoLuotNaoThanhCong("; ".join(f"{t['nhan']}: {t['loi']}" for t in that_bai))
    kiem_cau = _KiemCau(doc_trang)
    cau = {"khai_niem": {"tong": 0, "dung_trang": 0, "trang_khac": 0, "khong_co": 0},
           "quan_he": {"tong": 0, "dung_trang": 0, "trang_khac": 0, "khong_co": 0}}
    khong_co_kn, khong_co_qh = [], []

    khai_niem, theo_khoa = [], {}
    gop = ten_rong = 0
    for l in tot:
        for kn in l.luot.du_lieu["khai_niem"]:
            muc = kiem_cau.phan_loai(kn["cau_dinh_nghia"], kn["trang"], l.dau, l.cuoi)
            cau["khai_niem"]["tong"] += 1
            cau["khai_niem"][muc] += 1
            if muc == "khong_co":
                khong_co_kn.append({"loai": "khai_niem", "ten": kn["ten"]})
            khoa = chuan_hoa(kn["ten"])
            if not khoa:
                ten_rong += 1
                continue
            if khoa in theo_khoa:
                gop += 1
                da_co = khai_niem[theo_khoa[khoa]]
                for ten_khac in kn["ten_khac"]:
                    if ten_khac != da_co["ten"] and ten_khac not in da_co["ten_khac"]:
                        da_co["ten_khac"].append(ten_khac)
                continue
            theo_khoa[khoa] = len(khai_niem)
            khai_niem.append({
                "ma": f"b5-k{len(khai_niem) + 1:03d}", "ten": kn["ten"], "ten_khac": list(kn["ten_khac"]),
                "kieu": "khai_niem", "trang_thai_day": "taught",
                "cau_neo": {"trang": kn["trang"], "cau": kn["cau_dinh_nghia"], "ma_chunk": ""},
                "trong_day_hoc": False, "vi_tri": None, "module": None, "ung_vien_goc": None,
                "da_gop": False, "bi_loai": False})
    ma_theo_khoa = {khoa: khai_niem[i]["ma"] for khoa, i in theo_khoa.items()}

    canh, canh_da_co, quan_he_la, canh_lap = [], set(), [], 0
    for l in tot:
        for qh in l.luot.du_lieu["quan_he"]:
            muc = kiem_cau.phan_loai(qh["cau_bang_chung"], qh["trang"], l.dau, l.cuoi)
            cau["quan_he"]["tong"] += 1
            cau["quan_he"][muc] += 1
            if muc == "khong_co":
                khong_co_qh.append({"loai": "quan_he", "nguon": qh["nguon"], "dich": qh["dich"]})
            nguon, dich = ma_theo_khoa.get(chuan_hoa(qh["nguon"])), ma_theo_khoa.get(chuan_hoa(qh["dich"]))
            if nguon is None or dich is None:
                quan_he_la.append(dict(qh))
                continue
            if (nguon, dich) in canh_da_co:
                canh_lap += 1
                continue
            canh_da_co.add((nguon, dich))
            canh.append({"nguon": nguon, "dich": dich, "nguon_goc": "baseline", "mem": False, "ly_do_mem": None,
                         "bo_qua": False, "bang_chung": {"trang": qh["trang"], "cau": qh["cau_bang_chung"]}})

    day_hoc, vi_tri, module, day_lap, ten_la = [], {}, [], 0, 0
    for l in tot:
        lo_trinh = l.luot.du_lieu["lo_trinh"]
        for ten in lo_trinh["day_hoc"]:
            ma = ma_theo_khoa.get(chuan_hoa(ten))
            if ma is None:
                ten_la += 1
            elif ma in vi_tri:
                day_lap += 1
            else:
                vi_tri[ma] = len(day_hoc)
                day_hoc.append(ma)
        for m in lo_trinh["module"]:
            thanh_vien = []
            for ten in m["khai_niem"]:
                ma = ma_theo_khoa.get(chuan_hoa(ten))
                if ma is None:
                    ten_la += 1
                else:
                    thanh_vien.append(ma)
            module.append({"ma": f"b5-m{len(module) + 1:02d}", "ten": m["ten"], "thanh_vien": thanh_vien})
    module_cua = {}
    for m in module:
        for ma in m["thanh_vien"]:
            module_cua.setdefault(ma, m["ma"])
    for kn in khai_niem:
        kn["trong_day_hoc"] = kn["ma"] in vi_tri
        kn["vi_tri"] = vi_tri.get(kn["ma"])
        kn["module"] = module_cua.get(kn["ma"])

    hop_dong = {
        "schema": TEN_LUOC_DO,
        "dinh_danh": {"doc_id": manifest["ma_sach"], "sha256_pdf": manifest["pdf_sha256"], "so_trang": manifest["so_trang"],
                      "he": f"b5{che_do}", "bien_the": f"{PHIEN_BAN_LOI_NHAC}/k{k}", "luot_nhieu": k - 1,
                      "commit": commit, "hash_cau_hinh": hash_cau_hinh, "mo_hinh": mo_hinh, "transport": transport,
                      "ngay_chay": ngay_chay},
        "cau_truc": None, "khai_niem": khai_niem, "ban_do_danh_tinh": {}, "canh": canh, "cap_ung_vien": None,
        "lo_trinh": {"day_hoc": day_hoc, "module": module},
        "chi_phi": _chi_phi(luots, that_bai),
    }
    kiem_hoac_loi(hop_dong)
    bao_cao = {"so_luot": len(luots), "so_luot_ok": len(tot), "luot_that_bai": that_bai,
               "cat_vi_tran": any(l.luot.cat_vi_tran for l in luots),
               "quan_he_tro_khai_niem_la": len(quan_he_la), "quan_he_la": quan_he_la,
               "cau_trich": cau, "khong_co_trong_sach": khong_co_kn + khong_co_qh,
               "khai_niem_gop_theo_ten": gop, "khai_niem_ten_rong": ten_rong, "canh_lap": canh_lap,
               "day_hoc_lap": day_lap, "lo_trinh_ten_la": ten_la}
    return hop_dong, bao_cao
