"""D-04d: nhãn đa số dùng lượt C chỉ khi A, B lệch; nhãn giữ chỗ không được tính là phiếu bầu; độ chính xác và độ phủ đếm đúng."""
import importlib.util
from pathlib import Path

import pytest


def _load():
    spec = importlib.util.spec_from_file_location("do_luat_d04", Path("scripts/pass-phu-ml/do_luat_d04.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _row(label, reason="vì"):
    return {"nhan": label, "ly_do": reason}


HOLD = "đoạn Y không cho thấy quan hệ"


@pytest.mark.parametrize("a, b, c, expected", [
    (_row("can_hoc_truoc"), _row("can_hoc_truoc"), None, True),
    (_row("du_tai_cho"), _row("kien_thuc_nen"), None, False),
    (_row("can_hoc_truoc"), _row("kien_thuc_nen"), _row("kien_thuc_nen"), False),
    (_row("can_hoc_truoc"), _row("kien_thuc_nen"), _row("can_hoc_truoc"), True),
    (_row("can_hoc_truoc"), _row("khong_tien_quyet", HOLD), _row("can_hoc_truoc"), True),
    (_row("can_hoc_truoc"), _row("khong_tien_quyet", HOLD), _row("kien_thuc_nen"), None),
    (_row("can_hoc_truoc"), _row("kien_thuc_nen"), None, None),
])
def test_majority(a, b, c, expected):
    assert _load().majority(a, b, c) is expected


def test_measure_counts_precision_and_recall():
    module = _load()
    keys = [{"phieu_id": f"p{i}", "cung_chuong": i < 4} for i in range(8)]
    labels = {"p0": True, "p1": True, "p2": False, "p3": False, "p4": True, "p5": False, "p6": False, "p7": None}
    row = module.measure(keys, labels, lambda k: k["cung_chuong"])
    assert (row["n"], row["giu_cung"], row["dung"], row["can_hoc_truoc"]) == (7, 4, 2, 3)
    assert row["chinh_xac"] == 0.5 and row["do_phu"] == pytest.approx(2 / 3)
    assert row["wilson"][0] < 0.5 < row["wilson"][1]
    assert not module.passes(row)
    assert module.passes({"chinh_xac": 0.9, "wilson": [0.65, 0.97], "do_phu": 0.4})
    assert not module.passes({"chinh_xac": 0.9, "wilson": [0.55, 0.97], "do_phu": 0.4})
