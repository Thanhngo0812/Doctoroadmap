"""Dựng tay hợp đồng, vàng và bảng căn nhỏ cho test seam chấm. Chỉ dùng giá trị rõ ràng, không điền ngầm trong mã chính."""


def khai_niem(ma, ten=None, *, trong_day_hoc=True, bi_loai=False, da_gop=False, trang_thai="taught"):
    return {"ma": ma, "ten": ten or ma, "ten_khac": [], "kieu": "concept", "trang_thai_day": trang_thai,
            "cau_neo": None, "trong_day_hoc": trong_day_hoc, "vi_tri": None, "module": None,
            "ung_vien_goc": None, "da_gop": da_gop, "bi_loai": bi_loai}


def canh(nguon, dich, *, mem=False, bo_qua=False, nguon_goc="pass_chinh"):
    return {"nguon": nguon, "dich": dich, "nguon_goc": nguon_goc, "mem": mem,
            "ly_do_mem": "ngược thứ tự sách" if mem else None, "bo_qua": bo_qua, "bang_chung": None}


def hop_dong(khai_niem_, canh_, day_hoc, *, ban_do_danh_tinh=None, doc_id="S"):
    return {
        "schema": "danh-gia-xuat-1",
        "dinh_danh": {"doc_id": doc_id, "sha256_pdf": None, "so_trang": None, "he": "chinh", "bien_the": "mac_dinh",
                      "luot_nhieu": 0, "commit": "0" * 40, "hash_cau_hinh": "h", "mo_hinh": "m",
                      "transport": "vertex", "ngay_chay": "2026-10-26"},
        "cau_truc": None,
        "khai_niem": khai_niem_,
        "ban_do_danh_tinh": ban_do_danh_tinh or {},
        "canh": canh_,
        "cap_ung_vien": None,
        "lo_trinh": {"day_hoc": list(day_hoc), "module": []},
        "chi_phi": None,
    }


def g3(ma_sach, khai_niem_):
    """khai_niem_: danh sách (ma, chuong)."""
    return {"schema": "danh-gia-g3-1", "ma_sach": ma_sach, "nguoi_gan": "hoi-y", "phien_ban_huong_dan": "g3-1",
            "khai_niem": [{"ma": ma, "chuong": chuong, "ten": ma, "ten_khac": [], "trang_thai": "day_o_day",
                           "dinh_nghia": {"trang": 1, "cau": "x"}, "khong_chac": False, "ghi_chu": ""}
                          for ma, chuong in khai_niem_], "tranh_chap": []}


def g4(ma_sach, quan_he, *, tranh_chap=()):
    """quan_he: danh sách (nguon, dich) hoặc (nguon, dich, loai). nguon có thể là dict {"ngoai": {...}}."""
    rows = []
    for item in quan_he:
        nguon, dich = item[0], item[1]
        loai = item[2] if len(item) > 2 else "van_ban"
        rows.append({"dich": dich, "nguon": nguon, "loai": loai, "bang_chung": {"trang": 1, "cau": "x"},
                     "khong_chac": False, "ghi_chu": ""})
    chinh = [row for row in rows if row["loai"] == "van_ban" and [row["nguon"], row["dich"]] not in [list(t) for t in tranh_chap]]
    return {"schema": "danh-gia-g4-1", "ma_sach": ma_sach, "nguoi_gan": "hoi-y", "kho_chot_sha256": "0" * 64,
            "quan_he": rows, "vang_chinh": chinh, "vang_hop": chinh, "vang_giao": chinh,
            "tranh_chap": [{"nguon": n, "dich": d} for n, d in tranh_chap]}


def can(ma_sach, hang):
    """hang: danh sách (vang, may, quan_he)."""
    return {"schema": "danh-gia-can-1", "ma_sach": ma_sach,
            "hang": [{"vang": vang, "may": may, "quan_he": quan_he, "nguon_quyet_dinh": "tay", "nhat_ky": ""}
                      for vang, may, quan_he in hang]}


def ngoai(ten, trang=None):
    return {"ngoai": {"ten": ten, "trang": trang}}
