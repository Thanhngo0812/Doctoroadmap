"""Bảng giải thích (phần B): hệ số logistic chuẩn hoá và độ quan trọng gain của LightGBM đã chọn, 10 đặc trưng đầu mỗi mô hình. Ghi `tmp/dg20/giai-thich.json`.
Logistic học trên đủ 16 cuốn với `C` là giá trị được chọn nhiều nhất trong 16 lần chia LOBO."""
import json
import statistics
import sys
import warnings

import numpy as np

import chung
import logistic

warnings.filterwarnings("ignore")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ket_qua = {}
    for ten in ("m1", "m2", "m3"):
        data, features = chung.nap(ten)
        x, y = chung.noi(data, sorted(data))
        chon_c = [json.loads(d)["c"] for d in (chung.ra() / f"logistic-{ten}.jsonl").read_text(encoding="utf-8").splitlines()]
        c = statistics.mode(chon_c)
        mo = logistic.mo_hinh(c).fit(x, y)
        he_so = mo[-1].coef_[0]
        ten_cot = list(features) + [f"thieu_{features[i]}" for i in mo[0].indicator_.features_] if hasattr(mo[0], "indicator_") and mo[0].indicator_ is not None else list(features)
        ten_cot = ten_cot[:len(he_so)]
        top_lr = sorted(zip(ten_cot, he_so), key=lambda t: -abs(t[1]))[:10]
        manifest = json.loads((chung.ra() / "mo-hinh-moi" / f"{ten}-chon" / "manifest.json").read_text(encoding="utf-8"))
        ket_qua[ten] = {"c": c, "logistic_top10": [(n, round(float(h), 4)) for n, h in top_lr], "gain_top10": manifest["gain"][:10],
                        "trung_top10": sorted({n for n, _ in top_lr} & {n for n, _ in manifest["gain"][:10]})}
        print(ten, json.dumps(ket_qua[ten], ensure_ascii=False))
    (chung.ra() / "giai-thich.json").write_text(json.dumps(ket_qua, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
