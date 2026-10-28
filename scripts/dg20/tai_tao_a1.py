"""Kiểm tái tạo M1, M2: học lại với đúng cấu hình hiện tại trên 16 cuốn học, so với `vendor/a1-nhe` (SHA-256 tệp joblib và dự đoán trên mọi dòng học)."""
import hashlib
import io
import json
import sys

import joblib
import numpy as np
from lightgbm import LGBMClassifier

import chung

CONFIG = {
    "m1": dict(n_estimators=300, num_leaves=15, learning_rate=0.05, min_child_samples=30),
    "m2": dict(n_estimators=150, num_leaves=7, min_child_samples=10, learning_rate=0.05),
}
VENDOR = {"m1": "heading.joblib", "m2": "join.joblib"}


def fit(name, x, y):
    return LGBMClassifier(**CONFIG[name], class_weight="balanced", random_state=42, n_jobs=2, verbosity=-1,
                          deterministic=True, force_col_wise=True).fit(x, y)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    result = {}
    for name, loader in (("m1", chung.m1_data), ("m2", chung.m2_data)):
        data, _ = loader()
        books = sorted(data)
        x = np.concatenate([data[k][0] for k in books])
        y = np.concatenate([data[k][1] for k in books])
        model = fit(name, x, y)
        buffer = io.BytesIO()
        joblib.dump(model, buffer)
        vendor_path = chung.goc() / "vendor/a1-nhe" / VENDOR[name]
        vendor = joblib.load(vendor_path)
        diff = float(np.abs(vendor.predict_proba(x)[:, 1] - model.predict_proba(x)[:, 1]).max())
        result[name] = {"dong_hoc": int(len(y)), "sach": len(books), "ti_le_duong": float(y.mean()),
                        "sha256_moi": hashlib.sha256(buffer.getvalue()).hexdigest(),
                        "sha256_vendor": hashlib.sha256(vendor_path.read_bytes()).hexdigest(),
                        "sai_lech_du_doan_toi_da": diff, "dat": diff <= 1e-9}
        print(name, json.dumps(result[name]), flush=True)
    (chung.ra() / "tai-tao-a1.json").write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
