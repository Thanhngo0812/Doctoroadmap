"""Hợp đồng `danh-gia-xuat-1` từ kết quả phát lại, qua đúng bộ dựng của hệ chính (`xuat_tu_du_lieu`)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from danhgia.xuat.baseline.chung import CHI_PHI_KHONG
from danhgia.xuat.he_chinh import xuat_tu_du_lieu

def _doc(duong):
    return json.loads(Path(duong).read_text(encoding="utf-8"))


def hop_dong(kq, goc_kho, doc, phien_ban, *, dinh_danh, he, tham_so, nguon_goc_canh=None):
    """`dinh_danh`: các khoá như `xuat` (he bị thay bằng `he`). `tham_so`: dict mô tả biến thể, vào băm cấu hình."""
    goc_kho = Path(goc_kho)
    da_luu = kq.chuoi.da_luu
    config = da_luu.manifest["config"]
    hash_cau_hinh = hashlib.sha256(json.dumps({"goc": da_luu.manifest["config_hash"], "he": he, "tham_so": tham_so},
                                              sort_keys=True).encode()).hexdigest()[:16]
    manifest = {"config_hash": hash_cau_hinh, "config": {"model_id": config["model_id"],
                                                          "chunks_version": config["chunks_version"]}}
    duong = goc_kho / "chunks" / doc / f"v{config['chunks_version']}"
    return xuat_tu_du_lieu(doc, phien_ban, kq.payload, manifest, _doc(duong / "chunks.json"), _doc(duong / "sections.json"),
                           dinh_danh={**dinh_danh, "he": he}, chi_phi=CHI_PHI_KHONG, nguon_goc_canh=nguon_goc_canh)
