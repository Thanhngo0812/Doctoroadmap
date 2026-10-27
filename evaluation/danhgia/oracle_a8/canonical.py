"""Dựng canonical oracle từ kho chốt G3, kiểm lược đồ và ghi vào kho của lượt.

Mỗi khái niệm của kho chốt (`khai_niem`; `loai` và `tranh_chap` không vào) thành đúng một node:
- tên, tên khác; `learnable = true`; trạng thái dạy theo ánh xạ ngược (`anh_xa`), gồm `chi_nhac` và `kien_thuc_nen` (tiên quyết tiềm năng);
- câu định nghĩa gắn vào **chunk chứa câu**: tìm trong các chunk **cùng trang** vàng ghi, rồi chunk trang liền kề (lệch một trang, có cờ), bằng
  `do_khop_cau` với ngưỡng `NGUONG_CAU`. Không tìm trong trang xa hơn: một chunk sai trang là neo sai, không phải neo gần đúng;
- node `taught`/`uncertain` có chunk: `anchor`, `teaching_chunk_ids`, `defining_chunk_ids`; node `mentioned_only`/`prior_knowledge`: không `anchor`,
  `defining_chunk_ids` là chunk nhắc, `teaching_chunk_ids` rỗng (đúng như node thật của A5);
- không tìm được chunk (không có câu, không có trang, hay không khớp): node **vẫn vào canonical**, `anchor` và các danh sách chunk để trống,
  cờ `oracle_khong_co_chunk` trên node, và được đếm cùng lý do trong báo cáo (không bỏ ngầm).
"""
from __future__ import annotations

import difflib
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from danhgia.phieu.can import NGUONG_CAU
from danhgia.phieu.kiem import do_khop_cau

from .anh_xa import CO_NEO, sang_may

THUAT_TOAN = "oracle-a8-g3-v1"
SAU_TRANG_THAI = ("taught", "uncertain", "mentioned_only", "unchecked", "prior_knowledge", "not_subject_matter")
KHOA_NUT = ("node_id", "name", "aliases", "anchor", "anchor_candidate_id", "defining_chunk_ids", "defining_chunk_ids_source",
            "description", "evidence", "first_mention_index", "first_order_index", "learnable", "members", "name_kind", "node_type",
            "source_chunk_ids", "source_refs", "symbols", "teaching_chunk_ids", "teaching_conflict", "teaching_order_index",
            "teaching_status", "mentioned_in")
KHOA_PAYLOAD = ("nodes", "edges", "members", "redirects", "deferred", "deferred_pairs", "source_candidates", "stage", "upstream_chain",
                "canonical_has_anchors", "schema_version", "doc_id")


class GhiDeCanonical(ValueError):
    """Kho đã có canonical không phải oracle (chép từ lượt chính): oracle không được ghi đè, cũng không được đứng sau nó."""


def _ma(tien_to, ma):
    return tien_to + hashlib.sha256(ma.encode("utf-8")).hexdigest()[:24]


def tim_chunk(cau, trang, chunks, nguong=NGUONG_CAU):
    """Trả `(chunk | None, điểm, lý do)`. Lý do: `ok`, `ok_lech_trang`, `khong_co_cau`, `khong_co_trang`, `khong_khop`."""
    if not cau or not str(cau).strip():
        return None, 0.0, "khong_co_cau"
    if not isinstance(trang, int) or isinstance(trang, bool):
        return None, 0.0, "khong_co_trang"
    tot_nhat = 0.0
    for cac_trang, ly_do in (((trang,), "ok"), ((trang - 1, trang + 1), "ok_lech_trang")):
        ung = [c for c in chunks if c["page"] in cac_trang]
        diem = [(do_khop_cau(cau, c["text"]), c.get("role") == "noi_dung", -c["order_index"], c) for c in ung]
        if diem:
            tot = max(diem, key=lambda d: d[:3])
            tot_nhat = max(tot_nhat, tot[0])
            if tot[0] >= nguong:
                return tot[3], tot[0], ly_do
    return None, tot_nhat, "khong_khop"


def _vi_tri_cau(cau, van_ban):
    """(char_start, câu như trong chunk). Khớp nguyên văn thì lấy đúng đoạn; không thì lấy đầu khối khớp dài nhất."""
    cho = van_ban.find(cau)
    if cho >= 0:
        return cho, van_ban[cho:cho + len(cau)]
    kq = difflib.SequenceMatcher(None, van_ban, cau, autojunk=False).find_longest_match(0, len(van_ban), 0, len(cau))
    return max(0, kq.a - kq.b), cau


def dung_canonical(g3, chunks, *, doc_id, mau_manifest=None, g3_sha256, nguong=NGUONG_CAU):
    """Trả `(payload, manifest, bao_cao)`.

    `chunks`: danh sách chunk `{chunk_id, page, text, order_index, role}` của lượt chính (chunk có vai trò). `mau_manifest`: manifest canonical của
    lượt chính (nguồn của `source_hash`, `candidate_version`, `anchor_chunks_version`); thiếu thì dùng giá trị rỗng.
    """
    mau = mau_manifest or {}
    cau_hinh_mau = mau.get("config", {})
    nut, ung_vien, hang = [], [], []
    dem = {"tong": 0, "co_chunk": 0, "khong_co_chunk": 0, "trang_lech": 0, "theo_ly_do": {}, "theo_trang_thai": {}}
    for k in g3["khai_niem"]:
        ma = k["ma"]
        trang_thai = sang_may(k["trang_thai"])
        chunk, diem, ly_do = tim_chunk(k["dinh_nghia"]["cau"], k["dinh_nghia"]["trang"], chunks, nguong)
        node_id, cand_id = _ma("node_", ma), _ma("candidate_oracle_", ma)
        thu_tu = chunk["order_index"] if chunk else None
        bang_chung = anchor = None
        if chunk:
            cho, cau_trong_chunk = _vi_tri_cau(k["dinh_nghia"]["cau"], chunk["text"])
            bang_chung = {"chunk_id": chunk["chunk_id"], "char_start": cho, "char_end": cho + len(cau_trong_chunk), "quote": cau_trong_chunk}
            if trang_thai in CO_NEO | {"uncertain"}:
                anchor = {"chunk_id": chunk["chunk_id"], "char_start": cho, "sentence": cau_trong_chunk}
        ids = [chunk["chunk_id"]] if chunk else []
        co_day = trang_thai in CO_NEO | {"uncertain"}
        nut.append({
            "node_id": node_id, "name": k["ten"],
            "aliases": [{"name": t, "candidate_id": cand_id, "evidence": bang_chung or {}} for t in k["ten_khac"]],
            "anchor": anchor, "anchor_candidate_id": cand_id if anchor else None,
            "defining_chunk_ids": list(ids), "defining_chunk_ids_source": list(ids),
            "description": k["dinh_nghia"]["cau"] or k["ten"], "description_status": "oracle_g3",
            "evidence": [bang_chung] if bang_chung else [],
            "first_mention_index": thu_tu, "first_order_index": thu_tu, "learnable": True, "members": [cand_id],
            "name_kind": "name", "node_type": "concept", "caption_source": None, "media_id": None, "nghi_gop_nham": False,
            "orphan_reason": None, "source_chunk_ids": list(ids), "source_refs": [], "symbols": [],
            "teaching_chunk_ids": list(ids) if co_day else [], "teaching_conflict": False,
            "teaching_order_index": thu_tu if co_day else None, "teaching_status": trang_thai,
            "mentioned_in": [chunk.get("role")] if chunk and not co_day and chunk.get("role") else [],
            "oracle_ma_g3": ma, "oracle_khong_co_chunk": chunk is None, "oracle_ly_do_chunk": ly_do,
        })
        ung_vien.append({"candidate_id": cand_id, "name": k["ten"], "aliases": list(k["ten_khac"]), "doc_id": doc_id,
                         "evidence": [bang_chung] if bang_chung else [], "first_order_index": thu_tu, "learnable": True,
                         "node_type": "concept", "description": None, "source_refs": []})
        dem["tong"] += 1
        dem["co_chunk" if chunk else "khong_co_chunk"] += 1
        dem["trang_lech"] += ly_do == "ok_lech_trang"
        dem["theo_ly_do"][ly_do] = dem["theo_ly_do"].get(ly_do, 0) + 1
        dem["theo_trang_thai"][trang_thai] = dem["theo_trang_thai"].get(trang_thai, 0) + 1
        hang.append({"ma_g3": ma, "node_id": node_id, "trang_thai_vang": k["trang_thai"], "trang_thai_may": trang_thai,
                     "chunk_id": chunk["chunk_id"] if chunk else None, "diem_khop": round(diem, 4), "ly_do": ly_do,
                     "trang_vang": k["dinh_nghia"]["trang"]})
    thong_ke = {"node_count": len(nut), "candidate_count": len(ung_vien), "oracle": dem}
    payload = {
        "schema_version": 1, "doc_id": doc_id, "stage": "complete", "upstream_chain": "gop", "canonical_has_anchors": True,
        "nodes": nut, "edges": [], "members": {n["node_id"]: list(n["members"]) for n in nut}, "redirects": {}, "deferred": [],
        "deferred_pairs": [], "review": [], "merge_review": [], "decision_log": [], "anchor_log": [], "anchor_decision_log": [],
        "anchor_prior_verify_decision_log": [], "nominations": {}, "edge_types": {}, "candidate_quality": {},
        "source_candidates": ung_vien, "cost_summary": {"usd": 0.0, "input_tokens": 0, "output_tokens": 0}, "stats": thong_ke,
        "oracle": {"thuat_toan": THUAT_TOAN, "g3_sha256": g3_sha256, "ma_sach": g3["ma_sach"], "nguong_cau": nguong},
    }
    cau_hinh = {"algorithm_id": THUAT_TOAN, "upstream_chain": "gop", "canonical_has_anchors": True, "g3_sha256": g3_sha256,
                "nguong_cau": nguong, "candidate_version": cau_hinh_mau.get("candidate_version"),
                "candidate_config_hash": cau_hinh_mau.get("candidate_config_hash"),
                "anchor_chunks_version": cau_hinh_mau.get("anchor_chunks_version")}
    manifest = {"artifact_type": "canonical", "doc_id": doc_id, "source_hash": mau.get("source_hash"),
                "config": cau_hinh, "config_hash": hashlib.sha256(json.dumps(cau_hinh, sort_keys=True).encode()).hexdigest(),
                "upstream_version": cau_hinh_mau.get("candidate_version"), "upstream_chain": "gop", "canonical_has_anchors": True,
                "stats": thong_ke, "oracle": True}
    bao_cao = {**dem, "khong_co_chunk_ma_g3": [h["ma_g3"] for h in hang if h["chunk_id"] is None], "hang": hang,
               "g3_sha256": g3_sha256, "ngay": datetime.now(timezone.utc).date().isoformat()}
    return payload, manifest, bao_cao


def kiem_canonical(payload, manifest, chunk_ids=None):
    """Kiểm lược đồ canonical theo đúng các trường mà BuildClusters, BuildMentions, BuildMainEdges, ValidateGraph và BuildRoadmap đọc.
    Trả danh sách lỗi (rỗng nghĩa là hợp lệ)."""
    loi = []
    for khoa in KHOA_PAYLOAD:
        if khoa not in payload:
            loi.append(f"payload: thiếu {khoa}")
    if loi:
        return loi
    if payload["stage"] != "complete" or payload["upstream_chain"] != "gop" or payload["canonical_has_anchors"] is not True:
        loi.append("payload: stage phải là 'complete', upstream_chain 'gop', canonical_has_anchors true")
    if not isinstance(payload["nodes"], list) or not payload["nodes"]:
        loi.append("payload.nodes: phải là danh sách không rỗng")
        return loi
    ung = {c.get("candidate_id") for c in payload["source_candidates"]}
    thay = set()
    for i, n in enumerate(payload["nodes"]):
        noi = f"nodes[{i}]"
        for khoa in KHOA_NUT:
            if khoa not in n:
                loi.append(f"{noi}: thiếu {khoa}")
        if any(k not in n for k in KHOA_NUT):
            continue
        if not isinstance(n["node_id"], str) or n["node_id"] in thay:
            loi.append(f"{noi}: node_id thiếu hay trùng")
        thay.add(n["node_id"])
        if not str(n["name"]).strip():
            loi.append(f"{noi}: tên rỗng")
        if n["teaching_status"] not in SAU_TRANG_THAI:
            loi.append(f"{noi}: teaching_status {n['teaching_status']!r} ngoài sáu giá trị")
        if not isinstance(n["learnable"], bool):
            loi.append(f"{noi}: learnable phải là bool")
        for a in n["aliases"]:
            if not isinstance(a, dict) or not str(a.get("name", "")).strip():
                loi.append(f"{noi}: alias phải là dict có name")
        if n["anchor"] is not None:
            a = n["anchor"]
            if not (isinstance(a, dict) and a.get("chunk_id") and isinstance(a.get("char_start"), int) and str(a.get("sentence", "")).strip()):
                loi.append(f"{noi}: anchor cần chunk_id, char_start nguyên, sentence")
            elif n["teaching_chunk_ids"] != [a["chunk_id"]] or a["chunk_id"] not in n["defining_chunk_ids"]:
                loi.append(f"{noi}: anchor không khớp teaching_chunk_ids/defining_chunk_ids")
        for khoa in ("defining_chunk_ids", "defining_chunk_ids_source", "teaching_chunk_ids", "source_chunk_ids"):
            if not isinstance(n[khoa], list):
                loi.append(f"{noi}: {khoa} phải là danh sách")
            elif chunk_ids is not None and set(n[khoa]) - set(chunk_ids):
                loi.append(f"{noi}: {khoa} trỏ tới chunk không có: {sorted(set(n[khoa]) - set(chunk_ids))}")
        if n["teaching_status"] in ("mentioned_only", "prior_knowledge") and (n["anchor"] is not None or n["teaching_chunk_ids"]):
            loi.append(f"{noi}: node {n['teaching_status']} không được có anchor hay teaching_chunk_ids")
        if set(n["members"]) - ung:
            loi.append(f"{noi}: members trỏ tới ứng viên không có trong source_candidates")
    if set(payload["members"]) != thay:
        loi.append("payload.members: khoá phải đúng tập node_id")
    for khoa in ("artifact_type", "doc_id", "config_hash", "config"):
        if khoa not in manifest:
            loi.append(f"manifest: thiếu {khoa}")
    if "source_hash" not in manifest:
        loi.append("manifest: thiếu source_hash")
    cfg = manifest.get("config") or {}
    for khoa in ("algorithm_id", "upstream_chain", "canonical_has_anchors"):
        if khoa not in cfg:
            loi.append(f"manifest.config: thiếu {khoa}")
    return loi


def ghi_canonical(kho, doc_id, payload, manifest):
    """Ghi canonical oracle làm phiên bản canonical mới của kho lượt và trả số phiên bản.

    Kho lượt oracle không được có canonical của lượt chính. Nếu đã có canonical oracle cùng G3 thì dùng lại (chạy tiếp sau ngắt); nếu có
    canonical khác thì từ chối, không ghi đè."""
    goc = Path(kho) / "canonical" / doc_id
    co = sorted((int(p.name[1:]), p) for p in goc.iterdir() if p.name[1:].isdigit()) if goc.exists() else []
    if co:
        so, duong = co[-1]
        cu = json.loads((duong / "manifest.json").read_text(encoding="utf-8"))
        if cu.get("config", {}).get("algorithm_id") == THUAT_TOAN and cu["config"].get("g3_sha256") == manifest["config"]["g3_sha256"]:
            return so
        raise GhiDeCanonical(f"kho {kho} đã có canonical v{so} không phải oracle của G3 này; oracle không ghi đè canonical của lượt chính")
    so = 1
    thu_muc = goc / f"v{so}"
    thu_muc.mkdir(parents=True)
    ghi_manifest = {**manifest, "version": so, "created_at": datetime.now(timezone.utc).isoformat()}
    (thu_muc / "canonical.json").write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    (thu_muc / "manifest.json").write_text(json.dumps(ghi_manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return so
