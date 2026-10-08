import importlib.util
import json
import sys
from pathlib import Path

import pytest


def _load():
    spec = importlib.util.spec_from_file_location("kiem_nhan_d01", Path("scripts/pass-phu-ml/kiem_nhan_d01.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SHEET = {"phieu_id": "p1", "doc_id": "sach-1", "y_id": "y", "cau": [{"i": 0, "text": "a"}, {"i": 1, "text": "b"}],
         "cau_neo": 1, "ung_vien": [{"x_id": "x1", "trong_cua_so": True}, {"x_id": "x2", "trong_cua_so": False},
                                    {"x_id": "x3", "trong_cua_so": True}]}
GOOD = [
    {"x_id": "x1", "nhan": "can_de_hieu", "cau": 1, "trung_gian": None},
    {"x_id": "x2", "nhan": "khong", "cau": None, "trung_gian": "x1"},
    {"x_id": "x3", "nhan": "khop_nham", "cau": 0, "trung_gian": None},
]


def _run(tmp_path, monkeypatch, rows, *extra):
    (tmp_path / "phieu.jsonl").write_text(json.dumps(SHEET) + "\n", encoding="utf-8")
    lines = [json.dumps({"phieu_id": "p1", "doc_id": "sach-1", "y_id": "y", "ly_do": "vì câu 1",
                         "nguoi_gan": "agent", "luot": "A", **row}) for row in rows]
    (tmp_path / "nhan.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["kiem", "--phieu", str(tmp_path / "phieu.jsonl"),
                                      "--nhan", str(tmp_path / "nhan.jsonl"), *extra])
    return _load().main()


def test_complete_valid_labels_pass(tmp_path, monkeypatch):
    assert _run(tmp_path, monkeypatch, GOOD) == 0


def test_missing_pairs_fail_unless_partial(tmp_path, monkeypatch, capsys):
    assert _run(tmp_path, monkeypatch, GOOD[:2]) == 1
    assert "còn 1 cặp chưa gán" in capsys.readouterr().out
    assert _run(tmp_path, monkeypatch, GOOD[:2], "--mot-phan") == 0


@pytest.mark.parametrize("row, message", [
    ({"x_id": "x9", "nhan": "khong", "cau": None, "trung_gian": None}, "không phải ứng viên"),
    ({"x_id": "x1", "nhan": "can_de_hieu", "cau": None, "trung_gian": None}, "phải có cau"),
    ({"x_id": "x1", "nhan": "cong_cu", "cau": 7, "trung_gian": None}, "không phải chỉ số câu"),
    ({"x_id": "x1", "nhan": "khong", "cau": 0, "trung_gian": None}, "phải để cau = null"),
    ({"x_id": "x2", "nhan": "khop_nham", "cau": None, "trung_gian": None}, "trong_cua_so = true"),
    ({"x_id": "x1", "nhan": "nguoc", "cau": None, "trung_gian": "x2"}, "trung_gian chỉ dùng"),
    ({"x_id": "x1", "nhan": "khong", "cau": None, "trung_gian": "x1"}, "trung_gian chỉ dùng"),
    ({"x_id": "x1", "nhan": "dung", "cau": None, "trung_gian": None}, "nhãn lạ"),
])
def test_each_rule_violation_is_reported(tmp_path, monkeypatch, capsys, row, message):
    assert _run(tmp_path, monkeypatch, [row], "--mot-phan") == 1
    assert message in capsys.readouterr().out


def test_duplicate_long_reason_and_bad_round_are_reported(tmp_path, monkeypatch, capsys):
    rows = [GOOD[0], GOOD[0], {**GOOD[1], "ly_do": " ".join(["từ"] * 31)}, {**GOOD[2], "luot": "Z"}]
    assert _run(tmp_path, monkeypatch, rows, "--mot-phan") == 1
    out = capsys.readouterr().out
    assert "đã gán ở dòng trước" in out and "1 đến 30 từ" in out and "luot phải là" in out
