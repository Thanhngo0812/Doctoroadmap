"""Bộ khớp tên theo ranh giới từ của pass phụ ML (`dung_bang_cap.found_words`) phải khớp cả tên có âm tiết giữa từ ghép tận cùng bằng "y"
(quy luật, tỷ lệ, lý thuyết, mức ý nghĩa): phép đổi y→i của `_mention_normalize` phải áp như nhau cho tên và cho câu đã tách từ."""
import importlib.util
import sys
from pathlib import Path

import pytest

pytest.importorskip("underthesea")


def _load():
    if "src" not in sys.path:
        sys.path.insert(0, "src")
    spec = importlib.util.spec_from_file_location("dung_bang_cap", Path("scripts/pass-phu-ml/dung_bang_cap.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("name, sentence", [
    ("Quy luật", "Quy luật tự nhiên là những quy luật nẩy sinh trong giới tự nhiên."),
    ("Tỷ lệ", "Tỷ lệ mẫu được ký hiệu là f."),
    ("Lý thuyết", "Lý thuyết xác suất nghiên cứu các hiện tượng ngẫu nhiên."),
    ("Mức ý nghĩa", "Ta chọn mức ý nghĩa bằng 0,05."),
])
def test_ten_co_am_tiet_y_giua_tu_ghep_van_khop(name, sentence):
    dbc = _load()
    node = {"name": name}
    assert dbc.found(dbc.regexes(node), sentence)
    assert dbc.found_words(dbc.word_regexes(node), sentence)


def test_ten_mot_am_tiet_van_khong_khop_vao_giua_tu_ghep():
    dbc = _load()
    assert not dbc.found_words(dbc.word_regexes({"name": "Chất"}), "Thế giới vật chất tồn tại khách quan.")
