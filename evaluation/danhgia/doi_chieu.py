"""Đối chiếu bộ chấm mới với bộ chấm cũ trên cùng graph và cùng vàng. Được nhập mã pipeline (như seam xuất).

Bên cũ: `score_roadmap_order(remap_gold_ids=True)` cho Q6, Q7, Q7b; `score_edges` của `gold_scoring` cho hồ sơ spec; `grade` +
`reduced` của `scripts/doc-lo-trinh/thu_cua_so_rong_a8.py` (bộ chấm tập giữ lại v3) cho hồ sơ giu_lai_v3.
Bên mới: xuất hợp đồng, đổi vàng cũ sang G3/G4/bảng căn, rồi `cham`. Mọi sai lệch phải bằng 0; có lệch thì báo, không chỉnh số.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from danhgia.cham import dong
from danhgia.cham.bang import cham
from danhgia.vang.cu import chuyen
from danhgia.xuat import xuat
from danhgia.xuat.chuyen_huong import doc_chuyen_huong

_GOC_REPO = Path(__file__).resolve().parents[2]
DINH_DANH_DOI_CHIEU = {"he": "chinh", "bien_the": "mac_dinh", "luot_nhieu": 0, "commit": "doi-chieu", "ngay_chay": "doi-chieu",
                       "transport": "doi-chieu", "sha256_pdf": None, "so_trang": None}


def _nhap_bo_cham_cu():
    for duong in (_GOC_REPO / "src", _GOC_REPO / "scripts" / "doc-lo-trinh"):
        if str(duong) not in sys.path:
            sys.path.insert(0, str(duong))
    from doc2roadmap.application.use_cases import a8_score
    from doc2roadmap.domain import gold_scoring
    from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore
    import thu_cua_so_rong_a8
    return a8_score, gold_scoring, thu_cua_so_rong_a8, JsonArtifactStore


def _gop_moi(rows):
    return {(r["thuoc"], r["kieu"]): r for r in dong.gop_cuon(rows)}


def doi_chieu(kho, doc_id, phien_ban, duong_vang):
    """Trả `{"bang": [...], "lech": n, "ghi_chu": {...}}`; mỗi dòng của bảng có `chi_so`, `cu`, `moi`, `lech`."""
    a8_score, gold_scoring, thu, JsonArtifactStore = _nhap_bo_cham_cu()
    kho, duong_vang = Path(kho), Path(duong_vang)
    duong_graph = kho / "graph" / doc_id / f"v{phien_ban}" / "graph.json"
    payload = json.loads(duong_graph.read_text(encoding="utf-8"))
    identity = payload.get("identity_map", {})
    vang_cu = a8_score.load_gold(duong_vang)

    # --- bên cũ ---
    cu = a8_score.score_roadmap_order(duong_graph, [duong_vang], remap_gold_ids=True, store=JsonArtifactStore(kho))
    ten = {n["node_id"]: n.get("name") for n in [*payload["nodes"], *payload.get("excluded_nodes", []),
                                                  *payload.get("merged_nodes", []), *payload.get("mentioned_nodes", [])]}
    _, chuyen_huong = doc_chuyen_huong(kho, doc_id, phien_ban)
    (vang_r,), bao_cao_cu = a8_score._remap_golds([vang_cu], chuyen_huong, set(ten), mode="union")
    canh_vang = {(identity.get(a, a), identity.get(b, b)) for a, b in a8_score.gold_edges(vang_r)}
    canh_vang = {(a, b) for a, b in canh_vang if a != b}
    dich = {identity.get(t, t) for t in vang_r["targets"]}
    cung = {(identity.get(e["source"], e["source"]), identity.get(e["target"], e["target"])) for e in payload["requires_edges"]
            if e.get("edge_type", "requires") == "requires" and not e.get("soft")}
    cung = {(a, b) for a, b in cung if a != b}
    hien_dien = {n["node_id"] for n in [*payload["nodes"], *payload.get("mentioned_nodes", [])]}
    sach_cu = {
        "spec": {"truc_tiep": gold_scoring.score_edges(cung, canh_vang, targets=dich),
                 "bao_dong": gold_scoring.score_edges(cung, canh_vang, targets=dich, closure=True)},
    }
    truc, dong_ = thu.grade(thu.reduced(payload["requires_edges"]), vang_r, identity, hien_dien)
    sach_cu["giu_lai_v3"] = {"truc_tiep": truc, "bao_dong": dong_}

    # --- bên mới ---
    hd = xuat(kho, doc_id, phien_ban, dinh_danh=DINH_DANH_DOI_CHIEU)
    chuyen_ket_qua = chuyen(vang_cu, ma_sach=doc_id, ten={k["ma"]: k["ten"] for k in hd["khai_niem"]},
                            node_ids={k["ma"] for k in hd["khai_niem"]}, redirects=chuyen_huong)
    g3, g4, can = chuyen_ket_qua["g3"], chuyen_ket_qua["g4"], chuyen_ket_qua["can"]
    moi = {ho_so: _gop_moi(cham(hd, g3, g4, can, ho_so=ho_so)) for ho_so in ("spec", "giu_lai_v3")}

    bang = []

    def them(chi_so, gia_cu, gia_moi):
        bang.append({"chi_so": chi_so, "cu": gia_cu, "moi": gia_moi, "lech": gia_moi != gia_cu})

    for ho_so in ("spec", "giu_lai_v3"):
        for kieu, ten_thuoc in (("truc_tiep", "a8.f1_truc_tiep.nghiem"), ("bao_dong", "a8.f1_bao_dong.nghiem")):
            c, m = sach_cu[ho_so][kieu], moi[ho_so][(ten_thuoc, "f1")]
            for truong, ten_cu in (("tp", "true_positive"), ("fp", "false_positive"), ("fn", "false_negative")):
                them(f"{ho_so} {kieu} {truong}", c[ten_cu], m[truong])
            them(f"{ho_so} {kieu} P", c["precision"], dong.chi_so_f1(m)[0])
            them(f"{ho_so} {kieu} R", c["recall"], dong.chi_so_f1(m)[1])
            them(f"{ho_so} {kieu} F1", c["f1"], dong.chi_so_f1(m)[2])
    thang = moi["spec"]
    tt = cu["gold_order"]
    q6 = thang[("a10.q6.nghiem", "ti_le")]
    them("Q6 tử (violated + same_stage + out_of_scope)", tt["violated"] + tt["same_stage"] + tt["out_of_scope"], q6["tu"])
    them("Q6 mẫu (cạnh vàng sau danh tính)", cu["gold_edge_count"], q6["mau"])
    them("Q6", tt["learning_order_error"], dong.gia_tri(q6))
    for ten_cu, ten_moi, nhan in (("target_coverage", "a10.q7.nghiem", "Q7"),
                                  ("target_coverage_with_soft", "a10.q7_ca_mem.nghiem", "Q7 cạnh mềm")):
        m = thang[(ten_moi, "trung_binh")]
        them(f"{nhan} số đích", cu[ten_cu]["targets"], m["n"])
        them(f"{nhan} trung bình", cu[ten_cu]["mean_coverage"], dong.gia_tri(m))
    them("Q7 đích trọn", cu["target_coverage"]["complete"], thang[("a10.q7_tron.nghiem", "ti_le")]["tu"])
    m = thang[("a10.q7b.nghiem", "trung_binh")]
    them("Q7b số đích", cu["target_precision"]["targets"], m["n"])
    them("Q7b trung bình", cu["target_precision"]["mean_precision"], dong.gia_tri(m))
    tu_noi_cu = cu["identity_dropped_gold_edges"] + cu.get("redirect_dropped_gold_edges", 0)
    them("cạnh vàng tự nối (danh tính + chuyển hướng)", tu_noi_cu, thang[("can.tu_noi.nghiem", "dem")]["gia_tri"])
    return {
        "bang": bang, "lech": sum(1 for dong_ in bang if dong_["lech"]),
        "ghi_chu": {"so_canh_vang_goc": len(vang_cu["edges"]), "bao_cao_chuyen_vang": chuyen_ket_qua["bao_cao"],
                    "chuyen_huong_cu": bao_cao_cu,
                    "so_nut": len(payload["nodes"]), "so_canh_cung": len(cung),
                    "ban_do_danh_tinh": len(identity)},
    }


def in_bang(ket_qua, ten):
    dong_ = [f"### {ten}", "", "| Chỉ số | Cũ | Mới | Lệch |", "|---|---|---|---|"]
    for hang in ket_qua["bang"]:
        dong_.append(f"| {hang['chi_so']} | {hang['cu']} | {hang['moi']} | {'LỆCH' if hang['lech'] else '0'} |")
    dong_.append("")
    dong_.append(f"Tổng số chỉ số lệch: {ket_qua['lech']} trên {len(ket_qua['bang'])}.")
    return "\n".join(dong_)
