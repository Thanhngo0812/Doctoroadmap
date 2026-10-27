"""Phần B: baseline hồi quy logistic, cùng đặc trưng, cùng 16 lần chia LOBO và cùng vòng trong (3 cuốn dừng sớm) với LightGBM.

Ô thiếu thay bằng trung vị tập học kèm cột chỉ báo thiếu; chuẩn hoá đặc trưng; `class_weight` cân bằng; `C` ∈ {0,01; 0,1; 1; 10} chọn theo AP trên 3 cuốn
dừng sớm của vòng trong. Ghi `tmp/dg20/logistic-<mô hình>.jsonl`.  `--khong-chuan-hoa` là phép phá (bảng phá, mục logistic không chuẩn hoá).
  tmp/venv-ml/Scripts/python.exe scripts/dg20/logistic.py --mo-hinh=m3 [--khong-chuan-hoa]
"""
import json
import sys
import warnings

import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

import chung
from danhgia.hoc_lai.chia import chon_dung_som, kiem_tra_khong_ro_ri, lobo

C_LUOI = (0.01, 0.1, 1.0, 10.0)


def mo_hinh(c, chuan_hoa=True):
    buoc = [SimpleImputer(strategy="median", add_indicator=True)]
    if chuan_hoa:
        buoc.append(StandardScaler())
    buoc.append(LogisticRegression(C=c, class_weight="balanced", max_iter=4000))
    return make_pipeline(*buoc)


def lam_o(data, de_ra, chuan_hoa=True):
    dung, hoc = chon_dung_som(sorted(data), de_ra, seed=chung.SEED)
    kiem_tra_khong_ro_ri(de_ra, dung, hoc)
    xh, yh = chung.noi(data, hoc)
    xd, yd = chung.noi(data, dung)
    diem = {}
    for c in C_LUOI:
        diem[c] = chung.ap(yd, mo_hinh(c, chuan_hoa).fit(xh, yh).predict_proba(xd)[:, 1])
    tot = max(C_LUOI, key=lambda c: (diem[c] if diem[c] is not None else -1, -c))
    x15, y15 = chung.noi(data, hoc + dung)
    xr, yr = data[de_ra]
    p = mo_hinh(tot, chuan_hoa).fit(x15, y15).predict_proba(xr)[:, 1]
    return {"de_ra": de_ra, "c": tot, "ap_dung_som_theo_c": {str(c): v for c, v in diem.items()}, "dung_som": dung, "ap": chung.ap(yr, p),
            "f1_05": float(f1_score(yr, p >= 0.5, zero_division=0)) if yr.sum() else None, "so_dong_de_ra": int(len(yr)), "so_duong_de_ra": int(yr.sum())}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    warnings.filterwarnings("ignore")
    options = dict(a[2:].split("=", 1) for a in sys.argv[1:] if a.startswith("--") and "=" in a)
    ten = options["mo-hinh"]
    chuan_hoa = "--khong-chuan-hoa" not in sys.argv
    data, _ = chung.nap(ten)
    duong = chung.ra() / f"logistic-{ten}{'' if chuan_hoa else '-khong-chuan-hoa'}.jsonl"
    duong.write_text("", encoding="utf-8")
    for de_ra, _ in lobo(sorted(data)):
        ban_ghi = lam_o(data, de_ra, chuan_hoa)
        with open(duong, "a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(ban_ghi, ensure_ascii=False) + "\n")
        print(f"{ten} {de_ra}: C {ban_ghi['c']} AP {ban_ghi['ap']}", flush=True)


if __name__ == "__main__":
    main()
