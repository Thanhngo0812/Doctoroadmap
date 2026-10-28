"""Phần A: lưới `num_leaves` ∈ {7,15,31,63,127,255} × 16 cuốn để ra cho một mô hình LightGBM (m1, m2, m3), có điểm kiểm tiếp tục.

Mỗi ô: chia 15 cuốn còn lại thành 12 học + 3 dừng sớm (seed 20261027 và mã cuốn để ra), dừng sớm theo AP trên 3 cuốn (kiên nhẫn 100, trần 5000),
rồi học lại trên đủ 15 cuốn với số vòng tốt nhất và chấm trên cuốn để ra. Ghi `tmp/dg20/luoi-<mô hình>.jsonl`, mỗi dòng một ô.
  tmp/venv-ml/Scripts/python.exe scripts/dg20/luoi.py --mo-hinh=m3
"""
import json
import sys
import time

import lightgbm as lgb
import numpy as np
from sklearn.metrics import f1_score

import chung
from danhgia.hoc_lai.chia import chon_dung_som, lobo, kiem_tra_khong_ro_ri


def lam_o(mo_hinh, data, de_ra, so_la):
    dung, hoc = chon_dung_som(sorted(data), de_ra, seed=chung.SEED)
    kiem_tra_khong_ro_ri(de_ra, dung, hoc)
    xh, yh = chung.noi(data, hoc)
    xd, yd = chung.noi(data, dung)
    t0 = time.perf_counter()
    thu = chung.lgbm(mo_hinh, so_la, chung.MAX_ROUNDS, metric="average_precision")
    thu.fit(chung.cho_lgbm(mo_hinh, xh), yh, eval_X=chung.cho_lgbm(mo_hinh, xd), eval_y=yd,
            callbacks=[lgb.early_stopping(chung.PATIENCE, first_metric_only=True, verbose=False)])
    tot = int(thu.best_iteration_)
    x15, y15 = chung.noi(data, hoc + dung)
    cuoi = chung.lgbm(mo_hinh, so_la, tot).fit(chung.cho_lgbm(mo_hinh, x15), y15)
    xr, yr = data[de_ra]
    p = cuoi.predict_proba(chung.cho_lgbm(mo_hinh, xr))[:, 1]
    return {"de_ra": de_ra, "so_la": so_la, "so_vong": tot, "dung_som": dung, "ap": chung.ap(yr, p),
            "f1_05": float(f1_score(yr, p >= 0.5, zero_division=0)) if yr.sum() else None,
            "so_dong_de_ra": int(len(yr)), "so_duong_de_ra": int(yr.sum()), "giay": round(time.perf_counter() - t0, 1)}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    options = dict(a[2:].split("=", 1) for a in sys.argv[1:] if a.startswith("--") and "=" in a)
    mo_hinh = options["mo-hinh"]
    data, _ = chung.nap(mo_hinh)
    duong = chung.ra() / f"luoi-{mo_hinh}.jsonl"
    xong = set()
    if duong.exists():
        xong = {(r["de_ra"], r["so_la"]) for r in map(json.loads, duong.read_text(encoding="utf-8").splitlines() if duong.read_text(encoding="utf-8") else [])}
    for de_ra, _ in lobo(sorted(data)):
        for so_la in chung.LEAVES:
            if (de_ra, so_la) in xong:
                continue
            ban_ghi = lam_o(mo_hinh, data, de_ra, so_la)
            with open(duong, "a", encoding="utf-8", newline="\n") as f:
                f.write(json.dumps(ban_ghi, ensure_ascii=False) + "\n")
            print(f"{mo_hinh} {de_ra} lá {so_la}: vòng {ban_ghi['so_vong']} AP {ban_ghi['ap']} ({ban_ghi['giay']}s)", flush=True)


if __name__ == "__main__":
    main()
