"""Vé 18a: đóng băng mô hình E5 (lượt `e5-d01-a`) cho pass phụ không LLM của sản phẩm.

Học lại đúng như `thi_nghiem_e5.py` với nhãn lượt A, mọi phiếu, seed gốc 20261005:
- mô hình cuối học trên toàn bộ dòng D-01;
- bộ hiệu chỉnh isotonic học trên dự đoán ngoài mẫu chia theo sách.
Ghi ra thư mục mô hình (mặc định `vendor/a8-pass-phu-ml`):
- `model.txt`: định dạng văn bản của LightGBM;
- `manifest.json`: danh sách đặc trưng theo thứ tự, giá trị thay ô thiếu, bộ hiệu chỉnh (hai mảng điểm và xác suất, nội suy tuyến tính, kẹp hai đầu),
  nguồn nhãn, AP ngoài mẫu, băm SHA-256 của `model.txt`.
Sau đó tự kiểm: nạp lại bằng LightGBM thuần, chấm bảng của bốn tài liệu cũ, so với điểm và ngưỡng đã lưu của `e5-d01-a`; và tệp ra không chứa tên
khái niệm nào của D-01 hay bốn tài liệu cũ.
Cần `tmp/pass-phu-ml/bang-d01` và `tmp/pass-phu-ml/bang` (chỉ Claude có). Chạy bằng tmp/venv-ml:
  tmp/venv-ml/Scripts/python.exe scripts/pass-phu-ml/dong_bang_e5.py [--ra=vendor/a8-pass-phu-ml]
"""
import hashlib
import json
import sys
from datetime import date
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression

sys.path.insert(0, str(Path(__file__).resolve().parent))
import thi_nghiem_e5 as e5  # noqa: E402  (thêm --tach-tu --khong-main vào sys.argv như lượt gốc)

e2b = e5.e2b
VERSION = "e5-d01-a-v1"
MISSING = -1.0


def train():
    old, old_features = e2b.load(e5.OLD_DOCS, "y-dinh-cung")
    data = e5.load_d01("a", False, 1.0, None, "tmp/d01-gan-nhan/nhan-A-gop.jsonl")
    features = [c for c in old_features if c in data.columns]
    data[features] = data[features].apply(pd.to_numeric, errors="coerce")
    oof = np.zeros(len(data))
    for book in sorted(data.doc.unique()):
        mask = (data.doc == book).to_numpy()
        _, oof[mask] = e2b.fit_predict("lightgbm", data[~mask], data[mask], features)
    calibrator = IsotonicRegression(out_of_bounds="clip").fit(oof, data.nhan.to_numpy())
    model, _ = e2b.fit_predict("lightgbm", data, data.head(1), features)
    return old, data, features, calibrator, model


def calibrate(manifest, scores):
    table = manifest["hieu_chinh"]
    return np.interp(scores, table["diem"], table["xac_suat"])


def check(out, old, names):
    """Nạp lại từ tệp, chấm bảng bốn tài liệu cũ, so với lượt `e5-d01-a` đã lưu."""
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    model_bytes = (out / "model.txt").read_bytes()
    assert hashlib.sha256(model_bytes).hexdigest() == manifest["sha256_model"], "băm model.txt lệch"
    booster = lgb.Booster(model_file=str(out / "model.txt"))
    assert booster.feature_name() == manifest["dac_trung"], "thứ tự đặc trưng lệch"
    saved = json.loads(Path("tmp/pass-phu-ml/diem/e5-d01-a/nguong.json").read_text(encoding="utf-8"))
    worst = 0.0
    for doc in e5.OLD_DOCS:
        data = old[old.doc == doc]
        scores = booster.predict(data[manifest["dac_trung"]].fillna(manifest["gia_tri_thieu"]).to_numpy())
        scores = np.where(data.ung_vien == 1, scores, 0.0)
        reference = pd.read_csv(f"tmp/pass-phu-ml/diem/e5-d01-a/{doc}.csv")
        assert list(reference.pair_id) == list(data.pair_id) and list(reference.x) == list(data.x), f"{doc}: thứ tự dòng lệch"
        worst = max(worst, float(np.abs(reference.score.to_numpy() - scores).max()))
        asked = np.sort(scores[((data.ung_vien == 1) & data.status.isin(e2b.ASKED)).to_numpy()])[::-1]
        expected = int(round(float(calibrate(manifest, asked).sum())))
        threshold = float(asked[max(0, expected - 1)]) if len(asked) and expected else 1.0
        row = saved["tai_lieu"][doc]
        assert expected == row["so_duong_uoc_luong"], f"{doc}: số dương ước lượng {expected} ≠ {row['so_duong_uoc_luong']}"
        assert abs(threshold - row["nguong_hieu_chinh"]) <= 1e-9, f"{doc}: ngưỡng hiệu chỉnh lệch"
        print(f"  {doc:12s} số dương ước lượng {expected}, ngưỡng {threshold:.6f}: khớp")
    assert worst <= 1e-9, f"điểm lệch tối đa {worst}"
    text = (out / "manifest.json").read_text(encoding="utf-8") + model_bytes.decode("utf-8")
    # Chữ có sẵn trong mọi tệp LightGBM (tên tham số như "parser") không phải rò rỉ: dò trên một mô hình giả học từ dữ liệu ngẫu nhiên.
    rng = np.random.default_rng(0)
    dummy = lgb.LGBMClassifier(n_estimators=2, verbose=-1).fit(rng.random((50, 2)), rng.integers(0, 2, 50)).booster_.model_to_string()
    leaked = sorted(name for name in names if len(name) >= 4 and name in text and name not in dummy)
    assert not leaked, f"tệp chứa tên khái niệm: {leaked[:5]}"
    print(f"  điểm lệch tối đa {worst:.2e}; không tệp nào chứa tên khái niệm ({len(names)} tên đã dò)")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    options = dict(arg[2:].split("=", 1) for arg in sys.argv[1:] if arg.startswith("--") and "=" in arg)
    out = Path(options.get("ra", "vendor/a8-pass-phu-ml"))
    out.mkdir(parents=True, exist_ok=True)
    old, data, features, calibrator, model = train()
    # Mô hình học trên mảng numpy nên tên cột trong tệp là Column_i; thay bằng tên thật để bản cài kiểm được thứ tự đặc trưng.
    booster = model.booster_
    default = [f"Column_{i}" for i in range(len(features))]
    assert booster.feature_name() == default
    text = booster.model_to_string()
    assert text.count("feature_names=" + " ".join(default)) == 1
    text = text.replace("feature_names=" + " ".join(default), "feature_names=" + " ".join(features))
    (out / "model.txt").write_text(text, encoding="utf-8", newline="\n")
    manifest = {
        "phien_ban": VERSION,
        "ngay_hoc": date.today().isoformat(),
        "nguon_nhan": "D-01 lượt A (nhan-A-gop), nhãn dương can_de_hieu, dòng loai=thuc và trong_cua_so=1",
        "mo_hinh": "LightGBM 4.7.0, tham số như thi_nghiem_e2b.make_model, seed 20261005",
        "dong_hoc": int(len(data)), "sach_hoc": int(data.doc.nunique()), "ti_le_duong": round(float(data.nhan.mean()), 4),
        "ap_ngoai_mau_theo_sach_trung_vi": float(np.median(list(json.loads(
            Path("tmp/pass-phu-ml/diem/e5-d01-a/nguong.json").read_text(encoding="utf-8"))["ap_ngoai_mau_theo_sach"].values()))),
        "dac_trung": features,
        "gia_tri_thieu": MISSING,
        "hieu_chinh": {"cach": "isotonic trên dự đoán ngoài mẫu chia theo sách; nội suy tuyến tính, kẹp hai đầu",
                       "diem": [float(v) for v in calibrator.X_thresholds_], "xac_suat": [float(v) for v in calibrator.y_thresholds_]},
        "nguong": "k = round(tổng xác suất hiệu chỉnh trên ứng viên); ngưỡng = điểm của ứng viên thứ k theo điểm giảm dần; k = 0 thì không tạo cạnh",
        "sha256_model": hashlib.sha256((out / "model.txt").read_bytes()).hexdigest(),
    }
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"đã ghi {out}: {len(features)} đặc trưng, {len(data)} dòng học, {len(calibrator.X_thresholds_)} mốc hiệu chỉnh")
    names = set()
    for frame in (data, old):
        for column in ("ten_x", "ten_y"):
            if column in frame.columns:
                names |= set(frame[column].dropna().astype(str))
    assert names, "không đọc được tên khái niệm nào để dò rò rỉ"
    check(out, old, names)
    return 0


if __name__ == "__main__":
    sys.exit(main())
