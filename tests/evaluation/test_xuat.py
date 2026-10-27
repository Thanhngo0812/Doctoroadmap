"""Seam xuất: kho fixture nhỏ (cắt từ xstk-ch3-1 v68) -> hợp đồng. Trường thiếu phải báo lỗi rõ, không điền ngầm."""
import hashlib
import json
import shutil
from pathlib import Path

import pytest

from danhgia.hop_dong import kiem
from danhgia.xuat import LoiXuat, xuat

KHO = Path(__file__).resolve().parent / "fixtures" / "kho-nho"
DOC, PHIEN_BAN = "xstk-ch3-1", 68
DINH_DANH = {"he": "chinh", "bien_the": "mac_dinh", "luot_nhieu": 0, "commit": "a" * 40, "ngay_chay": "2026-10-18",
             "transport": "vertex", "sha256_pdf": None, "so_trang": None}


def doc(duong):
    return json.loads(Path(duong).read_text(encoding="utf-8"))


def ghi(duong, gia_tri):
    Path(duong).write_text(json.dumps(gia_tri, ensure_ascii=False), encoding="utf-8")


@pytest.fixture
def kho(tmp_path):
    dich = tmp_path / "kho"
    shutil.copytree(KHO, dich)
    return dich


def duong_graph(kho):
    return kho / "graph" / DOC / f"v{PHIEN_BAN}" / "graph.json"


def sua_graph(kho, ham):
    graph = doc(duong_graph(kho))
    ham(graph)
    ghi(duong_graph(kho), graph)


def bam_thu_muc(goc):
    return {str(p.relative_to(goc)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path(goc).rglob("*")) if p.is_file()}


def test_xuat_ra_hop_dong_qua_validator_va_dem_dung_theo_nguon_doc_lap():
    hd = xuat(KHO, DOC, PHIEN_BAN, dinh_danh=DINH_DANH)
    assert kiem(hd) == []
    graph = doc(duong_graph(KHO))
    assert [k["ma"] for k in hd["khai_niem"] if k["trong_day_hoc"]] == graph["sequence"]
    assert len(hd["khai_niem"]) == len(graph["nodes"]) + len(graph["mentioned_nodes"]) + len(graph["excluded_nodes"])
    mong_doi = {(e["source"], e["target"], bool(e.get("soft"))) for e in [*graph["requires_edges"], *graph["soft_backward_edges"]]}
    assert {(c["nguon"], c["dich"], c["mem"]) for c in hd["canh"]} == mong_doi
    assert len(hd["canh"]) == len(mong_doi)  # cạnh mềm nằm ở hai danh sách chỉ được xuất một lần
    assert hd["ban_do_danh_tinh"] == graph["identity_map"]
    assert hd["lo_trinh"]["day_hoc"] == graph["sequence"]
    assert hd["dinh_danh"]["doc_id"] == DOC and hd["dinh_danh"]["mo_hinh"] == "gemini-3.1-flash-lite"
    assert len(hd["dinh_danh"]["hash_cau_hinh"]) == 64


def test_cau_neo_va_bang_chung_mang_trang_cua_chunk():
    hd = xuat(KHO, DOC, PHIEN_BAN, dinh_danh=DINH_DANH)
    chunks = {c["chunk_id"]: c for c in doc(KHO / "chunks" / DOC / "v7" / "chunks.json")}
    co_neo = [k for k in hd["khai_niem"] if k["cau_neo"]]
    assert co_neo
    for k in co_neo:
        assert k["cau_neo"]["trang"] == chunks[k["cau_neo"]["ma_chunk"]]["page"]
    mem = [c for c in hd["canh"] if c["mem"]]
    assert mem and all(c["ly_do_mem"] for c in mem)
    assert {c["nguon_goc"] for c in hd["canh"]} <= {"pass_chinh", "pass_phu"}


def test_cap_ung_vien_noi_nhat_ky_pass_phu_theo_ma_cap():
    hd = xuat(KHO, DOC, PHIEN_BAN, dinh_danh=DINH_DANH)
    graph = doc(duong_graph(KHO))
    nhat_ky = {r["pair_id"]: r["status"] for r in graph["secondary_log"]}
    cap_goc = {(p["left"], p["right"]): nhat_ky.get(p["pair_id"], "khong_co_trong_nhat_ky") for p in graph["suspected_pairs"]}
    assert {(c["trai"], c["phai"]): c["quyet_dinh"] for c in hd["cap_ung_vien"]["cap"]} == cap_goc


def test_khong_ghi_vao_kho():
    truoc = bam_thu_muc(KHO)
    xuat(KHO, DOC, PHIEN_BAN, dinh_danh=DINH_DANH)
    assert bam_thu_muc(KHO) == truoc


@pytest.mark.parametrize("khoa", ["sequence", "requires_edges", "cost_summary", "secondary_log", "modules"])
def test_graph_thieu_truong_la_loi_neu_ten_truong(kho, khoa):
    sua_graph(kho, lambda g: g.pop(khoa))
    with pytest.raises(LoiXuat, match=khoa):
        xuat(kho, DOC, PHIEN_BAN, dinh_danh=DINH_DANH)


def test_dinh_danh_thieu_khoa_la_loi_khong_dien_ngam():
    thieu = {k: v for k, v in DINH_DANH.items() if k != "commit"}
    with pytest.raises(LoiXuat, match="commit"):
        xuat(KHO, DOC, PHIEN_BAN, dinh_danh=thieu)


def test_manifest_thieu_model_la_loi(kho):
    duong = kho / "graph" / DOC / f"v{PHIEN_BAN}" / "manifest.json"
    manifest = doc(duong)
    del manifest["config"]["model_id"]
    ghi(duong, manifest)
    with pytest.raises(LoiXuat, match="model_id"):
        xuat(kho, DOC, PHIEN_BAN, dinh_danh=DINH_DANH)


def test_canh_mem_thieu_ly_do_la_loi(kho):
    def hong(g):
        for e in g["requires_edges"]:
            if e.get("soft"):
                del e["soft_reason"]
    sua_graph(kho, hong)
    with pytest.raises(LoiXuat, match="soft_reason"):
        xuat(kho, DOC, PHIEN_BAN, dinh_danh=DINH_DANH)


def test_session_id_la_khong_doan_nguon_goc(kho):
    def hong(g):
        g["requires_edges"][0]["session_id"] = "bat_ngo_123"
    sua_graph(kho, hong)
    with pytest.raises(LoiXuat, match="bat_ngo_123"):
        xuat(kho, DOC, PHIEN_BAN, dinh_danh=DINH_DANH)


def test_cau_neo_tro_toi_chunk_khong_co_la_loi(kho):
    def hong(g):
        nut = next(n for n in g["nodes"] if n.get("anchor"))
        nut["anchor"]["chunk_id"] = "c_khong_ton_tai"
    sua_graph(kho, hong)
    with pytest.raises(LoiXuat, match="c_khong_ton_tai"):
        xuat(kho, DOC, PHIEN_BAN, dinh_danh=DINH_DANH)


def test_vai_tro_la_khong_bi_anh_xa_ngam(kho):
    duong = kho / "chunks" / DOC / "v7" / "chunks.json"
    chunks = doc(duong)
    chunks[0]["role"] = "muc_luc_la"
    ghi(duong, chunks)
    with pytest.raises(LoiXuat, match="muc_luc_la"):
        xuat(kho, DOC, PHIEN_BAN, dinh_danh=DINH_DANH)


def tao_kho_pha_b(duong, hang):
    ghi(duong, {"cache": {}, "records": {}, "usage": hang})
    return duong


def test_chi_dat_ten_module_lay_dung_tu_usage_kho_pha_b_cua_luot(tmp_path):
    hang = [
        {"purpose": "module_title", "doc_id": DOC, "input_tokens": 100, "output_tokens": 10, "thought_tokens": 5,
         "cost_usd": 0.001, "elapsed_ms": 2000},
        {"purpose": "module_title", "doc_id": DOC, "input_tokens": 50, "output_tokens": 4, "thought_tokens": 0,
         "cost_usd": 0.0005, "elapsed_ms": 1000},
        {"purpose": "assistant", "doc_id": DOC, "input_tokens": 999, "output_tokens": 999, "cost_usd": 9.0, "elapsed_ms": 9},
        {"purpose": "module_title", "doc_id": "doc-khac", "input_tokens": 777, "output_tokens": 7, "cost_usd": 7.0, "elapsed_ms": 7},
    ]
    kho_pha_b = tao_kho_pha_b(tmp_path / "pha_b_luot.json", hang)
    hd = xuat(KHO, DOC, PHIEN_BAN, dinh_danh=DINH_DANH, kho_pha_b=kho_pha_b)
    ten = hd["chi_phi"]["theo_khau"]["dat_ten_module"]
    assert ten["so_loi_goi_mo_hinh"] == 2 and ten["token_vao"] == 150 and ten["token_ra"] == 19
    assert ten["usd"] == pytest.approx(0.0015) and ten["giay_chay"] == pytest.approx(3.0)
    graph = doc(duong_graph(KHO))
    assert hd["chi_phi"]["tong"]["usd"] == pytest.approx(graph["cost_summary"]["usd"] + 0.0015)


def test_khong_co_kho_pha_b_thi_khong_bia_chi_dat_ten_va_noi_ro():
    hd = xuat(KHO, DOC, PHIEN_BAN, dinh_danh=DINH_DANH)
    assert "dat_ten_module" not in hd["chi_phi"]["theo_khau"]
    assert "Pha B" in hd["chi_phi"]["ghi_chu"]
    assert "thời gian" in hd["chi_phi"]["ghi_chu"]  # artifact fixture không có số đo thời gian


def test_tu_choi_kho_pha_b_chung(tmp_path):
    chung = tmp_path / "artifacts" / "phase_b" / "live.json"
    chung.parent.mkdir(parents=True)
    tao_kho_pha_b(chung, [])
    with pytest.raises(LoiXuat, match="chung"):
        xuat(KHO, DOC, PHIEN_BAN, dinh_danh=DINH_DANH, kho_pha_b=chung)


def test_so_do_thoi_gian_theo_stage_duoc_dua_vao_chi_phi(kho):
    duong = kho / "graph" / DOC / f"v{PHIEN_BAN}" / "manifest.json"
    manifest = doc(duong)
    manifest["stats"] = {"runtime_seconds": 12.5, "model_calls": 3, "input_tokens": 400, "output_tokens": 40,
                         "embedding_model_calls": 2, "embedding_input_tokens": 8}
    ghi(duong, manifest)
    hd = xuat(kho, DOC, PHIEN_BAN, dinh_danh=DINH_DANH)
    khau = hd["chi_phi"]["theo_khau"][f"graph_v{PHIEN_BAN}_stages"]
    assert khau["giay_chay"] == 12.5 and khau["so_loi_goi_embedding"] == 2
    assert khau["giay_cho_embedding"] is None  # artifact cũ chưa có bộ đếm giây chờ embedding: null chứ không phải 0
    assert "thời gian" not in (hd["chi_phi"]["ghi_chu"] or "")


def test_giay_cho_embedding_doc_tu_stats_embedding_seconds(kho):
    duong = kho / "graph" / DOC / f"v{PHIEN_BAN}" / "manifest.json"
    manifest = doc(duong)
    manifest["stats"] = {"runtime_seconds": 12.5, "embedding_seconds": 4.25, "embedding_model_calls": 2}
    ghi(duong, manifest)
    hd = xuat(kho, DOC, PHIEN_BAN, dinh_danh=DINH_DANH)
    khau = hd["chi_phi"]["theo_khau"][f"graph_v{PHIEN_BAN}_stages"]
    assert khau["giay_cho_embedding"] == 4.25
    assert hd["chi_phi"]["tong"]["giay_cho_embedding"] == 4.25
