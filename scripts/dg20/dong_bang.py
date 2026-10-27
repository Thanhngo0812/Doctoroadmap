"""Đóng băng mô hình mới (phần A bước 8-9) vào `tmp/dg20/mo-hinh-moi/<mô hình>/` — KHÔNG ghi đè `vendor/`.

Cấu hình = số lá được luật một SE chọn (`chon-<mô hình>.json`), số vòng = trung vị số vòng tốt nhất của 16 lần chia. Học trên đủ 16 cuốn.
M3: bộ hiệu chỉnh isotonic học trên dự đoán ngoài mẫu theo cuốn (LOBO với cấu hình đã chọn), như `dong_bang_e5.py`; định dạng `model.txt` +
`manifest.json` giống `vendor/a8-pass-phu-ml`. M1, M2: tệp joblib giống `vendor/a1-nhe`.
  tmp/venv-ml/Scripts/python.exe scripts/dg20/dong_bang.py m3 [--so-la=<n>]
`--so-la` ghi đè số lá (để đóng băng cấu hình hiện tại làm mốc so sánh); không có thì lấy theo luật một SE.
"""
import hashlib
import io
import json
import statistics
import sys
from datetime import date

import joblib
import lightgbm as lgb
import numpy as np
import sklearn
from sklearn.isotonic import IsotonicRegression

import chung
from danhgia.hoc_lai.chia import lobo


def oof_theo_cuon(mo_hinh, data, cuon, so_la, so_vong):
    """Dự đoán ngoài mẫu: với mỗi cuốn, học trên các cuốn khác trong `cuon` (số vòng cố định) rồi chấm cuốn đó."""
    ket_qua = {}
    for de_ra in cuon:
        x, y = chung.noi(data, [c for c in cuon if c != de_ra])
        mo = chung.lgbm(mo_hinh, so_la, so_vong).fit(chung.cho_lgbm(mo_hinh, x), y)
        ket_qua[de_ra] = mo.predict_proba(chung.cho_lgbm(mo_hinh, data[de_ra][0]))[:, 1]
    return ket_qua


def hieu_chinh_long(mo_hinh, data, so_la, so_vong, trong_mau=False):
    """Bộ hiệu chỉnh thật theo từng cuốn để ra: học isotonic trên 15 cuốn còn lại (ngoài mẫu theo cuốn, hay `trong_mau` = phép phá), rồi áp lên cuốn đó.
    Trả {cuốn: {ap_hieu_chinh, so_duong_uoc_luong, so_duong_that}}."""
    ket_qua = {}
    for de_ra, hoc in lobo(sorted(data)):
        x, y = chung.noi(data, hoc)
        if trong_mau:
            mo_hinh_trong = chung.lgbm(mo_hinh, so_la, so_vong).fit(chung.cho_lgbm(mo_hinh, x), y)
            diem = mo_hinh_trong.predict_proba(chung.cho_lgbm(mo_hinh, x))[:, 1]
            truoc = mo_hinh_trong
        else:
            oof = oof_theo_cuon(mo_hinh, data, hoc, so_la, so_vong)
            diem = np.concatenate([oof[c] for c in hoc])
            truoc = chung.lgbm(mo_hinh, so_la, so_vong).fit(chung.cho_lgbm(mo_hinh, x), y)
        iso = IsotonicRegression(out_of_bounds="clip").fit(diem, y)
        xr, yr = data[de_ra]
        p = truoc.predict_proba(chung.cho_lgbm(mo_hinh, xr))[:, 1]
        ket_qua[de_ra] = {"ap_hieu_chinh": chung.ap(yr, iso.predict(p)), "so_duong_uoc_luong": float(iso.predict(p).sum()), "so_duong_that": int(yr.sum())}
        print("hiệu chỉnh", de_ra, ket_qua[de_ra], flush=True)
    return ket_qua


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    mo_hinh = sys.argv[1]
    options = dict(a[2:].split("=", 1) for a in sys.argv[2:] if a.startswith("--") and "=" in a)
    chon = json.loads((chung.ra() / f"chon-{mo_hinh}.json").read_text(encoding="utf-8"))
    so_la = int(options.get("so-la", chon["chon"]["chon"]))
    so_vong = int(round(chon["trung_vi_so_vong"][str(so_la)]))
    nhan = "hien-tai" if "so-la" in options else "chon"
    out = chung.ra() / "mo-hinh-moi" / f"{mo_hinh}-{nhan}"
    out.mkdir(parents=True, exist_ok=True)
    data, features = chung.nap(mo_hinh)
    cuon = sorted(data)
    x, y = chung.noi(data, cuon)
    mo = chung.lgbm(mo_hinh, so_la, so_vong).fit(chung.cho_lgbm(mo_hinh, x), y)
    manifest = {"phien_ban": f"dg20-{mo_hinh}-{nhan}", "ngay_hoc": date.today().isoformat(), "mo_hinh": mo_hinh,
                "cau_hinh": {"num_leaves": so_la, "n_estimators": so_vong, **{k: v for k, v in chung.CAU_HINH[mo_hinh].items()}},
                "luat_chon": "một sai số chuẩn trên AP theo cuốn, LOBO-16, dừng sớm 3 cuốn theo seed " + str(chung.SEED),
                "se": chon["chon"]["se"], "nguong_mot_se": chon["chon"]["nguong"], "tot_nhat_so_la": chon["chon"]["tot_nhat"],
                "ap_trung_binh_theo_so_la": chon["chon"]["ap_trung_binh"], "bang_luoi_ap_theo_cuon": chon["ap_theo_cuon"],
                "dong_hoc": int(len(y)), "sach_hoc": len(cuon), "seed": chung.SEED,
                "thu_vien": {"lightgbm": lgb.__version__, "scikit-learn": sklearn.__version__, "numpy": np.__version__}}
    if mo_hinh == "m3":
        vendor = json.loads((chung.goc() / "vendor/a8-pass-phu-ml/manifest.json").read_text(encoding="utf-8"))
        oof = oof_theo_cuon(mo_hinh, data, cuon, so_la, so_vong)
        diem = np.concatenate([oof[c] for c in cuon])
        iso = IsotonicRegression(out_of_bounds="clip").fit(diem, y)
        text = mo.booster_.model_to_string()
        macdinh = "feature_names=" + " ".join(f"Column_{i}" for i in range(len(features)))
        assert text.count(macdinh) == 1
        text = text.replace(macdinh, "feature_names=" + " ".join(features))
        (out / "model.txt").write_text(text, encoding="utf-8", newline="\n")
        manifest.update({"dac_trung": features, "gia_tri_thieu": vendor["gia_tri_thieu"], "nguong": vendor["nguong"],
                         "hieu_chinh": {"cach": "isotonic trên dự đoán ngoài mẫu chia theo sách (LOBO-16, cấu hình đã chọn); nội suy tuyến tính, kẹp hai đầu",
                                        "diem": [float(v) for v in iso.X_thresholds_], "xac_suat": [float(v) for v in iso.y_thresholds_]},
                         "sha256_model": hashlib.sha256((out / "model.txt").read_bytes()).hexdigest()})
    else:
        mo.set_params(n_jobs=2)  # giữ n_jobs=2 như bản đang chạy trong sản phẩm (không ảnh hưởng điểm: deterministic=True)
        buffer = io.BytesIO()
        joblib.dump(mo, buffer)
        (out / ("heading.joblib" if mo_hinh == "m1" else "join.joblib")).write_bytes(buffer.getvalue())
        manifest.update({"dac_trung": features, "sha256_joblib": hashlib.sha256(buffer.getvalue()).hexdigest()})
    gain = sorted(zip(features, mo.booster_.feature_importance("gain")), key=lambda t: -t[1])
    tong = sum(g for _, g in gain) or 1.0
    manifest["gain"] = [(n, round(float(g) / tong, 4)) for n, g in gain]
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print("đã ghi", out, "lá", so_la, "vòng", so_vong)


if __name__ == "__main__":
    main()
