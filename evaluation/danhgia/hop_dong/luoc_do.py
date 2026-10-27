"""Lược đồ JSON `danh-gia-xuat-1` (tập con của JSON Schema) và bộ kiểm chỉ dùng thư viện chuẩn.

Phần nào hệ không có thì để `null`; trường bắt buộc thiếu là lỗi, không có giá trị mặc định ngầm.
"""
from __future__ import annotations

TEN_LUOC_DO = "danh-gia-xuat-1"

TRANG_THAI_DAY = ["taught", "uncertain", "mentioned_only", "unchecked", "prior_knowledge", "not_subject_matter"]
VAI_TRO_VUNG = ["noi_dung", "bai_tap", "de_cuong", "mo_dau", "hanh_chinh", "cuoi_sach"]
NGUON_GOC_CANH = ["pass_chinh", "pass_phu", "luat", "baseline"]


def _doi(*loai):
    return {"type": list(loai)}


def _vat(thuoc_tinh):
    """Object đóng: mọi trường đều bắt buộc, không có trường lạ."""
    return {"type": "object", "properties": thuoc_tinh, "required": sorted(thuoc_tinh), "additionalProperties": False}


_CHUOI, _SO_NGUYEN, _SO, _BOOL = {"type": "string"}, {"type": "integer"}, {"type": "number"}, {"type": "boolean"}
_DS_CHUOI = {"type": "array", "items": _CHUOI}
_CHUOI_HOAC_NULL, _NGUYEN_HOAC_NULL, _SO_HOAC_NULL = _doi("string", "null"), _doi("integer", "null"), _doi("number", "null")

_CHI_PHI_KHAU = _vat({
    "giay_chay": _SO_HOAC_NULL, "giay_cho_embedding": _SO_HOAC_NULL, "so_loi_goi_mo_hinh": _NGUYEN_HOAC_NULL,
    "token_vao": _NGUYEN_HOAC_NULL, "token_ra": _NGUYEN_HOAC_NULL, "so_loi_goi_embedding": _NGUYEN_HOAC_NULL,
    "usd": _SO_HOAC_NULL,
})

LUOC_DO = {
    "type": "object",
    "required": ["schema", "dinh_danh", "cau_truc", "khai_niem", "ban_do_danh_tinh", "canh", "cap_ung_vien",
                 "lo_trinh", "chi_phi"],
    "additionalProperties": False,
    "properties": {
        "schema": {"enum": [TEN_LUOC_DO]},
        "dinh_danh": _vat({
            "doc_id": _CHUOI, "sha256_pdf": _CHUOI_HOAC_NULL, "so_trang": _NGUYEN_HOAC_NULL, "he": _CHUOI,
            "bien_the": _CHUOI, "luot_nhieu": _SO_NGUYEN, "commit": _CHUOI, "hash_cau_hinh": _CHUOI,
            "mo_hinh": _CHUOI, "transport": _CHUOI, "ngay_chay": _CHUOI,
        }),
        "cau_truc": {"type": ["object", "null"], "required": ["tieu_de", "muc", "doan_van"],
                     "additionalProperties": False, "properties": {
            "tieu_de": {"type": "array", "items": _vat({
                "ma": _CHUOI, "chu": _CHUOI, "cap": _NGUYEN_HOAC_NULL, "cha": _CHUOI_HOAC_NULL,
                "trang": _NGUYEN_HOAC_NULL,
                "ma_dong": {"type": ["array", "null"], "items": _CHUOI}})},   # mã dòng của bảng dòng, hoặc null nếu chưa căn
            "muc": {"type": "array", "items": _vat({"ma": _CHUOI, "vai_tro": {"enum": VAI_TRO_VUNG}})},
            "doan_van": {"type": "array", "items": _vat({
                "ma": _CHUOI, "trang": _NGUYEN_HOAC_NULL, "duong_muc": _DS_CHUOI, "vai_tro": {"enum": VAI_TRO_VUNG}})},
            # tuỳ chọn (DG-13): căn dòng của bảng dòng với mục; hợp đồng B5 và baseline không có vẫn hợp lệ
            "dong_thuoc_muc": {"type": "object", "additionalProperties": _CHUOI_HOAC_NULL},
            "dong_khong_can": _DS_CHUOI,
        }},
        "khai_niem": {"type": "array", "items": _vat({
            "ma": _CHUOI, "ten": _CHUOI, "ten_khac": _DS_CHUOI, "kieu": _CHUOI,
            "trang_thai_day": {"enum": TRANG_THAI_DAY},
            "cau_neo": {"type": ["object", "null"], "required": ["trang", "cau", "ma_chunk"],
                        "additionalProperties": False,
                        "properties": {"trang": _NGUYEN_HOAC_NULL, "cau": _CHUOI, "ma_chunk": _CHUOI}},
            "trong_day_hoc": _BOOL, "vi_tri": _NGUYEN_HOAC_NULL, "module": _CHUOI_HOAC_NULL,
            "ung_vien_goc": {"type": ["array", "null"], "items": _CHUOI}, "da_gop": _BOOL, "bi_loai": _BOOL})},
        "ban_do_danh_tinh": {"type": "object", "additionalProperties": _CHUOI},
        "canh": {"type": "array", "items": _vat({
            "nguon": _CHUOI, "dich": _CHUOI, "nguon_goc": {"enum": NGUON_GOC_CANH}, "mem": _BOOL,
            "ly_do_mem": _CHUOI_HOAC_NULL, "bo_qua": _BOOL,
            "bang_chung": {"type": ["object", "null"], "required": ["trang", "cau"], "additionalProperties": False,
                           "properties": {"trang": _NGUYEN_HOAC_NULL, "cau": _CHUOI}}})},
        "cap_ung_vien": {"type": ["object", "null"], "required": ["cap", "cua_so_dinh_nghia"],
                         "additionalProperties": False, "properties": {
            "cap": {"type": "array", "items": _vat({
                "trai": _CHUOI, "phai": _CHUOI, "nguon_de_cu": _DS_CHUOI, "quyet_dinh": _CHUOI,
                "nguong": _SO_HOAC_NULL,
                "diem_ml": {"type": ["object", "null"], "required": ["trai_sang_phai", "phai_sang_trai"],
                            "additionalProperties": False,
                            "properties": {"trai_sang_phai": _SO_HOAC_NULL, "phai_sang_trai": _SO_HOAC_NULL}}})},
            "cua_so_dinh_nghia": {"type": ["object", "null"]},
        }},
        "lo_trinh": {"type": ["object", "null"], "required": ["day_hoc", "module"], "additionalProperties": False,
                     "properties": {"day_hoc": _DS_CHUOI,
                                    "module": {"type": "array", "items": _vat({
                                        "ma": _CHUOI, "ten": _CHUOI, "thanh_vien": _DS_CHUOI})}}},
        "chi_phi": {"type": ["object", "null"], "required": ["theo_khau", "tong", "ghi_chu"],
                    "additionalProperties": False, "properties": {
            "theo_khau": {"type": "object", "additionalProperties": _CHI_PHI_KHAU},
            "tong": {"anyOf": [_CHI_PHI_KHAU, {"type": "null"}]},
            "ghi_chu": _CHUOI_HOAC_NULL}},
    },
}

_KIEU = {"string": str, "boolean": bool, "object": dict, "array": list, "null": type(None)}


def _dung_kieu(gia_tri, ten):
    if ten == "integer":
        return isinstance(gia_tri, int) and not isinstance(gia_tri, bool)
    if ten == "number":
        return isinstance(gia_tri, (int, float)) and not isinstance(gia_tri, bool)
    return isinstance(gia_tri, _KIEU[ten])


def kiem_theo_luoc_do(gia_tri, luoc_do, duong="", loi=None):
    """Kiểm một giá trị với tập con JSON Schema dùng ở đây: type, enum, properties, required, items, anyOf."""
    loi = [] if loi is None else loi
    nhan = duong or "(gốc)"
    if "anyOf" in luoc_do:
        if not any(not kiem_theo_luoc_do(gia_tri, nhanh, duong, []) for nhanh in luoc_do["anyOf"]):
            loi.append(f"{nhan}: không khớp nhánh nào cho phép")
        return loi
    if "enum" in luoc_do:
        if gia_tri not in luoc_do["enum"]:
            loi.append(f"{nhan}: {gia_tri!r} ngoài danh sách {luoc_do['enum']}")
        return loi
    kieu = luoc_do.get("type")
    if kieu is not None:
        kieu = [kieu] if isinstance(kieu, str) else kieu
        if not any(_dung_kieu(gia_tri, ten) for ten in kieu):
            loi.append(f"{nhan}: cần kiểu {'/'.join(kieu)}, đang là {type(gia_tri).__name__}")
            return loi
    if isinstance(gia_tri, dict):
        for khoa in luoc_do.get("required", ()):
            if khoa not in gia_tri:
                loi.append(f"{nhan}: thiếu trường {khoa}")
        thuoc_tinh = luoc_do.get("properties", {})
        them = luoc_do.get("additionalProperties", True)
        for khoa, con in gia_tri.items():
            duong_con = f"{duong}.{khoa}" if duong else khoa
            if khoa in thuoc_tinh:
                kiem_theo_luoc_do(con, thuoc_tinh[khoa], duong_con, loi)
            elif them is False:
                loi.append(f"{duong_con}: trường không có trong lược đồ")
            elif isinstance(them, dict):
                kiem_theo_luoc_do(con, them, duong_con, loi)
    elif isinstance(gia_tri, list) and "items" in luoc_do:
        for chi_so, con in enumerate(gia_tri):
            kiem_theo_luoc_do(con, luoc_do["items"], f"{duong}[{chi_so}]", loi)
    return loi
