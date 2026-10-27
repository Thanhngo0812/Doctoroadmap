"""Cài lỗi đã biết vào bản nháp G1/G2 (lệnh của người giữ; spec mục 5).

Ba loại: đổi cấp một tiêu đề, bỏ một tiêu đề, gán sai vai trò một mục. 3–5 lỗi mỗi cuốn, mỗi lỗi một tiêu đề khác nhau, tất định theo seed.
Mỗi lỗi chỉ được nhận khi bản nháp sau cài vẫn qua validator, để lỗi trông như lỗi thật của người làm nháp.

Sổ lỗi (trả về, người giữ cất ngoài repo) khoá theo mã dòng đầu của tiêu đề, kèm bản ghi gốc để hoàn nguyên. Bản nháp sau cài
đánh lại id liên tục để lỗ hổng id không lộ chỗ bỏ.
"""
import copy

from danhgia.g1g2 import kiem_cay
from danhgia.g1g2.kiem_cay import NHANH_DAU, VAI_TRO, doi_so
from danhgia.thong_ke.lcg import Lcg

LOAI = ("doi_cap", "bo_tieu_de", "gan_sai_vai_tro")
SO_LOI_TOI_THIEU, SO_LOI_TOI_DA = 3, 5


def _xao(n, rng):
    chi_so = list(range(n))
    for i in range(n - 1, 0, -1):
        j = rng.chi_so(i + 1)
        chi_so[i], chi_so[j] = chi_so[j], chi_so[i]
    return chi_so


def _thu(muc, i, loai, rng):
    """Bản nháp sau khi cài một lỗi `loai` ở tiêu đề thứ i, cùng bản ghi `cai`; None nếu loại này không áp dụng được."""
    ra = copy.deepcopy(muc)
    h = ra[i]
    if loai == "bo_tieu_de":
        del ra[i]
        return ra, None
    if loai == "doi_cap":
        lua = [c for c in (h["cap"] - 1, h["cap"] + 1) if 1 <= c <= 6]
        h["cap"] = lua[rng.chi_so(len(lua))]
        h["vung"] = h["vai_tro"] if h["cap"] == 1 else None
        return ra, {"cap": h["cap"]}
    lua = [v for v in VAI_TRO if v != h["vai_tro"] and (h["cap"] > 1 or (v in NHANH_DAU) == (h["vai_tro"] in NHANH_DAU))]
    h["vai_tro"] = lua[rng.chi_so(len(lua))]
    if h["cap"] == 1:
        h["vung"] = h["vai_tro"]
    return ra, {"vai_tro": h["vai_tro"]}


def cai_loi(nhap, dong, *, seed, so_loi=None):
    """(bản nháp sau cài, sổ lỗi). Không sửa `nhap`."""
    if kiem_cay.kiem_cay(nhap[0]["sach"], nhap, dong):
        raise ValueError("bản nháp đầu vào chưa qua validator")
    rng = Lcg(seed)
    for _ in range(4):  # bỏ vài số đầu: seed liền nhau cho số đầu tương quan
        rng.chi_so(2)
    if so_loi is None:
        so_loi = SO_LOI_TOI_THIEU + rng.chi_so(SO_LOI_TOI_DA - SO_LOI_TOI_THIEU + 1)
    if not SO_LOI_TOI_THIEU <= so_loi <= SO_LOI_TOI_DA:
        raise ValueError(f"số lỗi phải từ {SO_LOI_TOI_THIEU} đến {SO_LOI_TOI_DA}")
    loai_cua_lan = [LOAI[i % len(LOAI)] for i in range(so_loi)]
    loai_cua_lan = [loai_cua_lan[i] for i in _xao(so_loi, rng)]
    hien, so, da_chon = copy.deepcopy(nhap), [], set()
    sach = nhap[0]["sach"]
    goc_nhap = {h["dong"][0]: h for h in nhap}
    for loai in loai_cua_lan:
        for i in _xao(len(hien), rng):
            khoa = hien[i]["dong"][0]
            if khoa in da_chon:
                continue
            ung, cai = _thu(hien, i, loai, rng)
            ung = kiem_cay.tinh_cha(ung)
            if kiem_cay.kiem_cay(sach, ung, dong):
                continue
            so.append({"loai": loai, "khoa": khoa, "goc": copy.deepcopy(goc_nhap[khoa]), "cai": cai})
            da_chon.add(khoa)
            hien = ung
            break
        else:
            raise ValueError(f"không cài được lỗi {loai} vào bản nháp này")
    return doi_so(hien), so
