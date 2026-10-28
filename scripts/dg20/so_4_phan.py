"""Phần C, phía laptop: chấm LightGBM đã chọn, LightGBM hiện tại, logistic và (khi đã có) cross-encoder trên CÙNG 4 phần theo cuốn (`chia-4-phan.json`).

Với mỗi phần k: học trên 12 cuốn còn lại, đoán 4 cuốn của phần k (ngoài mẫu). LightGBM dùng số lá và số vòng đã chọn ở phần A (không dừng sớm lại);
logistic chọn `C` theo AP trên 3 cuốn dừng sớm của 12 cuốn học (seed 20261027). Cross-encoder đọc `ngoai-mau-nep<k>-e<epoch>.jsonl` do `ce_hoc.py` ghi,
điểm = p[can_de_hieu]; epoch 3 là chính (khai trước), epoch 1, 2 chỉ báo kèm.
So trên các dòng chung của mọi hệ (cross-encoder bỏ 5 dòng `khong_ro` nên ít hơn M3 vài dòng): AP theo cuốn (16) và theo phần (4); hiệu cặp theo cuốn
có bootstrap theo cuốn và kiểm định dấu; thước vận hành: bộ hiệu chỉnh isotonic của phần k học trên dự đoán ngoài mẫu của 3 phần còn lại (cùng hệ),
rồi mỗi cuốn lấy k = round(tổng xác suất hiệu chỉnh), top-k theo điểm, báo P, R, F1 và |k - số dương thật|.
  tmp/venv-ml/Scripts/python.exe scripts/dg20/so_4_phan.py [--ce=<thư mục kết quả cross-encoder>] [--ra=tmp/dg20/so-4-phan.json]
Lưu ý: bộ hiệu chỉnh của phần k dùng dự đoán ngoài mẫu của các phần khác, mà mô hình sinh chúng đã học cả phần k; rò rỉ nhẹ, áp như nhau cho mọi hệ.
"""
import json
import statistics
import sys
import warnings
from pathlib import Path

import numpy as np
from sklearn.isotonic import IsotonicRegression

import chung
import logistic
from danhgia.hoc_lai.chia import chon_dung_som
from danhgia.hoc_lai.so_sanh import so_sanh_cap

warnings.filterwarnings("ignore")


def khoa(frame):
    return (frame.phieu_id + "|" + frame.x).to_numpy()


def du_doan_lgbm(frame, x, y, phan, so_la, so_vong):
    oof = np.full(len(y), np.nan)
    doc = frame.doc.to_numpy()
    for k, cuon in enumerate(phan):
        mask = np.isin(doc, cuon)
        mo = chung.lgbm("m3", so_la, so_vong).fit(chung.cho_lgbm("m3", x[~mask]), y[~mask])
        oof[mask] = mo.predict_proba(chung.cho_lgbm("m3", x[mask]))[:, 1]
    return oof


C_RONG = (1e-6, 1e-5, 1e-4, 1e-3, 1e-2, 0.1, 1.0, 10.0)


def du_doan_logistic(frame, x, y, phan, luoi_c=logistic.C_LUOI):
    oof = np.full(len(y), np.nan)
    doc = frame.doc.to_numpy()
    for k, cuon in enumerate(phan):
        mask = np.isin(doc, cuon)
        hoc = sorted(set(doc[~mask]))
        dung, con = chon_dung_som(hoc, f"phan-{k}", seed=chung.SEED, so_cuon=3)
        m_dung, m_con = np.isin(doc, dung), np.isin(doc, con)
        diem = {c: chung.ap(y[m_dung], logistic.mo_hinh(c).fit(x[m_con], y[m_con]).predict_proba(x[m_dung])[:, 1]) for c in luoi_c}
        tot = max(luoi_c, key=lambda c: (diem[c], -c))
        oof[mask] = logistic.mo_hinh(tot).fit(x[~mask], y[~mask]).predict_proba(x[mask])[:, 1]
    return oof


def doc_ce(thu_muc, khoa_dong, phan):
    """{epoch: mảng điểm theo thứ tự `khoa_dong` (nan nếu dòng không có trong jsonl)}."""
    ket_qua = {}
    chi_so = {k: i for i, k in enumerate(khoa_dong)}
    for epoch in (1, 2, 3):
        diem = np.full(len(khoa_dong), np.nan)
        for k in range(len(phan)):
            tep = Path(thu_muc) / f"ngoai-mau-nep{k}-e{epoch}.jsonl"
            if not tep.exists():
                break
            for dong in tep.read_text(encoding="utf-8").splitlines():
                r = json.loads(dong)
                if r["id"] in chi_so:
                    diem[chi_so[r["id"]]] = r["p"][0]
        else:
            ket_qua[epoch] = diem
    return ket_qua


def ap_theo_cuon(doc, y, diem, mask):
    return {c: chung.ap(y[mask & (doc == c)], diem[mask & (doc == c)]) for c in sorted(set(doc))}


def van_hanh(doc, y, diem, mask, phan):
    """Hiệu chỉnh isotonic của phần k học trên dự đoán ngoài mẫu của các phần khác; top-k theo cuốn."""
    ket_qua = {}
    for k, cuon in enumerate(phan):
        khac = mask & ~np.isin(doc, cuon)
        iso = IsotonicRegression(out_of_bounds="clip").fit(diem[khac], y[khac])
        for c in cuon:
            m = mask & (doc == c)
            xac_suat = iso.predict(diem[m])
            so_k = int(round(float(xac_suat.sum())))
            hang = np.argsort(-diem[m], kind="stable")[:so_k]
            tp = int(y[m][hang].sum())
            p = tp / so_k if so_k else 0.0
            r = tp / max(int(y[m].sum()), 1)
            ket_qua[c] = {"k": so_k, "duong_that": int(y[m].sum()), "P": p, "R": r, "F1": 2 * p * r / (p + r) if p + r else 0.0}
    return ket_qua


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    options = dict(a[2:].split("=", 1) for a in sys.argv[1:] if a.startswith("--") and "=" in a)
    phan = json.loads((Path(__file__).with_name("chia-4-phan.json")).read_text(encoding="utf-8"))["phan"]
    chon = json.loads((chung.ra() / "chon-m3.json").read_text(encoding="utf-8"))
    la, vong = chon["chon"]["chon"], int(round(chon["trung_vi_so_vong"][str(chon["chon"]["chon"])]))
    data, features = chung.nap("m3")
    frame = chung.m3_data().sort_values(["doc"], kind="stable").reset_index(drop=True)
    x = frame[features].to_numpy(dtype=float)
    y = frame.nhan.to_numpy()
    doc = frame.doc.to_numpy()
    he = {f"lightgbm_chon_{la}_la": du_doan_lgbm(frame, x, y, phan, la, vong),
          f"lightgbm_hien_tai_{chung.HIEN_TAI['m3']}_la": du_doan_lgbm(frame, x, y, phan, chung.HIEN_TAI["m3"], chung.VONG_HIEN_TAI["m3"]),
          "logistic": du_doan_logistic(frame, x, y, phan),
          "logistic_c_rong": du_doan_logistic(frame, x, y, phan, C_RONG)}
    epoch_ce = None
    if options.get("ce"):
        theo_epoch = doc_ce(options["ce"], list(khoa(frame)), phan)
        if sorted(theo_epoch) != [1, 2, 3]:
            raise SystemExit("chưa có đủ 4 nếp của cả 3 epoch")
        epoch_ce = 3  # khai trước: epoch cuối là chính; hai epoch kia chỉ báo kèm
        he["cross_encoder_e5"] = theo_epoch[3]
        for e in (1, 2):
            he[f"cross_encoder_e5_epoch{e}"] = theo_epoch[e]
    chung_mask = np.ones(len(y), bool)
    for d in he.values():
        chung_mask &= ~np.isnan(d)
    ket_qua = {"so_dong_chung": int(chung_mask.sum()), "epoch_ce": epoch_ce, "phan": phan, "he": {}}
    for ten, d in he.items():
        ap_cuon = ap_theo_cuon(doc, y, d, chung_mask)
        ap_phan = {k: chung.ap(y[chung_mask & np.isin(doc, cuon)], d[chung_mask & np.isin(doc, cuon)]) for k, cuon in enumerate(phan)}
        vh = van_hanh(doc, y, d, chung_mask, phan)
        ket_qua["he"][ten] = {"ap_theo_cuon": ap_cuon, "ap_trung_binh_cuon": statistics.fmean(ap_cuon.values()), "ap_theo_phan": ap_phan,
                              "van_hanh_theo_cuon": vh, "F1_trung_binh": statistics.fmean(v["F1"] for v in vh.values()),
                              "sai_so_k_tuyet_doi_trung_binh": statistics.fmean(abs(v["k"] - v["duong_that"]) / max(v["duong_that"], 1) for v in vh.values())}
    ten_he = list(he)
    ket_qua["so_cap"] = {f"{a}_tru_{b}": so_sanh_cap(ket_qua["he"][a]["ap_theo_cuon"], ket_qua["he"][b]["ap_theo_cuon"], seed=chung.SEED)
                         for a in ten_he for b in ten_he if a < b}
    duong = Path(options.get("ra", chung.ra() / "so-4-phan.json"))
    duong.write_text(json.dumps(ket_qua, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for ten, v in ket_qua["he"].items():
        print(f"{ten:28s} AP cuốn {v['ap_trung_binh_cuon']:.4f} | AP phần " + " ".join(f"{a:.3f}" for a in v["ap_theo_phan"].values())
              + f" | F1 top-k {v['F1_trung_binh']:.3f} | sai số k {v['sai_so_k_tuyet_doi_trung_binh']:.3f}")
    for ten, v in ket_qua["so_cap"].items():
        print(ten, {k: (round(x, 4) if isinstance(x, float) else x) for k, x in v.items()})


if __name__ == "__main__":
    main()
