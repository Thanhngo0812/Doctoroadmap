"""Chạy trọn đường xuất -> kiểm -> chuyển vàng -> chấm qua CLI trên fixture."""
import json
from pathlib import Path

from danhgia.__main__ import main

KHO = Path(__file__).resolve().parent / "fixtures" / "kho-nho"


def test_duong_trong_cli_ra_bang_so(tmp_path, capsys):
    hd, thu_muc, bang = tmp_path / "hd.json", tmp_path / "vang", tmp_path / "bang.json"
    assert main(["xuat", "--kho", str(KHO), "--doc", "xstk-ch3-1", "--phien-ban", "68", "--he", "chinh",
                 "--bien-the", "mac_dinh", "--luot-nhieu", "0", "--commit", "c" * 40, "--ngay-chay", "2026-10-26",
                 "--transport", "vertex", "--ra", str(hd)]) == 0
    assert main(["kiem", str(hd)]) == 0
    assert main(["chuyen-vang", "--kho", str(KHO), "--doc", "xstk-ch3-1", "--phien-ban", "68", "--hop-dong", str(hd),
                 "--vang-cu", str(KHO / "a8-gold" / "xstk-nho-vang.json"), "--ra", str(thu_muc)]) == 0
    assert main(["cham", "--hop-dong", str(hd), "--g3", str(thu_muc / "g3.json"), "--g4", str(thu_muc / "g4.json"),
                 "--can", str(thu_muc / "can.json"), "--ra", str(bang)]) == 0
    ket_qua = json.loads(bang.read_text(encoding="utf-8"))
    q6 = next(r for r in ket_qua["theo_cuon"] if r["thuoc"] == "a10.q6.nghiem")
    assert (q6["tu"], q6["mau"]) == (15, 61)  # trùng số của bộ chấm cũ trên fixture (xem test_doi_chieu)
    assert "a10.q6.nghiem" in capsys.readouterr().out


def test_kiem_tra_hop_dong_hong_tra_ma_loi_khac_khong(tmp_path):
    hong = tmp_path / "hong.json"
    hong.write_text(json.dumps({"schema": "sai"}), encoding="utf-8")
    assert main(["kiem", str(hong)]) == 1


def test_doi_chieu_qua_cli_tra_0_khi_khong_lech():
    assert main(["doi-chieu", "--kho", str(KHO), "--doc", "xstk-ch3-1", "--phien-ban", "68",
                 "--vang", str(KHO / "a8-gold" / "xstk-nho-vang.json")]) == 0


def test_ho_so_mac_dinh_cua_cli_la_spec():
    from danhgia.__main__ import _tham_so
    args = _tham_so().parse_args(["cham", "--hop-dong", "a", "--g3", "b", "--g4", "c", "--can", "d"])
    assert args.ho_so == "spec"
