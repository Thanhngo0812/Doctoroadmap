"""Tự kiểm sau khi đóng băng vào `vendor/`: nạp ba mô hình qua ĐÚNG đường nạp của sản phẩm, chấm một bảng nhỏ, so với điểm của mô hình học lại độc lập từ cấu hình đã chọn.
- A1: `NheParser(model_dir=vendor/a1-nhe)` (kiểm băm và phiên bản trong `__init__`), `joblib.load` như `parse`, chấm 600 dòng cuối của d01-16 (M1) và toàn bộ dòng cặp d01-16 (M2).
- A8: `LightGBMSecondaryScorer()` mặc định (đọc `vendor/a8-pass-phu-ml`, kiểm băm, thứ tự 82 đặc trưng), chấm 600 dòng đầu của bảng M3 với ô thiếu để trống, rồi `calibrate`.
Độ lệch tối đa phải ≤ 1e-9. Chạy: DG20_GOC=<thư mục chung> tmp/venv-ml/Scripts/python.exe scripts/dg20/tu_kiem_san_pham.py
"""
import json
import sys

import joblib
import numpy as np

import chung

sys.path.append(str(chung.goc() / ".venv/Lib/site-packages"))  # pypdfium2 cho nhe_parser, sau site-packages của venv-ml
sys.path.insert(0, str(chung.WORKTREE / "src"))
from doc2roadmap.domain.secondary_features import FEATURE_NAMES  # noqa: E402
from doc2roadmap.infrastructure.parsing.nhe_parser import NheParser  # noqa: E402
from doc2roadmap.infrastructure.secondary_model import LightGBMSecondaryScorer  # noqa: E402


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    vendor = chung.WORKTREE / "vendor"
    parser = NheParser(model_dir=vendor / "a1-nhe")
    ket_qua = {"a1_pipeline_config": parser.pipeline_config}
    for ten, tep, tai in (("m1", "heading.joblib", chung.m1_data), ("m2", "join.joblib", chung.m2_data)):
        data, _ = tai()
        la = {"m1": 7, "m2": 15}[ten]
        vong = {"m1": 343, "m2": 126}[ten]
        x16, _ = data["d01-16"]
        x16 = x16[-600:]
        san_pham = joblib.load(vendor / "a1-nhe" / tep).predict_proba(x16)[:, 1]
        x, y = chung.noi(data, sorted(data))
        doc_lap = chung.lgbm(ten, la, vong, ).set_params(n_jobs=2).fit(x, y).predict_proba(x16)[:, 1]
        ket_qua[ten] = {"so_dong": int(len(x16)), "lech_toi_da": float(np.abs(san_pham - doc_lap).max())}
    data, features = chung.nap("m3")
    assert list(features) == list(FEATURE_NAMES)
    scorer = LightGBMSecondaryScorer()
    x, y = chung.noi(data, sorted(data))
    hang = x[:600]
    dong = [{n: ("" if np.isnan(v) else float(v)) for n, v in zip(FEATURE_NAMES, r)} for r in hang]
    diem = np.asarray(scorer.score(dong))
    doc_lap = chung.lgbm("m3", 7, 251).fit(chung.cho_lgbm("m3", x), y).predict_proba(chung.cho_lgbm("m3", hang))[:, 1]
    xs = np.asarray(scorer.calibrate(diem))
    ket_qua["m3"] = {"so_dong": 600, "lech_toi_da": float(np.abs(diem - doc_lap).max()), "phien_ban": scorer.metadata["version"],
                     "xac_suat_hieu_chinh_trung_binh": float(xs.mean()), "ti_le_duong_hoc": float(y.mean())}
    ket_qua["dat"] = all(ket_qua[m]["lech_toi_da"] <= 1e-9 for m in ("m1", "m2", "m3"))
    (chung.ra() / "tu-kiem-san-pham.json").write_text(json.dumps(ket_qua, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(ket_qua, ensure_ascii=False, indent=1))
    assert ket_qua["dat"], "điểm sản phẩm lệch mô hình học lại"


if __name__ == "__main__":
    main()
