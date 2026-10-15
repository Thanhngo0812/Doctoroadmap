"""D-04a: phần thuần của bộ xuất phiếu cạnh ngược — bỏ sách T-01, phiếu không lộ khoá, lấy mẫu có trần và tất định, phiếu lặp."""
import importlib.util
import json
import random
from pathlib import Path


def _load():
    spec = importlib.util.spec_from_file_location("xuat_phieu_d04", Path("scripts/pass-phu-ml/xuat_phieu_d04.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _pair(x, y, same=True, **extra):
    block = {"ten": x, "bi_danh": [], "muc": ["Chương 1"], "cau": [{"i": 0, "text": "a"}], "cau_neo": 0}
    return {"x": x, "y": y, "x_block": block, "y_block": {**block, "ten": y, "cau_co_ten_x": [0]}, "cung_chuong": same,
            "so_muc_giua": 2, **extra}


def test_holdout_docs_are_the_test_split():
    module = _load()
    manifest = {"books": [{"id": "d01-01", "split": "train"}, {"id": "d01-t01", "split": "test"}, {"id": "gia-t99", "split": "test"}]}
    assert module.holdout_docs(manifest) == {"d01-t01", "gia-t99"}


def test_card_does_not_leak_key_fields():
    module = _load()
    secret = "BI-MAT-KHOA-7f3a"
    pair = _pair("x1", "y1", nguon=1, he=[secret], pass_=[secret], confidence=0.123456, nhan_d01=secret, p_e5=0.987654,
                 e5_de_xuat=True)
    pair["pass"] = [secret]
    text = json.dumps(module.card("doc-4", "Khoa học xã hội", pair), ensure_ascii=False)
    assert secret not in text and "0.123456" not in text and "0.987654" not in text
    assert "doc-4" not in text
    assert "cung_chuong" not in text and "so_muc_giua" not in text
    key = module.key_row("doc-4", pair, module.card("doc-4", "Khoa học xã hội", pair))
    assert key["he"] == [secret] and key["nhan_d01"] == secret and key["doc_id"] == "doc-4"


def test_sampling_caps_balances_and_is_deterministic():
    module = _load()
    pairs = [_pair(f"x{i}", "y", same=i % 4 == 0) for i in range(200)]  # 50 cùng chương, 150 khác chương
    first = module.sample_pairs(pairs, 60, "s")
    assert len(first) == 60
    assert sum(p["cung_chuong"] for p in first) == 30
    assert first == module.sample_pairs(list(reversed(pairs)), 60, "s")
    few_same = [_pair(f"x{i}", "y", same=i < 5) for i in range(100)]
    chosen = module.sample_pairs(few_same, 60, "s")
    assert len(chosen) == 60 and sum(p["cung_chuong"] for p in chosen) == 5
    assert len(module.sample_pairs(pairs[:10], 60, "s")) == 10


def test_repeats_reorder_blocks_and_point_to_original():
    module = _load()
    items = [("d01-01", "Toán", _pair(f"x{i}", f"y{i}")) for i in range(40)]
    cards, keys = module.with_repeats(items, 0.05, random.Random(1))
    repeats = [k for k in keys if k["lap_cua"]]
    assert len(cards) == 42 and len(repeats) == 2
    by_id = {c["phieu_id"]: c for c in cards}
    for key in repeats:
        repeat, original = by_id[key["phieu_id"]], by_id[key["lap_cua"]]
        assert key["phieu_id"] != key["lap_cua"]
        assert list(repeat).index("x") < list(repeat).index("y")
        assert list(original).index("y") < list(original).index("x")
        assert repeat["x"] == original["x"] and repeat["y"] == original["y"]
    assert len({c["phieu_id"] for c in cards}) == len(cards)
