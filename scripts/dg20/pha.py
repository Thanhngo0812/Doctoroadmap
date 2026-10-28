"""Bảng phá của DG-20: cố ý làm hỏng quy trình rồi đo điểm lệch bao nhiêu so với quy trình đúng.
  1. dừng sớm trên cuốn để ra          2. bỏ luật một SE (tính từ lưới, ở tong_hop)
  3. chia ngẫu nhiên theo dòng         4. logistic không chuẩn hoá (logistic.py --khong-chuan-hoa)
  5. hiệu chỉnh isotonic học trên dự đoán trong mẫu
  tmp/venv-ml/Scripts/python.exe scripts/dg20/pha.py <1|3|5> <mô hình>
"""
import json
import statistics
import sys

import lightgbm as lgb
import numpy as np

import chung
import dong_bang
from danhgia.hoc_lai.chia import _xao_mot_phan, lobo
from danhgia.thong_ke.lcg import Lcg


def pha_dung_som_tren_cuon_de_ra(mo_hinh, data):
    """Cuốn để ra làm luôn tập dừng sớm; học trên 15 cuốn còn lại với số vòng chọn theo chính điểm trên cuốn để ra."""
    ket_qua = {}
    for la in chung.LEAVES:
        dong = []
        for de_ra, hoc in lobo(sorted(data)):
            x, y = chung.noi(data, hoc)
            xr, yr = data[de_ra]
            mo = chung.lgbm(mo_hinh, la, chung.MAX_ROUNDS, metric="average_precision").fit(
                chung.cho_lgbm(mo_hinh, x), y, eval_X=chung.cho_lgbm(mo_hinh, xr), eval_y=yr,
                callbacks=[lgb.early_stopping(chung.PATIENCE, first_metric_only=True, verbose=False)])
            dong.append({"de_ra": de_ra, "so_vong": int(mo.best_iteration_), "ap": chung.ap(yr, mo.predict_proba(chung.cho_lgbm(mo_hinh, xr), num_iteration=mo.best_iteration_)[:, 1])})
        ket_qua[la] = dong
        print("phá 1", mo_hinh, la, statistics.fmean([d["ap"] for d in dong if d["ap"] is not None]), flush=True)
    return ket_qua


def pha_chia_dong(mo_hinh, data, so_la, so_vong):
    """16 phần chia ngẫu nhiên theo dòng (cuốn lọt cả hai bên), cùng số lá và số vòng."""
    cuon = sorted(data)
    x, y = chung.noi(data, cuon)
    xs = chung.cho_lgbm(mo_hinh, x)
    oof = np.zeros(len(y))
    for k in np.array_split(np.array(_xao_mot_phan(range(len(y)), len(y), Lcg(chung.SEED))), 16):
        mask = np.ones(len(y), bool)
        mask[k] = False
        mo = chung.lgbm(mo_hinh, so_la, so_vong).fit(xs[mask], y[mask])
        oof[k] = mo.predict_proba(xs[k])[:, 1]
    ten = np.concatenate([[c] * len(data[c][1]) for c in cuon])
    ap_cuon = {c: chung.ap(y[ten == c], oof[ten == c]) for c in cuon}
    return ap_cuon


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    buoc, mo_hinh = sys.argv[1], sys.argv[2]
    data, _ = chung.nap(mo_hinh)
    chon = json.loads((chung.ra() / f"chon-{mo_hinh}.json").read_text(encoding="utf-8"))
    la = chon["chon"]["chon"]
    vong = int(round(chon["trung_vi_so_vong"][str(la)]))
    if buoc == "1":
        kq = pha_dung_som_tren_cuon_de_ra(mo_hinh, data)
    elif buoc == "3":
        kq = {"ap_theo_cuon": pha_chia_dong(mo_hinh, data, la, vong), "so_la": la, "so_vong": vong}
    elif buoc == "5":
        kq = {"ngoai_mau": dong_bang.hieu_chinh_long(mo_hinh, data, la, vong, False),
              "trong_mau": dong_bang.hieu_chinh_long(mo_hinh, data, la, vong, True), "so_la": la, "so_vong": vong}
    else:
        raise SystemExit("bước 1, 3 hay 5")
    (chung.ra() / f"pha-{buoc}-{mo_hinh}.json").write_text(json.dumps(kq, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
