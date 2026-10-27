"""DG-08: điều phối lượt chạy, với pipeline giả (đếm lời gọi mô hình), transport và kho chung bị chặn.

Lượt chạy thật có chi do Claude chạy sau khi ghép; ở đây không có lời gọi mạng nào và không có mô hình thật.
"""
import hashlib
import json
import socket
from pathlib import Path

import pytest

import b5_ho_tro as ht
import luot_ho_tro as lh
from danhgia.__main__ import main
from danhgia.hop_dong import kiem
from danhgia.luot import ban_ghi, chay, thu_muc, uoc_chi
from tests.evaluation.ho_tro import tao_pdf

DOC = lh.DOC
G6 = json.loads((lh.KHO_MAU / "graph" / DOC / "v6" / "graph.json").read_text(encoding="utf-8"))
CHUNKS = {c["chunk_id"]: c for c in json.loads((lh.KHO_MAU / "chunks" / DOC / "v1" / "chunks.json").read_text(encoding="utf-8"))}
NODE = list(G6["sequence"])
TRANG_NODE = {n["node_id"]: CHUNKS[n["anchor"]["chunk_id"]]["page"] for n in G6["nodes"] if n.get("anchor")}
TRANG_GIUA = sorted(TRANG_NODE.values())[len(TRANG_NODE) // 2]
SO_CHUNK = len(CHUNKS)


# ---------- chuẩn bị ----------

@pytest.fixture(autouse=True)
def chan_mang(monkeypatch, tmp_path):
    """Mạng, kho chung và pipeline thật đều bị chặn; thư mục làm việc là tmp_path (nên `artifacts/` mặc định là kho chung giả)."""
    import doc2roadmap.infrastructure.llm.gemini as gm

    def cam(*a, **k):
        raise AssertionError("đã gọi mạng")

    monkeypatch.setattr(gm, "urlopen", cam)
    monkeypatch.setattr(socket, "socket", cam)
    monkeypatch.setattr(socket, "create_connection", cam)
    monkeypatch.setattr(chay, "chay_cli_that", cam)  # không có pipeline thật nếu test quên thay bản giả
    monkeypatch.chdir(tmp_path)
    chung = tmp_path / "artifacts"
    chung.mkdir()
    (chung / "da-co.txt").write_text("kho chung", encoding="utf-8")
    lh.canh_kho_chung(chung)
    yield
    lh.canh_kho_chung(None)


@pytest.fixture
def gia(monkeypatch):
    g = lh.GiaPipeline()
    monkeypatch.setattr(chay, "chay_cli_that", g)
    return g


@pytest.fixture
def sach(tmp_path):
    pdf = tao_pdf(tmp_path / "xstk-ch3-1.pdf", [ht.TRANG[n].replace("\n", " ") for n in (1, 2, 3, 4)])
    sau = TRANG_NODE and max(TRANG_NODE.values()) + 5
    m = {"schema": "danh-gia-sach-1", "ma_sach": "dev-xstk", "chu_de": "toan", "tap": "phat_trien", "tep_pdf": "xstk-ch3-1.pdf",
         "pdf_sha256": ht.sha256(pdf), "so_trang": sau, "quyen": "da_xac_nhan",
         "chuong": [{"ma": "c1", "so": "1", "ten": "dau", "trang_dau": 1, "trang_cuoi": TRANG_GIUA, "loai": "noi_dung"},
                    {"ma": "c2", "so": "2", "ten": "sau", "trang_dau": TRANG_GIUA + 1, "trang_cuoi": sau, "loai": "noi_dung"}],
         "boc": {"seed": None, "n_trang_toi_thieu": None, "chuong": ["c1"], "ly_do": "thử"}}
    mf = tmp_path / "manifest.json"
    mf.write_text(json.dumps(m), encoding="utf-8")
    vang = tmp_path / "vang"
    vang.mkdir()
    for ten, gt in zip(("g3", "g4", "can"), lh.vang_tay(NODE[:4])):
        (vang / f"{ten}.json").write_text(json.dumps(gt), encoding="utf-8")
    (tmp_path / "a4-vang.json").write_text("{}", encoding="utf-8")
    return {"pdf": pdf, "manifest": mf, "vang": vang, "a4": tmp_path / "a4-vang.json", "m": m}


def lenh(sach, ra, bien_the, *them, co_vang=False, co_chi=True):
    a = ["luot", "--manifest", str(sach["manifest"]), "--pdf", str(sach["pdf"]), "--bien-the", bien_the, "--ra", str(ra),
         "--commit", "c" * 40, "--ngay", "2026-11-01"]
    if "a4" in sach:
        a += ["--vang-a4", str(sach["a4"])]
    if co_vang:
        a += ["--g3", str(sach["vang"] / "g3.json"), "--g4", str(sach["vang"] / "g4.json"), "--can", str(sach["vang"] / "can.json")]
    if co_chi:
        a.append("--allow-spend")
    return a + list(them)


def doc_json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def bam(thu_muc_goc):
    """Băm nội dung mọi tệp dưới một thư mục (để chứng minh lượt khác không bị đụng)."""
    goc = Path(thu_muc_goc)
    return {p.relative_to(goc).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(goc.rglob("*")) if p.is_file()}


@pytest.fixture
def chinh(sach, gia, tmp_path):
    ra = tmp_path / "luot" / "chinh"
    assert main(lenh(sach, ra, "chinh", co_vang=True)) == 0
    return ra


# ---------- chạy trọn ----------

def test_chinh_chay_tron_tu_pdf_den_hop_dong_va_bang_diem(chinh, gia, tmp_path):
    ban = ban_ghi.doc(chinh)
    assert ban_ghi.da_xong(ban) and [b["ten"] for b in ban["buoc"]] == [
        "ingest", "label-roles", "a3", "a4", "roadmap", "pha-b-rieng", "xuat", "cham"]
    hd = doc_json(chinh / "hop-dong.json")
    assert kiem(hd) == [] and hd["dinh_danh"]["he"] == "chinh" and hd["dinh_danh"]["doc_id"] == DOC
    assert hd["dinh_danh"]["sha256_pdf"] == ban["sha256_pdf"] and hd["dinh_danh"]["transport"] == "vertex"
    bang = doc_json(chinh / "bang-diem.json")
    assert bang["theo_chuong"] and any(r["thuoc"] == "a10.q6.nghiem" for r in bang["theo_cuon"])
    assert {t: gia.goi_mo_hinh[t] for t in ("label-roles", "a3", "a4", "roadmap")} == {"label-roles": 1, "a3": 1, "a4": 1, "roadmap": 1}
    assert (chinh / "so-chi.json").exists()


def test_ban_ghi_du_truong_va_cau_hinh(chinh):
    ban = ban_ghi.doc(chinh)
    assert ban_ghi.kiem(ban) == []
    assert (ban["mo_hinh"], ban["transport"], ban["commit"], ban["ngay"], ban["bien_the"]) == (
        "gemini-3.1-flash-lite", "vertex", "c" * 40, "2026-11-01", "chinh")
    assert len(ban["hash_cau_hinh"]) == 64 and ban["seed"] is None and all(b["trang_thai"] == "xong" for b in ban["buoc"])


def test_moi_lenh_pipeline_dung_kho_rieng_cua_luot(chinh, gia, tmp_path):
    kho = str((chinh / "kho").resolve())
    assert gia.lenh and all(Path(e["DOC2ROADMAP_ARTIFACT_DIR"]).resolve() == Path(kho) for _, e in gia.lenh)
    assert all(e["DOC2ROADMAP_MAIN_CONTEXT_SHUFFLE_SEED"] == "" and e["DOC2ROADMAP_SECONDARY_MODE"] == "ml" for _, e in gia.lenh)
    assert [a[0] for a, _ in gia.lenh] == ["ingest", "label-roles", "a3", "a4", "roadmap"]
    assert "--a1" not in gia.lenh[0][0] and gia.lenh[3][0][gia.lenh[3][0].index("--gold") + 1].endswith("a4-vang.json")
    assert not (tmp_path / "artifacts" / "graph").exists()  # kho chung không bị đụng


def test_kho_pha_b_rieng_duoc_dua_vao_hop_dong(sach, gia, tmp_path):
    gia.so_dong_pha_b = 3
    a = tmp_path / "a"
    assert main(lenh(sach, a, "chinh")) == 0
    gia.so_dong_pha_b = 5
    b = tmp_path / "b"
    assert main(lenh(sach, b, "chinh")) == 0
    for ra, so in ((a, 3), (b, 5)):
        assert doc_json(ra / "kho-pha-b.json") == doc_json(ra / "kho" / "phase_b" / "live.json")
        hd = doc_json(ra / "hop-dong.json")
        assert hd["chi_phi"]["theo_khau"]["dat_ten_module"]["so_loi_goi_mo_hinh"] == so


def test_so_chi_lay_tu_usage_cua_kho_luot(chinh):
    so = doc_json(chinh / "so-chi.json")
    pha_b = next(h for h in so["hang"] if h["nguon"] == "pha-b:dat-ten-module")
    assert pha_b["model_calls"] == 1 and pha_b["input_tokens"] == 400 and pha_b["usd"] == pytest.approx(0.0001)
    assert so["tong"]["usd"] >= 0.0001 and any(h["stage"] == "stages" for h in so["hang"])


# ---------- không có --allow-spend ----------

def test_thieu_allow_spend_chi_dry_run_khong_goi_mo_hinh(sach, gia, tmp_path):
    ra = tmp_path / "luot"
    assert main(lenh(sach, ra, "chinh", co_chi=False)) == 0
    assert sum(gia.goi_mo_hinh.values()) == 0 and [a[0] for a, _ in gia.lenh] == ["ingest"]  # ingest không tốn tiền
    bao = doc_json(ra / "dry-run.json")
    assert bao["buoc_co_chi"] == ["label-roles", "a3", "a4", "roadmap"] and "allow-spend" in bao["ly_do"]
    assert bao["du_toan"]["so_chunk"] == SO_CHUNK and bao["du_toan"]["tong"]["usd"] > 0
    assert not ban_ghi.da_xong(ban_ghi.doc(ra)) and not (ra / "hop-dong.json").exists()


def test_dry_run_chan_ca_khi_co_allow_spend(sach, gia, tmp_path):
    assert main(lenh(sach, tmp_path / "luot", "chinh", "--dry-run")) == 0
    assert sum(gia.goi_mo_hinh.values()) == 0


# ---------- chạy tiếp ----------

def test_chay_tiep_sau_ngat_khong_goi_lai_buoc_da_xong(sach, gia, tmp_path):
    ra = tmp_path / "luot"
    gia.hong_o = "a4"
    assert main(lenh(sach, ra, "chinh")) == 1
    ban = ban_ghi.doc(ra)
    assert [b["trang_thai"] for b in ban["buoc"]][:5] == ["xong", "xong", "xong", "loi", "cho"]
    truoc = bam(ra / "kho")
    assert main(lenh(sach, ra, "chinh")) == 0
    # a4 được gọi hai lần (lần ngắt và lần chạy tiếp); mọi bước đã xong chỉ một lần
    assert dict(gia.goi_mo_hinh) == {"label-roles": 1, "a3": 1, "a4": 2, "roadmap": 1}
    assert [a[0] for a, _ in gia.lenh].count("ingest") == 1
    sau = bam(ra / "kho")
    assert all(sau[t] == h for t, h in truoc.items())  # không xoá, không sinh lại bản đã xong
    assert ban_ghi.da_xong(ban_ghi.doc(ra))


def test_chay_lai_lượt_da_xong_khong_lam_gi(chinh, gia, sach):
    so_lenh = len(gia.lenh)
    assert main(lenh(sach, chinh, "chinh", co_vang=True)) == 0
    assert len(gia.lenh) == so_lenh


def test_chay_tiep_voi_hash_cau_hinh_khac_bi_tu_choi(sach, gia, tmp_path, capsys):
    ra = tmp_path / "luot"
    gia.hong_o = "a4"
    assert main(lenh(sach, ra, "chinh")) == 1
    truoc, so_lenh = bam(ra), len(gia.lenh)
    a = lenh(sach, ra, "chinh")
    a[a.index("--commit") + 1] = "d" * 40
    assert main(a) == 2
    assert "hash cấu hình" in capsys.readouterr().err
    assert bam(ra) == truoc and len(gia.lenh) == so_lenh  # không gọi gì, không sửa gì


def test_chay_tiep_doi_bien_the_bi_tu_choi(sach, gia, tmp_path):
    ra = tmp_path / "luot"
    gia.hong_o = "a4"
    assert main(lenh(sach, ra, "chinh")) == 1
    assert main(lenh(sach, ra, "docling")) == 2


# ---------- bản ghi thiếu trường ----------

@pytest.mark.parametrize("truong", sorted(ban_ghi.TRUONG))
def test_thieu_truong_thi_luot_khong_xong(truong, chinh, capsys):
    ban = ban_ghi.doc(chinh)
    assert ban_ghi.da_xong(ban)
    del ban[truong]
    assert not ban_ghi.da_xong(ban) and any(truong in l for l in ban_ghi.kiem(ban))
    ban_ghi.ghi(chinh, ban)
    assert main(["luot", "--kiem", str(chinh)]) == 1


def test_con_buoc_chua_xong_thi_luot_khong_xong(chinh):
    ban = ban_ghi.doc(chinh)
    ban["buoc"][2]["trang_thai"] = "loi"
    assert not ban_ghi.da_xong(ban)
    ban["buoc"][2]["trang_thai"] = "xong"
    ban["xong"] = False
    assert not ban_ghi.da_xong(ban)


def test_kiem_luot_xong_thoat_0(chinh, capsys):
    assert main(["luot", "--kiem", str(chinh)]) == 0 and "xong" in capsys.readouterr().out


# ---------- kho chung và cache lượt khác ----------

def test_chot_chan_kho_chung_that_su_do_khi_co_ghi(tmp_path):
    with pytest.raises(AssertionError, match="kho chung"):
        (tmp_path / "artifacts" / "x.txt").write_text("ghi", encoding="utf-8")
    with pytest.raises(AssertionError, match="kho chung"):
        (tmp_path / "artifacts" / "con").mkdir()


def test_lượt_nam_trong_kho_chung_bi_tu_choi(sach, gia, tmp_path, capsys):
    assert main(lenh(sach, tmp_path / "artifacts" / "luot", "chinh")) == 2
    assert "kho chung" in capsys.readouterr().err and sum(gia.goi_mo_hinh.values()) == 0
    assert sorted(p.name for p in (tmp_path / "artifacts").iterdir()) == ["da-co.txt"]


def test_kho_chung_khai_bao_bang_tham_so_cung_bi_chan(sach, gia, tmp_path):
    ngoai = tmp_path / "kho-khac"
    assert main(lenh(sach, ngoai / "luot", "chinh", "--kho-chung", str(ngoai))) == 2


def test_luot_moi_ma_kho_da_co_noi_dung_bi_tu_choi(sach, gia, tmp_path, capsys):
    ra = tmp_path / "luot"
    (ra / "kho" / "chunks").mkdir(parents=True)
    (ra / "kho" / "chunks" / "cua-luot-khac.json").write_text("{}", encoding="utf-8")
    assert main(lenh(sach, ra, "chinh")) == 2
    assert "cache của lượt khác" in capsys.readouterr().err and not gia.lenh


def test_hai_luot_chinh_khong_chung_cache(sach, gia, tmp_path):
    assert main(lenh(sach, tmp_path / "a", "chinh")) == 0
    assert main(lenh(sach, tmp_path / "b", "chinh")) == 0
    assert [a[0] for a, _ in gia.lenh].count("ingest") == 2 and gia.goi_mo_hinh["roadmap"] == 2  # lượt b chạy từ đầu


def test_luot_di_qua_lien_ket_bi_tu_choi(sach, gia, tmp_path):
    import os
    if os.name != "nt":
        pytest.skip("junction chỉ có trên Windows")
    import subprocess
    that = tmp_path / "that"
    that.mkdir()
    lk = tmp_path / "lk"
    r = subprocess.run(["cmd", "/c", "mklink", "/J", str(lk), str(that)], capture_output=True)
    if r.returncode != 0:
        pytest.skip("không tạo được junction")
    assert main(lenh(sach, lk / "luot", "chinh")) == 2 and not gia.lenh


# ---------- biến thể dùng lại thượng nguồn ----------

def test_xao_k_chep_thuong_nguon_va_khong_ghi_de_luot_chinh(sach, gia, chinh, tmp_path):
    truoc = bam(chinh)
    ra = tmp_path / "xao"
    assert main(lenh(sach, ra, "xao-k", "--tu-luot", str(chinh), "--k", "3", "--seed", "10")) == 0
    assert bam(chinh) == truoc  # lượt chính không đổi một byte
    lenh_roadmap = [e for a, e in gia.lenh_dau("roadmap")][1:]
    assert [e["DOC2ROADMAP_MAIN_CONTEXT_SHUFFLE_SEED"] for e in lenh_roadmap] == ["10", "11", "12"]
    assert [a[0] for a, _ in gia.lenh].count("a3") == 1 and [a[0] for a, _ in gia.lenh].count("ingest") == 1  # không chạy lại thượng nguồn
    for i in (1, 2, 3):
        con = ra / f"xao-{i}"
        ban = ban_ghi.doc(con)
        assert ban_ghi.da_xong(ban) and ban["seed"] == 9 + i and ban["luot_nhieu"] == i and ban["k"] == 3
        assert Path(lenh_roadmap[i - 1]["DOC2ROADMAP_ARTIFACT_DIR"]).resolve() == (con / "kho").resolve()
        chunk = con / "kho" / "chunks" / DOC / "v1" / "chunks.json"
        assert chunk.is_file() and not thu_muc.la_lien_ket(chunk) and not thu_muc.la_lien_ket(con / "kho")
        assert chunk.read_bytes() == (chinh / "kho" / "chunks" / DOC / "v1" / "chunks.json").read_bytes()
        hd = doc_json(con / "hop-dong.json")
        assert kiem(hd) == [] and hd["dinh_danh"]["he"] == "xao" and hd["dinh_danh"]["bien_the"] == f"xao-seed{9 + i}"


def test_xao_k_chi_chep_den_clusters_mentions(sach, gia, chinh, tmp_path):
    assert main(lenh(sach, tmp_path / "xao", "xao-k", "--tu-luot", str(chinh), "--k", "1")) == 0
    ban = ban_ghi.doc(tmp_path / "xao" / "xao-1")
    assert ban["ket_qua"]["cat_den_graph"] == 1  # fixture: chỉ graph v1 (clusters) thuộc thượng nguồn của pass chính


def test_xao_k_so_chi_khong_cong_lai_phan_chep(sach, gia, chinh, tmp_path):
    assert main(lenh(sach, tmp_path / "xao", "xao-k", "--tu-luot", str(chinh), "--k", "1")) == 0
    so = doc_json(tmp_path / "xao" / "xao-1" / "so-chi.json")
    assert any(h["da_chep_tu_luot_nguon"] for h in so["hang"])
    assert so["tong"]["usd"] == pytest.approx(sum(h["usd"] for h in so["hang"] if not h["da_chep_tu_luot_nguon"]))


def test_pass_phu_llm_dat_che_do_llm_va_loc_dich_theo_chuong_boc(sach, gia, chinh, tmp_path):
    ra = tmp_path / "pp"
    assert main(lenh(sach, ra, "pass-phu-llm", "--tu-luot", str(chinh))) == 0
    env = gia.lenh_dau("roadmap")[-1][1]
    chinh_hd = doc_json(chinh / "hop-dong.json")
    mong = sorted(k["ma"] for k in chinh_hd["khai_niem"] if k["trong_day_hoc"] and k["cau_neo"] and k["cau_neo"]["trang"] <= TRANG_GIUA)
    loc = json.loads(env["DOC2ROADMAP_SECONDARY_TARGET_FILTER"])
    assert env["DOC2ROADMAP_SECONDARY_MODE"] == "llm" and loc == mong and 0 < len(loc) < len(chinh_hd["khai_niem"])
    assert doc_json(ra / "hop-dong.json")["dinh_danh"]["he"] == "pass_phu_llm"


def test_docling_doi_khau_dau_nen_co_kho_rieng(sach, gia, tmp_path):
    ra = tmp_path / "dl"
    assert main(lenh(sach, ra, "docling")) == 0
    ingest = gia.lenh_dau("ingest")[0][0]
    assert ingest[ingest.index("--a1") + 1] == "docling"
    assert ban_ghi.doc(ra)["tu_luot"] is None and doc_json(ra / "hop-dong.json")["dinh_danh"]["he"] == "docling"


def test_bien_the_dung_lai_can_luot_chinh_da_xong(sach, gia, tmp_path, capsys):
    assert main(lenh(sach, tmp_path / "x", "xao-k")) == 2  # không có --tu-luot
    dang_do = tmp_path / "dang-do"
    gia.hong_o = "a4"
    assert main(lenh(sach, dang_do, "chinh")) == 1
    assert main(lenh(sach, tmp_path / "y", "xao-k", "--tu-luot", str(dang_do))) == 2
    assert "chưa xong" in capsys.readouterr().err


# ---------- phát lại, baseline: không chi ----------

@pytest.mark.parametrize("bien_the,he", [("tat-r17", "tat_r17"), ("bo-pass-chinh", "bo_pass_chinh"), ("bo-pass-phu", "bo_pass_phu"),
                                          ("oracle-a10", "oracle_a10"), ("b1", "b1"), ("b2", "b2"), ("b3", "b3"), ("b4", "b4")])
def test_bien_the_khong_chi_chay_khong_can_allow_spend(bien_the, he, sach, gia, chinh, tmp_path):
    truoc, so_lenh = bam(chinh), len(gia.lenh)
    ra = tmp_path / bien_the
    assert main(lenh(sach, ra, bien_the, "--tu-luot", str(chinh), co_vang=True, co_chi=False)) == 0
    assert len(gia.lenh) == so_lenh and bam(chinh) == truoc  # không gọi pipeline, không đụng lượt chính
    hd = doc_json(ra / "hop-dong.json")
    assert kiem(hd) == [] and hd["dinh_danh"]["he"] == he and ban_ghi.da_xong(ban_ghi.doc(ra))
    assert (ra / "bang-diem.json").exists()
    assert hd["chi_phi"]["tong"]["usd"] == 0.0 and hd["chi_phi"]["tong"]["so_loi_goi_mo_hinh"] == 0


def test_ablation_pass_dung_nguon_goc_canh(sach, gia, chinh, tmp_path):
    for bien_the, mong in (("bo-pass-phu", {"pass_chinh"}), ("bo-pass-chinh", {"pass_phu"})):
        ra = tmp_path / bien_the
        assert main(lenh(sach, ra, bien_the, "--tu-luot", str(chinh), co_chi=False)) == 0
        hd = doc_json(ra / "hop-dong.json")
        assert hd["canh"] and {c["nguon_goc"] for c in hd["canh"]} == mong


def test_baseline_canh_mang_nhan_baseline(sach, gia, chinh, tmp_path):
    ra = tmp_path / "b2"
    assert main(lenh(sach, ra, "b2", "--tu-luot", str(chinh), co_chi=False)) == 0
    hd = doc_json(ra / "hop-dong.json")
    assert hd["canh"] and {c["nguon_goc"] for c in hd["canh"]} == {"baseline"}


# ---------- B5 ----------

@pytest.fixture
def sach_b5(tmp_path):
    pdf = tao_pdf(tmp_path / "thien-van.pdf", [ht.TRANG[n].replace("\n", " ") for n in (1, 2, 3, 4)])
    m = ht.manifest(ht.sha256(pdf))
    mf = tmp_path / "m-b5.json"
    mf.write_text(json.dumps(m), encoding="utf-8")
    return {"pdf": pdf, "manifest": mf}


def test_b5_thieu_allow_spend_chi_dry_run(sach_b5, tmp_path, monkeypatch):
    import danhgia.xuat.b5.lenh as b5
    monkeypatch.setattr(b5, "tao_khach", lambda: (_ for _ in ()).throw(AssertionError("dựng khách mô hình thật")))
    ra = tmp_path / "b5"
    assert main(lenh(sach_b5, ra, "b5a", co_chi=False)) == 0
    bao = doc_json(ra / "dry-run.json")
    assert bao["buoc_co_chi"] == ["b5"] and bao["du_toan"]["so_loi_goi"] == 1 and bao["du_toan"]["usd_toi_da"] > 0
    assert not (ra / "hop-dong.json").exists()


def test_b5_co_allow_spend_ra_hop_dong_qua_validator(sach_b5, tmp_path, monkeypatch):
    import danhgia.xuat.b5.lenh as b5
    from danhgia.xuat.b5 import goi

    class Khach:
        so_lan = 0

        def goi(self, he_thong, nguoi_dung, luoc_do):
            Khach.so_lan += 1
            return goi.PhanHoi(text=ht.van_ban_mo_hinh(ht.phan_hoi_a()), usage={"promptTokenCount": 300, "candidatesTokenCount": 80})

    monkeypatch.setattr(b5, "tao_khach", lambda: (Khach(), "vertex"))
    ra = tmp_path / "b5"
    assert main(lenh(sach_b5, ra, "b5a", "--bien-the-b5", "2")) == 0
    hd = doc_json(ra / "hop-dong.json")
    assert kiem(hd) == [] and hd["dinh_danh"]["he"] == "b5a" and Khach.so_lan == 1
    assert ban_ghi.da_xong(ban_ghi.doc(ra)) and ban_ghi.doc(ra)["cau_hinh"]["bien_the_b5"] == 2


# ---------- dự toán ----------

def test_du_toan_tinh_tay():
    gia_ = uoc_chi.DON_GIA
    chinh = uoc_chi.du_toan("chinh", 100)
    assert [h["buoc"] for h in chinh["hang"]] == ["label-roles", "a3", "a4", "embedding", "pass-chinh", "nhan-va-ten-module"]
    a3 = next(h for h in chinh["hang"] if h["buoc"] == "a3")
    assert a3["token_vao"] == round(gia_["a3"]["vao"] * 100) and a3["so_loi_goi"] == round(gia_["a3"]["goi"] * 100, 1)
    assert a3["usd"] == pytest.approx((gia_["a3"]["vao"] * 100 * 0.25 + gia_["a3"]["ra"] * 100 * 1.5) / 1e6, abs=1e-4)
    assert chinh["tong"]["usd"] == pytest.approx(sum(h["usd"] for h in chinh["hang"]), abs=1e-3)


def test_du_toan_xao_k_nhan_k_lan_pass_chinh_va_pass_phu_theo_ty_le():
    mot = uoc_chi.du_toan("xao-k", 100, k=1)["tong"]["usd"]
    nam = uoc_chi.du_toan("xao-k", 100, k=5)["tong"]["usd"]
    assert nam == pytest.approx(5 * mot, rel=0.02)
    day = uoc_chi.du_toan("pass-phu-llm", 100, ty_le_dich=1.0)["hang"][0]["usd"]
    mot_phan_tu = uoc_chi.du_toan("pass-phu-llm", 100, ty_le_dich=0.25)["hang"][0]["usd"]
    assert day == pytest.approx(gia_pp(100), abs=1e-3) and mot_phan_tu == pytest.approx(day / 4, abs=1e-4)
    assert uoc_chi.du_toan("tat-r17", 100)["tong"]["usd"] == 0


def gia_pp(n):
    return 2.34870825 / 126 * n


# ---------- kiến trúc ----------

def test_chi_ba_mo_dun_cua_luot_nhap_pipeline():
    import ast
    goc = Path(__file__).resolve().parents[2] / "evaluation" / "danhgia" / "luot"
    co = set()
    for p in goc.glob("*.py"):
        for nut in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
            ten = [x.name for x in nut.names] if isinstance(nut, ast.Import) else \
                [nut.module or ""] if isinstance(nut, ast.ImportFrom) and nut.level == 0 else []
            if any(t.split(".")[0] == "doc2roadmap" for t in ten):
                co.add(p.name)
    assert co == {"chay_cli.py", "so_chi.py", "uoc_chi.py"}


def test_lenh_luot_trong_bang_lenh():
    from danhgia.__main__ import _LENH
    assert _LENH["luot"] == "danhgia.luot.lenh"
