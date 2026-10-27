"""B2 luật đơn giản: cạnh X -> Y khi tên hay tên khác của X nằm trong cửa sổ định nghĩa của Y và X được dạy trước Y.

Chọn cách định nghĩa (dùng một cách cho mọi sách):
- **cửa sổ định nghĩa của Y** = toàn bộ văn bản của chunk chứa câu neo của Y (`cau_neo.ma_chunk`);
- **khớp tên** = `danhgia.ten`: chuỗi âm tiết của tên (đã chuẩn hoá) xuất hiện liền kề, đúng ranh giới âm tiết, trong chuỗi âm tiết của
  cửa sổ, nên "lượn" không khớp "lượng";
- **X dạy trước Y** = vị trí dạy của X nhỏ hơn hẳn vị trí dạy của Y; vị trí = (thứ tự chunk của câu neo, vị trí câu neo trong chunk).
  Vị trí lấy từ chữ trong sách, không lấy từ dãy học của hệ chính (dãy đó đã phụ thuộc các cạnh của hệ chính);
- chỉ xét khái niệm hệ chính đã xếp vào dãy học (`trong_day_hoc`) và có câu neo; không lọc tên chung, không lọc tên ngắn.

Dãy học của B2 không tính ở đây: cạnh đi vào hàm dãy học A10 qua bộ phát lại (`phat_lai(canh_thay=...)`).
"""
from __future__ import annotations

import re

from danhgia.ten import am_tiet

_XA = 10**9  # không tìm thấy câu neo trong chunk: xếp sau mọi vị trí tìm được (như `_FAR` của A10)
_CAU = re.compile(r"(?<=[.!?;])\s+|\n+")
_DO_DAI_TEN_TOI_DA = 12


def _vi_tri(khai_niem, chunk):
    neo = khai_niem["cau_neo"]
    cho = chunk["text"].find(neo["cau"]) if neo.get("cau") else -1
    return chunk["order_index"], cho if cho >= 0 else _XA


def _n_gram(am):
    """Mọi dãy âm tiết liền kề độ dài 1.._DO_DAI_TEN_TOI_DA của cửa sổ; tên dài hơn thế không bao giờ khớp (không có tên như vậy trong thực tế)."""
    return {am[i:i + n] for n in range(1, _DO_DAI_TEN_TOI_DA + 1) for i in range(len(am) - n + 1)}


def _cau_chua_ten(van_ban, ten_am):
    for cau in _CAU.split(van_ban):
        am = am_tiet(cau)
        if any(am[i:i + len(ten_am)] == ten_am for i in range(len(am) - len(ten_am) + 1)):
            return cau.strip()
    return None


def canh_b2(hop_dong, chunks):
    """Trả danh sách cạnh `{"source", "target", "edge_type", "session_id", "quote", "chunk_ids"}` cho hàm dãy học A10.

    `chunks`: các chunk của sách, mỗi chunk `{"chunk_id", "order_index", "text"}`. Khái niệm có câu neo trỏ vào chunk không có trong
    `chunks` là lỗi (không đoán).
    """
    theo_ma = {c["chunk_id"]: c for c in chunks}
    xet = []
    for k in hop_dong["khai_niem"]:
        if not k["trong_day_hoc"] or not k["cau_neo"]:
            continue
        chunk = theo_ma.get(k["cau_neo"]["ma_chunk"])
        if chunk is None:
            raise ValueError(f"khái niệm {k['ma']}: chunk câu neo {k['cau_neo']['ma_chunk']!r} không có trong danh sách chunk")
        ten = {am for am in (am_tiet(t) for t in [k["ten"], *k["ten_khac"]]) if am}
        xet.append({"ma": k["ma"], "ten": ten, "chunk": chunk, "vi_tri": _vi_tri(k, chunk),
                    "cua_so": _n_gram(am_tiet(chunk["text"]))})
    canh = []
    for y in sorted(xet, key=lambda k: k["ma"]):
        for x in sorted(xet, key=lambda k: k["ma"]):
            if x["ma"] == y["ma"] or not x["vi_tri"] < y["vi_tri"]:
                continue
            khop = next((t for t in sorted(x["ten"]) if t in y["cua_so"]), None)
            if khop is None:
                continue
            canh.append({"source": x["ma"], "target": y["ma"], "edge_type": "requires", "session_id": "baseline_b2",
                         "quote": _cau_chua_ten(y["chunk"]["text"], khop), "chunk_ids": [y["chunk"]["chunk_id"]]})
    return canh
