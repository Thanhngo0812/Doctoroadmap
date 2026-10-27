"""Seam chấm, hợp đồng và phiếu không nhập mã pipeline; chỉ seam xuất (và lớp đối chiếu) được nhập `doc2roadmap`."""
import ast
from pathlib import Path

GOC = Path(__file__).resolve().parents[2] / "evaluation" / "danhgia"


def _nhap(duong):
    ten = []
    for nut in ast.walk(ast.parse(duong.read_text(encoding="utf-8"))):
        if isinstance(nut, ast.Import):
            ten += [x.name for x in nut.names]
        elif isinstance(nut, ast.ImportFrom) and nut.level == 0:
            ten.append(nut.module or "")
    return ten


def _cam(thu_muc):
    tep = sorted((GOC / thu_muc).rglob("*.py"))
    assert tep, f"không có tệp trong {thu_muc}"
    for duong in tep:
        for ten in _nhap(duong):
            assert not ten.split(".")[0].startswith("doc2roadmap"), f"{duong}: {ten}"


def test_cham_khong_nhap_doc2roadmap():
    _cam("cham")


def test_hop_dong_khong_nhap_doc2roadmap():
    _cam("hop_dong")


def test_vang_khong_nhap_doc2roadmap():
    _cam("vang")


def test_phieu_khong_nhap_doc2roadmap():
    _cam("phieu")


def test_seam_phieu_co_mo_dun_cua_ve_dg02():
    # chặn kiểm vô nghĩa: phải thực sự quét được mã của seam phiếu
    ten_tep = {p.name for p in (GOC / "phieu").rglob("*.py")} | {p.name for p in (GOC / "vang").rglob("*.py")}
    assert {"g3.py", "kiem.py", "can.py", "bat_dong.py", "trang.py"} <= ten_tep
    assert (GOC / "ten.py").is_file()


def test_chi_xuat_va_doi_chieu_duoc_nhap_pipeline():
    cho_phep = {"xuat", "doi_chieu.py", "phat_lai"}
    for duong in GOC.rglob("*.py"):
        tuong_doi = duong.relative_to(GOC).parts
        if tuong_doi[0] in cho_phep:
            continue
        for ten in _nhap(duong):
            assert not ten.split(".")[0].startswith("doc2roadmap"), f"{duong}: {ten}"
