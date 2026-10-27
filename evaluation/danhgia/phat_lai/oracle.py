"""Oracle A10: cạnh vàng G4 **đã căn** đặt thẳng vào hàm dãy học, trên node của hệ chính.

Cạnh vàng `(a, b)` thành mọi cặp node `(u, v)` với `u` căn với `a` và `v` căn với `b` theo bảng căn mức nghiêm (`khop`), qua đúng
`doc_vang` của bộ chấm, nên oracle và bộ chấm dùng cùng một cách đọc bảng căn. Cạnh có một đầu chưa căn được bị bỏ và được đếm: oracle
không được đặt cạnh trỏ vào id vàng, vì A10 chỉ biết node.
"""
from __future__ import annotations

from danhgia.cham.can import doc_vang

PHIEN_BAN_PHIEN = "oracle_g4"


def canh_oracle(hop_dong, g3, g4, can, ids_node, *, vang="chinh", muc="nghiem"):
    """Trả `(canh, thong_ke)`. `canh`: dict cạnh cứng cho A10; `ids_node`: node A10 biết (node không có ở đó bị bỏ và đếm)."""
    d = doc_vang(g3, g4, can, muc, hop_dong["ban_do_danh_tinh"], vang=vang)
    nut_cua_vang, ids = d["nut_cua_vang"], set(ids_node)
    canh, da_co = [], set()
    chua_can = node_la = tu_noi = 0
    for a, b in sorted(d["cap"]):
        if not nut_cua_vang.get(a) or not nut_cua_vang.get(b):
            chua_can += 1
            continue
        for u in sorted(nut_cua_vang[a]):
            for v in sorted(nut_cua_vang[b]):
                if u == v:
                    tu_noi += 1
                elif u not in ids or v not in ids:
                    node_la += 1
                elif (u, v) not in da_co:
                    da_co.add((u, v))
                    canh.append({"source": u, "target": v, "edge_type": "requires", "session_id": PHIEN_BAN_PHIEN,
                                 "quote": None, "chunk_ids": []})
    return canh, {"canh_vang": len(d["cap"]), "canh_chua_can": chua_can, "cap_node_la": node_la, "cap_tu_noi": tu_noi,
                  "canh_dat_vao_a10": len(canh)}
