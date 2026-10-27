"""DG-11: bộ phát lại A9 -> A10, các biến thể, oracle A10, B1/B2/B3/B4 qua CLI, trên fixture `kho-phat-lai` (xstk-ch3-1 v68 cắt 17 node).

Fixture tự nhất quán: A10 v5 do mã pipeline hiện tại sinh ra từ chuỗi cắt, v6 mô phỏng bước đặt tên module (như v68 trên v63).
Số tính tay lấy từ chính tệp fixture (đếm cạnh trong `v2/graph.json`), không từ đầu ra của bộ phát lại.
Kiểm trên graph thật (xstk v68, doc-4 v27) chạy khi đặt `DANHGIA_KHO_CHUNG=<đường dẫn artifacts chung>`, vì doc-4 nặng; kho chỉ được đọc.
"""
import json
import os
import shutil
import socket
from pathlib import Path

import pytest

import dung_tay as dt
from danhgia.__main__ import main
from danhgia.hop_dong import kiem
from danhgia.phat_lai import canh_oracle, hop_dong, kiem_tai_tao, phat_lai
from danhgia.phat_lai.kho import MoHinhDaGhi
from danhgia.xuat import xuat

KHO = Path(__file__).resolve().parent / "fixtures" / "kho-phat-lai"
DOC, PB = "xstk-ch3-1", 6
DINH_DANH = {"he": "chinh", "bien_the": "mac_dinh", "luot_nhieu": 0, "commit": "a" * 40, "ngay_chay": "2026-10-28",
             "transport": "vertex", "sha256_pdf": None, "so_trang": None}


def _doc(duong):
    return json.loads(Path(duong).read_text(encoding="utf-8"))


EDGES = _doc(KHO / "graph" / DOC / "v2" / "graph.json")
SO_CHINH, SO_PHU = len(EDGES["main_edges"]), len(EDGES["secondary_edges"])


@pytest.fixture
def chan_mang(monkeypatch):
    """Mọi đường ra mạng đều là lỗi: urlopen của adapter Gemini, socket, và khách mô hình thật của B5."""
    import doc2roadmap.infrastructure.llm.gemini as gm

    def cam(*a, **k):
        raise AssertionError("đã gọi mạng")

    monkeypatch.setattr(gm, "urlopen", cam)
    monkeypatch.setattr(socket, "socket", cam)
    monkeypatch.setattr(socket, "create_connection", cam)


def cung_hoac_mem(payload):
    cung = [e for e in payload["requires_edges"] if not e.get("soft")]
    mem = [e for e in payload["requires_edges"] if e.get("soft")]
    return cung, mem


def cap(canh):
    return {(e["source"], e["target"]) for e in canh}


@pytest.fixture(scope="module")
def goc():
    return phat_lai(KHO, DOC, PB)


# ---------- kiểm tái tạo ----------

def test_fixture_dung_nhu_da_mo_ta():
    assert (SO_CHINH, SO_PHU) == (18, 10)  # số cạnh pass chính, pass phụ trong tệp edges của fixture


def test_tai_tao_khong_doi_canh_ra_dung_sequence_va_requires_edges(chan_mang):
    ket_qua = kiem_tai_tao(KHO, DOC, PB)
    assert ket_qua["tai_tao_dung"] is True and ket_qua["a10_goc"] == 5
    assert ket_qua["sequence_so_phan_tu"] == [17, 17] and ket_qua["requires_edges_so_phan_tu"] == [28, 28]


def test_tai_tao_phat_hien_khi_doi_canh(tmp_path):
    kho = tmp_path / "kho"
    shutil.copytree(KHO, kho)
    duong = kho / "graph" / DOC / "v2" / "graph.json"
    du_lieu = _doc(duong)
    du_lieu["main_edges"] = du_lieu["main_edges"][1:]  # bỏ một cạnh trong đầu vào; artifact A10 đã lưu giữ nguyên
    duong.write_text(json.dumps(du_lieu, ensure_ascii=False), encoding="utf-8")
    ket_qua = kiem_tai_tao(kho, DOC, PB)
    assert ket_qua["tai_tao_dung"] is False and ket_qua["requires_edges_dung"] is False


def test_tim_chuoi_di_qua_ca_lop_dat_ten_module(goc):
    c = goc.chuoi
    assert (c.da_luu.version, c.a10.version, c.nhan.version, c.a9.version, c.canh.version) == (6, 5, 4, 3, 2)


def test_phat_lai_khong_ghi_vao_kho(tmp_path, chan_mang):
    kho = tmp_path / "kho"
    shutil.copytree(KHO, kho)
    truoc = sorted((p.relative_to(kho).as_posix(), p.stat().st_size) for p in kho.rglob("*") if p.is_file())
    phat_lai(kho, DOC, PB, tat_luat_r17=True)
    sau = sorted((p.relative_to(kho).as_posix(), p.stat().st_size) for p in kho.rglob("*") if p.is_file())
    assert truoc == sau


def test_mo_hinh_da_ghi_khong_bao_gio_goi_mang():
    from doc2roadmap.domain.canonical import digest
    dau_vao = {"node_id": "n1", "label": "Hình 1", "anchor_sentence": "Hình 1 minh hoạ."}
    mo_hinh = MoHinhDaGhi("m", [{"input": dau_vao, "output": {"node_id": "n1", "display_name": "Biểu đồ"}}])
    phien = mo_hinh.start_session("p")
    tra = phien.ask_json(json.dumps(dau_vao), response_schema={})
    assert tra.payload == {"node_id": "n1", "display_name": "Biểu đồ"} and digest(dau_vao)
    with pytest.raises(AssertionError, match="chưa ghi"):
        phien.ask_json(json.dumps({**dau_vao, "node_id": "n2"}), response_schema={})


# ---------- tắt R17 ----------

def test_tat_r17_lam_cung_dung_cac_canh_bi_r17_lam_mem(goc, chan_mang):
    cung_bat, mem_bat = cung_hoac_mem(goc.payload)
    r17 = [e for e in mem_bat if e.get("soft_reason") == "ngược thứ tự sách"]
    assert (len(cung_bat), len(mem_bat), len(r17)) == (23, 5, 4)  # tính tay từ fixture: 23 cứng, 4 bị R17, 1 cong_cu
    kq = phat_lai(KHO, DOC, PB, tat_luat_r17=True)
    cung_tat, mem_tat = cung_hoac_mem(kq.payload)
    assert len(cung_tat) == 27 and kq.payload["stats"]["soft_backward_edge_count"] == 0
    assert cap(cung_tat) == cap(cung_bat) | cap(r17)


def test_tat_r17_giu_canh_mem_co_san(goc):
    kq = phat_lai(KHO, DOC, PB, tat_luat_r17=True)
    _, mem = cung_hoac_mem(kq.payload)
    assert [e["soft_reason"] for e in mem] == ["cong_cu"]  # cạnh đã mềm từ trước vẫn mềm, không bị coi là cứng
    assert len(kq.payload["requires_edges"]) == 28


def test_tat_r17_hoan_lai_ham_goc():
    import doc2roadmap.application.use_cases.build_roadmap as br
    truoc = br.soften_backward_edges
    phat_lai(KHO, DOC, PB, tat_luat_r17=True)
    assert br.soften_backward_edges is truoc
    cung, mem = cung_hoac_mem(phat_lai(KHO, DOC, PB).payload)  # lần sau không tắt: R17 lại làm mềm
    assert len(mem) == 5


def test_tat_r17_canh_mem_co_san_khong_vao_tien_quyet_cua_node(goc):
    """Cạnh `cong_cu` mềm từ trước không được thành ràng buộc cứng của hàm dãy học, dù bật hay tắt R17."""
    for kq in (goc, phat_lai(KHO, DOC, PB, tat_luat_r17=True)):
        (cong_cu,) = [e for e in kq.payload["requires_edges"] if e.get("soft_reason") == "cong_cu"]
        nut = {n["node_id"]: n for n in kq.payload["nodes"]}
        assert cong_cu["source"] not in nut[cong_cu["target"]]["prerequisites"]


# ---------- bỏ cạnh pass chính / pass phụ ----------

def test_bo_pass_chinh_chi_con_canh_pass_phu():
    kq = phat_lai(KHO, DOC, PB, bo_pass_chinh=True)
    assert kq.payload["requires_edges"] and len(kq.payload["requires_edges"]) == SO_PHU
    assert {e["session_id"].split("_")[0] for e in kq.payload["requires_edges"]} == {"secondary"}


def test_bo_pass_phu_chi_con_canh_pass_chinh():
    kq = phat_lai(KHO, DOC, PB, bo_pass_phu=True)
    assert kq.payload["requires_edges"] and len(kq.payload["requires_edges"]) == SO_CHINH
    assert {e["session_id"].split("_")[0] for e in kq.payload["requires_edges"]} == {"main"}
    assert cap(kq.payload["requires_edges"]) <= cap(EDGES["main_edges"])


def test_bo_pass_phu_khong_con_canh_pass_phu_trong_hop_dong():
    kq = phat_lai(KHO, DOC, PB, bo_pass_phu=True)
    hd = hop_dong(kq, KHO, DOC, PB, dinh_danh=DINH_DANH, he="bo_pass_phu", tham_so={})
    assert kiem(hd) == [] and hd["canh"] and {c["nguon_goc"] for c in hd["canh"]} == {"pass_chinh"}


def test_bo_pass_chinh_hop_dong_chi_con_pass_phu():
    kq = phat_lai(KHO, DOC, PB, bo_pass_chinh=True)
    hd = hop_dong(kq, KHO, DOC, PB, dinh_danh=DINH_DANH, he="bo_pass_chinh", tham_so={})
    assert {c["nguon_goc"] for c in hd["canh"]} == {"pass_phu"}


def test_canh_thay_khong_di_cung_bo_pass():
    from danhgia.phat_lai import LoiPhatLai
    with pytest.raises(LoiPhatLai):
        phat_lai(KHO, DOC, PB, canh_thay=[], bo_pass_phu=True)


# ---------- B1: dãy học A10 không cạnh ----------

def test_b1_khong_canh_day_hoc_theo_vi_tri_day():
    kq = phat_lai(KHO, DOC, PB, canh_thay=[])
    assert kq.payload["requires_edges"] == [] and len(kq.payload["sequence"]) == 17
    chunks = {c["chunk_id"]: c["order_index"] for c in _doc(KHO / "chunks" / DOC / "v1" / "chunks.json")}
    nut = {n["node_id"]: n for n in kq.payload["nodes"]}
    thu_tu = [min(chunks[c] for c in nut[ma]["teaching_chunk_ids"]) for ma in kq.payload["sequence"]]
    assert thu_tu == sorted(thu_tu)  # độc lập với A10: thứ tự chunk dạy không giảm
    assert thu_tu != [thu_tu[0]] * 17  # chặn kiểm vô nghĩa: các node nằm ở nhiều chunk khác nhau


# ---------- oracle A10 ----------

def hd_oracle(ma_node):
    return dt.hop_dong([dt.khai_niem(m) for m in ma_node], [], list(ma_node))


def vang_oracle(node):
    """Vàng nhỏ: G1..G5; G1-3 căn `khop` vào node[0..2], G4 căn `may_rong_hon`, G5 không căn. Cạnh vàng: G1>G2, G2>G3, G3>G4, G5>G1."""
    ma = "S"
    g3 = dt.g3(ma, [(f"G{i}", "c1") for i in range(1, 6)])
    g4 = dt.g4(ma, [("G1", "G2"), ("G2", "G3"), ("G3", "G4"), ("G5", "G1")])
    can = dt.can(ma, [("G1", node[0], "khop"), ("G2", node[1], "khop"), ("G3", node[2], "khop"),
                      ("G4", node[3], "may_rong_hon")])
    return g3, g4, can


def test_oracle_chi_dat_canh_vang_da_can_muc_nghiem(goc):
    node = goc.payload["sequence"][:4]
    g3, g4, can = vang_oracle(node)
    canh, thong_ke = canh_oracle(hd_oracle(node), g3, g4, can, set(node))
    assert cap(canh) == {(node[0], node[1]), (node[1], node[2])}
    assert thong_ke["canh_vang"] == 4 and thong_ke["canh_chua_can"] == 2 and thong_ke["canh_dat_vao_a10"] == 2


def test_oracle_khong_dung_id_vang_chua_can(goc):
    node = goc.payload["sequence"][:4]
    g3, g4, can = vang_oracle(node)
    canh, _ = canh_oracle(hd_oracle(node), g3, g4, can, set(node))
    ma_dung = {e["source"] for e in canh} | {e["target"] for e in canh}
    assert ma_dung <= set(node) and not any(m.startswith("G") for m in ma_dung)


def test_oracle_bo_cap_ngoai_node_a10(goc):
    node = goc.payload["sequence"][:4]
    g3, g4, can = vang_oracle(node)
    canh, thong_ke = canh_oracle(hd_oracle(node), g3, g4, can, {node[0], node[1]})  # A10 không biết node[2]
    assert cap(canh) == {(node[0], node[1])} and thong_ke["cap_node_la"] == 1


def test_oracle_chay_thang_vao_a10_tren_node_cua_he_chinh(goc, chan_mang):
    seq = goc.payload["sequence"]
    node = [seq[2], seq[6], seq[9], seq[12]]  # thuận thứ tự sách: không bị R17 làm mềm
    g3, g4, can = vang_oracle(node)
    canh, _ = canh_oracle(hd_oracle(node), g3, g4, can, set(seq))
    kq = phat_lai(KHO, DOC, PB, canh_thay=canh)
    cung, mem = cung_hoac_mem(kq.payload)
    assert cap(cung) == {(node[0], node[1]), (node[1], node[2])} and mem == []
    assert set(kq.payload["sequence"]) == set(seq)  # cùng node với hệ chính
    pos = {m: i for i, m in enumerate(kq.payload["sequence"])}
    assert pos[node[0]] < pos[node[1]] < pos[node[2]]


def test_oracle_canh_nguoc_thu_tu_sach_van_qua_r17():
    goc = phat_lai(KHO, DOC, PB)
    seq = goc.payload["sequence"]
    node = [seq[9], seq[2], seq[6], seq[12]]  # G1 dạy sau G2: cạnh G1 > G2 ngược thứ tự sách
    g3, g4, can = vang_oracle(node)
    canh, _ = canh_oracle(hd_oracle(node), g3, g4, can, set(seq))
    kq = phat_lai(KHO, DOC, PB, canh_thay=canh)
    _, mem = cung_hoac_mem(kq.payload)
    assert [(e["source"], e["target"]) for e in mem] == [(node[0], node[1])]


def test_hop_dong_oracle_hop_le_nguon_goc_baseline(goc):
    seq = goc.payload["sequence"]
    node = [seq[2], seq[6], seq[9], seq[12]]
    g3, g4, can = vang_oracle(node)
    canh, _ = canh_oracle(hd_oracle(node), g3, g4, can, set(seq))
    kq = phat_lai(KHO, DOC, PB, canh_thay=canh)
    hd = hop_dong(kq, KHO, DOC, PB, dinh_danh=DINH_DANH, he="oracle_a10", tham_so={}, nguon_goc_canh="baseline")
    assert kiem(hd) == [] and hd["dinh_danh"]["he"] == "oracle_a10"
    assert {c["nguon_goc"] for c in hd["canh"]} == {"baseline"} and len(hd["canh"]) == 2
    assert hd["chi_phi"]["tong"]["usd"] == 0.0 and hd["chi_phi"]["tong"]["so_loi_goi_mo_hinh"] == 0


# ---------- CLI ----------

@pytest.fixture(scope="module")
def hd_chinh(tmp_path_factory):
    duong = tmp_path_factory.mktemp("chinh") / "chinh.json"
    duong.write_text(json.dumps(xuat(KHO, DOC, PB, dinh_danh=DINH_DANH), ensure_ascii=False), encoding="utf-8")
    return duong


def test_cli_phat_lai_khong_doi_ma_thoat_0_va_1(tmp_path, capsys, chan_mang):
    assert main(["phat-lai", "--kho", str(KHO), "--doc", DOC, "--phien-ban", str(PB), "--bien-the", "khong-doi"]) == 0
    assert json.loads(capsys.readouterr().out)["tai_tao_dung"] is True
    kho = tmp_path / "kho"
    shutil.copytree(KHO, kho)
    duong = kho / "graph" / DOC / "v2" / "graph.json"
    du_lieu = _doc(duong)
    du_lieu["secondary_edges"] = du_lieu["secondary_edges"][1:]
    duong.write_text(json.dumps(du_lieu, ensure_ascii=False), encoding="utf-8")
    assert main(["phat-lai", "--kho", str(kho), "--doc", DOC, "--phien-ban", str(PB), "--bien-the", "khong-doi"]) == 1


@pytest.mark.parametrize("bien_the,he", [("tat-r17", "tat_r17"), ("bo-pass-chinh", "bo_pass_chinh"),
                                          ("bo-pass-phu", "bo_pass_phu")])
def test_cli_phat_lai_ra_hop_dong_hop_le(bien_the, he, tmp_path, hd_chinh, chan_mang):
    ra = tmp_path / "ra.json"
    assert main(["phat-lai", "--kho", str(KHO), "--doc", DOC, "--phien-ban", str(PB), "--bien-the", bien_the,
                 "--hop-dong", str(hd_chinh), "--ra", str(ra)]) == 0
    hd = _doc(ra)
    assert kiem(hd) == [] and hd["dinh_danh"]["he"] == he and hd["dinh_danh"]["doc_id"] == DOC


def test_cli_oracle_a10(tmp_path, hd_chinh, chan_mang):
    chinh = _doc(hd_chinh)
    seq = chinh["lo_trinh"]["day_hoc"]
    node = [seq[2], seq[6], seq[9], seq[12]]
    g3, g4, can = vang_oracle(node)
    for ten, gia_tri in (("g3", g3), ("g4", g4), ("can", can)):
        (tmp_path / f"{ten}.json").write_text(json.dumps(gia_tri), encoding="utf-8")
    ra = tmp_path / "oracle.json"
    assert main(["phat-lai", "--kho", str(KHO), "--doc", DOC, "--phien-ban", str(PB), "--bien-the", "oracle-a10",
                 "--hop-dong", str(hd_chinh), "--g3", str(tmp_path / "g3.json"), "--g4", str(tmp_path / "g4.json"),
                 "--can", str(tmp_path / "can.json"), "--ra", str(ra)]) == 0
    hd = _doc(ra)
    assert kiem(hd) == [] and len(hd["canh"]) == 2 and hd["dinh_danh"]["he"] == "oracle_a10"


def chay_baseline(loai, hd_chinh, tmp_path):
    ra = tmp_path / f"{loai}.json"
    assert main(["baseline", "--loai", loai, "--kho", str(KHO), "--doc", DOC, "--phien-ban", str(PB),
                 "--hop-dong", str(hd_chinh), "--ra", str(ra)]) == 0
    return _doc(ra)


def test_cli_b1_khong_canh_cung_node_voi_he_chinh(tmp_path, hd_chinh, chan_mang):
    hd, chinh = chay_baseline("b1", hd_chinh, tmp_path), _doc(hd_chinh)
    assert kiem(hd) == [] and hd["dinh_danh"]["he"] == "b1" and hd["canh"] == []
    assert {k["ma"] for k in hd["khai_niem"]} == {k["ma"] for k in chinh["khai_niem"]}
    assert set(hd["lo_trinh"]["day_hoc"]) == set(chinh["lo_trinh"]["day_hoc"]) and len(hd["lo_trinh"]["day_hoc"]) == 17


def test_cli_b2_canh_la_ten_trong_cua_so_chunk_cau_neo(tmp_path, hd_chinh, chan_mang):
    hd, chinh = chay_baseline("b2", hd_chinh, tmp_path), _doc(hd_chinh)
    assert kiem(hd) == [] and hd["dinh_danh"]["he"] == "b2"
    assert hd["canh"] and {c["nguon_goc"] for c in hd["canh"]} == {"baseline"}
    chunks = {c["chunk_id"]: c["text"] for c in _doc(KHO / "chunks" / DOC / "v1" / "chunks.json")}
    ten = {k["ma"]: [k["ten"], *k["ten_khac"]] for k in chinh["khai_niem"]}
    neo = {k["ma"]: k["cau_neo"]["ma_chunk"] for k in chinh["khai_niem"] if k["cau_neo"]}
    from danhgia.ten import xuat_hien
    for c in hd["canh"]:  # mỗi cạnh: tên của nguồn xuất hiện (theo âm tiết) trong chunk câu neo của đích
        assert any(xuat_hien(t, chunks[neo[c["dich"]]]) for t in ten[c["nguon"]]), c


def test_cli_b3_moi_tieu_de_cap_1_tro_len_la_mot_khai_niem(tmp_path, hd_chinh, chan_mang):
    hd, chinh = chay_baseline("b3", hd_chinh, tmp_path), _doc(hd_chinh)
    so_tieu_de = sum(1 for t in chinh["cau_truc"]["tieu_de"] if t["cap"] is None or t["cap"] >= 1)
    assert kiem(hd) == [] and hd["dinh_danh"]["he"] == "b3" and len(hd["khai_niem"]) == so_tieu_de > 0
    assert hd["canh"] == []


def test_cli_b4_gop_theo_ten_tren_ung_vien_cua_canonical(tmp_path, hd_chinh, chan_mang):
    hd = chay_baseline("b4", hd_chinh, tmp_path)
    ung_vien = _doc(KHO / "canonical" / DOC / "v1" / "canonical.json")["source_candidates"]
    ten_khac_nhau = {u["name"].strip().casefold() for u in ung_vien if u["learnable"]}  # đếm độc lập với chuan_hoa
    assert kiem(hd) == [] and hd["dinh_danh"]["he"] == "b4" and len(hd["khai_niem"]) == len(ten_khac_nhau)
    assert len(ten_khac_nhau) < sum(1 for u in ung_vien if u["learnable"])  # fixture có ứng viên trùng tên thật
    goc_chung = [m for k in hd["khai_niem"] for m in k["ung_vien_goc"]]
    assert sorted(goc_chung) == sorted(u["candidate_id"] for u in ung_vien if u["learnable"])


# ---------- graph thật (tập phát triển), chỉ đọc kho chung ----------

def kho_chung():
    duong = os.environ.get("DANHGIA_KHO_CHUNG")
    return Path(duong) if duong else None


@pytest.mark.skipif(kho_chung() is None, reason="đặt DANHGIA_KHO_CHUNG=<artifacts của thư mục chung> để kiểm trên graph thật")
@pytest.mark.parametrize("doc,phien_ban,so_dung,so_canh", [("xstk-ch3-1", 68, 82, 156), ("doc-4", 27, 495, 1273)])
def test_tai_tao_tren_graph_thuc_tap_phat_trien(doc, phien_ban, so_dung, so_canh, chan_mang):
    ket_qua = kiem_tai_tao(kho_chung(), doc, phien_ban)
    assert ket_qua["tai_tao_dung"] is True
    assert ket_qua["sequence_so_phan_tu"] == [so_dung, so_dung] and ket_qua["requires_edges_so_phan_tu"] == [so_canh, so_canh]
