"""DG-14: oracle A8 (canonical dựng từ kho chốt G3), kiểm lược đồ, chạy qua biến thể `oracle-a8` của lệnh `luot` với pipeline giả.

G3 và chunk dựng tay (đầu ra tính tay). Không mô hình thật, không mạng, không ghi vào kho chung.
"""
import copy
import hashlib
import json
from pathlib import Path

import pytest

import luot_ho_tro as lh
import test_luot as tl
from test_luot import chan_mang, chinh, gia, sach  # noqa: F401 — fixture dùng chung với test điều phối lượt
from danhgia.__main__ import main
from danhgia.hop_dong import kiem
from danhgia.luot import ban_ghi
from danhgia.oracle_a8 import GhiDeCanonical, MAY_TU_VANG, dung_canonical, ghi_canonical, kiem_canonical, tim_chunk
from danhgia.oracle_a8.canonical import THUAT_TOAN

# ---------- dữ liệu dựng tay ----------

CHUNKS = [
    {"chunk_id": "c1", "page": 1, "order_index": 0, "role": "noi_dung",
     "text": "Tổng thể là tập hợp các phần tử. Mẫu là một phần của tổng thể được chọn ra."},
    {"chunk_id": "c2", "page": 2, "order_index": 1, "role": "noi_dung",
     "text": "Phương sai đo độ phân tán của mẫu quanh trung bình mẫu. Phương sai luôn không âm."},
    {"chunk_id": "c3", "page": 2, "order_index": 2, "role": "bai_tap", "text": "Bài 1. Mẫu là một phần của tổng thể được chọn ra."},
    {"chunk_id": "c4", "page": 3, "order_index": 3, "role": "noi_dung", "text": "Độ lệch chuẩn là căn bậc hai của phương sai."},
    {"chunk_id": "c5", "page": 9, "order_index": 4, "role": "noi_dung", "text": "Kiểm định giả thiết dùng thống kê kiểm định."},
]


def kn(ma, ten, trang_thai, trang, cau, ten_khac=()):
    return {"ma": ma, "chuong": "c1", "ten": ten, "ten_khac": list(ten_khac), "trang_thai": trang_thai,
            "dinh_nghia": {"trang": trang, "cau": cau}, "khong_chac": False, "ghi_chu": ""}


G3 = {"schema": "danh-gia-g3-1", "ma_sach": "S", "nguoi_gan": "hoi-y", "phien_ban_huong_dan": "g3-1", "chuong": ["c1"], "tranh_chap": [],
      "loai": [],
      "khai_niem": [
          kn("G-S-001", "Tổng thể", "day_o_day", 1, "Tổng thể là tập hợp các phần tử.", ["quần thể"]),
          # câu có ở c1 (trang 1) và c3 (trang 2): vàng ghi trang 2 nên phải gắn vào c3 dù c1 có thứ tự nhỏ hơn và là nội dung
          kn("G-S-002", "Mẫu", "day_o_day", 2, "Mẫu là một phần của tổng thể được chọn ra."),
          kn("G-S-003", "Phương sai", "day_qua_vi_du", 2, "Phương sai đo độ phân tán của mẫu quanh trung bình mẫu."),
          # câu nằm ở trang 3 nhưng vàng ghi trang 2: lệch đúng một trang
          kn("G-S-004", "Độ lệch chuẩn", "chi_nhac", 2, "Độ lệch chuẩn là căn bậc hai của phương sai."),
          # câu chỉ có ở trang 9, vàng ghi trang 3: quá xa, không được gắn
          kn("G-S-005", "Kiểm định giả thiết", "day_o_day", 3, "Kiểm định giả thiết dùng thống kê kiểm định."),
          kn("G-S-006", "Số thực", "kien_thuc_nen", None, None),
          kn("G-S-007", "Xác suất", None, 1, None),
      ]}
MAU_MANIFEST = {"source_hash": "h-nguon", "config": {"candidate_version": 3, "candidate_config_hash": "hc", "anchor_chunks_version": 7}}


def dung(g3=G3, chunks=CHUNKS, **kw):
    return dung_canonical(g3, chunks, doc_id="D", mau_manifest=MAU_MANIFEST, g3_sha256="s" * 64, **kw)


def nut_theo_ma(payload):
    return {n["oracle_ma_g3"]: n for n in payload["nodes"]}


# ---------- gắn câu neo vào chunk ----------

def test_cau_gan_vao_chunk_cung_trang_vang_ghi():
    payload, _, bao = dung()
    n = nut_theo_ma(payload)
    assert n["G-S-001"]["anchor"] == {"chunk_id": "c1", "char_start": 0, "sentence": "Tổng thể là tập hợp các phần tử."}
    assert n["G-S-002"]["anchor"]["chunk_id"] == "c3" and n["G-S-002"]["defining_chunk_ids"] == ["c3"]  # trang 2, không phải c1
    assert n["G-S-003"]["anchor"]["chunk_id"] == "c2"
    chunk = {c["chunk_id"]: c for c in CHUNKS}["c1"]
    assert chunk["text"][n["G-S-001"]["anchor"]["char_start"]:][:12] == "Tổng thể là "


def test_chunk_lech_mot_trang_duoc_nhan_va_dem():
    chunk, diem, ly_do = tim_chunk("Độ lệch chuẩn là căn bậc hai của phương sai.", 2, CHUNKS)
    assert chunk["chunk_id"] == "c4" and diem == 1.0 and ly_do == "ok_lech_trang"
    assert dung()[2]["trang_lech"] == 1


def test_chunk_o_trang_xa_khong_duoc_gan():
    chunk, diem, ly_do = tim_chunk("Kiểm định giả thiết dùng thống kê kiểm định.", 3, CHUNKS)
    assert chunk is None and ly_do == "khong_khop"


def test_lech_hai_trang_khong_duoc_gan_nhung_lech_mot_trang_hai_phia_duoc():
    cau = "Độ lệch chuẩn là căn bậc hai của phương sai."  # nằm ở trang 3 (c4)
    assert tim_chunk(cau, 1, CHUNKS)[2] == "khong_khop" and tim_chunk(cau, 5, CHUNKS)[2] == "khong_khop"
    assert tim_chunk(cau, 2, CHUNKS)[2] == "ok_lech_trang" and tim_chunk(cau, 4, CHUNKS)[2] == "ok_lech_trang"
    assert tim_chunk(cau, 3, CHUNKS)[2] == "ok"


def test_cau_co_o_trang_dung_thi_khong_nhay_sang_trang_khac():
    # cùng câu có ở trang 1 (c1) và trang 2 (c3): vàng ghi trang 2 thì luôn c3, vàng ghi trang 1 thì luôn c1
    cau = "Mẫu là một phần của tổng thể được chọn ra."
    assert tim_chunk(cau, 2, CHUNKS)[0]["chunk_id"] == "c3"
    assert tim_chunk(cau, 1, CHUNKS)[0]["chunk_id"] == "c1"


def test_ly_do_khong_tim_duoc_phan_biet():
    assert tim_chunk(None, 1, CHUNKS)[2] == "khong_co_cau" and tim_chunk("  ", 1, CHUNKS)[2] == "khong_co_cau"
    assert tim_chunk("Tổng thể là tập hợp các phần tử.", None, CHUNKS)[2] == "khong_co_trang"
    assert tim_chunk("Câu hoàn toàn khác không có trong sách nào cả.", 1, CHUNKS)[2] == "khong_khop"


# ---------- khái niệm không có chunk: báo, đếm, không bỏ ngầm ----------

def test_khai_niem_khong_co_chunk_van_vao_canonical_va_duoc_dem():
    payload, _, bao = dung()
    assert len(payload["nodes"]) == 7 == len(G3["khai_niem"])  # không rơi node nào
    assert (bao["tong"], bao["co_chunk"], bao["khong_co_chunk"]) == (7, 4, 3)
    assert bao["khong_co_chunk_ma_g3"] == ["G-S-005", "G-S-006", "G-S-007"]
    assert bao["theo_ly_do"] == {"ok": 3, "ok_lech_trang": 1, "khong_khop": 1, "khong_co_cau": 2}
    n = nut_theo_ma(payload)
    for ma in ("G-S-005", "G-S-006", "G-S-007"):
        assert n[ma]["oracle_khong_co_chunk"] is True and n[ma]["anchor"] is None
        assert n[ma]["defining_chunk_ids"] == [] and n[ma]["teaching_chunk_ids"] == [] and n[ma]["evidence"] == []
    assert payload["stats"]["oracle"]["khong_co_chunk"] == 3 and len(payload["source_candidates"]) == 7


def test_bao_cao_ghi_tung_khai_niem_ly_do_va_diem():
    hang = {h["ma_g3"]: h for h in dung()[2]["hang"]}
    assert hang["G-S-005"]["chunk_id"] is None and hang["G-S-005"]["ly_do"] == "khong_khop" and hang["G-S-005"]["diem_khop"] < 0.9
    assert hang["G-S-001"]["chunk_id"] == "c1" and hang["G-S-001"]["diem_khop"] == 1.0


# ---------- trạng thái dạy ----------

def test_trang_thai_may_theo_anh_xa_nguoc():
    n = nut_theo_ma(dung()[0])
    assert {ma: x["teaching_status"] for ma, x in n.items()} == {
        "G-S-001": "taught", "G-S-002": "taught", "G-S-003": "taught", "G-S-004": "mentioned_only", "G-S-005": "taught",
        "G-S-006": "prior_knowledge", "G-S-007": "uncertain"}


def test_chi_nhac_va_kien_thuc_nen_vao_canonical_voi_chunk_nhac_khong_co_neo():
    n = nut_theo_ma(dung()[0])
    nhac = n["G-S-004"]
    assert nhac["anchor"] is None and nhac["teaching_chunk_ids"] == [] and nhac["defining_chunk_ids"] == ["c4"]
    assert nhac["evidence"][0]["chunk_id"] == "c4" and nhac["learnable"] is True and nhac["mentioned_in"] == ["noi_dung"]
    assert n["G-S-006"]["learnable"] is True and n["G-S-006"]["teaching_status"] == "prior_knowledge"


def test_node_taught_co_chunk_day_du_truong_cua_a5():
    x = nut_theo_ma(dung()[0])["G-S-003"]
    assert x["teaching_chunk_ids"] == ["c2"] == x["defining_chunk_ids"] and x["teaching_order_index"] == 1 == x["first_order_index"]
    assert x["anchor_candidate_id"] == x["members"][0] and x["description"].startswith("Phương sai đo")


def test_anh_xa_nguoc_la_nghich_dao_cua_chieu_xuoi():
    xuoi = json.loads((Path(__file__).resolve().parents[2] / "evaluation" / "giao-thuc" / "anh-xa-trang-thai.json").read_text(encoding="utf-8"))
    for vang, may in MAY_TU_VANG.items():
        if vang is None:
            assert may == "uncertain"
        else:
            assert vang in xuoi["may_sang_vang"][may], f"{vang} -> {may} không nằm trong chiều xuôi"
    assert MAY_TU_VANG["chi_nhac"] != "taught" and MAY_TU_VANG["kien_thuc_nen"] != "taught"
    with pytest.raises(ValueError, match="không có trong ánh xạ"):
        dung(copy.deepcopy({**G3, "khai_niem": [kn("G-S-009", "X", "la", 1, None)]}))


# ---------- tên, tên khác, loại ----------

def test_ten_khac_thanh_alias_va_loai_tranh_chap_khong_vao():
    g3 = copy.deepcopy(G3)
    g3["loai"] = [kn("G-S-100", "Bị loại", "chi_nhac", 1, None)]
    g3["tranh_chap"] = [{"chuong": "c1", "muc": kn("G-S-101", "Tranh chấp", "day_o_day", 1, None), "quyet_dinh": {}}]
    payload, _, bao = dung(g3)
    assert bao["tong"] == 7 and "Bị loại" not in {n["name"] for n in payload["nodes"]}
    assert [a["name"] for a in nut_theo_ma(payload)["G-S-001"]["aliases"]] == ["quần thể"]


def test_node_id_on_dinh_va_khong_trung():
    a, b = dung()[0], dung()[0]
    assert [n["node_id"] for n in a["nodes"]] == [n["node_id"] for n in b["nodes"]] and len({n["node_id"] for n in a["nodes"]}) == 7


# ---------- kiểm lược đồ ----------

def test_canonical_oracle_qua_kiem_luoc_do():
    payload, manifest, _ = dung()
    assert kiem_canonical(payload, manifest, {c["chunk_id"] for c in CHUNKS}) == []
    assert manifest["config"]["algorithm_id"] == THUAT_TOAN and manifest["source_hash"] == "h-nguon"
    assert manifest["config"]["candidate_version"] == 3 and manifest["upstream_version"] == 3


@pytest.mark.parametrize("sua,mong", [
    (lambda p, m: p["nodes"][0].__setitem__("teaching_status", "day_o_day"), "ngoài sáu giá trị"),
    (lambda p, m: p["nodes"][0].__setitem__("node_id", p["nodes"][1]["node_id"]), "trùng"),
    (lambda p, m: p["nodes"][0]["anchor"].__setitem__("chunk_id", "c_la"), "anchor không khớp"),
    (lambda p, m: p["nodes"][0].__setitem__("defining_chunk_ids", ["c_la"]), "chunk không có"),
    (lambda p, m: p["nodes"][3].__setitem__("teaching_chunk_ids", ["c4"]), "không được có anchor"),
    (lambda p, m: p["nodes"][0].pop("members"), "thiếu members"),
    (lambda p, m: p["nodes"][0].__setitem__("members", ["cand_la"]), "ứng viên không có"),
    (lambda p, m: p.pop("redirects"), "thiếu redirects"),
    (lambda p, m: p.__setitem__("stage", "partial"), "stage"),
    (lambda p, m: m["config"].pop("algorithm_id"), "algorithm_id"),
    (lambda p, m: m.pop("source_hash"), "source_hash"),
    (lambda p, m: p["nodes"][0]["aliases"].append("chuoi"), "alias"),
])
def test_kiem_luoc_do_bat_loi(sua, mong):
    payload, manifest, _ = dung()
    sua(payload, manifest)
    loi = kiem_canonical(payload, manifest, {c["chunk_id"] for c in CHUNKS})
    assert loi and any(mong in l for l in loi), loi


# ---------- ghi vào kho, không ghi đè canonical của lượt chính ----------

def test_ghi_canonical_phien_ban_1_va_chay_tiep_dung_lai(tmp_path):
    payload, manifest, _ = dung()
    kho = tmp_path / "kho"
    assert ghi_canonical(kho, "D", payload, manifest) == 1
    duong = kho / "canonical" / "D" / "v1"
    truoc = (duong / "canonical.json").read_bytes()
    assert json.loads((duong / "manifest.json").read_text(encoding="utf-8"))["version"] == 1
    assert ghi_canonical(kho, "D", payload, manifest) == 1  # cùng G3: dùng lại
    assert (duong / "canonical.json").read_bytes() == truoc


def test_ghi_canonical_tu_choi_khi_kho_co_canonical_cua_luot_chinh(tmp_path):
    payload, manifest, _ = dung()
    kho = tmp_path / "kho"
    cu = kho / "canonical" / "D" / "v9"
    cu.mkdir(parents=True)
    (cu / "canonical.json").write_text('{"cua": "luot-chinh"}', encoding="utf-8")
    (cu / "manifest.json").write_text(json.dumps({"config": {"algorithm_id": "a4-names-v3"}}), encoding="utf-8")
    with pytest.raises(GhiDeCanonical):
        ghi_canonical(kho, "D", payload, manifest)
    assert (cu / "canonical.json").read_text(encoding="utf-8") == '{"cua": "luot-chinh"}' and not (kho / "canonical" / "D" / "v1").exists()


def test_ghi_canonical_tu_choi_oracle_cua_g3_khac(tmp_path):
    payload, manifest, _ = dung()
    kho = tmp_path / "kho"
    ghi_canonical(kho, "D", payload, manifest)
    payload2, manifest2, _ = dung_canonical(G3, CHUNKS, doc_id="D", mau_manifest=MAU_MANIFEST, g3_sha256="k" * 64)
    with pytest.raises(GhiDeCanonical):
        ghi_canonical(kho, "D", payload2, manifest2)


# ---------- stage thật của pipeline nhận canonical oracle ----------

def test_build_clusters_that_nhan_canonical_oracle_tren_fixture(tmp_path):
    import shutil
    from doc2roadmap.application.use_cases.build_clusters import BuildClusters
    from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore

    kho = tmp_path / "kho"
    shutil.copytree(lh.KHO_MAU / "chunks", kho / "chunks")
    chunks = json.loads((kho / "chunks" / lh.DOC / "v1" / "chunks.json").read_text(encoding="utf-8"))
    g3 = copy.deepcopy(G3)
    g3["khai_niem"] = [kn(f"G-F-{i:03d}", f"Khái niệm {i}", ["day_o_day", "chi_nhac", "kien_thuc_nen"][i % 3], c["page"], c["text"][:70])
                       for i, c in enumerate(chunks[:6])]
    payload, manifest, bao = dung_canonical(g3, chunks, doc_id=lh.DOC, g3_sha256="f" * 64,
                                            mau_manifest=json.loads((lh.KHO_MAU / "canonical" / lh.DOC / "v1" / "manifest.json").read_text(encoding="utf-8")))
    assert bao["co_chunk"] == 6 and kiem_canonical(payload, manifest, {c["chunk_id"] for c in chunks}) == []
    ghi_canonical(kho, lh.DOC, payload, manifest)

    class GiaEmbedding:
        identifier, embedding_model_id, transport = "gia", "gia", "gia"

        def embed(self, requests):
            return [[(hashlib.sha256((r.text + str(i)).encode()).digest()[i] - 128) / 128 for i in range(8)] for r in requests]

    store = JsonArtifactStore(kho)
    ket = BuildClusters(store, GiaEmbedding()).plan(lh.DOC)
    assert ket.remaining_items == 6
    artifact, _ = BuildClusters(store, GiaEmbedding()).execute(lh.DOC)
    ten = {n["name"]: n["teaching_status"] for n in artifact.payload["nodes"]}
    assert artifact.payload["stage"] == "clusters" and len(ten) == 6
    assert sorted(ten.values()) == ["mentioned_only", "mentioned_only", "prior_knowledge", "prior_knowledge", "taught", "taught"]


# ---------- biến thể oracle-a8 của lệnh luot (pipeline giả) ----------

CHUNKS_FIXTURE = json.loads((lh.KHO_MAU / "chunks" / lh.DOC / "v1" / "chunks.json").read_text(encoding="utf-8"))
G6 = json.loads((lh.KHO_MAU / "graph" / lh.DOC / "v6" / "graph.json").read_text(encoding="utf-8"))


def g3_tu_fixture():
    nut = [n for n in G6["nodes"] if n.get("anchor")]
    chunk = {c["chunk_id"]: c for c in CHUNKS_FIXTURE}
    ds = [kn(f"G-X-{i:03d}", f"Khái niệm vàng {i}", "day_o_day", chunk[n["anchor"]["chunk_id"]]["page"], n["anchor"]["sentence"])
          for i, n in enumerate(nut[:3], 1)]
    mot = CHUNKS_FIXTURE[-1]
    ds.append(kn("G-X-004", "Chỉ nhắc", "chi_nhac", mot["page"], mot["text"][:60]))
    ds.append(kn("G-X-005", "Kiến thức nền", "kien_thuc_nen", None, None))
    ds.append(kn("G-X-006", "Không có trong sách", "day_o_day", mot["page"], "Câu này hoàn toàn không xuất hiện ở bất kỳ chunk nào của sách."))
    return {**G3, "ma_sach": "dev-xstk", "khai_niem": ds}


def chay_oracle(sach, gia, chinh, ra, *them, co_chi=True):
    g3 = ra.parent / "g3-chot.json"
    g3.write_text(json.dumps(g3_tu_fixture()), encoding="utf-8")
    return main(tl.lenh(sach, ra, "oracle-a8", "--tu-luot", str(chinh), "--g3", str(g3), *them, co_chi=co_chi)), g3


def test_oracle_a8_chay_tron_thay_canonical_va_xuat_hop_dong(sach, gia, chinh, tmp_path):
    ra = tmp_path / "oracle"
    truoc = tl.bam(chinh)
    ma, g3 = chay_oracle(sach, gia, chinh, ra)
    assert ma == 0 and tl.bam(chinh) == truoc  # lượt chính không đổi một byte
    ban = ban_ghi.doc(ra)
    assert ban_ghi.da_xong(ban) and [b["ten"] for b in ban["buoc"]] == ["chep-thuong-nguon", "dung-oracle", "roadmap", "pha-b-rieng", "xuat"]
    # roadmap thấy đúng một canonical, là oracle, không có canonical của lượt chính
    assert gia.canonical_luc_roadmap[-1] == [THUAT_TOAN]
    ket = ban["ket_qua"]["oracle_a8"]
    assert (ket["so_khai_niem"], ket["co_chunk"], ket["khong_co_chunk"]) == (6, 4, 2)
    assert ket["khong_co_chunk_ma_g3"] == ["G-X-005", "G-X-006"] and ket["g3_sha256"] == hashlib.sha256(g3.read_bytes()).hexdigest()
    assert ket["theo_trang_thai"] == {"taught": 4, "mentioned_only": 1, "prior_knowledge": 1}
    hd = json.loads((ra / "hop-dong.json").read_text(encoding="utf-8"))
    assert kiem(hd) == [] and hd["dinh_danh"]["he"] == "oracle_a8" and hd["dinh_danh"]["bien_the"] == "oracle-a8-g3"
    assert (ra / "oracle-a8-bao-cao.json").exists()
    assert ban["cau_hinh"]["vang"]["g3"] == hashlib.sha256(g3.read_bytes()).hexdigest()


def test_oracle_a8_chep_thuong_nguon_toi_a3_khong_canonical_khong_graph(sach, gia, chinh, tmp_path):
    ra = tmp_path / "oracle"
    assert chay_oracle(sach, gia, chinh, ra, co_chi=False)[0] == 0  # dừng ở dry-run trước roadmap
    kho = ra / "kho"
    assert (kho / "chunks").is_dir() and (kho / "candidates").is_dir()
    assert not list((kho / "graph").rglob("*")) if (kho / "graph").exists() else True
    ca = sorted(p.name for p in (kho / "canonical" / lh.DOC).iterdir())
    assert ca == ["v1"] and json.loads((kho / "canonical" / lh.DOC / "v1" / "manifest.json").read_text(encoding="utf-8"))["config"]["algorithm_id"] == THUAT_TOAN
    assert sum(gia.goi_mo_hinh[t] for t in ("roadmap",)) == 1  # chỉ lần roadmap của lượt chính, oracle chưa gọi


def test_oracle_a8_thieu_allow_spend_khong_goi_roadmap(sach, gia, chinh, tmp_path):
    so = gia.goi_mo_hinh["roadmap"]
    ra = tmp_path / "oracle"
    assert chay_oracle(sach, gia, chinh, ra, co_chi=False)[0] == 0
    assert gia.goi_mo_hinh["roadmap"] == so and (ra / "dry-run.json").exists()
    assert not (ra / "hop-dong.json").exists()


def test_oracle_a8_can_g3_va_luot_chinh_da_xong(sach, gia, chinh, tmp_path, capsys):
    assert main(tl.lenh(sach, tmp_path / "x", "oracle-a8", "--tu-luot", str(chinh))) == 2
    assert "--g3" in capsys.readouterr().err


def test_oracle_a8_khong_ghi_de_canonical_luot_chinh_khi_kho_lan_co_canonical(sach, gia, chinh, tmp_path):
    """Kho lượt oracle lỡ có canonical của lượt chính (chép nhầm): bước dựng oracle phải dừng, không ghi đè và không đứng sau nó."""
    ra = tmp_path / "oracle"
    (ra / "kho" / "canonical" / lh.DOC / "v1").mkdir(parents=True)
    # kho không rỗng và chưa có bản ghi => lượt từ chối ngay từ cổng cache của lượt khác
    assert chay_oracle(sach, gia, chinh, ra)[0] == 2
    assert not (ra / "kho" / "canonical" / lh.DOC / "v1" / "canonical.json").exists()


def test_oracle_a8_hash_cau_hinh_gom_g3(sach, gia, chinh, tmp_path):
    ra = tmp_path / "oracle"
    gia.hong_o = "roadmap"
    assert chay_oracle(sach, gia, chinh, ra)[0] == 1
    g3 = ra.parent / "g3-chot.json"
    d = json.loads(g3.read_text(encoding="utf-8"))
    d["khai_niem"][0]["dinh_nghia"]["trang"] += 1
    g3.write_text(json.dumps(d), encoding="utf-8")
    assert main(tl.lenh(sach, ra, "oracle-a8", "--tu-luot", str(chinh), "--g3", str(g3))) == 2  # đổi vàng giữa chừng bị từ chối


# ---------- câu vàng có công thức, chunk giữ chỗ [formula] (bộ khớp mảnh của DG-10) ----------

CHUNKS_CT = [
    {"chunk_id": "k1", "page": 4, "order_index": 0, "role": "noi_dung",
     "text": "Với độ tin cậy cho trước, ta tìm được số t từ công thức:\n[formula]\nKhi đó ta tính được độ chính xác ε của ước lượng p theo công thức:\n[formula]\n"
             "Khoảng ước lượng của p có dạng:\n[formula]\n"},
    {"chunk_id": "k2", "page": 4, "order_index": 1, "role": "noi_dung",
     "text": "Ví dụ 1. Điều tra về tỉ lệ phế phẩm của một kho hàng. Khi đó ta tính được độ chính xác của ước lượng theo cách khác."},
    {"chunk_id": "k3", "page": 4, "order_index": 2, "role": "noi_dung", "text": "Đoạn kết thúc ở cuối trang, câu định nghĩa vắt sang chunk"},
    {"chunk_id": "k4", "page": 5, "order_index": 3, "role": "noi_dung", "text": "kế tiếp ở đầu trang sau và kết thúc tại đây."},
]
CAU_CT = "Khi đó ta tính được độ chính xác ε của ước lượng p theo công thức: ε = t_α √(f(1-f)/n)"


def test_che_cong_thuc_tinh_tay():
    from danhgia.oracle_a8.canonical import che_cong_thuc
    assert che_cong_thuc(CAU_CT) == "Khi đó ta tính được độ chính xác [formula] của ước lượng [formula] theo công thức: [formula]"
    assert che_cong_thuc("Mẫu là một phần của tổng thể") == "Mẫu là một phần của tổng thể"  # câu chữ không đổi
    assert che_cong_thuc("N = [ t_α² f(1-f) / ε² ] + 1") == "[formula] 1"  # số đứng riêng là chữ thường, giữ lại


def test_cau_vang_co_cong_thuc_gan_dung_chunk_co_cho_giu_cho():
    from danhgia.phieu.kiem import do_khop_cau
    chunk, diem, ly_do = tim_chunk(CAU_CT, 4, CHUNKS_CT)
    assert chunk["chunk_id"] == "k1" and diem >= 0.9 and ly_do == "ok"  # k2 cũng có đoạn "Khi đó ta tính được độ chính xác" nhưng ngắn hơn nhiều
    # đối chứng độc lập: bộ khớp thường (không tách công thức) không đạt ngưỡng trên đúng chunk này
    assert do_khop_cau(CAU_CT, CHUNKS_CT[0]["text"]) < 0.9


def test_cau_vang_co_cong_thuc_vao_canonical_co_anchor_va_dem_la_co_chunk():
    g3 = {**G3, "khai_niem": [kn("G-S-001", "Độ chính xác", "day_o_day", 4, CAU_CT)]}
    payload, _, bao = dung_canonical(g3, CHUNKS_CT, doc_id="D", mau_manifest=MAU_MANIFEST, g3_sha256="s" * 64)
    nut = payload["nodes"][0]
    assert (bao["co_chunk"], bao["khong_co_chunk"]) == (1, 0) and nut["anchor"]["chunk_id"] == "k1"
    assert CHUNKS_CT[0]["text"][nut["anchor"]["char_start"]:].startswith("Khi đó ta tính được độ chính xác")
    assert kiem_canonical(payload, dung_canonical(g3, CHUNKS_CT, doc_id="D", mau_manifest=MAU_MANIFEST, g3_sha256="s" * 64)[1],
                          {c["chunk_id"] for c in CHUNKS_CT}) == []


def test_cau_toan_ky_hieu_khong_co_phan_chu_thi_khong_co_cau():
    assert tim_chunk("ε = t_α √(f(1-f)/n)", 4, CHUNKS_CT)[2] == "khong_co_cau"


def test_cau_vat_hai_chunk_ke_ca_hai_trang_gan_vao_chunk_dau():
    cau = "Đoạn kết thúc ở cuối trang, câu định nghĩa vắt sang chunk kế tiếp ở đầu trang sau và kết thúc tại đây."
    chunk, diem, ly_do = tim_chunk(cau, 4, CHUNKS_CT)
    assert chunk["chunk_id"] == "k3" and ly_do == "ok_vat_chunk" and diem >= 0.9


def test_cau_chu_co_nghia_khac_voi_cong_thuc_van_khong_khop():
    # cùng khung "Khi đó ... công thức:" nhưng phần chữ khác hẳn: không được gắn vào k1 chỉ vì có chỗ công thức
    cau = "Bây giờ ta xét hoàn toàn khác một bài toán kiểm định giả thiết: H0 : μ = μ0 , H1 : μ ≠ μ0"
    assert tim_chunk(cau, 4, CHUNKS_CT)[0] is None
