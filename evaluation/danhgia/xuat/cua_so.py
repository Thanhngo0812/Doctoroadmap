"""Cửa sổ định nghĩa của từng đích (khối `cap_ung_vien.cua_so_dinh_nghia` của hợp đồng), dựng bằng chính hàm của pipeline.

Seam xuất được nhập `doc2roadmap`, nên không viết lại: `window_sentences` (domain/secondary_features, gọi `definition_window` của
domain/prerequisites) dựng câu của cửa sổ quanh câu neo với `definition_before`, `definition_after` của lượt chạy; tên X có trong cửa sổ của Y
được nhận bằng đúng `regexes` và `hit` mà `SecondaryFeatureContext.named_in` dùng cho đặc trưng pass phụ (`x_trong_ywin`).

Dạng ghi: `{mã node đích Y: [mã node X có tên trong cửa sổ của Y]}`, mỗi node đích có cửa sổ (định vị được câu neo) một khoá, danh sách có thể rỗng.
Node không định vị được cửa sổ không có khoá. `definition_before/after` lấy từ manifest đầu tiên có chúng trên chuỗi `upstream_version`
(stage `edges` ghi cấu hình pass chính), đúng như `BuildSecondaryEdges` đọc `main_config`; không thấy thì không dựng cửa sổ (trả `None`).
"""
from __future__ import annotations

import json
from pathlib import Path

from doc2roadmap.domain.mentions import _mention_normalize
from doc2roadmap.domain.models import Chunk
from doc2roadmap.domain.secondary_features import hit, regexes, window_sentences


def tham_so_cua_so(kho, doc_id, phien_ban):
    """`(definition_before, definition_after)` của lượt chạy, hoặc `None` nếu chuỗi manifest không ghi."""
    kho, van, da_qua = Path(kho), phien_ban, set()
    while van is not None and van not in da_qua:
        da_qua.add(van)
        duong = kho / "graph" / doc_id / f"v{van}" / "manifest.json"
        if not duong.exists():
            return None
        manifest = json.loads(duong.read_text(encoding="utf-8"))
        cau_hinh = manifest.get("config", {})
        if "definition_before" in cau_hinh:
            return int(cau_hinh["definition_before"]), int(cau_hinh.get("definition_after", 2))
        van = manifest.get("upstream_version")
    return None


def cua_so_dinh_nghia(dich, nguon, chunks_list, *, truoc, sau):
    """`dich`: node đích (graph["nodes"]); `nguon`: node có thể được nhắc (đích cộng node chỉ nhắc đến); `chunks_list`: chunk dạng JSON."""
    chunks = [Chunk.from_dict(c) for c in chunks_list]
    mau = {n["node_id"]: regexes(n) for n in nguon}
    ket = {}
    for y in dich:
        cau, _ = window_sentences(y, chunks, truoc, sau)
        if not cau:
            continue
        chuan = [(c, _mention_normalize(c)) for c in cau]
        ket[y["node_id"]] = sorted(x for x, m in mau.items() if x != y["node_id"] and any(hit(m, c, n) for c, n in chuan))
    return ket
