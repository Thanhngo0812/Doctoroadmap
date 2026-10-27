"""Căn hai bản thô G3 bằng luật tự động (spec mục 7), rồi tách phần còn lại thành cặp "gần nhau".

Luật, chạy theo thứ tự, trong từng chương (khái niệm khác chương không bao giờ khớp):
1. `ten`: tên hoặc tên khác của hai bên trùng nhau sau chuẩn hoá, so theo âm tiết.
2. `cau`: cùng trang và câu định nghĩa giống nhau (độ giống >= nguong_cau).
Cặp còn lại gần nhau (đưa vào phiếu bất đồng thành câu hỏi "có phải cùng khái niệm không") khi:
- tên này chứa tên kia liền kề theo âm tiết; hoặc
- tập âm tiết của hai tên có Jaccard >= 0,5; hoặc
- cùng trang và câu định nghĩa giống nhau >= nguong_gan.
"""

import re

from danhgia.ten import am_tiet, do_giong

SCHEMA_CAN = "danh-gia-g3-can-1"
NGUONG_CAU = 0.9
NGUONG_GAN = 0.5
NGUONG_JACCARD = 0.5


def khoa_chuong(ma: str) -> list:
    return [int(x) if x.isdigit() else x for x in re.split(r"(\d+)", ma)]


def _khoa_ten(e: dict) -> set[tuple[str, ...]]:
    return {k for k in (am_tiet(t) for t in [e["ten"], *e["ten_khac"]]) if k}


def _chua(a: tuple[str, ...], b: tuple[str, ...]) -> bool:
    n = len(b)
    return 0 < n <= len(a) and any(a[i : i + n] == b for i in range(len(a) - n + 1))


def _gan_ten(ea: dict, eb: dict) -> bool:
    for ka in _khoa_ten(ea):
        for kb in _khoa_ten(eb):
            if _chua(ka, kb) or _chua(kb, ka):
                return True
            if len(set(ka) & set(kb)) / len(set(ka) | set(kb)) >= NGUONG_JACCARD:
                return True
    return False


def _cung_trang_giong_cau(ea: dict, eb: dict, nguong: float) -> bool:
    da, db = ea["dinh_nghia"], eb["dinh_nghia"]
    if da["trang"] is None or da["trang"] != db["trang"] or not am_tiet(da["cau"]) or not am_tiet(db["cau"]):
        return False
    return do_giong(da["cau"], db["cau"]) >= nguong


def can_hai_ban(ban_1: dict, ban_2: dict, *, nguong_cau: float = NGUONG_CAU, nguong_gan: float = NGUONG_GAN) -> dict:
    if ban_1["ma_sach"] != ban_2["ma_sach"]:
        raise ValueError(f"hai bản khác ma_sach: {ban_1['ma_sach']} và {ban_2['ma_sach']}")
    if ban_1["nguoi_gan"] == ban_2["nguoi_gan"]:
        raise ValueError(f"hai bản cùng nguoi_gan: {ban_1['nguoi_gan']}")
    if ban_1["phien_ban_huong_dan"] != ban_2["phien_ban_huong_dan"]:
        raise ValueError("hai bản khác phien_ban_huong_dan")
    ban_a, ban_b = sorted((ban_1, ban_2), key=lambda b: b["nguoi_gan"])
    ent_a = {e["ma"]: e for e in ban_a["khai_niem"]}
    ent_b = {e["ma"]: e for e in ban_b["khai_niem"]}
    if len(ent_a) != len(ban_a["khai_niem"]) or len(ent_b) != len(ban_b["khai_niem"]):
        raise ValueError("mã dòng bị trùng trong một bản")
    chuong = sorted({e["chuong"] for e in [*ent_a.values(), *ent_b.values()]}, key=khoa_chuong)
    khop, cap_gan, chi_a, chi_b = [], [], [], []
    for ch in chuong:
        con_a = sorted(m for m, e in ent_a.items() if e["chuong"] == ch)
        con_b = sorted(m for m, e in ent_b.items() if e["chuong"] == ch)

        def ghep(luat: str, tot) -> None:
            for ma in list(con_a):
                ung_vien = [(tot(ent_a[ma], ent_b[mb]), mb) for mb in con_b]
                ung_vien = [(d, mb) for d, mb in ung_vien if d]
                if ung_vien:
                    mb = sorted(ung_vien, key=lambda x: (-x[0], x[1]))[0][1]
                    khop.append({"chuong": ch, "a": ma, "b": mb, "luat": luat})
                    con_a.remove(ma)
                    con_b.remove(mb)

        ghep("ten", lambda x, y: len(_khoa_ten(x) & _khoa_ten(y)))
        ghep("cau", lambda x, y: _cung_trang_giong_cau(x, y, nguong_cau))
        for ma in con_a:
            for mb in con_b:
                if _gan_ten(ent_a[ma], ent_b[mb]):
                    cap_gan.append({"chuong": ch, "a": ma, "b": mb, "ly_do": "gan_ten"})
                elif _cung_trang_giong_cau(ent_a[ma], ent_b[mb], nguong_gan):
                    cap_gan.append({"chuong": ch, "a": ma, "b": mb, "ly_do": "gan_cau"})
        chi_a += con_a
        chi_b += con_b
    return {
        "schema": SCHEMA_CAN, "ma_sach": ban_a["ma_sach"], "phien_ban_huong_dan": ban_a["phien_ban_huong_dan"],
        "nguoi": [ban_a["nguoi_gan"], ban_b["nguoi_gan"]], "chuong": chuong,
        "khai_niem": {"a": ent_a, "b": ent_b},
        "khop": khop, "cap_gan": cap_gan, "chi_a": chi_a, "chi_b": chi_b,
    }
