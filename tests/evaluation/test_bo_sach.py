"""DG-01: manifest sách, bốc 3 chương theo seed, kiểm PDF gốc chỉ in số."""
import json
from pathlib import Path

import pytest

from danhgia.bo_sach import boc_chuong, kiem_manifest, kiem_pdf_goc, tom_tat_kiem_pdf

PHAT_TRIEN = Path(__file__).resolve().parents[2] / "evaluation" / "bo-sach" / "phat-trien"


def _manifest(chuong):
    return {
        "schema": "danh-gia-sach-1", "ma_sach": "thu-nghiem", "chu_de": "toan", "tap": "thu",
        "pdf_sha256": "0" * 64, "so_trang": 300, "quyen": "da_xac_nhan", "chuong": chuong, "boc": None,
    }


def _chuong(n, *, mo_dau=1, bai_tap=(), trang=20):
    ket = []
    for i in range(1, n + 1):
        loai = "mo_dau" if i <= mo_dau else ("bai_tap" if i in bai_tap else "noi_dung")
        ket.append({"ma": f"c{i}", "so": str(i), "ten": f"Chương {i}", "trang_dau": 1 + (i - 1) * trang,
                    "trang_cuoi": i * trang, "loai": loai})
    return ket


def test_cung_seed_cung_ket_qua_va_dung_ba_phan():
    m = _manifest(_chuong(10))
    lan_1 = boc_chuong(m, seed=11, n_trang_toi_thieu=5)
    assert lan_1 == boc_chuong(m, seed=11, n_trang_toi_thieu=5)
    # 9 chương hợp lệ (c2…c10) chia ba phần liền nhau: c2–c4, c5–c7, c8–c10; mỗi phần đúng một chương.
    phan = [{"c2", "c3", "c4"}, {"c5", "c6", "c7"}, {"c8", "c9", "c10"}]
    for seed in range(60):
        chon = boc_chuong(m, seed=seed, n_trang_toi_thieu=5)["chuong"]
        assert len(chon) == 3
        assert all(ma in nhom for ma, nhom in zip(chon, phan)), (seed, chon)


def test_seed_khac_co_the_ra_chuong_khac():
    m = _manifest(_chuong(10))
    ket = {tuple(boc_chuong(m, seed=s, n_trang_toi_thieu=5)["chuong"]) for s in range(20)}
    assert len(ket) > 1


def test_chuong_bi_loc_khong_bao_gio_duoc_boc():
    chuong = _chuong(12, mo_dau=2, bai_tap={6, 11})
    chuong[3]["trang_cuoi"] = chuong[3]["trang_dau"] + 1      # c4 chỉ 2 trang, dưới N
    m = _manifest(chuong)
    cam = {"c1", "c2", "c6", "c11", "c4"}
    for s in range(200):
        assert not set(boc_chuong(m, seed=s, n_trang_toi_thieu=5)["chuong"]) & cam


def test_it_hon_ba_chuong_hop_le_thi_bao_loi():
    with pytest.raises(ValueError):
        boc_chuong(_manifest(_chuong(3)), seed=1, n_trang_toi_thieu=5)


def test_kiem_manifest_bat_loi():
    m = _manifest(_chuong(5))
    assert kiem_manifest(m) == []
    hong = json.loads(json.dumps(m))
    hong["chuong"][2]["trang_dau"] = 999
    hong["chuong"][1]["loai"] = "khac"
    hong["tap"] = "test"
    loi = kiem_manifest(hong)
    assert any("trang" in l for l in loi) and any("loai" in l for l in loi) and any("tap" in l for l in loi)


def test_kiem_manifest_bat_chuong_chong_lan_va_boc_ngoai_danh_sach():
    m = _manifest(_chuong(5))
    m["chuong"][2]["trang_dau"] = m["chuong"][1]["trang_dau"]
    m["boc"] = {"seed": 1, "n_trang_toi_thieu": 5, "chuong": ["c9"]}
    loi = kiem_manifest(m)
    assert any("chồng" in l for l in loi) and any("c9" in l for l in loi)


def test_manifest_phat_trien_hop_le():
    tep = sorted(PHAT_TRIEN.glob("*.json"))
    assert {t.stem for t in tep} == {"dev-xstk", "dev-doc-1", "dev-nhap-mon-ml"}
    for t in tep:
        assert kiem_manifest(json.loads(t.read_text(encoding="utf-8"))) == [], t.name


def _pdf_chu(tmp_path, trang_chu, trang_trang):
    """PDF tối thiểu viết tay: `trang_chu` trang có lớp chữ Helvetica, rồi `trang_trang` trang trống (như trang ảnh của bản quét)."""
    so_trang = trang_chu + trang_trang
    doi_tuong = ["<< /Type /Catalog /Pages 2 0 R >>", None, "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    trang_ids = []
    for i in range(so_trang):
        cau = f"Day la trang co lop chu so {i}, du dai de vuot nguong tam muoi ky tu khong trang. " * 2
        chu = f"BT /F1 12 Tf 50 700 Td ({cau}) Tj ET" if i < trang_chu else ""
        doi_tuong.append(f"<< /Length {len(chu)} >>\nstream\n{chu}\nendstream")
        noi_dung_id = len(doi_tuong)
        doi_tuong.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents {noi_dung_id} 0 R "
                         "/Resources << /Font << /F1 3 0 R >> >> >>")
        trang_ids.append(len(doi_tuong))
    doi_tuong[1] = f"<< /Type /Pages /Kids [{' '.join(f'{i} 0 R' for i in trang_ids)}] /Count {so_trang} >>"
    ra = bytearray(b"%PDF-1.4\n")
    vi_tri = []
    for so, than in enumerate(doi_tuong, start=1):
        vi_tri.append(len(ra))
        ra += f"{so} 0 obj\n{than}\nendobj\n".encode("latin-1")
    xref = len(ra)
    ra += f"xref\n0 {len(doi_tuong) + 1}\n0000000000 65535 f \n".encode("latin-1")
    ra += "".join(f"{v:010d} 00000 n \n" for v in vi_tri).encode("latin-1")
    ra += f"trailer\n<< /Size {len(doi_tuong) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode("latin-1")
    duong = tmp_path / f"bi-mat-TEN-SACH-GIA-{trang_chu}-{trang_trang}.pdf"
    duong.write_bytes(bytes(ra))
    return duong


def test_kiem_pdf_goc_dem_trang_co_lop_chu(tmp_path):
    ket = kiem_pdf_goc(_pdf_chu(tmp_path, 4, 1))
    assert ket["so_trang"] == 5
    assert ket["so_trang_co_chu"] == 4
    assert ket["nghi_ban_quet"] is False
    ket_quet = kiem_pdf_goc(_pdf_chu(tmp_path, 1, 4))
    assert ket_quet["nghi_ban_quet"] is True


def test_tom_tat_kiem_pdf_chi_in_truong_so_trong_allowlist(tmp_path):
    ket = kiem_pdf_goc(_pdf_chu(tmp_path, 4, 1))
    ket["duong_dan"] = "C:/bi-mat-TEN-SACH-GIA.pdf"            # lồng chuỗi bí mật giả vào kết quả
    ket["chi_tiet"] = {"ten": "bi-mat-TEN-SACH-GIA"}
    dong = tom_tat_kiem_pdf("T", ket)
    assert "bi-mat" not in dong and "TEN-SACH-GIA" not in dong
    assert "so_trang=5" in dong


# --- bổ sung sau soát độc lập (agent A, 2026-10-27: S-01, S-06, S-10) ----------------------------------------------

def test_kiem_pdf_tep_thieu_hoac_hong_khong_lo_duong_dan(tmp_path):
    # Lỗi thật S-01: traceback in đường dẫn tập thử. Chạy qua đúng CLI, bắt cả stdout lẫn stderr.
    import subprocess
    import sys
    evaluation = Path(__file__).resolve().parents[2] / "evaluation"
    hong = tmp_path / "bi-mat-TEN-SACH-GIA-hong.pdf"
    hong.write_bytes(b"khong phai pdf")
    for duong in (tmp_path / "bi-mat-TEN-SACH-GIA-thieu.pdf", hong):
        kq = subprocess.run([sys.executable, "-m", "danhgia.bo_sach", "kiem-pdf", "T", str(duong)],
                            capture_output=True, text=True, cwd=evaluation, encoding="utf-8")
        assert kq.returncode == 1
        dau_ra = kq.stdout + kq.stderr
        assert "bi-mat" not in dau_ra and "TEN-SACH-GIA" not in dau_ra
        assert "T loi_doc_pdf" in kq.stdout


def test_boc_bao_loi_khong_dua_ten_sach_vao_thong_diep():
    m = _manifest(_chuong(3))
    m["ma_sach"] = "bi-mat-TEN-SACH-GIA"
    with pytest.raises(ValueError) as loi:
        boc_chuong(m, seed=1, n_trang_toi_thieu=5)
    assert "bi-mat" not in str(loi.value)


@pytest.mark.parametrize("so_chuong, kich", [(10, (4, 3, 3)), (11, (4, 4, 3))])
def test_chia_ba_phan_du_don_ve_dau(so_chuong, kich):
    # S-06: số chương hợp lệ không chia hết cho 3, phần dư dồn về các phần đầu.
    m = _manifest(_chuong(so_chuong + 1))          # c1 là mở đầu, c2… hợp lệ
    hop_le = [f"c{i}" for i in range(2, so_chuong + 2)]
    phan, dau = [], 0
    for k in kich:
        phan.append(set(hop_le[dau:dau + k]))
        dau += k
    da_thay = [set(), set(), set()]
    for seed in range(300):
        for i, ma in enumerate(boc_chuong(m, seed=seed, n_trang_toi_thieu=5)["chuong"]):
            assert ma in phan[i]
            da_thay[i].add(ma)
    assert da_thay == phan                          # mọi chương trong mỗi phần đều có lúc được bốc


def test_chuong_dung_n_trang_hop_le_n_tru_1_bi_loai():
    # S-06: c2 dài đúng N = 5 trang thì hợp lệ; c3 dài 4 trang thì bị loại. Hợp lệ còn c2, c4, c5, c6 (chia 2-1-1).
    chuong = _chuong(6, trang=10)
    chuong[1]["trang_cuoi"] = chuong[1]["trang_dau"] + 4
    chuong[2]["trang_cuoi"] = chuong[2]["trang_dau"] + 3
    m = _manifest(chuong)
    chon = {ma for s in range(200) for ma in boc_chuong(m, seed=s, n_trang_toi_thieu=5)["chuong"]}
    assert "c2" in chon and "c3" not in chon


def test_nguong_80_ky_tu_khong_trang(tmp_path):
    pytest.importorskip("pypdfium2")
    from danhgia.bo_sach import NGUONG_KY_TU
    assert NGUONG_KY_TU == 80
    duong = _pdf_chu_dai(tmp_path, [79, 80])
    ket = kiem_pdf_goc(duong)
    assert ket["so_trang_co_chu"] == 1               # trang 79 ký tự không tính, trang 80 ký tự tính


def _pdf_chu_dai(tmp_path, so_ky_tu):
    """Mỗi trang đúng `n` ký tự không trắng (chữ x liền nhau)."""
    doi_tuong = ["<< /Type /Catalog /Pages 2 0 R >>", None, "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    trang_ids = []
    for n in so_ky_tu:
        chu = f"BT /F1 8 Tf 20 700 Td ({'x' * n}) Tj ET"
        doi_tuong.append(f"<< /Length {len(chu)} >>\nstream\n{chu}\nendstream")
        doi_tuong.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents {len(doi_tuong)} 0 R "
                         "/Resources << /Font << /F1 3 0 R >> >> >>")
        trang_ids.append(len(doi_tuong))
    doi_tuong[1] = f"<< /Type /Pages /Kids [{' '.join(f'{i} 0 R' for i in trang_ids)}] /Count {len(trang_ids)} >>"
    ra, vi_tri = bytearray(b"%PDF-1.4\n"), []
    for so, than in enumerate(doi_tuong, start=1):
        vi_tri.append(len(ra))
        ra += f"{so} 0 obj\n{than}\nendobj\n".encode("latin-1")
    xref = len(ra)
    ra += f"xref\n0 {len(doi_tuong) + 1}\n0000000000 65535 f \n".encode("latin-1")
    ra += "".join(f"{v:010d} 00000 n \n" for v in vi_tri).encode("latin-1")
    ra += f"trailer\n<< /Size {len(doi_tuong) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode("latin-1")
    duong = tmp_path / "dai.pdf"
    duong.write_bytes(bytes(ra))
    return duong


def test_kiem_manifest_bat_schema_sha_va_kieu():
    m = _manifest(_chuong(5))
    m["schema"] = "khac"
    m["pdf_sha256"] = "xyz"
    m["so_trang"] = True
    m["boc"] = {"seed": "1", "n_trang_toi_thieu": 5, "chuong": []}
    loi = " | ".join(kiem_manifest(m))
    assert "schema" in loi and "pdf_sha256" in loi and "so_trang" in loi and "seed" in loi
