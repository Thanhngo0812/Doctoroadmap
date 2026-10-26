"""Đổi vàng A8 cũ (`a8-gold/*-vang.json`, id node) sang G3 (kho khái niệm), G4 (quan hệ) và bảng căn.

Mỗi khái niệm đích của vàng cũ thành một khái niệm G3 (`G-<sách>-<nnn>`); đầu nguồn nằm ngoài các đích thành nguồn "ngoài chương"
của G4. Bảng căn nối mỗi khái niệm vàng với node đang có trong đồ thị qua **bảng chuyển hướng** của canonical, đúng như
`score_roadmap_order(..., remap_gold_ids=True)`. Bản đồ danh tính không áp ở đây: nó nằm trong hợp đồng của hệ và do lõi chấm áp.

Khái niệm không quy được thì từ chối chuyển, như bộ chấm cũ (danh tính lệch cho điểm giả).

Vàng cũ không có trạng thái dạy, trang hay câu định nghĩa; các trường đó để null, trạng thái là `day_o_day` vì mọi đích của vàng cũ
là khái niệm được dạy trong chương.
"""
from __future__ import annotations


def _quy(ma, chuyen_huong, node_ids):
    hien, thay = ma, set()
    while hien in chuyen_huong:
        if hien in thay:
            raise ValueError(f"bảng chuyển hướng có vòng lặp khi quy {ma}: {hien}")
        thay.add(hien)
        hien = chuyen_huong[hien]
    return hien if hien in node_ids else None


class KhongQuyDuoc(ValueError):
    """Khái niệm của vàng cũ không quy được về node trong đồ thị: danh tính lệch, như `UnresolvedGoldConcepts` của bộ chấm cũ."""


def chuyen(vang_cu, *, ma_sach, ten, node_ids, redirects, cho_phep_chua_can=False):
    nhan_chuong = vang_cu["chapter"]["label"]
    dich = list(dict.fromkeys(vang_cu["targets"]))
    dau_nguon = list(dict.fromkeys(e["prerequisite"] for e in vang_cu["edges"] if e["prerequisite"] not in set(dich)))
    quy = {ma: _quy(ma, redirects, node_ids) for ma in [*dich, *dau_nguon]}
    chua_can = sorted(ma for ma, nut in quy.items() if nut is None)
    if chua_can and not cho_phep_chua_can:
        raise KhongQuyDuoc(f"{len(chua_can)} khái niệm của vàng cũ không quy được về node trong đồ thị: "
                           + ", ".join(chua_can) + "; từ chối chuyển (đặt cho_phep_chua_can để chuyển phần còn lại)")
    thieu_ten = sorted(ma for ma, nut in quy.items() if nut is not None and ma not in ten and nut not in ten)
    if thieu_ten:
        raise ValueError(f"thiếu tên cho khái niệm {thieu_ten}; bộ chuyển không tự đặt tên")

    def ten_cua(ma):
        return ten[ma] if ma in ten else ten[quy[ma]] if quy[ma] is not None else ma

    ma_g = {ma: f"G-{ma_sach}-{so:03d}" for so, ma in enumerate(dich, 1)}
    g3 = {"schema": "danh-gia-g3-1", "ma_sach": ma_sach, "nguoi_gan": "hoi-y", "phien_ban_huong_dan": "g3-1",
          "khai_niem": [], "tranh_chap": []}
    for ma in dich:
        ghi_chu = f"chuyển từ vàng A8 cũ, id cũ {ma}"
        if quy[ma] is None:
            ghi_chu += "; id không quy được về node trong đồ thị"
        g3["khai_niem"].append({
            "ma": ma_g[ma], "chuong": nhan_chuong, "ten": ten_cua(ma), "ten_khac": [], "trang_thai": "day_o_day",
            "dinh_nghia": {"trang": None, "cau": None}, "khong_chac": False, "ghi_chu": ghi_chu})
    ngoai, khoa_ngoai = {}, {}
    for ma in dau_nguon:
        khoa = (ten_cua(ma), None)
        if khoa in khoa_ngoai:
            raise ValueError(f"hai nguồn ngoài chương trùng tên {khoa[0]!r}: {khoa_ngoai[khoa]} và {ma}")
        khoa_ngoai[khoa] = ma
        ngoai[ma] = {"ngoai": {"ten": khoa[0], "trang": None}}
    quan_he = []
    for canh in vang_cu["edges"]:
        nguon = ma_g[canh["prerequisite"]] if canh["prerequisite"] in ma_g else ngoai[canh["prerequisite"]]
        quan_he.append({"dich": ma_g[canh["target"]], "nguon": nguon, "loai": "van_ban",
                        "bang_chung": {"trang": None, "cau": canh.get("note") or None},
                        "khong_chac": False, "ghi_chu": ""})
    g4 = {"schema": "danh-gia-g4-1", "ma_sach": ma_sach, "nguoi_gan": "hoi-y", "kho_chot_sha256": None,
          "quan_he": quan_he, "vang_chinh": quan_he, "vang_hop": quan_he, "vang_giao": quan_he, "tranh_chap": []}
    hang = []
    for ma in [*dich, *dau_nguon]:
        if quy[ma] is not None:
            hang.append({"vang": ma_g[ma] if ma in ma_g else ngoai[ma], "may": quy[ma], "quan_he": "khop",
                         "nguon_quyet_dinh": "chuyen_vang_cu", "nhat_ky": f"id cũ {ma} -> {quy[ma]}"})
    can = {"schema": "danh-gia-can-1", "ma_sach": ma_sach, "hang": hang}
    bao_cao = {
        "so_khai_niem": len(dich), "so_nguon_ngoai": len(dau_nguon), "so_canh": len(quan_he),
        "chua_can": chua_can,
        "chuyen_huong": {ma: nut for ma, nut in quy.items() if nut is not None and nut != ma},
    }
    return {"g3": g3, "g4": g4, "can": can, "bao_cao": bao_cao}
