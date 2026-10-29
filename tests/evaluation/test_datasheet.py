"""Vé DG-17: lệnh `datasheet` sinh khung datasheet cho bộ vàng; chỉ số tự động khớp số tính tay, chỗ điền tay để trống, không lộ tên khái niệm hay câu."""
import hashlib
import json
import re

from danhgia.__main__ import main
from tests.evaluation import bang_hinh_ho_tro as H

SO_TRANG = {"A": 300, "B": 250, "C": 400}
# G3 mỗi cuốn: (số khái niệm dạy ở đây, dạy qua ví dụ, chỉ nhắc, kiến thức nền, trạng thái tranh chấp, số bị loại, số tranh chấp)
G3 = {"A": (3, 1, 1, 0, 1, 2, 1), "B": (2, 2, 0, 1, 0, 0, 0), "C": (4, 0, 0, 0, 0, 1, 0)}
G4 = {"A": (5, 6, 4, 2, 1, 3), "B": (3, 3, 3, 0, 0, 0), "C": (7, 9, 7, 1, 2, 1)}       # vang_chinh, vang_hop, vang_giao, kien_thuc, tranh_chap, loai


def manifest(ma, tap="phat_trien"):
    return {**H.manifest(ma, tap), "so_trang": SO_TRANG[ma], "pdf_sha256": ma.lower() * 64,
            "chuong": [{"ma": f"c{i}", "so": str(i), "ten": H.SECRET + "-CHUONG", "trang_dau": 1, "trang_cuoi": 2, "loai": "noi_dung"} for i in range(1, 4)],
            "boc": {"seed": 1, "n_trang_toi_thieu": 1, "chuong": ["c1", "c2"]},
            "stats": {"long": {"khai_niem": {H.SECRET: 1}, "cau": H.SECRET}}}


def kho_g3(ma):
    n_day, n_vd, n_nhac, n_nen, n_tc, n_loai, n_cho = G3[ma]
    tt = ["day_o_day"] * n_day + ["day_qua_vi_du"] * n_vd + ["chi_nhac"] * n_nhac + ["kien_thuc_nen"] * n_nen + [None] * n_tc
    return {"schema": "danh-gia-g3-1", "ma_sach": ma,
            "khai_niem": [{"ma": f"G-{ma}-{i:03d}", "ten": H.SECRET + "-TEN", "trang_thai": t, "dinh_nghia": {"trang": 1, "cau": H.SECRET + "-CAU"}} for i, t in enumerate(tt)],
            "loai": [{"ten": H.SECRET}] * n_loai, "tranh_chap": [{"ten": H.SECRET}] * n_cho}


def vang_g4(ma):
    lop = dict(zip(("vang_chinh", "vang_hop", "vang_giao", "kien_thuc", "tranh_chap", "loai"), G4[ma]))
    return {"schema": "danh-gia-g4-1", "ma_sach": ma, **{k: [{"nguon": H.SECRET, "dich": H.SECRET}] * v for k, v in lop.items()}, "bao_ham_bac_cau": 2}


def dt_g3(ma):
    a, b, c = {"A": (8, 2, 2), "B": (5, 5, 5), "C": (9, 1, 1)}[ma]
    return {"theo_chuong": {}, "tong": {"a": a, "b": b, "c": c, "f1": 2 * a / (2 * a + b + c)}}


def dt_g4(ma):
    a, b, c = {"A": (16, 2, 2), "B": (12, 4, 4), "C": (8, 6, 6)}[ma]
    tong = {"a": a, "b": b, "c": c, "f1": 2 * a / (2 * a + b + c)}
    return {"khong_bac_cau": {"theo_chuong": {}, "tong": {"tong": tong}}, "bac_cau": {"theo_chuong": {}, "tong": {"tong": {**tong, "f1": 0.5}}}}


def dung_argv(tmp_path, *, tap="phat_trien", bo_g3=()):
    argv = ["datasheet", "--manifest", *[H.ghi_json(tmp_path / f"m-{s}.json", manifest(s, tap)) for s in H.SACH]]
    argv += ["--g3", *[f"{s}={H.ghi_json(tmp_path / f'g3-{s}.json', kho_g3(s))}" for s in H.SACH if s not in bo_g3]]
    argv += ["--g4", *[f"{s}={H.ghi_json(tmp_path / f'g4-{s}.json', vang_g4(s))}" for s in H.SACH]]
    argv += ["--dong-thuan-g3", *[f"{s}={H.ghi_json(tmp_path / f'dt3-{s}.json', dt_g3(s))}" for s in H.SACH]]
    argv += ["--dong-thuan-g4", *[f"{s}={H.ghi_json(tmp_path / f'dt4-{s}.json', dt_g4(s))}" for s in H.SACH]]
    return argv + ["--ra", str(tmp_path / "datasheet.md")]


def chay(tmp_path, capsys, **kw):
    assert main(dung_argv(tmp_path, **kw)) == 0
    out = capsys.readouterr()
    return (tmp_path / "datasheet.md").read_text(encoding="utf-8"), out


def hang(text, nhan):
    for dong in text.splitlines():
        cot = [c.strip() for c in dong.strip().strip("|").split("|")]
        if cot and cot[0] == nhan:
            return cot
    raise AssertionError(nhan)


def test_chi_so_tu_dong_khop_so_tinh_tay(tmp_path, capsys):
    text, _ = chay(tmp_path, capsys)
    assert "Bộ vàng gồm 3 cuốn; 950 trang; 9 chương, trong đó 6 chương bốc" in text
    a = hang(text, "A")                                                                 # bảng 1: mã, chủ đề, tập, trang, chương, bốc, hash
    assert a[1:6] == ["Toán rời rạc", "phat_trien", "300", "3", "2"]
    # G3 cuốn A: 3 + 1 + 1 + 0 + 1 tranh chấp trạng thái = 6 khái niệm vào kho
    assert "| A | 6 | 3 | 1 | 1 | 0 | 1 | 2 | 1 |" in text
    assert "| B | 5 | 2 | 2 | 0 | 1 | 0 | 0 | 0 |" in text
    assert "Tổng khái niệm vào kho: 15; bị loại: 3; tranh chấp: 1." in text
    assert "| A | 5 | 6 | 4 | 2 | 1 | 3 | 2 |" in text                                   # G4 theo lớp vàng và bao hàm bắc cầu
    assert "| C | 7 | 9 | 7 | 1 | 2 | 1 | 2 |" in text


def test_dong_thuan_va_hash_vang(tmp_path, capsys):
    text, _ = chay(tmp_path, capsys)
    # F1 G3 cuốn A: 16 / (16 + 4) = 0,8; G4 không bắc cầu cuốn B: 24 / 32 = 0,75
    assert "| A | 0,800 | 0,889 | 0,500 |" in text
    assert "| B | 0,500 | 0,750 | 0,500 |" in text
    g3 = hashlib.sha256((tmp_path / "g3-A.json").read_bytes()).hexdigest()
    g4 = hashlib.sha256((tmp_path / "g4-A.json").read_bytes()).hexdigest()
    assert f"| A | `{g3}` | `{g4}` |" in text
    assert f"`{('a' * 64)[:64]}`" in text                                                  # SHA-256 PDF lấy từ manifest


def test_cuon_thieu_g3_hien_gach_ngang_khong_phai_0(tmp_path, capsys):
    text, _ = chay(tmp_path, capsys, bo_g3=("B",))
    assert "| B | — | — | — | — | — | — | — | — |" in text
    assert "Tổng khái niệm vào kho: 10;" in text                                             # 6 + 4, không tính cuốn B


def test_cho_dien_tay_cho_nguoi_gan_an_danh_va_khai_ai(tmp_path, capsys):
    text, _ = chay(tmp_path, capsys)
    for i in range(1, 17):
        assert f"| S{i} | [ĐIỀN TAY] | [ĐIỀN TAY] | [ĐIỀN TAY] | [ĐIỀN TAY] |" in text
    assert "S17" not in text and "S0 " not in text
    for muc in ("Cách tuyển người gán", "Thù lao", "Đồng ý tham gia", "Giới hạn", "Khai việc dùng AI", "Codex", "Claude", "Sonnet"):
        assert muc in text
    # chỉ có mã S1..S16 ở cột người gán: không có dòng nào khác ghi tên người
    assert len(re.findall(r"^\| S\d+ \|", text, flags=re.M)) == 16


def test_man_hinh_va_tep_khong_lo_chuoi_bi_mat_tren_tap_thu(tmp_path, capsys):
    text, out = chay(tmp_path, capsys, tap="thu")
    assert H.SECRET not in text and H.SECRET not in out.out and H.SECRET not in out.err
    dong = out.out.strip().splitlines()
    assert "tap_thu true" in dong and "so_cuon 3" in dong and "so_khai_niem 15" in dong and "so_trang 950" in dong
    for d in dong:
        assert re.fullmatch(r"[a-z_]+ (true|false|null|-?[0-9.]+)", d), d
    assert json.loads((tmp_path / "m-A.json").read_text(encoding="utf-8"))["stats"]["long"]["cau"] == H.SECRET     # chuỗi có thật trong đầu vào
