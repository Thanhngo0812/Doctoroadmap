"""D-04c: lượt C nhận đúng các phiếu lệch nhị phân `can_hoc_truoc` hoặc có nhãn giữ chỗ, không nhận phiếu chỉ lệch nhãn phụ."""
import importlib.util
from pathlib import Path

import pytest


def _load():
    spec = importlib.util.spec_from_file_location("chon_luot_c_d04", Path("scripts/pass-phu-ml/chon_luot_c_d04.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _row(label, reason="vì"):
    return {"nhan": label, "ly_do": reason}


@pytest.mark.parametrize("a, b, expected", [
    (_row("can_hoc_truoc"), _row("kien_thuc_nen"), True),
    (_row("nguoc"), _row("can_hoc_truoc"), True),
    (_row("can_hoc_truoc"), _row("can_hoc_truoc"), False),
    (_row("du_tai_cho"), _row("kien_thuc_nen"), False),
    (_row("khong_tien_quyet"), _row("khong_tien_quyet", "đoạn Y không cho thấy quan hệ"), True),
])
def test_needs_arbitration(a, b, expected):
    assert _load().needs_arbitration(a, b) is expected
