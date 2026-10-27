"""Bảng chuyển hướng id của đúng canonical mà một graph đã dùng (đọc JSON thẳng, chỉ đọc).

Đi theo manifest của graph, rồi theo `upstream_version`, tới khi gặp `config.canonical_version`; không lấy canonical mới nhất.
"""
from __future__ import annotations

import json
from pathlib import Path


def _doc(duong):
    return json.loads(Path(duong).read_text(encoding="utf-8"))


def phien_ban_canonical(kho, doc_id, phien_ban):
    kho, da_qua = Path(kho), set()
    van = phien_ban
    while True:
        manifest = _doc(kho / "graph" / doc_id / f"v{van}" / "manifest.json")
        if manifest.get("doc_id") != doc_id:
            raise ValueError(f"manifest graph v{van} thuộc {manifest.get('doc_id')!r}, không phải {doc_id!r}")
        version = manifest.get("config", {}).get("canonical_version")
        if version is not None:
            return version
        van = manifest.get("upstream_version")
        if van is None:
            raise ValueError("manifest graph không xác định được canonical; không thể chuyển id vàng")
        if van in da_qua:
            raise ValueError("manifest graph có vòng lặp upstream; không thể xác định canonical")
        da_qua.add(van)


def doc_chuyen_huong(kho, doc_id, phien_ban):
    version = phien_ban_canonical(kho, doc_id, phien_ban)
    return version, _doc(Path(kho) / "canonical" / doc_id / f"v{version}" / "canonical.json").get("redirects", {})
