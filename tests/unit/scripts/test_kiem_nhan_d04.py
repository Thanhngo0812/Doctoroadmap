"""D-04: bộ kiểm định dạng nhãn cạnh ngược bắt từng loại lỗi, và cho tệp hợp lệ qua."""
import importlib.util
import json
from pathlib import Path

import pytest


def _load():
    spec = importlib.util.spec_from_file_location("kiem_nhan_d04", Path("scripts/pass-phu-ml/kiem_nhan_d04.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CARDS = [{"phieu_id": pid, "y": {"cau": [{"i": 0, "text": "a"}, {"i": 1, "text": "b"}]}, "x": {"cau": [{"i": 0, "text": "c"}]}}
         for pid in ("p1", "p2")]
BASE = {"ly_do": "vì", "nguoi_gan": "agent", "luot": "A"}
GOOD = [{"phieu_id": "p1", "nhan": "du_tai_cho", "cau_y": 1, "cau_giai_thich": 0, **BASE},
        {"phieu_id": "p2", "nhan": "khong_tien_quyet", "cau_y": None, **BASE}]


def _check(rows):
    return _load().check(CARDS, [row if isinstance(row, str) else json.dumps(row) for row in rows])


def test_valid_file_passes():
    assert _check(GOOD) == []


@pytest.mark.parametrize("rows, fragment", [
    (["{không phải json", GOOD[1]], "không đọc được"),
    ([{k: v for k, v in GOOD[0].items() if k != "nguoi_gan"}, GOOD[1]], "thiếu trường nguoi_gan"),
    ([{**GOOD[0], "nhan": "can_de_hieu"}, GOOD[1]], "nhãn lạ"),
    ([GOOD[0], GOOD[1], {**GOOD[1], "phieu_id": "p9"}], "không có trong tệp phiếu"),
    ([GOOD[0]], "p2: thiếu nhãn trong lượt A"),
    ([GOOD[0], GOOD[1], GOOD[1]], "2 nhãn trong lượt A"),
    ([{**GOOD[0], "cau_y": 5}, GOOD[1]], "`cau_y` = 5"),
    ([{**GOOD[0], "nhan": "can_hoc_truoc", "cau_giai_thich": None, "cau_y": None}, GOOD[1]], "`cau_y` = None"),
    ([{**GOOD[0], "cau_giai_thich": None}, GOOD[1]], "cần `cau_giai_thich`"),
    ([{**GOOD[0], "cau_giai_thich": 7}, GOOD[1]], "cần `cau_giai_thich`"),
    ([GOOD[0], {**GOOD[1], "cau_giai_thich": 0}], "chỉ dùng cho nhãn du_tai_cho"),
])
def test_each_error_kind_is_caught(rows, fragment):
    errors = _check(rows)
    assert any(fragment in error for error in errors), errors


def test_partial_mode_skips_only_missing_labels():
    module = _load()
    lines = [json.dumps(GOOD[0])]
    assert module.check(CARDS, lines, partial=True) == []
    assert any("thiếu nhãn" in e for e in module.check(CARDS, lines))
    bad = [json.dumps({**GOOD[0], "nhan": "can_de_hieu"})]
    assert any("nhãn lạ" in e for e in module.check(CARDS, bad, partial=True))


def test_two_runs_are_checked_separately():
    run_b = [{**row, "luot": "B"} for row in GOOD]
    assert _check(GOOD + run_b) == []
    assert any("thiếu nhãn trong lượt B" in e for e in _check(GOOD + run_b[:1]))
