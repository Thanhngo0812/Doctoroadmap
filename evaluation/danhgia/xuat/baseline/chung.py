"""Phần chung của baseline: khung hợp đồng, chi phí 0, nguồn gốc cạnh."""
from __future__ import annotations

import hashlib
import json

from danhgia.hop_dong import kiem_hoac_loi
from danhgia.hop_dong.luoc_do import TEN_LUOC_DO

NGUON_GOC = "baseline"
CHI_PHI_KHONG = {
    "theo_khau": {},
    "tong": {"giay_chay": None, "giay_cho_embedding": None, "so_loi_goi_mo_hinh": 0, "token_vao": 0, "token_ra": 0,
             "so_loi_goi_embedding": 0, "usd": 0.0},
    "ghi_chu": "tính lại từ artifact đã lưu, không gọi mô hình; chi phí của lượt chạy hệ chính không cộng vào đây",
}


def khai_niem_mau(ma, ten, *, kieu, cau_neo, vi_tri, ten_khac=None, ung_vien_goc=None):
    """Một khái niệm baseline: luôn `taught` (baseline không có bước xét trạng thái dạy), nằm trong dãy học, không module."""
    return {"ma": ma, "ten": ten, "ten_khac": list(ten_khac or []), "kieu": kieu, "trang_thai_day": "taught",
            "cau_neo": cau_neo, "trong_day_hoc": True, "vi_tri": vi_tri, "module": None, "ung_vien_goc": ung_vien_goc,
            "da_gop": False, "bi_loai": False}


def dung_hop_dong(hop_dong_chinh, he, khai_niem, canh=(), *, tham_so):
    """Dãy học là thứ tự `khai_niem`; mọi cấu trúc, cặp ứng viên, module để rỗng hay null. Kiểm bằng validator trước khi trả."""
    hash_cau_hinh = hashlib.sha256(json.dumps({"goc": hop_dong_chinh["dinh_danh"]["hash_cau_hinh"], "he": he,
                                               "tham_so": tham_so}, sort_keys=True).encode()).hexdigest()[:16]
    ket_qua = {
        "schema": TEN_LUOC_DO,
        "dinh_danh": {**hop_dong_chinh["dinh_danh"], "he": he, "hash_cau_hinh": hash_cau_hinh},
        "cau_truc": None, "khai_niem": khai_niem, "ban_do_danh_tinh": {}, "canh": list(canh), "cap_ung_vien": None,
        "lo_trinh": {"day_hoc": [k["ma"] for k in khai_niem], "module": []},
        "chi_phi": CHI_PHI_KHONG,
    }
    kiem_hoac_loi(ket_qua)
    return ket_qua


def canh_hop_dong(nguon, dich, bang_chung):
    return {"nguon": nguon, "dich": dich, "nguon_goc": NGUON_GOC, "mem": False, "ly_do_mem": None, "bo_qua": False,
            "bang_chung": bang_chung}
