"""Seam chấm và hợp đồng không nhập mã pipeline; chỉ seam xuất (và lớp đối chiếu) được nhập `doc2roadmap`."""
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


def test_vang_cu_khong_nhap_doc2roadmap():
    _cam("vang")


def test_chi_xuat_va_doi_chieu_duoc_nhap_pipeline():
    cho_phep = {"xuat", "doi_chieu.py"}
    for duong in GOC.rglob("*.py"):
        tuong_doi = duong.relative_to(GOC).parts
        if tuong_doi[0] in cho_phep:
            continue
        for ten in _nhap(duong):
            assert not ten.split(".")[0].startswith("doc2roadmap"), f"{duong}: {ten}"
