"""Đưa vàng G3/G4 sang không gian node của hệ qua bảng căn và bản đồ danh tính.

Cạnh vàng `(G, H)` thành tập cặp node `align(G) x align(H)`. Khái niệm vàng chưa căn được (theo mức đang xét)
nhận một node ảo riêng, nên cạnh của nó vẫn nằm trong mẫu số của recall và Q6 thay vì rơi lặng lẽ.
Hai khái niệm vàng dồn chung một node thì cạnh giữa chúng thành tự nối và rời phép chấm; số lượng được đếm riêng.
"""
from __future__ import annotations

MUC_CAN = {"nghiem": frozenset({"khop"}), "noi": frozenset({"khop", "may_rong_hon", "may_hep_hon"})}
LOAI_CHINH = "van_ban"
_TIEN_TO_ANH = "~vang~"


def khoa_vang(tham_chieu):
    """Khoá chung cho khái niệm vàng: mã G-… hoặc cặp (tên, trang) của nguồn ngoài chương."""
    if isinstance(tham_chieu, str):
        return tham_chieu
    ngoai = tham_chieu["ngoai"]
    return f"ngoai:{ngoai['ten']}|{ngoai.get('trang')}"


def la_anh(nut):
    return nut.startswith(_TIEN_TO_ANH)


def bang_node(can, muc, ban_do_danh_tinh):
    """khoá vàng -> tập node máy (đã qua danh tính, đúng một bước như bộ chấm cũ)."""
    chap_nhan = MUC_CAN[muc]
    bang = {}
    for hang in can["hang"]:
        if hang["quan_he"] in chap_nhan:
            nut = ban_do_danh_tinh.get(hang["may"], hang["may"])
            bang.setdefault(khoa_vang(hang["vang"]), set()).add(nut)
    return bang


def nut_cua(khoa, bang):
    return frozenset(bang[khoa]) if khoa in bang else frozenset({_TIEN_TO_ANH + khoa})


def doc_vang(g3, g4, can, muc, ban_do_danh_tinh, *, vang="chinh"):
    """Trả về `{"dich_theo_chuong", "cap", "tu_noi"}`.

    - `dich_theo_chuong[chuong]`: tập node đích (kể cả node ảo) của các khái niệm vàng trong chương;
    - `cap[chuong]`: tập cặp node `(nguon, dich)` của cạnh vàng có đích thuộc chương;
    - `tu_noi[chuong]`: số cạnh vàng bị tự nối vì hai đầu dồn chung node.
    """
    danh_sach = {"chinh": g4["vang_chinh"], "hop": g4["vang_hop"], "giao": g4["vang_giao"]}
    if vang not in danh_sach:
        raise ValueError(f"vàng phải là chinh, hop hoặc giao, không phải {vang!r}")
    cua = {k["ma"]: k["chuong"] for k in g3["khai_niem"]}
    tranh_chap = {(khoa_vang(t["nguon"]), t["dich"]) for t in g4.get("tranh_chap", ())}
    bang = bang_node(can, muc, ban_do_danh_tinh)
    dich_theo_chuong = {}
    for ma, chuong in cua.items():
        dich_theo_chuong.setdefault(chuong, set()).update(nut_cua(ma, bang))
    cap, tu_noi = {chuong: set() for chuong in dich_theo_chuong}, dict.fromkeys(dich_theo_chuong, 0)
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
        chuong = cua[dich]
        cap_node = {(u, v) for u in nut_cua(nguon, bang) for v in nut_cua(dich, bang) if u != v}
        if not cap_node:
            tu_noi[chuong] += 1
        cap[chuong] |= cap_node
    return {"dich_theo_chuong": dich_theo_chuong, "cap": cap, "tu_noi": tu_noi}
