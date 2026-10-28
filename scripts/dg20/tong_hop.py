"""Gom bảng lưới (`luoi-<mô hình>.jsonl`) và logistic thành kết quả chọn: luật một SE, so cặp với logistic, bảng markdown. Ghi `tmp/dg20/chon-<mô hình>.json`."""
import json
import statistics
import sys

import chung
from danhgia.hoc_lai.chon import chon_ap_cao_nhat, chon_mot_se
from danhgia.hoc_lai.so_sanh import so_sanh_cap


def doc(duong):
    return [json.loads(d) for d in duong.read_text(encoding="utf-8").splitlines() if d.strip()]


def luoi(mo_hinh):
    bang = {}
    for r in doc(chung.ra() / f"luoi-{mo_hinh}.jsonl"):
        bang.setdefault(r["so_la"], {})[r["de_ra"]] = r
    return bang


def theo_cuon(bang, truong):
    cuon = sorted(next(iter(bang.values())))
    return {la: [bang[la][c][truong] for c in cuon] for la in sorted(bang)}, cuon


def tong_hop(mo_hinh):
    bang = luoi(mo_hinh)
    ap, cuon = theo_cuon(bang, "ap")
    assert sorted(bang) == sorted(chung.LEAVES) and len(cuon) == 16, "bảng lưới chưa đủ 6 × 16"
    chon = chon_mot_se(ap)
    cao_nhat = chon_ap_cao_nhat(ap)
    vong, _ = theo_cuon(bang, "so_vong")
    f1, _ = theo_cuon(bang, "f1_05")
    ket_qua = {"mo_hinh": mo_hinh, "cuon": cuon, "chon": chon, "ap_cao_nhat_khong_se": cao_nhat["chon"], "hien_tai": chung.HIEN_TAI[mo_hinh],
               "trung_vi_so_vong": {str(la): statistics.median(vong[la]) for la in vong},
               "f1_05_trung_binh": {str(la): statistics.fmean([x for x in f1[la] if x is not None]) for la in f1},
               "ap_theo_cuon": {str(la): dict(zip(cuon, ap[la])) for la in ap}}
    duong = chung.ra() / f"logistic-{mo_hinh}.jsonl"
    if duong.exists() and len(doc(duong)) == 16:
        lg = {r["de_ra"]: r for r in doc(duong)}
        ap_lg = {c: lg[c]["ap"] for c in cuon}
        ket_qua["logistic"] = {"ap_theo_cuon": ap_lg, "c": {c: lg[c]["c"] for c in cuon},
                               "ap_trung_binh": statistics.fmean([v for v in ap_lg.values() if v is not None]),
                               "f1_05_trung_binh": statistics.fmean([lg[c]["f1_05"] for c in cuon if lg[c]["f1_05"] is not None])}
        co = [c for c in cuon if ap_lg[c] is not None]
        for ten, la in (("chon", chon["chon"]), ("hien_tai", chung.HIEN_TAI[mo_hinh])):
            ket_qua["logistic"][f"lgbm_{ten}_tru_logistic"] = so_sanh_cap(
                {c: bang[la][c]["ap"] for c in co}, {c: ap_lg[c] for c in co}, seed=chung.SEED)
    (chung.ra() / f"chon-{mo_hinh}.json").write_text(json.dumps(ket_qua, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return ket_qua


def bang_md(kq):
    cuon = kq["cuon"]
    dong = ["| lá | " + " | ".join(c[-2:] for c in cuon) + " | TB |", "|---" * (len(cuon) + 2) + "|"]
    for la, v in kq["ap_theo_cuon"].items():
        gia_tri = [v[c] for c in cuon]
        dong.append(f"| {la} | " + " | ".join("–" if x is None else f"{x:.3f}" for x in gia_tri) + f" | {kq['chon']['ap_trung_binh'][int(la)]:.4f} |")
    if "logistic" in kq:
        v = kq["logistic"]["ap_theo_cuon"]
        dong.append("| logistic | " + " | ".join("–" if v[c] is None else f"{v[c]:.3f}" for c in cuon) + f" | {kq['logistic']['ap_trung_binh']:.4f} |")
    return "\n".join(dong)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    for ten in sys.argv[1:]:
        kq = tong_hop(ten)
        c = kq["chon"]
        print(f"## {ten}: chọn {c['chon']} lá (tốt nhất {c['tot_nhat']} lá, AP {c['ap_tot_nhat']:.4f}, SE {c['se']:.4f}, ngưỡng {c['nguong']:.4f}); "
              f"bỏ luật SE chọn {kq['ap_cao_nhat_khong_se']}; hiện tại {kq['hien_tai']} lá AP {c['ap_trung_binh'][kq['hien_tai']]:.4f}")
        print(bang_md(kq))
        if "logistic" in kq:
            print({k: v for k, v in kq["logistic"].items() if k.startswith("lgbm")})
