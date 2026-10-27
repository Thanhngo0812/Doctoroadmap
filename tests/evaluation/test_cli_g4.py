import copy
import json

import pytest

from danhgia.__main__ import main
from danhgia.phieu import bat_dong, bat_dong_g4, g4
from tests.evaluation.ho_tro import KHO, ma_khai_niem, tao_pdf
from tests.evaluation.test_g4_phieu import dien


@pytest.fixture
def tep(tmp_path, manifest):
    (tmp_path / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    (tmp_path / "kho.json").write_text(json.dumps(KHO, ensure_ascii=False), encoding="utf-8")
    return tmp_path


def chay(*args) -> int:
    return main(["phieu-g4", *map(str, args)])


def k(so):
    return ma_khai_niem(so)


def test_cli_g4_tron_vong_sinh_kiem_can_bat_dong_chot_dem(tep, capsys):
    pdf = tao_pdf(tep / "s.pdf", ["x"] * 6)
    m, kho = tep / "manifest.json", tep / "kho.json"
    for nguoi in ("T1-a", "T1-b"):
        assert chay("sinh", "--manifest", m, "--kho", kho, "--nguoi", nguoi, "--ra", tep / f"{nguoi}.xlsx", "--so-dong", 6) == 0
    kt = {"loai": "kien_thuc"}
    dien(tep / "T1-a.xlsx", {
        "c10-q001": {"dich": k(2), "nguon": k(1), **kt},
        "c10-q002": {"dich": k(4), "nguon": k(2), **kt},
        "c10-q003": {"dich": k(4), "nguon": k(1), **kt},    # B chỉ có đường 001→002→004: được tín dụng bắc cầu
        "c10-q004": {"dich": k(2), "nguon": "ngoai", "ngoai_ten": "Tập hợp", "ngoai_trang": 3, **kt},
    })
    dien(tep / "T1-b.xlsx", {
        "c10-q001": {"dich": k(2), "nguon": k(1), **kt},
        "c10-q002": {"dich": k(4), "nguon": k(2), **kt},
        "c10-q003": {"dich": k(2), "nguon": "ngoai", "ngoai_ten": "tập hợp", "ngoai_trang": 4, **kt},
        "c10-q004": {"dich": k(3), "nguon": k(1), **kt},
    })
    for nguoi in ("T1-a", "T1-b"):
        assert chay("kiem", "--manifest", m, "--kho", kho, "--pdf", pdf, "--phieu", tep / f"{nguoi}.xlsx", "--ra", tep / f"{nguoi}.json") == 0
    assert chay("can", "--kho", kho, "--a", tep / "T1-a.json", "--b", tep / "T1-b.json", "--ra", tep / "can.json") == 0
    can = json.loads((tep / "can.json").read_text(encoding="utf-8"))
    assert len(can["khop"]) == 3 and len(can["chi_a"]) == 1 and len(can["chi_b"]) == 1
    assert chay("bat-dong", "--can", tep / "can.json", "--ra-dir", tep / "bd") == 0
    muc = bat_dong_g4.tao_muc_g4(can)
    for nguoi in ("T1-a", "T1-b"):
        bat_dong.dien_thu(tep / "bd" / f"bat-dong-g4-{nguoi}.xlsx", {x["id"]: ("giu", "ok") for x in muc})
        assert chay("kiem-bat-dong", "--can", tep / "can.json", "--phieu", tep / "bd" / f"bat-dong-g4-{nguoi}.xlsx") == 0
    assert chay("chot", "--can", tep / "can.json", "--a", tep / "bd/bat-dong-g4-T1-a.xlsx", "--b", tep / "bd/bat-dong-g4-T1-b.xlsx",
                "--ra", tep / "vang.json") == 0
    vang = json.loads((tep / "vang.json").read_text(encoding="utf-8"))
    assert vang["vang_chinh"] == [] and len(vang["kien_thuc"]) == 5 and len(vang["vang_giao"]) == 0
    capsys.readouterr()
    assert chay("dem", "--can", tep / "can.json") == 0
    d = json.loads(capsys.readouterr().out)
    assert d["khong_bac_cau"]["tong"]["tong"]["a"] == 3 and d["bac_cau"]["tong"]["tong"]["a"] == 4
    assert d["khong_bac_cau"]["tong"]["kien_thuc"]["a"] == 3


def test_cli_g4_kiem_ma_thoat_1_khong_ghi_json_khi_kho_lech(tep, capsys):
    pdf = tao_pdf(tep / "s.pdf", ["x"] * 6)
    m, kho = tep / "manifest.json", tep / "kho.json"
    chay("sinh", "--manifest", m, "--kho", kho, "--nguoi", "T1-a", "--ra", tep / "a.xlsx", "--so-dong", 3)
    kho_khac = copy.deepcopy(KHO)
    kho_khac["khai_niem"][0]["ten"] = "Đã sửa"
    (tep / "kho2.json").write_text(json.dumps(kho_khac, ensure_ascii=False), encoding="utf-8")
    assert chay("kiem", "--manifest", m, "--kho", tep / "kho2.json", "--pdf", pdf, "--phieu", tep / "a.xlsx", "--ra", tep / "a.json") == 1
    assert not (tep / "a.json").exists() and "kho_lech_hash" in capsys.readouterr().out
    assert g4.kho_sha256(kho_khac) != g4.kho_sha256(KHO)
