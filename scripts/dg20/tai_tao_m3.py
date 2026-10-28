"""Kiểm tái tạo M3: học lại với đúng cấu hình hiện tại trên đúng dữ liệu, so với `vendor/a8-pass-phu-ml` (SHA-256 mô hình và dự đoán trên mọi dòng học)."""
import hashlib
import json
import sys

import lightgbm as lgb
import numpy as np

import chung

PARAMS = dict(n_estimators=300, learning_rate=0.03, num_leaves=15, min_child_samples=20, subsample=0.8, subsample_freq=1,
              colsample_bytree=0.8, reg_lambda=1.0, is_unbalance=True, random_state=20261005, verbose=-1)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    vendor = chung.goc() / "vendor/a8-pass-phu-ml"
    manifest = json.loads((vendor / "manifest.json").read_text(encoding="utf-8"))
    features = manifest["dac_trung"]
    data = chung.m3_data()
    x = data[features].apply(lambda c: c).fillna(manifest["gia_tri_thieu"]).to_numpy()
    model = lgb.LGBMClassifier(n_jobs=chung.THREADS, **PARAMS).fit(x, data.nhan.to_numpy())
    text = model.booster_.model_to_string()
    default = " ".join(f"Column_{i}" for i in range(len(features)))
    text = text.replace("feature_names=" + default, "feature_names=" + " ".join(features))
    sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    vendor_text = (vendor / "model.txt").read_bytes()
    booster = lgb.Booster(model_file=str(vendor / "model.txt"))
    old = booster.predict(x)
    new = model.predict_proba(x)[:, 1]
    diff = float(np.abs(old - new).max())
    out = {"sha256_moi": sha, "sha256_vendor": hashlib.sha256(vendor_text).hexdigest(), "trung_sha": sha == hashlib.sha256(vendor_text).hexdigest(),
           "sai_lech_du_doan_toi_da": diff, "dong": int(len(data)), "dat": diff <= 1e-9,
           "thu_vien": {"lightgbm": lgb.__version__, "numpy": np.__version__}}
    (chung.ra() / "tai-tao-m3.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
