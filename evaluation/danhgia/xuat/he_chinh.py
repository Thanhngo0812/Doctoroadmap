"""Seam xuất: kho artifact (chỉ đọc) của lượt chạy hệ chính -> hợp đồng `danh-gia-xuat-1`.

Chuỗi phiên bản đi theo manifest của graph: graph ở stage `stages`, chunks theo `chunks_version` của manifest, các manifest
upstream cho số đo từng stage. Trường thiếu là lỗi (`LoiXuat`), không có giá trị điền ngầm; chỗ nào artifact không có đo đạc
thì ghi `null` và nói rõ trong `chi_phi.ghi_chu`.

Seam này đọc tệp JSON thẳng, không gọi mô hình và không ghi vào kho. Kho Pha B nhận bằng tham số; kho Pha B chung
(`artifacts/phase_b/live.json`) bị từ chối.
"""
from __future__ import annotations

import json
from pathlib import Path

from danhgia.hop_dong import LoiHopDong, kiem_hoac_loi
from danhgia.hop_dong.luoc_do import TEN_LUOC_DO

KHOA_DINH_DANH = ("he", "bien_the", "luot_nhieu", "commit", "ngay_chay", "transport", "sha256_pdf", "so_trang")
KHOA_GRAPH = ("nodes", "mentioned_nodes", "excluded_nodes", "requires_edges", "soft_backward_edges", "bypassed_edges",
              "sequence", "modules", "suspected_pairs", "secondary_log", "cost_summary", "stage")
TIEN_TO_NGUON_GOC = (("main_", "pass_chinh"), ("secondary_pair", "pass_phu"))


class LoiXuat(ValueError):
    """`args[0]` là danh sách mọi lỗi tìm được."""

    def __init__(self, loi):
        super().__init__(loi)
        self.loi = loi

    def __str__(self):
        return "không xuất được hợp đồng:\n- " + "\n- ".join(self.loi)


def _doc(duong: Path):
    try:
        return json.loads(duong.read_text(encoding="utf-8"))
    except OSError as loi:
        raise LoiXuat([f"không đọc được {duong}: {loi}"]) from loi


def _lay(doi_tuong, khoa, noi, loi, *, kieu=None):
    if khoa not in doi_tuong:
        loi.append(f"{noi}: thiếu {khoa}")
        return None
    gia_tri = doi_tuong[khoa]
    if kieu is not None and not isinstance(gia_tri, kieu):
        loi.append(f"{noi}.{khoa}: cần {kieu.__name__}, đang là {type(gia_tri).__name__}")
        return None
    return gia_tri


def _nguon_goc(ma_phien, noi, loi):
    for tien_to, ten in TIEN_TO_NGUON_GOC:
        if isinstance(ma_phien, str) and ma_phien.startswith(tien_to):
            return ten
    loi.append(f"{noi}: session_id {ma_phien!r} không rõ là pass chính hay pass phụ")
    return None


def _ten_khac(aliases, noi, loi):
    """Alias trong graph là {name, evidence, candidate_id}; hợp đồng chỉ cần tên."""
    if aliases is None:
        return None
    ket_qua = []
    for chi_so, alias in enumerate(aliases):
        ten = alias.get("name") if isinstance(alias, dict) else alias
        if not isinstance(ten, str):
            loi.append(f"{noi}.aliases[{chi_so}]: không lấy được tên")
        else:
            ket_qua.append(ten)
    return ket_qua


def _khai_niem(nut, *, trong_day_hoc, bi_loai, da_gop, vi_tri, chunks, loi):
    noi = f"nút {nut.get('node_id')}"
    anchor = nut.get("anchor")
    cau_neo = None
    if anchor:
        ma_chunk = anchor.get("chunk_id")
        if ma_chunk not in chunks:
            loi.append(f"{noi}: câu neo trỏ tới chunk {ma_chunk!r} không có trong kho chunks")
        else:
            cau_neo = {"trang": chunks[ma_chunk]["page"], "cau": anchor.get("sentence"), "ma_chunk": ma_chunk}
    ket_qua = {"ma": _lay(nut, "node_id", noi, loi), "ten": _lay(nut, "name", noi, loi),
               "ten_khac": _ten_khac(_lay(nut, "aliases", noi, loi, kieu=list), noi, loi), "kieu": _lay(nut, "node_type", noi, loi),
               "trang_thai_day": _lay(nut, "teaching_status", noi, loi), "cau_neo": cau_neo,
               "trong_day_hoc": trong_day_hoc, "vi_tri": vi_tri, "module": nut.get("module_id"),
               "ung_vien_goc": _lay(nut, "members", noi, loi, kieu=list), "da_gop": da_gop, "bi_loai": bi_loai}
    if vi_tri is not None and nut.get("sequence_index") != vi_tri:
        loi.append(f"{noi}: sequence_index {nut.get('sequence_index')!r} khác vị trí trong dãy học {vi_tri}")
    return ket_qua


def _canh(graph, chunks, loi, nguon_goc=None):
    """`nguon_goc` (tuỳ chọn): ép mọi cạnh về một giá trị, cho hệ không phải hệ chính (baseline, oracle) vốn không có session_id pass chính/phụ."""
    ket_qua, thay = [], {}
    nhom = (("requires_edges", False), ("bypassed_edges", True), ("soft_backward_edges", False))
    for ten_nhom, bo_qua in nhom:
        for chi_so, e in enumerate(graph[ten_nhom]):
            noi = f"{ten_nhom}[{chi_so}]"
            if e.get("edge_type", "requires") != "requires":
                loi.append(f"{noi}: edge_type {e.get('edge_type')!r} chưa có chỗ trong hợp đồng")
                continue
            mem = bool(e.get("soft"))
            if mem and not e.get("soft_reason"):
                loi.append(f"{noi}: cạnh mềm không có soft_reason")
                continue
            khoa = (e["source"], e["target"], mem, bo_qua)
            if khoa in thay:
                continue
            thay[khoa] = True
            bang_chung = None
            if e.get("quote"):
                ma_chunk = (e.get("chunk_ids") or [None])[0]
                trang = chunks[ma_chunk]["page"] if ma_chunk in chunks else None
                bang_chung = {"trang": trang, "cau": e["quote"]}
            ket_qua.append({"nguon": e["source"], "dich": e["target"],
                            "nguon_goc": nguon_goc or _nguon_goc(e.get("session_id"), noi, loi), "mem": mem,
                            "ly_do_mem": e["soft_reason"] if mem else None, "bo_qua": bo_qua,
                            "bang_chung": bang_chung})
    return ket_qua


def _cap_ung_vien(graph):
    nhat_ky = {row["pair_id"]: row for row in graph["secondary_log"]}
    cap = []
    for cap_tho in graph["suspected_pairs"]:
        dong = nhat_ky.get(cap_tho["pair_id"])
        diem = None
        if dong is not None and dong.get("score_left_to_right") is not None:
            diem = {"trai_sang_phai": dong["score_left_to_right"], "phai_sang_trai": dong.get("score_right_to_left")}
        cap.append({"trai": cap_tho["left"], "phai": cap_tho["right"], "nguon_de_cu": list(cap_tho.get("sources", [])),
                    "quyet_dinh": dong["status"] if dong is not None else "khong_co_trong_nhat_ky",
                    "nguong": dong.get("threshold") if dong is not None else None, "diem_ml": diem})
    return {"cap": cap, "cua_so_dinh_nghia": None}


def _cau_truc(chunks_list, sections, loi):
    from danhgia.hop_dong.luoc_do import VAI_TRO_VUNG
    trang_nho_nhat = {}
    for c in chunks_list:
        trang_nho_nhat[c["parent_section_id"]] = min(c["page"], trang_nho_nhat.get(c["parent_section_id"], c["page"]))
    for nhan, muc in (("chunk", chunks_list), ("section", sections)):
        la = sorted({m["role"] for m in muc} - set(VAI_TRO_VUNG))
        if la:
            loi.append(f"{nhan}: vai trò {la} ngoài sáu giá trị của hợp đồng; không tự ánh xạ")
    return {
        "tieu_de": [{"ma": s["section_id"], "chu": s["title"], "cap": s["level"], "cha": s["parent_section_id"],
                     "trang": trang_nho_nhat.get(s["section_id"]), "ma_dong": None} for s in sections],
        "muc": [{"ma": s["section_id"], "vai_tro": s["role"]} for s in sections],
        "doan_van": [{"ma": c["chunk_id"], "trang": c["page"], "duong_muc": list(c["section_path"]),
                      "vai_tro": c["role"]} for c in chunks_list],
    }


def _khau_tu_stats(manifest):
    stats = manifest.get("stats") or {}
    if "runtime_seconds" not in stats:
        return None
    return {"giay_chay": stats["runtime_seconds"], "giay_cho_embedding": stats.get("embedding_wait_seconds"),
            "so_loi_goi_mo_hinh": stats.get("model_calls"), "token_vao": stats.get("input_tokens"),
            "token_ra": stats.get("output_tokens"), "so_loi_goi_embedding": stats.get("embedding_model_calls"),
            "usd": None}


def _chi_phi(kho, doc_id, phien_ban, graph, kho_pha_b, loi):
    theo_khau, ghi_chu = {}, []
    chuoi, van = [], phien_ban
    while van is not None:
        duong = kho / "graph" / doc_id / f"v{van}" / "manifest.json"
        if not duong.exists():
            break
        manifest = _doc(duong)
        chuoi.append((van, manifest))
        van = manifest.get("upstream_version")
    for so, manifest in chuoi:
        khau = _khau_tu_stats(manifest)
        if khau is not None:
            theo_khau[f"graph_v{so}_{manifest.get('stage')}"] = khau
    cs = graph["cost_summary"]
    gom = theo_khau.setdefault(f"graph_v{phien_ban}_{graph['stage']}", {
        "giay_chay": None, "giay_cho_embedding": None, "so_loi_goi_mo_hinh": None, "token_vao": None, "token_ra": None,
        "so_loi_goi_embedding": None, "usd": None})
    gom.update({"token_vao": cs.get("input_tokens"), "token_ra": cs.get("output_tokens"), "usd": cs.get("usd")})
    if not any(k["giay_chay"] is not None for k in theo_khau.values()):
        ghi_chu.append("artifact không có đo thời gian theo stage (stats.runtime_seconds); giay_chay là null")
    if kho_pha_b is None:
        ghi_chu.append("không chỉ định kho Pha B nên không có chi đặt tên module")
    else:
        duong = Path(kho_pha_b)
        if duong.name == "live.json" and duong.parent.name == "phase_b":
            loi.append(f"{duong}: kho Pha B chung không được đọc; dùng kho riêng của lượt chạy")
        else:
            hang = [r for r in _doc(duong).get("usage", []) if r.get("purpose") == "module_title"
                    and r.get("doc_id") == doc_id]
            theo_khau["dat_ten_module"] = {
                "giay_chay": sum(r.get("elapsed_ms", 0) for r in hang) / 1000, "giay_cho_embedding": None,
                "so_loi_goi_mo_hinh": len(hang), "token_vao": sum(r.get("input_tokens", 0) for r in hang),
                "token_ra": sum(r.get("output_tokens", 0) + r.get("thought_tokens", 0) for r in hang),
                "so_loi_goi_embedding": None, "usd": sum(r.get("cost_usd", 0.0) for r in hang)}
    tong = {}
    for truong in ("giay_chay", "giay_cho_embedding", "so_loi_goi_mo_hinh", "token_vao", "token_ra",
                   "so_loi_goi_embedding", "usd"):
        co = [k[truong] for k in theo_khau.values() if k[truong] is not None]
        tong[truong] = sum(co) if co else None
    return {"theo_khau": theo_khau, "tong": tong, "ghi_chu": "; ".join(ghi_chu) if ghi_chu else None}


def xuat(kho, doc_id, phien_ban, *, dinh_danh, kho_pha_b=None):
    """Xuất hợp đồng cho graph `phien_ban` của `doc_id`. `dinh_danh` do người chạy khai: những gì artifact không ghi."""
    kho = Path(kho)
    loi = []
    thieu = [khoa for khoa in KHOA_DINH_DANH if khoa not in dinh_danh]
    if thieu:
        loi.append(f"dinh_danh: thiếu {thieu}")
    duong_graph = kho / "graph" / doc_id / f"v{phien_ban}"
    graph, manifest = _doc(duong_graph / "graph.json"), _doc(duong_graph / "manifest.json")
    for khoa in KHOA_GRAPH:
        _lay(graph, khoa, "graph.json", loi)
    if graph.get("stage") != "stages":
        loi.append(f"graph.json: stage là {graph.get('stage')!r}, cần 'stages'")
    config = manifest.get("config", {})
    for khoa in ("model_id", "chunks_version"):
        if khoa not in config:
            loi.append(f"manifest.config: thiếu {khoa}")
    if "config_hash" not in manifest:
        loi.append("manifest: thiếu config_hash")
    if loi:
        raise LoiXuat(loi)
    duong_chunks = kho / "chunks" / doc_id / f"v{config['chunks_version']}"
    chunks_list, sections = _doc(duong_chunks / "chunks.json"), _doc(duong_chunks / "sections.json")
    return xuat_tu_du_lieu(doc_id, phien_ban, graph, manifest, chunks_list, sections, dinh_danh=dinh_danh, kho=kho,
                           kho_pha_b=kho_pha_b, loi=loi)


def xuat_tu_du_lieu(doc_id, phien_ban, graph, manifest, chunks_list, sections, *, dinh_danh, kho=None, kho_pha_b=None,
                    loi=None, chi_phi=None, nguon_goc_canh=None):
    """Dựng hợp đồng từ graph đã nạp (không đọc kho). Hệ chính đi qua `xuat`; bộ phát lại và baseline đưa graph tự dựng vào đây.

    `chi_phi` (tuỳ chọn) thay phần đo của kho: hệ không chạy pipeline không có đo đạc để đọc. `nguon_goc_canh` ép nguồn gốc
    cạnh (baseline, oracle). `manifest` cần `config_hash` và `config.model_id`.
    """
    loi = [] if loi is None else loi
    config = manifest.get("config", {})
    chunks = {c["chunk_id"]: c for c in chunks_list}
    vi_tri = {ma: i for i, ma in enumerate(graph["sequence"])}
    khai_niem = []
    for nut in graph["nodes"]:
        khai_niem.append(_khai_niem(nut, trong_day_hoc=nut["node_id"] in vi_tri, bi_loai=False, da_gop=False,
                                    vi_tri=vi_tri.get(nut["node_id"]), chunks=chunks, loi=loi))
    for khoa, bi_loai, da_gop in (("mentioned_nodes", False, False), ("excluded_nodes", True, False),
                                  ("merged_nodes", False, True)):
        for nut in graph.get(khoa) or []:
            khai_niem.append(_khai_niem(nut, trong_day_hoc=False, bi_loai=bi_loai, da_gop=da_gop, vi_tri=None,
                                        chunks=chunks, loi=loi))
    hop_dong = {
        "schema": TEN_LUOC_DO,
        "dinh_danh": {"doc_id": doc_id, "sha256_pdf": dinh_danh.get("sha256_pdf"), "so_trang": dinh_danh.get("so_trang"),
                      "he": dinh_danh.get("he"), "bien_the": dinh_danh.get("bien_the"),
                      "luot_nhieu": dinh_danh.get("luot_nhieu"), "commit": dinh_danh.get("commit"),
                      "hash_cau_hinh": manifest["config_hash"], "mo_hinh": config["model_id"],
                      "transport": dinh_danh.get("transport"), "ngay_chay": dinh_danh.get("ngay_chay")},
        "cau_truc": _cau_truc(chunks_list, sections, loi),
        "khai_niem": khai_niem,
        "ban_do_danh_tinh": dict(graph.get("identity_map") or {}),
        "canh": _canh(graph, chunks, loi, nguon_goc_canh),
        "cap_ung_vien": _cap_ung_vien(graph),
        "lo_trinh": {"day_hoc": list(graph["sequence"]),
                     "module": [{"ma": m["module_id"], "ten": m["title"], "thanh_vien": list(m["node_ids"])}
                                for m in graph["modules"]]},
        "chi_phi": chi_phi if chi_phi is not None else _chi_phi(Path(kho), doc_id, phien_ban, graph, kho_pha_b, loi),
    }
    if loi:
        raise LoiXuat(loi)
    try:
        kiem_hoac_loi(hop_dong)
    except LoiHopDong as ngoai_le:
        raise LoiXuat([f"hợp đồng xuất ra không qua validator: {x}" for x in ngoai_le.loi]) from ngoai_le
    return hop_dong
