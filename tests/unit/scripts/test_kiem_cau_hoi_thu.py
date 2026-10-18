"""Script kiểm bộ câu hỏi thử (SA-19): tệp đúng thì ĐẠT; mỗi lỗi cài vào thì báo đúng lỗi. Gói mẫu tự soạn ở lĩnh vực sinh học thực vật."""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

DOC = "sach-mau"


def _load():
    spec = importlib.util.spec_from_file_location("kiem_cau_hoi_thu", Path("scripts/pha-b/kiem_cau_hoi_thu.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")


CHI_TIEU = {"dinh_nghia": 1, "tien_quyet": 0, "so_sanh": 1, "vi_du": 0, "lo_trinh": 0, "ngoai_tai_lieu": 1, "nhieu_luot": 1}


def _goi(root, cau_kiem=None):
    base = root / "goi" / DOC
    base.mkdir(parents=True)
    (base / "thong_tin.json").write_text(json.dumps({"doc_id": DOC, "chi_tieu": CHI_TIEU}), encoding="utf-8")
    _jsonl(base / "module.jsonl", [
        {"module_id": "module_001", "so_thu_tu": 1, "ten": "Quang hợp", "section_code": "1", "khai_niem": ["node_aaaaaa01", "node_aaaaaa02"]},
        {"module_id": "module_002", "so_thu_tu": 2, "ten": "Hô hấp", "section_code": "2", "khai_niem": ["node_aaaaaa03"]},
    ])
    _jsonl(base / "khai_niem.jsonl", [
        {"node_id": "node_aaaaaa01", "ten": "Quang hợp", "bi_danh": [], "module_id": "module_001", "mo_ta": ""},
        {"node_id": "node_aaaaaa02", "ten": "Diệp lục", "bi_danh": [], "module_id": "module_001", "mo_ta": ""},
        {"node_id": "node_aaaaaa03", "ten": "Hô hấp tế bào", "bi_danh": [], "module_id": "module_002", "mo_ta": ""},
    ])
    _jsonl(base / "doan.jsonl", [
        {"chunk_id": "c_aaaaaa01", "trang": 3, "muc": ["1 Quang hợp"], "thu_tu": 1,
         "text": "Quang hợp là quá trình cây dùng năng lượng ánh sáng để tổng hợp chất hữu cơ từ khí cacbonic và nước."},
        {"chunk_id": "c_aaaaaa02", "trang": 4, "muc": ["1 Quang hợp"], "thu_tu": 2,
         "text": "Diệp lục là sắc tố màu lục, hấp thụ ánh sáng đỏ và xanh tím cho quang hợp."},
        {"chunk_id": "c_aaaaaa03", "trang": 9, "muc": ["2 Hô hấp"], "thu_tu": 3,
         "text": "Hô hấp tế bào phân giải chất hữu cơ để giải phóng năng lượng cho cây."},
    ])
    if cau_kiem is not None:
        _jsonl(base / "cau_kiem.jsonl", cau_kiem)


def _row(i, loai, **over):
    row = {"cau_id": f"{DOC}-q{i:03d}", "doc_id": DOC, "loai": loai, "module_dang_mo": "module_001",
           "luot_truoc": [], "cau_hoi": "Quang hợp là gì?", "van_phong": "chuan",
           "khai_niem_ky_vong": ["node_aaaaaa01"], "doan_tham_chieu": ["c_aaaaaa01"], "tra_loi_duoc": True,
           "y_chinh": [{"y": "Cây dùng ánh sáng để tổng hợp chất hữu cơ.", "doan": "c_aaaaaa01"}],
           "kieu_ngoai": None, "da_tim": [], "chua_chac": False, "ghi_chu": "", "nguoi_tao": "agent-thu"}
    row.update(over)
    return row


def good_rows():
    return [
        _row(1, "dinh_nghia"),
        _row(2, "so_sanh", cau_hoi="Hô hấp tế bào ngược với quang hợp ở chỗ nào?", van_phong="than_mat",
             khai_niem_ky_vong=["node_aaaaaa01", "node_aaaaaa03"], doan_tham_chieu=["c_aaaaaa01", "c_aaaaaa03"],
             y_chinh=[{"y": "Một bên tổng hợp, một bên phân giải chất hữu cơ.", "doan": "c_aaaaaa03"}]),
        _row(3, "ngoai_tai_lieu", cau_hoi="Cây xương rồng sống được bao lâu không cần tưới?",
             khai_niem_ky_vong=[], doan_tham_chieu=[], tra_loi_duoc=False, y_chinh=[], kieu_ngoai="gan_chu_de",
             da_tim=["xương rồng", "tưới"]),
        _row(4, "nhieu_luot", luot_truoc=["Diệp lục là gì?"], cau_hoi="Nó hấp thụ ánh sáng màu nào?",
             module_dang_mo="module_002", khai_niem_ky_vong=["node_aaaaaa02"], doan_tham_chieu=["c_aaaaaa02"],
             y_chinh=[{"y": "Ánh sáng đỏ và xanh tím.", "doan": "c_aaaaaa02"}]),
    ]


def _run(tmp_path, monkeypatch, rows, *extra, cau_kiem=None, kiem=None):
    _goi(tmp_path, cau_kiem)
    _jsonl(tmp_path / "cau" / f"{DOC}.jsonl", rows)
    if kiem is not None:
        _jsonl(tmp_path / "kiem" / f"{DOC}.jsonl", kiem)
    monkeypatch.setattr(sys, "argv", ["kiem", "--doc", DOC, "--thu-muc", str(tmp_path), *extra])
    return _load().main()


def test_good_file_passes(tmp_path, monkeypatch, capsys):
    assert _run(tmp_path, monkeypatch, good_rows()) == 0
    out = capsys.readouterr().out
    assert "ĐẠT" in out and "CẢNH BÁO" not in out


def _mutate(index, **over):
    rows = good_rows()
    rows[index] = {**rows[index], **over}
    return rows


@pytest.mark.parametrize("rows, message", [
    (_mutate(0, loai="dinh-nghia"), "loai lạ"),
    (_mutate(0, module_dang_mo="module_009"), "module_dang_mo"),
    (_mutate(0, cau_hoi="Giải thích node_aaaaaa01?"), "mã nội bộ"),
    (_mutate(0, khai_niem_ky_vong=["node_ffffff99"]), "khai_niem_ky_vong có node_id"),
    (_mutate(0, doan_tham_chieu=["c_ffffff99"]), "doan_tham_chieu có chunk_id"),
    (_mutate(0, tra_loi_duoc=False), "tra_loi_duoc phải là true"),
    (_mutate(0, y_chinh=[]), "cần 1–3 ý chính"),
    (_mutate(0, y_chinh=[{"y": "Đúng.", "doan": "c_aaaaaa02"}]), "không nằm trong doan_tham_chieu"),
    (_mutate(0, luot_truoc=["Trước đó?"]), "chỉ nhieu_luot mới có luot_truoc"),
    (_mutate(1, khai_niem_ky_vong=["node_aaaaaa01"]), "so_sanh cần 2–3"),
    (_mutate(2, khai_niem_ky_vong=["node_aaaaaa01"]), "ngoai_tai_lieu phải để khai_niem_ky_vong"),
    (_mutate(2, da_tim=["xương rồng"]), "ít nhất 2 từ"),
    (_mutate(2, kieu_ngoai=None), "kieu_ngoai là"),
    (_mutate(2, tra_loi_duoc=True), "tra_loi_duoc phải là false"),
    (_mutate(3, luot_truoc=[]), "nhieu_luot cần 1–2"),
    (_mutate(0, chua_chac=True), "ghi_chu phải nói"),
    (_mutate(0, nguoi_tao=""), "nguoi_tao rỗng"),
    (_mutate(1, cau_id=f"{DOC}-q001"), "lặp"),
    (_mutate(1, cau_hoi="Quang hợp là gì?", loai="dinh_nghia", khai_niem_ky_vong=["node_aaaaaa01"]), "trùng"),
    (_mutate(0, cau_id="q1"), "cau_id phải có dạng"),
    ([{k: v for k, v in good_rows()[0].items() if k != "van_phong"}, *good_rows()[1:]], "thiếu trường"),
])
def test_each_planted_error_is_reported(tmp_path, monkeypatch, capsys, rows, message):
    assert _run(tmp_path, monkeypatch, rows) == 1
    assert message in capsys.readouterr().out


def test_quota_shortfall_fails_unless_partial_and_excess_always_fails(tmp_path, monkeypatch, capsys):
    assert _run(tmp_path, monkeypatch, good_rows()[:3]) == 1
    assert "nhieu_luot có 0, còn thiếu 1" in capsys.readouterr().out
    (tmp_path / "goi").rename(tmp_path / "goi-cu")
    assert _run(tmp_path, monkeypatch, good_rows()[:3], "--mot-phan") == 0
    capsys.readouterr()
    (tmp_path / "goi").rename(tmp_path / "goi-cu-2")
    extra = _row(5, "dinh_nghia", cau_hoi="Diệp lục là gì?", khai_niem_ky_vong=["node_aaaaaa02"],
                 doan_tham_chieu=["c_aaaaaa02"], y_chinh=[{"y": "Sắc tố màu lục.", "doan": "c_aaaaaa02"}])
    assert _run(tmp_path, monkeypatch, [*good_rows(), extra], "--mot-phan") == 1
    assert "vượt 1" in capsys.readouterr().out


def test_outside_term_found_in_book_and_verbatim_copy_only_warn(tmp_path, monkeypatch, capsys):
    rows = _mutate(2, da_tim=["xương rồng", "diệp lục"])
    rows[0] = {**rows[0], "cau_hoi": "Vì sao quá trình cây dùng năng lượng ánh sáng để tổng hợp chất hữu cơ từ khí cacbonic?"}
    assert _run(tmp_path, monkeypatch, rows) == 0
    out = capsys.readouterr().out
    assert "'diệp lục' CÓ trong tài liệu" in out
    assert "chép nguyên văn" in out


def test_check_items_must_be_filled_without_editing_given_fields(tmp_path, monkeypatch, capsys):
    given = [{"cau_id": f"{DOC}-k01", "loai": "dinh_nghia", "module_dang_mo": "module_002",
              "luot_truoc": [], "cau_hoi": "Hô hấp tế bào làm gì?"}]
    filled = _row(1, "dinh_nghia", cau_id=f"{DOC}-k01", module_dang_mo="module_002", cau_hoi="Hô hấp tế bào làm gì?",
                  khai_niem_ky_vong=["node_aaaaaa03"], doan_tham_chieu=["c_aaaaaa03"],
                  y_chinh=[{"y": "Phân giải chất hữu cơ để lấy năng lượng.", "doan": "c_aaaaaa03"}])
    assert _run(tmp_path, monkeypatch, good_rows(), cau_kiem=given, kiem=[]) == 1
    assert "còn 1 câu kiểm chưa điền" in capsys.readouterr().out
    (tmp_path / "goi").rename(tmp_path / "goi-cu")
    assert _run(tmp_path, monkeypatch, good_rows(), cau_kiem=given, kiem=[{**filled, "cau_hoi": "Sửa đề?"}]) == 1
    assert "không được sửa trường cau_hoi" in capsys.readouterr().out
    (tmp_path / "goi").rename(tmp_path / "goi-cu-2")
    assert _run(tmp_path, monkeypatch, good_rows(), cau_kiem=given, kiem=[filled]) == 0
