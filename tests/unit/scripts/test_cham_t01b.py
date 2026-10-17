"""Script chấm T-01b chỉ được in trường số trong allowlist: chuỗi bí mật cài trong trường lồng, kể cả dưới khoá được phép, không lọt ra."""
import importlib.util
import json
from pathlib import Path

SECRET = "TEN-KHAI-NIEM-BI-MAT"


def _load():
    spec = importlib.util.spec_from_file_location("cham_t01b", Path("scripts/t01/cham_t01b.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _row():
    return {
        "v3": {"Q7": 0.5, "graph_version": 3, "canh_vang": 69, "Q6": SECRET,  # chuỗi dưới khoá được phép
               "bao_dong_dem": {"dung": 4, "vang": 9, "ghi_chu": SECRET},  # khoá lạ lồng trong khoá được phép
               "inputs": [SECRET], "graph": f"artifacts/graph/{SECRET}/v1"},  # khoá lạ ở mức một
        "gop": {"tu_choi_cham": True, "khai_niem_vang_khong_quy_duoc": 2, "loi": {"message": SECRET}},
        "dich_cung_trang_thai": 40,
        "warnings": [SECRET],
    }


def test_allow_keeps_numbers_and_drops_every_string():
    module = _load()
    out = json.dumps(module.allow(_row()), ensure_ascii=False)
    assert SECRET not in out
    kept = json.loads(out)
    assert kept == {"v3": {"Q7": 0.5, "graph_version": 3, "canh_vang": 69, "bao_dong_dem": {"dung": 4, "vang": 9}},
                    "gop": {"tu_choi_cham": True, "khai_niem_vang_khong_quy_duoc": 2}, "dich_cung_trang_thai": 40}


def test_naive_dump_would_leak_the_secret():
    # Bằng chứng test trên bắt được lỗi thật: in nguyên dict (bản ngây thơ) thì lộ chuỗi bí mật.
    assert SECRET in json.dumps(_row(), ensure_ascii=False)


def test_main_refuses_documents_outside_t01(monkeypatch, capsys):
    module = _load()
    monkeypatch.setattr("sys.argv", ["cham_t01b.py", "doc-1", "1", "2"])
    try:
        module.main()
    except SystemExit as error:
        assert "d01-t01" in str(error)
    else:
        raise AssertionError("phải từ chối tài liệu ngoài T-01")
    assert capsys.readouterr().out == ""
