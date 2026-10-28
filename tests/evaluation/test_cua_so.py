"""DG-15: cửa sổ định nghĩa do seam xuất điền, dựng bằng hàm của pipeline (xuat/cua_so.py)."""
import json
import shutil
from pathlib import Path

import pytest

from danhgia.hop_dong import kiem
from danhgia.xuat import xuat
from danhgia.xuat.cua_so import cua_so_dinh_nghia, tham_so_cua_so
from doc2roadmap.domain.models import Chunk
from doc2roadmap.domain.prerequisites import definition_window

CAU = ["Câu một nói về alpha.", "Câu hai nói về beta.", "Câu ba nói về gamma.", "Câu bốn nói về delta.",
       "Câu năm nói về epsilon.", "Câu sáu là câu neo định nghĩa zeta.", "Câu bảy nhắc theta.", "Câu tám nhắc iota.",
       "Câu chín nhắc kappa."]
VAN_BAN = " ".join(CAU)
KHO_NHO = Path(__file__).resolve().parent / "fixtures" / "kho-nho"


def chunk():
    return Chunk(chunk_id="c1", doc_id="d", order_index=0, split_index=0, page=1, char_start=0, char_end=len(VAN_BAN),
                 parent_section_id="s", section_path=["Muc"], heading_level=1, block_types=["paragraph"], text=VAN_BAN,
                 context_prefix=None, image_refs=[], token_count=50, tokenizer_id="t")


def nut(ma, ten, *, neo=False):
    n = {"node_id": ma, "name": ten, "aliases": []}
    if neo:
        n["anchor"] = {"chunk_id": "c1", "sentence": CAU[5], "char_start": VAN_BAN.index(CAU[5])}
    return n


TEN = {"a": "alpha", "b": "beta", "t": "theta", "k": "kappa", "z": "zeta"}


def the_gioi():
    dich = nut("z", "zeta", neo=True)
    return dich, [dich] + [nut(m, ten) for m, ten in TEN.items() if m != "z"]


def tinh(truoc, sau):
    dich, nguon = the_gioi()
    return cua_so_dinh_nghia([dich], nguon, [chunk().to_dict()], truoc=truoc, sau=sau)


@pytest.mark.parametrize("truoc,sau", [(4, 2), (0, 2), (4, 0), (1, 1), (0, 0), (9, 9)])
def test_cua_so_khop_cua_so_ma_pipeline_tinh_tren_cung_chunk(truoc, sau):
    dich, _ = the_gioi()
    cua_so = definition_window(dich, [chunk()], before=truoc, after=sau)     # văn bản cửa sổ do chính hàm của pipeline tính
    mong_doi = sorted(m for m, ten in TEN.items() if m != "z" and ten in cua_so)
    assert tinh(truoc, sau) == {"z": mong_doi}


def test_cua_so_mac_dinh_4_2_la_beta_gamma_theta_iota_vao_alpha_va_kappa_ra():
    # câu neo là câu thứ 6 (chỉ số 5): lấy 4 câu trước (chỉ số 1..4) và 2 câu sau (6..7)
    assert tinh(4, 2) == {"z": ["b", "t"]}
    assert tinh(0, 2) == {"z": ["t"]}      # bỏ câu trước: beta ra khỏi cửa sổ
    assert tinh(4, 0) == {"z": ["b"]}      # bỏ câu sau: theta ra khỏi cửa sổ


def test_node_khong_dinh_vi_duoc_cua_so_khong_co_khoa():
    dich, nguon = the_gioi()
    dich_hong = dict(dich, anchor={"chunk_id": "khong-co", "sentence": CAU[5], "char_start": 0})
    ket = cua_so_dinh_nghia([dich_hong, nut("q", "kappa")], nguon, [chunk().to_dict()], truoc=4, sau=2)
    assert ket == {}


def test_tham_so_cua_so_di_theo_chuoi_upstream(tmp_path):
    def manifest(so, **kw):
        duong = tmp_path / "graph" / "d" / f"v{so}"
        duong.mkdir(parents=True)
        (duong / "manifest.json").write_text(json.dumps(kw), encoding="utf-8")
    manifest(3, config={}, upstream_version=2)
    manifest(2, config={"definition_before": 3, "definition_after": 1}, upstream_version=1)
    manifest(1, config={"definition_before": 9}, upstream_version=None)
    assert tham_so_cua_so(tmp_path, "d", 3) == (3, 1)           # gặp manifest đầu tiên có cấu hình, không đi tới v1
    assert tham_so_cua_so(tmp_path, "d", 1) == (9, 2)           # thiếu definition_after: mặc định 2 như BuildSecondaryEdges
    manifest(5, config={}, upstream_version=None)
    assert tham_so_cua_so(tmp_path, "d", 5) is None
    assert tham_so_cua_so(tmp_path, "d", 77) is None


def test_xuat_dien_cua_so_khi_chuoi_manifest_ghi_cau_hinh_va_qua_validator(tmp_path):
    kho = tmp_path / "kho"
    shutil.copytree(KHO_NHO, kho)
    duong = kho / "graph" / "xstk-ch3-1"
    ghi = lambda p, v: p.write_text(json.dumps(v, ensure_ascii=False), encoding="utf-8")  # noqa: E731
    m68 = json.loads((duong / "v68" / "manifest.json").read_text(encoding="utf-8"))
    dinh_danh = {"he": "chinh", "bien_the": "mac_dinh", "luot_nhieu": 0, "commit": "a" * 40, "ngay_chay": "2026-10-28",
                 "transport": "vertex", "sha256_pdf": None, "so_trang": None}
    # chunk của fixture chỉ có 5 trường (không có văn bản): bù văn bản từ câu neo của các node và các trường còn thiếu để dựng được cửa sổ
    duong_chunks = kho / "chunks" / "xstk-ch3-1" / "v7" / "chunks.json"
    graph = json.loads((duong / "v68" / "graph.json").read_text(encoding="utf-8"))
    cau_cua = {}
    for n in graph["nodes"]:
        neo = n.get("anchor") or {}
        if neo.get("sentence"):
            cau_cua.setdefault(neo["chunk_id"], []).append(neo["sentence"])
    # node chỉ nhắc đến: tên đặt trong câu neo của một đích (trong cửa sổ) và trong câu cách xa 6 câu (ngoài cửa sổ)
    dich_y = next(n for n in graph["nodes"] if (n.get("anchor") or {}).get("sentence"))
    cho_nho = {"aliases": [], "name_kind": "concept"}
    graph["mentioned_nodes"][0].update(cho_nho, name="zzmentionedtrong")
    graph["mentioned_nodes"][1].update(cho_nho, name="zzmentionedngoai")
    dich_y["anchor"]["sentence"] += " zzmentionedtrong"
    for n in graph["nodes"]:     # các node khác chung câu neo với dich_y phải cùng sửa để văn bản chunk còn khớp
        if n is not dich_y and (n.get("anchor") or {}).get("sentence") and n["anchor"]["chunk_id"] == dich_y["anchor"]["chunk_id"]                 and n["anchor"]["sentence"] == dich_y["anchor"]["sentence"].removesuffix(" zzmentionedtrong"):
            n["anchor"]["sentence"] = dich_y["anchor"]["sentence"]
    ghi(duong / "v68" / "graph.json", graph)
    cau_cua = {}
    for n in graph["nodes"]:
        neo = n.get("anchor") or {}
        if neo.get("sentence"):
            cau_cua.setdefault(neo["chunk_id"], []).append(neo["sentence"])
    day_du = []
    for i, c in enumerate(json.loads(duong_chunks.read_text(encoding="utf-8"))):
        van_ban = " ".join(dict.fromkeys(cau_cua.get(c["chunk_id"], [])))
        if c["chunk_id"] == dich_y["anchor"]["chunk_id"]:
            van_ban += " " + " ".join(f"Cau dem so {k} khong lien quan." for k in range(8)) + " Cau xa zzmentionedngoai."
        day_du.append({"doc_id": "xstk-ch3-1", "order_index": i, "split_index": 0, "char_start": 0, "char_end": len(van_ban), "heading_level": 1,
                       "block_types": ["paragraph"], "text": van_ban, "context_prefix": None, "image_refs": [], "token_count": 10,
                       "tokenizer_id": "t", **c})
    ghi(duong_chunks, day_du)
    hd_khong = xuat(kho, "xstk-ch3-1", 68, dinh_danh=dinh_danh)
    assert hd_khong["cap_ung_vien"]["cua_so_dinh_nghia"] is None     # chuỗi manifest không có cấu hình: không bịa cửa sổ
    (duong / "v60").mkdir()
    ghi(duong / "v60" / "manifest.json", {"stage": "edges", "doc_id": "xstk-ch3-1", "config": {"definition_before": 4, "definition_after": 2}})
    ghi(duong / "v68" / "manifest.json", dict(m68, upstream_version=60))
    hd = xuat(kho, "xstk-ch3-1", 68, dinh_danh=dinh_danh)
    cua_so = hd["cap_ung_vien"]["cua_so_dinh_nghia"]
    assert isinstance(cua_so, dict) and cua_so, "fixture phải định vị được ít nhất một cửa sổ"
    ma = {k["ma"] for k in hd["khai_niem"]}
    assert set(cua_so) <= ma and all(set(v) <= ma and d not in v for d, v in cua_so.items())
    ma_trong, ma_ngoai = graph["mentioned_nodes"][0]["node_id"], graph["mentioned_nodes"][1]["node_id"]
    assert ma_trong in cua_so[dich_y["node_id"]], "node chỉ nhắc có tên trong cửa sổ phải là nguồn của đích"
    assert ma_ngoai not in cua_so[dich_y["node_id"]], "tên nằm ngoài cửa sổ thì không là nguồn"
    assert kiem(hd) == []


def test_cua_so_khop_named_in_cua_pipeline_khi_ten_chi_khop_sau_chuan_hoa():
    """Tên khác chữ hoa/thường, dạng dựng sẵn so với tổ hợp, và y/i; đối chiếu `SecondaryFeatureContext.named_in` trên cùng ca."""
    import unicodedata

    from doc2roadmap.domain.secondary_features import SecondaryFeatureContext
    cau = ["Mo dau.", "Ta xet HÀM SỐ lien tuc.", "Dung " + unicodedata.normalize("NFD", "phép biến đổi") + " o day.", "Theo QUY LUẬT chung.",
           "Cau neo noi ve zeta o day.", "Ket thuc."]
    van_ban = " ".join(cau)
    c = Chunk(chunk_id="c1", doc_id="d", order_index=0, split_index=0, page=1, char_start=0, char_end=len(van_ban), parent_section_id="s",
              section_path=["M"], heading_level=1, block_types=["paragraph"], text=van_ban, context_prefix=None, image_refs=[],
              token_count=30, tokenizer_id="t")
    neo = {"chunk_id": "c1", "sentence": cau[4], "char_start": van_ban.index(cau[4])}
    nodes = [{"node_id": "z", "name": "zeta", "aliases": [], "anchor": neo, "teaching_status": "taught", "defining_chunk_ids": ["c1"],
              "cluster_id": "k"},
             {"node_id": "h", "name": "hàm số", "aliases": [], "anchor": None, "teaching_status": "taught", "defining_chunk_ids": ["c1"],
              "cluster_id": "k"},
             {"node_id": "p", "name": unicodedata.normalize("NFC", "phép biến đổi"), "aliases": [], "anchor": None,
              "teaching_status": "taught", "defining_chunk_ids": ["c1"], "cluster_id": "k"},
             {"node_id": "q", "name": "quy luật", "aliases": [], "anchor": None, "teaching_status": "taught", "defining_chunk_ids": ["c1"],
              "cluster_id": "k"}]
    ctx = SecondaryFeatureContext({"nodes": nodes, "mention_map": {}, "citations": [], "pair_cluster_ledger": []}, [c], 4, 2,
                                  tokenize=lambda t: t.split())
    pipeline = set(ctx.named_in["z"])
    assert pipeline == {"h", "p", "q"}, "ca phải khiến pipeline nhận đủ ba tên khác dạng"
    ket = cua_so_dinh_nghia([nodes[0]], nodes, [c.to_dict()], truoc=4, sau=2)
    assert set(ket["z"]) == pipeline
