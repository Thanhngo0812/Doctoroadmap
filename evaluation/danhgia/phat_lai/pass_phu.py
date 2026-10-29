"""Chấm lại pass phụ bằng bộ chấm khác rồi phát lại A9 -> A10 (vé DG-21). Seam xuất; chỉ đọc kho, không gọi mạng.

`BuildSecondaryMLEdges` của sản phẩm chạy trên `KhoPhatLai` (artifact mới chỉ nằm trong bộ nhớ, không ghi tệp nào của kho lượt chính) với artifact
pass chính của lượt đó. Thiếu artifact pass chính riêng (kho fixture cắt) thì dựng lại từ artifact edges bằng cách gỡ phần pass phụ.
Cạnh pass phụ và nhật ký pass phụ mới thay vào đồ thị edges rồi bộ phát lại chạy A9 -> A10 (`phat_lai(..., phu_thay=...)`).
"""
from __future__ import annotations

from types import SimpleNamespace

from doc2roadmap.application.use_cases.build_secondary_ml_edges import BuildSecondaryMLEdges
from doc2roadmap.domain.secondary import select_secondary_pairs
from doc2roadmap.domain.secondary_features import SecondaryFeatureContext, is_candidate, pair_features

from danhgia.xuat.cap_ce import hang_cap

from .chay import phat_lai, tim_chuoi
from .kho import KhoPhatLai

KHOA_PHU = ("secondary_edges", "secondary_log", "secondary_flags", "secondary_model_metrics", "completed_secondary_pairs",
            "secondary_base_config_hash", "main_decision_log_version")
KHOA_THAY = ("secondary_edges", "secondary_log", "secondary_flags", "secondary_model_metrics", "completed_secondary_pairs", "stats")


def _tach_tu():
    from doc2roadmap.infrastructure.secondary_tokenizer import VietnameseWordTokenizer
    return VietnameseWordTokenizer()


def _pass_chinh(kho, doc, canh):
    """Artifact pass chính của lượt: artifact upstream của edges nếu nó là pass chính chưa có pass phụ; không thì dựng từ edges bằng cách gỡ pass phụ."""
    tren = canh.manifest.get("upstream_version")
    if tren is not None:
        try:
            artifact = kho.load_graph(doc, tren)
        except FileNotFoundError:
            artifact = None
        if (artifact is not None and artifact.payload.get("stage") == "edges" and artifact.payload.get("main_complete")
                and not artifact.payload.get("secondary_complete")):
            return artifact
    du_lieu = {k: v for k, v in canh.payload.items() if k not in KHOA_PHU}
    du_lieu["secondary_complete"] = False
    return SimpleNamespace(payload=du_lieu, version=tren if tren is not None else canh.version, manifest=canh.manifest, path=None)


def _chuan_bi(goc_kho, doc, phien_ban):
    kho = KhoPhatLai(goc_kho)
    chuoi = tim_chuoi(kho, doc, phien_ban)
    return kho, chuoi, _pass_chinh(kho, doc, chuoi.canh)


def _loc_dich(chuoi):
    return chuoi.canh.manifest.get("config", {}).get("target_filter")


def chay_pass_phu(goc_kho, doc, phien_ban, bo_cham):
    """Chấm lại pass phụ bằng `bo_cham`. Trả `(artifact_pass_phu, chuoi)`; không ghi vào kho."""
    kho, chuoi, chinh = _chuan_bi(goc_kho, doc, phien_ban)
    use_case = BuildSecondaryMLEdges(kho, bo_cham, _tach_tu(), target_filter=_loc_dich(chuoi))
    artifact, _ = use_case.execute(doc, upstream=chinh)
    return artifact, chuoi


def phat_lai_voi_bo_cham(goc_kho, doc, phien_ban, bo_cham):
    """Chấm lại pass phụ rồi phát lại A9 -> A10. Trả `(KetQua, artifact_pass_phu)`."""
    artifact, _ = chay_pass_phu(goc_kho, doc, phien_ban, bo_cham)
    thay = {k: artifact.payload[k] for k in KHOA_THAY}
    return phat_lai(goc_kho, doc, phien_ban, phu_thay=thay), artifact


def so_voi_da_luu(ket_qua, artifact):
    """So pass phụ mới với pass phụ đã lưu trong edges, và dãy học, cạnh sau A10 với graph đã lưu. Trả dict các cờ và số đếm."""
    cu = ket_qua.chuoi.canh.payload
    da_luu = ket_qua.chuoi.da_luu.payload
    moi = artifact.payload
    cong = {
        "canh_phu_dung": moi["secondary_edges"] == cu["secondary_edges"],
        "nhat_ky_phu_dung": moi["secondary_log"] == cu["secondary_log"],
        "day_hoc_dung": ket_qua.payload["sequence"] == da_luu["sequence"],
        "canh_requires_dung": ket_qua.payload["requires_edges"] == da_luu["requires_edges"],
    }
    cong["tai_tao_dung"] = all(cong.values())
    so = {"so_canh_phu": [len(moi["secondary_edges"]), len(cu["secondary_edges"])],
          "so_dong_nhat_ky_phu": [len(moi["secondary_log"]), len(cu["secondary_log"])],
          "so_day_hoc": [len(ket_qua.payload["sequence"]), len(da_luu["sequence"])]}
    cap_moi = {(e["source"], e["target"]) for e in moi["secondary_edges"]}
    cap_cu = {(e["source"], e["target"]) for e in cu["secondary_edges"]}
    return {**cong, **so, "canh_phu_chi_o_moi": len(cap_moi - cap_cu), "canh_phu_chi_o_cu": len(cap_cu - cap_moi)}


def cap_ung_vien(goc_kho, doc, phien_ban):
    """Mọi chiều ứng viên pass phụ theo đúng thứ tự `BuildSecondaryMLEdges` chấm: danh sách `(ma_cap, x, y, dòng đặc trưng, dòng văn bản)`."""
    kho, chuoi, chinh = _chuan_bi(goc_kho, doc, phien_ban)
    cau_hinh = chinh.manifest.get("config", {})
    truoc, sau = cau_hinh.get("definition_before", 0), cau_hinh.get("definition_after", 2)
    version = cau_hinh.get("chunks_version")
    chunks = (kho.load_chunks(doc, version) if version is not None else kho.load_latest_chunks(doc)).result.chunks
    payload = chinh.payload
    tach_tu = _tach_tu()
    use_case = BuildSecondaryMLEdges(kho, None, tach_tu, target_filter=_loc_dich(chuoi))
    nodes, so_cai, huong = payload["nodes"], payload.get("pair_cluster_ledger", []), payload["routing"]["route"]
    cap, _ = select_secondary_pairs(nodes, payload.get("suspected_pairs", []), so_cai, [], route=huong)
    cap = use_case._loc_cap(cap, nodes)
    ctx = SecondaryFeatureContext(payload, chunks, truoc, sau, tokenize=tach_tu)
    du_dieu, _ = select_secondary_pairs(nodes, cap, so_cai, list(payload.get("main_edges", [])), route=huong)
    ket_qua = []
    for c in du_dieu:
        for x, y in ((c["left"], c["right"]), (c["right"], c["left"])):
            dong = pair_features(ctx, x, y, c)
            if is_candidate(ctx, x, y, dong):
                ket_qua.append((c["pair_id"], x, y, dong, hang_cap(ctx, tach_tu, c["pair_id"], x, y, doc)))
    return ket_qua
