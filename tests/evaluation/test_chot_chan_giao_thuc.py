"""DG-18a: lượt trên tập thử phải mang SHA-256 của giao thức đăng ký trước (spec mục 15; giao thức dk-0 đầu tệp). Manifest giả `tap = "thu"` trong tmp_path."""
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from danhgia.__main__ import main
from danhgia.luot import ban_ghi, chay, thu_muc
from tests.evaluation.test_luot import (bam, chan_mang, chinh, doc_json, gia, lenh, sach, sach_b5, THAM_SO_HASH)  # noqa: F401  (fixture dùng lại)

BI_MAT = "NOI-DUNG-GIAO-THUC-BI-MAT-XYZ"
GIAO_THUC_CHOT = f"# Giao thức dk-1\n\nBản chốt, mọi ô đã điền. {BI_MAT}\n".encode("utf-8")


def sha(b):
    return hashlib.sha256(b).hexdigest()


@pytest.fixture
def thu(sach):
    """Cùng sách, manifest đổi sang tập thử."""
    sach["m"]["tap"] = "thu"
    sach["manifest"].write_text(json.dumps(sach["m"]), encoding="utf-8")
    return sach


@pytest.fixture
def giao_thuc(tmp_path):
    duong = tmp_path / "dk-1.md"
    duong.write_bytes(GIAO_THUC_CHOT)
    return duong


def khong_dung_gi(gia, ra):
    assert not Path(ra).exists(), "thư mục lượt đã được tạo trước khi kiểm giao thức"
    assert gia.lenh == [] and not gia.goi_mo_hinh


# ---------------------------------------------------------------- từ chối trước bước đầu tiên


def test_tap_thu_thieu_giao_thuc_bi_tu_choi_khong_tao_thu_muc_khong_goi_pipeline(thu, gia, tmp_path, capsys):
    ra = tmp_path / "luot" / "chinh"
    assert main(lenh(thu, ra, "chinh", co_vang=True)) == 2
    assert "giao thức" in capsys.readouterr().err
    khong_dung_gi(gia, ra)
    assert not (tmp_path / "luot").exists()


@pytest.mark.parametrize("chu", ["CHỜ", "NHÁP"])
def test_giao_thuc_con_cho_hay_nhap_bi_tu_choi(chu, thu, gia, tmp_path, capsys):
    tep = tmp_path / "dk-0.md"
    tep.write_text(f"# Giao thức\n\nPhiên bản dk-0 ({chu}, chưa chốt). {BI_MAT}\n", encoding="utf-8")
    ra = tmp_path / "luot"
    assert main(lenh(thu, ra, "chinh", "--giao-thuc", str(tep), co_vang=True)) == 2
    loi = capsys.readouterr().err
    assert "chưa chốt" in loi and BI_MAT not in loi          # thông báo không chép nội dung giao thức
    khong_dung_gi(gia, ra)


def test_giao_thuc_con_cho_viet_dang_nfd_van_bi_tu_choi(thu, gia, tmp_path):
    import unicodedata
    tep = tmp_path / "dk-0.md"
    tep.write_text(unicodedata.normalize("NFD", "# Giao thức\n\nô CHỜ\n"), encoding="utf-8")
    ra = tmp_path / "luot"
    assert main(lenh(thu, ra, "chinh", "--giao-thuc", str(tep), co_vang=True)) == 2
    khong_dung_gi(gia, ra)


def test_giao_thuc_khong_ton_tai_bi_tu_choi(thu, gia, tmp_path):
    ra = tmp_path / "luot"
    assert main(lenh(thu, ra, "chinh", "--giao-thuc", str(tmp_path / "khong-co.md"), co_vang=True)) == 2
    khong_dung_gi(gia, ra)


def test_dry_run_tren_tap_thu_cung_can_giao_thuc(thu, gia, tmp_path):
    ra = tmp_path / "luot"
    assert main(lenh(thu, ra, "chinh", "--dry-run", co_chi=False)) == 2
    khong_dung_gi(gia, ra)


def test_tap_la_bat_buoc_va_phai_hop_le(thu, gia, tmp_path):
    thu["m"]["tap"] = "khac"
    thu["manifest"].write_text(json.dumps(thu["m"]), encoding="utf-8")
    ra = tmp_path / "luot"
    assert main(lenh(thu, ra, "chinh", co_vang=True)) == 2
    khong_dung_gi(gia, ra)



def test_manifest_thieu_tap_bi_tu_choi_khong_coi_la_phat_trien():
    from danhgia.giao_thuc import LoiGiaoThuc, kiem_giao_thuc
    with pytest.raises(LoiGiaoThuc):
        kiem_giao_thuc({"ma_sach": "x"}, None)
    assert kiem_giao_thuc({"ma_sach": "x", "tap": "phat_trien"}, None) is None


# ---------------------------------------------------------------- hợp lệ: SHA vào bản ghi và vào hash cấu hình


def test_giao_thuc_hop_le_ghi_sha_dung_vao_ban_ghi_va_chi_in_sha(thu, gia, giao_thuc, tmp_path, capsys):
    ra = tmp_path / "luot" / "chinh"
    assert main(lenh(thu, ra, "chinh", "--giao-thuc", str(giao_thuc), co_vang=True)) == 0
    ban = ban_ghi.doc(ra)
    assert ban["sha256_giao_thuc"] == hashlib.sha256(GIAO_THUC_CHOT).hexdigest() and ban["tap"] == "thu"
    assert ban_ghi.da_xong(ban) and ban_ghi.kiem(ban) == []
    ra_man_hinh = capsys.readouterr()
    assert ban["sha256_giao_thuc"] in ra_man_hinh.out and BI_MAT not in ra_man_hinh.out + ra_man_hinh.err
    assert str(thu["manifest"]) not in ra_man_hinh.out
    assert gia.lenh, "giao thức hợp lệ thì pipeline được chạy"


def test_doi_mot_byte_giao_thuc_doi_hash_cau_hinh_va_chay_tiep_bao_cau_hinh_doi(thu, gia, giao_thuc, tmp_path, capsys):
    a, b = tmp_path / "luot-a", tmp_path / "luot-b"
    assert main(lenh(thu, a, "chinh", "--giao-thuc", str(giao_thuc), co_vang=True)) == 0
    khac = tmp_path / "dk-1-khac.md"
    khac.write_bytes(GIAO_THUC_CHOT.replace(b"dk-1", b"dk-2"))      # đổi đúng một byte
    assert sha(khac.read_bytes()) != sha(GIAO_THUC_CHOT)
    assert main(lenh(thu, b, "chinh", "--giao-thuc", str(khac), co_vang=True)) == 0
    assert ban_ghi.doc(a)["hash_cau_hinh"] != ban_ghi.doc(b)["hash_cau_hinh"]
    # chạy tiếp thư mục a với giao thức khác: CauHinhDoi, không sửa gì
    truoc, so_lenh = bam(a), len(gia.lenh)
    capsys.readouterr()
    assert main(lenh(thu, a, "chinh", "--giao-thuc", str(khac), co_vang=True)) == 2
    assert "hash cấu hình" in capsys.readouterr().err
    assert bam(a) == truoc and len(gia.lenh) == so_lenh


def test_giao_thuc_nam_trong_thanh_phan_hash():
    goc = ban_ghi.hash_cau_hinh(ban_ghi.thanh_phan(**THAM_SO_HASH))
    co = ban_ghi.hash_cau_hinh(ban_ghi.thanh_phan(**THAM_SO_HASH, sha256_giao_thuc="a" * 64))
    khac = ban_ghi.hash_cau_hinh(ban_ghi.thanh_phan(**THAM_SO_HASH, sha256_giao_thuc="b" * 64))
    assert len({goc, co, khac}) == 3
    assert ban_ghi.hash_cau_hinh(ban_ghi.thanh_phan(**THAM_SO_HASH, sha256_giao_thuc=None)) == goc   # không SHA thì băm như trước (tập phát triển)


# ---------------------------------------------------------------- tập phát triển, bản ghi cũ, thượng nguồn


def test_tap_phat_trien_khong_can_giao_thuc_va_sha_la_null(chinh):
    ban = ban_ghi.doc(chinh)
    assert ban["sha256_giao_thuc"] is None and ban["tap"] == "phat_trien" and ban_ghi.da_xong(ban)


def test_tap_phat_trien_co_giao_thuc_thi_ghi_sha_khong_can_da_chot(sach, gia, tmp_path):
    tep = tmp_path / "dk-0.md"
    tep.write_text("NHÁP và CHỜ đều được chấp nhận ở tập phát triển\n", encoding="utf-8")
    ra = tmp_path / "luot"
    assert main(lenh(sach, ra, "chinh", "--giao-thuc", str(tep), co_vang=True)) == 0
    assert ban_ghi.doc(ra)["sha256_giao_thuc"] == sha(tep.read_bytes())


def test_ban_ghi_cu_thieu_truong_van_doc_duoc_va_xong_o_tap_phat_trien(chinh):
    ban = ban_ghi.doc(chinh)
    del ban["sha256_giao_thuc"], ban["tap"]
    assert ban_ghi.kiem(ban) == [] and ban_ghi.da_xong(ban)


@pytest.mark.parametrize("sua", ["thieu", "null", "khong_phai_sha"])
def test_tap_thu_thieu_hay_hong_sha_trong_ban_ghi_thi_chua_xong(sua, thu, gia, giao_thuc, tmp_path):
    ra = tmp_path / "luot"
    assert main(lenh(thu, ra, "chinh", "--giao-thuc", str(giao_thuc), co_vang=True)) == 0
    ban = ban_ghi.doc(ra)
    assert ban_ghi.da_xong(ban)
    if sua == "thieu":
        del ban["sha256_giao_thuc"]
    elif sua == "null":
        ban["sha256_giao_thuc"] = None
    else:
        ban["sha256_giao_thuc"] = "xyz"
    assert not ban_ghi.da_xong(ban) and any("sha256_giao_thuc" in l for l in ban_ghi.kiem(ban))
    ban_ghi.ghi(ra, ban)
    assert main(["luot", "--kiem", str(ra)]) == 1


def test_bien_the_dung_lai_tren_tap_thu_can_cung_sha_voi_luot_nguon(thu, gia, giao_thuc, tmp_path, capsys):
    chinh_thu = tmp_path / "chinh"
    assert main(lenh(thu, chinh_thu, "chinh", "--giao-thuc", str(giao_thuc), co_vang=True)) == 0
    khac = tmp_path / "dk-khac.md"
    khac.write_bytes(GIAO_THUC_CHOT + b"\nthem\n")
    ra_sai = tmp_path / "b1-sai"
    capsys.readouterr()
    assert main(lenh(thu, ra_sai, "b1", "--tu-luot", str(chinh_thu), "--giao-thuc", str(khac), co_chi=False)) == 2
    assert "lượt nguồn" in capsys.readouterr().err and not ra_sai.exists()
    ra_dung = tmp_path / "b1-dung"
    assert main(lenh(thu, ra_dung, "b1", "--tu-luot", str(chinh_thu), "--giao-thuc", str(giao_thuc), co_chi=False)) == 0
    assert ban_ghi.doc(ra_dung)["sha256_giao_thuc"] == sha(GIAO_THUC_CHOT)


def test_xao_k_tren_tap_thu_cung_can_giao_thuc(thu, gia, tmp_path):
    ra = tmp_path / "xao"
    assert main(lenh(thu, ra, "xao-k", "--tu-luot", str(tmp_path / "chua-co"), "--k", "2")) == 2
    khong_dung_gi(gia, ra)


# ---------------------------------------------------------------- lệnh b5 độc lập


def chay_b5(manifest, pdf, ra, **them):
    from danhgia.xuat.b5 import lenh as b5
    return b5.chay(SimpleNamespace(manifest=str(manifest), pdf=str(pdf), che_do="a", bien_the=1, seed=None, ra=str(ra), dry_run=True,
                                   allow_spend=False, commit="c" * 40, ngay_chay="2026-11-01", **them))


def sach_b5_thu(sach_b5):
    m = json.loads(sach_b5["manifest"].read_text(encoding="utf-8"))
    m["tap"] = "thu"
    sach_b5["manifest"].write_text(json.dumps(m), encoding="utf-8")
    return sach_b5


def test_b5_doc_lap_tren_tap_thu_thieu_giao_thuc_bi_tu_choi_khong_tao_thu_muc(sach_b5, tmp_path, capsys):
    s = sach_b5_thu(sach_b5)
    ra = tmp_path / "b5"
    assert chay_b5(s["manifest"], s["pdf"], ra) == 2
    assert "giao thức" in capsys.readouterr().err and not ra.exists()
    assert chay_b5(s["manifest"], s["pdf"], ra, giao_thuc=None) == 2 and not ra.exists()


def test_b5_doc_lap_giao_thuc_chot_ghi_sha_vao_dry_run(sach_b5, giao_thuc, tmp_path, capsys):
    s = sach_b5_thu(sach_b5)
    ra = tmp_path / "b5"
    assert chay_b5(s["manifest"], s["pdf"], ra, giao_thuc=str(giao_thuc)) == 0
    assert doc_json(ra / "dry-run.json")["sha256_giao_thuc"] == sha(GIAO_THUC_CHOT)
    assert BI_MAT not in capsys.readouterr().out


def test_b5_doc_lap_giao_thuc_con_cho_bi_tu_choi(sach_b5, tmp_path):
    s = sach_b5_thu(sach_b5)
    tep = tmp_path / "dk-0.md"
    tep.write_text("ô CHỜ", encoding="utf-8")
    ra = tmp_path / "b5"
    assert chay_b5(s["manifest"], s["pdf"], ra, giao_thuc=str(tep)) == 2 and not ra.exists()


def test_b5_qua_lenh_luot_tren_tap_thu_chuyen_giao_thuc_xuong_lenh_b5(sach_b5, giao_thuc, tmp_path, monkeypatch):
    import danhgia.xuat.b5.lenh as b5
    from danhgia.xuat.b5 import goi
    s = sach_b5_thu(sach_b5)

    class Khach:
        def goi(self, he_thong, nguoi_dung, luoc_do):
            from tests.evaluation import b5_ho_tro as ht
            return goi.PhanHoi(text=ht.van_ban_mo_hinh(ht.phan_hoi_a()), usage={"promptTokenCount": 300, "candidatesTokenCount": 80})

    monkeypatch.setattr(b5, "tao_khach", lambda: (Khach(), "vertex"))
    ra = tmp_path / "b5luot"
    assert main(lenh(s, ra, "b5a", "--giao-thuc", str(giao_thuc))) == 0
    ban = ban_ghi.doc(ra)
    assert ban["sha256_giao_thuc"] == sha(GIAO_THUC_CHOT) and ban_ghi.da_xong(ban)
    assert main(lenh(s, tmp_path / "b5khong", "b5a")) == 2


def test_b5_hash_cau_hinh_doi_theo_giao_thuc_va_giu_nguyen_khi_khong_co():
    from danhgia.xuat.b5 import lenh as b5
    khong = b5._hash_cau_hinh("a", 1)
    assert b5._hash_cau_hinh("a", 1, None) == khong
    a, b = b5._hash_cau_hinh("a", 1, "0" * 64), b5._hash_cau_hinh("a", 1, "1" * 64)
    assert len({khong, a, b}) == 3
