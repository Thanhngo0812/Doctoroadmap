"""`--khop-sach` (D-04): bí danh cắt cụt từ tên chính không còn khớp; tên viết tắt chỉ khớp đúng chữ hoa. Tắt cờ thì giữ hành vi cũ."""
import importlib.util
import sys
from pathlib import Path

import pytest


@pytest.fixture()
def dbc():
    sys.path.insert(0, "src")
    spec = importlib.util.spec_from_file_location("dung_bang_cap_test", Path("scripts/pass-phu-ml/dung_bang_cap.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    yield module
    sys.path.remove("src")


SCIENCE = {"name": "Ý thức khoa học", "aliases": [{"name": "khoa học"}, {"name": "hình thái ý thức khoa học"}]}
OXYGEN = {"name": "Oxy hoà tan", "aliases": [{"name": "DO"}]}


@pytest.mark.parametrize("clean, node, text, expected", [
    (False, SCIENCE, "Các ngành khoa học tự nhiên phát triển.", True),
    (True, SCIENCE, "Các ngành khoa học tự nhiên phát triển.", False),
    (True, SCIENCE, "Ý thức khoa học phản ánh thế giới.", True),
    (True, SCIENCE, "Đây là một hình thái ý thức khoa học.", True),
    (False, OXYGEN, "Cá chết do thiếu oxy.", True),
    (True, OXYGEN, "Cá chết do thiếu oxy.", False),
    (True, OXYGEN, "Chỉ số DO của nước thấp.", True),
])
def test_found(dbc, clean, node, text, expected):
    dbc.CLEAN = clean
    assert dbc.found(dbc.regexes(node), text) is expected
