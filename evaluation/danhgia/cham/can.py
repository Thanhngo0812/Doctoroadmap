"""Đưa cạnh máy sang **không gian vàng** qua bảng căn và bản đồ danh tính.

Luật ánh xạ (đếm trong không gian vàng, nên tập cạnh vàng không phình theo số node):
- một cạnh máy `(u, v)` thành mọi cặp `(g_u, g_v)`, với `g_u` là khái niệm vàng mà `u` căn (mức nghiêm: `khop`; mức nới thêm
  `may_rong_hon`, `may_hep_hon`), `g_v` cũng vậy; rồi khử trùng và bỏ cặp tự nối;
- node chưa căn được nhận một khái niệm ảo riêng (`~may~<node>`), nên cạnh máy có đầu không căn được vẫn là FP nếu đích của nó
  nằm trong phạm vi; đích ảo không bao giờ nằm trong phạm vi;
- node căn với hai khái niệm vàng (gộp nhầm) ánh xạ sang cả hai;
- khái niệm vàng tách thành nhiều node không làm tăng mẫu số hay FN (lỗi tách đã có thước A4 riêng);
- cạnh vàng mà hai đầu có chung một node (hai khái niệm vàng dồn vào một node) rời phép chấm và được đếm riêng (`tu_noi`);
- vị trí của một khái niệm vàng trong dãy học là vị trí **sớm nhất** trong các node căn với nó (xem `a10`).
"""
from __future__ import annotations

MUC_CAN = {"nghiem": frozenset({"khop"}), "noi": frozenset({"khop", "may_rong_hon", "may_hep_hon"})}
LOAI_CHINH = "van_ban"
_TIEN_TO_MAY = "~may~"


def khoa_vang(tham_chieu):
    """Khoá chung cho khái niệm vàng: mã G-… hoặc cặp (tên, trang) của nguồn ngoài chương."""
    if isinstance(tham_chieu, str):
        return tham_chieu
    ngoai = tham_chieu["ngoai"]
    return f"ngoai:{ngoai['ten']}|{ngoai.get('trang')}"


def bang_node(can, muc, ban_do_danh_tinh):
    """Trả `(nut_cua_vang, vang_cua_nut)`; node đã qua bản đồ danh tính (đúng một bước như bộ chấm cũ)."""
    chap_nhan = MUC_CAN[muc]
    nut_cua_vang, vang_cua_nut = {}, {}
    for hang in can["hang"]:
        if hang["quan_he"] in chap_nhan:
            nut = ban_do_danh_tinh.get(hang["may"], hang["may"])
            khoa = khoa_vang(hang["vang"])
            nut_cua_vang.setdefault(khoa, set()).add(nut)
            vang_cua_nut.setdefault(nut, set()).add(khoa)
    return nut_cua_vang, vang_cua_nut


def anh_xa_canh(canh_node, vang_cua_nut):
    """Cạnh máy `(u, v)` -> tập cặp khái niệm vàng, khử trùng, bỏ tự nối."""
    ket_qua = set()
    for u, v in canh_node:
        for gu in vang_cua_nut.get(u, {_TIEN_TO_MAY + u}):
            for gv in vang_cua_nut.get(v, {_TIEN_TO_MAY + v}):
                if gu != gv:
                    ket_qua.add((gu, gv))
    return ket_qua


def doc_vang(g3, g4, can, muc, ban_do_danh_tinh, *, vang="chinh"):
    """Trả `dich_theo_chuong` (khái niệm vàng của mỗi chương), `cap` (cặp vàng, khử trùng), `tu_noi`,
    `nut_cua_vang` và `vang_cua_nut`."""
    danh_sach = {"chinh": g4["vang_chinh"], "hop": g4["vang_hop"], "giao": g4["vang_giao"]}
    if vang not in danh_sach:
        raise ValueError(f"vàng phải là chinh, hop hoặc giao, không phải {vang!r}")
    cua = {k["ma"]: k["chuong"] for k in g3["khai_niem"]}
    tranh_chap = {(khoa_vang(t["nguon"]), t["dich"]) for t in g4.get("tranh_chap", ())}
    nut_cua_vang, vang_cua_nut = bang_node(can, muc, ban_do_danh_tinh)
    dich_theo_chuong = {}
    for ma, chuong in cua.items():
        dich_theo_chuong.setdefault(chuong, set()).add(ma)
    cap, tu_noi = set(), dict.fromkeys(dich_theo_chuong, 0)
    for quan_he in danh_sach[vang]:
        if quan_he["loai"] != LOAI_CHINH:
            continue
        nguon, dich = khoa_vang(quan_he["nguon"]), quan_he["dich"]
        if dich not in cua:
            raise ValueError(f"cạnh vàng có đích {dich!r} không thuộc kho khái niệm G3")
        if isinstance(quan_he["nguon"], str) and nguon not in cua:
            raise ValueError(f"cạnh vàng có nguồn {nguon!r} không thuộc kho khái niệm G3")
        if (nguon, dich) in tranh_chap:
            raise ValueError(f"cạnh {nguon!r} > {dich!r} vừa nằm trong vàng vừa nằm trong tranh chấp")
        if nut_cua_vang.get(nguon, set()) & nut_cua_vang.get(dich, set()):
            tu_noi[cua[dich]] += 1
        elif nguon != dich:
            cap.add((nguon, dich))
    return {"dich_theo_chuong": dich_theo_chuong, "cap": cap, "tu_noi": tu_noi,
            "nut_cua_vang": nut_cua_vang, "vang_cua_nut": vang_cua_nut}
