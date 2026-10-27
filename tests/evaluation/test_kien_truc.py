import ast
from pathlib import Path

EVALUATION = Path(__file__).resolve().parents[2] / "evaluation" / "danhgia"
# seam phiếu (phieu/, vang/, ten.py) và seam chấm (cham/, nếu có) không nhập mã pipeline
SEAM_SACH = [EVALUATION / "phieu", EVALUATION / "vang", EVALUATION / "cham", EVALUATION / "ten.py"]


def _tep_py():
    for muc in SEAM_SACH:
        if muc.is_file():
            yield muc
        elif muc.is_dir():
            yield from muc.rglob("*.py")


def _nhap(path: Path) -> list[str]:
    ten = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            ten += [n.name for n in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            ten.append(node.module or "")
    return ten


def test_seam_phieu_co_mo_dun_cua_ve_dg02() -> None:
    # chặn kiểm vô nghĩa: phải thực sự quét được mã của seam phiếu
    ten_tep = {p.name for p in _tep_py()}
    assert {"g3.py", "kiem.py", "can.py", "bat_dong.py", "ten.py", "trang.py"} <= ten_tep


def test_seam_phieu_va_cham_khong_nhap_doc2roadmap() -> None:
    for tep in _tep_py():
        for ten in _nhap(tep):
            assert ten.split(".", 1)[0] != "doc2roadmap", f"{tep}: {ten}"
