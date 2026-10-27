import json

import pytest

from danhgia.__main__ import main
from danhgia.phieu import bat_dong
from tests.evaluation.test_phieu_g3 import CAU_1, CAU_2, dien
from tests.evaluation.ho_tro import TRANG, tao_pdf


@pytest.fixture
def tep(tmp_path, manifest):
    (tmp_path / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    return tmp_path


def chay(*args) -> int:
    return main(["phieu-g3", *map(str, args)])


def test_cli_tron_vong_sinh_kiem_can_bat_dong_chot_dem(tep, capsys):
    pdf = tao_pdf(tep / "s.pdf", ["x"] * 6)  # văn bản PDF ASCII không khớp: chỉ sinh cảnh báo, không chặn
    m = tep / "manifest.json"
    for nguoi in ("T1-a", "T1-b"):
        assert chay("sinh", "--manifest", m, "--nguoi", nguoi, "--ra", tep / f"{nguoi}.xlsx", "--so-dong", 10) == 0
    dien(tep / "T1-a.xlsx", {
        "c10-001": {"ten": "Quy luật số lớn", "trang_thai": "day_o_day", "trang": 1, "cau": CAU_1},
        "c10-002": {"ten": "Xác suất có điều kiện", "trang_thai": "day_o_day", "trang": 2, "cau": CAU_2},
        "c10-003": {"ten": "Mốt", "trang_thai": "chi_nhac"},
    })
    dien(tep / "T1-b.xlsx", {
        "c10-001": {"ten": "quy luật số lớn", "trang_thai": "day_o_day", "trang": 1, "cau": CAU_1},
        "c10-002": {"ten": "Trung vị", "trang_thai": "chi_nhac"},
    })
    for nguoi in ("T1-a", "T1-b"):
        assert chay("kiem", "--manifest", m, "--pdf", pdf, "--phieu", tep / f"{nguoi}.xlsx", "--ra", tep / f"{nguoi}.json") == 0
    assert chay("can", "--a", tep / "T1-a.json", "--b", tep / "T1-b.json", "--ra", tep / "can.json") == 0
    assert chay("bat-dong", "--can", tep / "can.json", "--ra-dir", tep / "bd") == 0
    can = json.loads((tep / "can.json").read_text(encoding="utf-8"))
    muc = bat_dong.tao_muc(can)
    assert len(muc) == 3  # Xác suất có đk, Mốt (a); Trung vị (b)
    for nguoi in ("T1-a", "T1-b"):
        bat_dong.dien_thu(tep / "bd" / f"bat-dong-{nguoi}.xlsx", {x["id"]: ("giu", "ok") for x in muc})
    assert chay("chot", "--can", tep / "can.json", "--a", tep / "bd/bat-dong-T1-a.xlsx", "--b", tep / "bd/bat-dong-T1-b.xlsx",
                "--ra", tep / "kho.json") == 0
    kho = json.loads((tep / "kho.json").read_text(encoding="utf-8"))
    assert [k["ma"] for k in kho["khai_niem"]] == ["G-dev-test-001", "G-dev-test-002", "G-dev-test-003", "G-dev-test-004"]
    capsys.readouterr()
    assert chay("dem", "--can", tep / "can.json", "--kho", tep / "kho.json") == 0
    ra = json.loads(capsys.readouterr().out)
    assert ra["dong_thuan_truoc_hoi_y"]["tong"]["a"] == 1 and ra["kho_chot"]["tong"]["vao_kho"] == 4


def test_cli_kiem_tra_ma_thoat_1_va_khong_ghi_json_khi_phieu_loi(tep, capsys):
    pdf = tao_pdf(tep / "s.pdf", ["x"] * 6)
    m = tep / "manifest.json"
    chay("sinh", "--manifest", m, "--nguoi", "T1-a", "--ra", tep / "a.xlsx", "--so-dong", 3)
    dien(tep / "a.xlsx", {"c10-001": {"ten": "Mốt", "trang_thai": "sai"}})
    assert chay("kiem", "--manifest", m, "--pdf", pdf, "--phieu", tep / "a.xlsx", "--ra", tep / "a.json") == 1
    assert not (tep / "a.json").exists()
    assert "gia_tri_ngoai_danh_sach" in capsys.readouterr().out
