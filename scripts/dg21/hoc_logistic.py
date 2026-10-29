"""DG-21 phần A: học logistic cuối (M1 nhận tiêu đề, M2 nối dòng, M3 pass phụ) trên đủ 16 cuốn học D-01.

Đặc trưng, xử lý thiếu và chuẩn hoá đúng như `scripts/dg20/logistic.py` (`logistic.mo_hinh`). `C` là giá trị được chọn NHIỀU NHẤT qua 16 lần chia ở lưới mở rộng
(`report/danh-gia-pha-a/DG-20-ket-qua/logistic-<m>-c-rong.jsonl`); hoà thì lấy `C` nhỏ hơn (`danhgia.hoc_lai.chon.chon_c_nhieu_nhat`).
M3: hiệu chỉnh isotonic học trên dự đoán NGOÀI MẪU theo cuốn (LOBO-16, cùng `C`), như DG-20 làm cho LightGBM (`dong_bang.py`).
Chỉ D-01. Ghi `evaluation/mo-hinh/dg21/<m>-logistic/{model.joblib,manifest.json}`.
  tmp/venv-ml/Scripts/python.exe scripts/dg21/hoc_logistic.py m1|m2|m3 [--ra=evaluation/mo-hinh/dg21]
  tmp/venv-ml/Scripts/python.exe scripts/dg21/hoc_logistic.py a1 [--ra=...]   gom m1, m2 thành thư mục `a1-logistic/` (heading.joblib, join.joblib) cho `NheLogistic`
"""
import shutil
import hashlib
import io
import json
import sys
import warnings
from datetime import date
from pathlib import Path

import joblib
import numpy as np
import sklearn
from sklearn.isotonic import IsotonicRegression

GOC = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(GOC / "scripts" / "dg20"))
import chung  # noqa: E402
import logistic  # noqa: E402
from danhgia.hoc_lai.chia import lobo  # noqa: E402
from danhgia.hoc_lai.chon import chon_c_nhieu_nhat  # noqa: E402

KET_QUA_DG20 = GOC / "report/danh-gia-pha-a/DG-20-ket-qua"
TEN = {"m1": "tiêu đề (heading.joblib)", "m2": "nối dòng tiêu đề (join.joblib)", "m3": "pass phụ"}


def sha_du_lieu(data, cuon):
    h = hashlib.sha256()
    for c in cuon:
        x, y = data[c]
        h.update(c.encode("utf-8"))
        h.update(np.ascontiguousarray(x, dtype=np.float64).tobytes())
        h.update(np.ascontiguousarray(y, dtype=np.int64).tobytes())
    return h.hexdigest()


def mau_kiem(mo, x):
    """Ba dòng đầu vào (ô thiếu là null) và xác suất mô hình cho ra: test nạp lại mô hình và so với đây."""
    dong = x[[0, len(x) // 2, len(x) - 1]]
    return {"dtype": str(x.dtype), "x": [[None if np.isnan(v) else float(v) for v in d] for d in dong], "p": [float(v) for v in mo.predict_proba(dong)[:, 1]]}


def doc_c_dg20(mo_hinh):
    tep = KET_QUA_DG20 / f"logistic-{mo_hinh}-c-rong.jsonl"
    ban_ghi = [json.loads(d) for d in tep.read_text(encoding="utf-8").splitlines() if d.strip()]
    assert len(ban_ghi) == 16, f"{tep}: cần đủ 16 lần chia"
    return ban_ghi, hashlib.sha256(tep.read_bytes()).hexdigest()


def hieu_chinh_ngoai_mau(data, cuon, c):
    """Isotonic trên dự đoán ngoài mẫu: mỗi cuốn được chấm bởi mô hình học trên 15 cuốn còn lại."""
    diem, nhan = [], []
    for de_ra, hoc in lobo(cuon):
        x, y = chung.noi(data, hoc)
        diem.append(logistic.mo_hinh(c).fit(x, y).predict_proba(data[de_ra][0])[:, 1])
        nhan.append(data[de_ra][1])
    diem, nhan = np.concatenate(diem), np.concatenate(nhan)
    return IsotonicRegression(out_of_bounds="clip").fit(diem, nhan)


def gom_a1(goc_ra):
    out = goc_ra / "a1-logistic"
    out.mkdir(parents=True, exist_ok=True)
    models, nguon = {}, {}
    for m, ten in (("m1", "heading.joblib"), ("m2", "join.joblib")):
        manifest = json.loads((goc_ra / f"{m}-logistic/manifest.json").read_text(encoding="utf-8"))
        shutil.copyfile(goc_ra / f"{m}-logistic/model.joblib", out / ten)
        models[ten] = hashlib.sha256((out / ten).read_bytes()).hexdigest()
        assert models[ten] == manifest["sha256_model"]
        nguon[ten] = {"manifest": f"{m}-logistic/manifest.json", "C": manifest["cau_hinh"]["C"]}
    (out / "manifest.json").write_text(json.dumps({"version": "dg21-a1-logistic", "models": models, "nguon": nguon}, ensure_ascii=False, indent=1) + chr(10),
                                       encoding="utf-8", newline=chr(10))
    print("đã ghi", out, models)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    warnings.filterwarnings("ignore")
    mo_hinh = sys.argv[1]
    options = dict(a[2:].split("=", 1) for a in sys.argv[2:] if a.startswith("--") and "=" in a)
    if mo_hinh == "a1":
        return gom_a1(Path(options.get("ra", GOC / "evaluation/mo-hinh/dg21")))
    out = Path(options.get("ra", GOC / "evaluation/mo-hinh/dg21")) / f"{mo_hinh}-logistic"
    out.mkdir(parents=True, exist_ok=True)
    ban_ghi, sha_c = doc_c_dg20(mo_hinh)
    chon = chon_c_nhieu_nhat(r["c"] for r in ban_ghi)
    c = chon["chon"]
    data, dac_trung = chung.nap(mo_hinh)
    cuon = sorted(data)
    x, y = chung.noi(data, cuon)
    mo = logistic.mo_hinh(c).fit(x, y)
    bo = io.BytesIO()
    joblib.dump(mo, bo)
    (out / "model.joblib").write_bytes(bo.getvalue())
    lai = joblib.load(out / "model.joblib")
    sai_lech = float(np.abs(lai.predict_proba(x)[:, 1] - mo.predict_proba(x)[:, 1]).max())
    manifest = {"phien_ban": f"dg21-{mo_hinh}-logistic", "mo_hinh": mo_hinh, "dung_cho": TEN[mo_hinh], "ngay_hoc": date.today().isoformat(),
                "cau_hinh": {"loai": "logistic", "C": c, "class_weight": "balanced", "max_iter": 4000, "buoc": [str(b) for _, b in mo.steps],
                             "ghi_chu": "SimpleImputer(median, add_indicator) -> StandardScaler -> LogisticRegression, đúng scripts/dg20/logistic.py"},
                "luat_chon_c": "C được chọn nhiều nhất qua 16 lần chia LOBO ở lưới mở rộng của DG-20; hoà lấy C nhỏ hơn",
                "ly_do_chon_c": f"C = {c} được chọn {chon['dem'][c]}/16 lần; đếm {chon['dem']}" + (f"; hoà giữa {chon['hoa']} nên lấy nhỏ nhất" if len(chon["hoa"]) > 1 else ""),
                "dem_c": {str(k): v for k, v in chon["dem"].items()}, "sha256_c_rong_dg20": sha_c,
                "dac_trung": list(dac_trung), "sach_hoc": cuon, "dong_hoc": int(len(y)), "so_duong": int(y.sum()),
                "sha256_du_lieu": sha_du_lieu(data, cuon), "sha256_model": hashlib.sha256(bo.getvalue()).hexdigest(),
                "seed": chung.SEED, "ghi_chu_seed": "lbfgs tất định; seed 20261027 chỉ dùng cho chia dừng sớm lúc DG-20 chọn C",
                "thu_vien": {"scikit-learn": sklearn.__version__, "numpy": np.__version__, "joblib": joblib.__version__},
                "kiem_nap_lai": {"sai_lech_du_doan_toi_da": sai_lech},
                "mau_kiem": mau_kiem(mo, x)}
    if mo_hinh == "m3":
        iso = hieu_chinh_ngoai_mau(data, cuon, c)
        manifest["hieu_chinh"] = {"cach": "isotonic trên dự đoán ngoài mẫu theo cuốn (LOBO-16, cùng C); nội suy tuyến tính, kẹp hai đầu",
                                  "diem": [float(v) for v in iso.X_thresholds_], "xac_suat": [float(v) for v in iso.y_thresholds_]}
        manifest["gia_tri_thieu"] = "NaN (trung vị tập học + cột chỉ báo thiếu), không phải -1 như LightGBM"
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(mo_hinh, "C", c, manifest["ly_do_chon_c"], "| sai lệch nạp lại", sai_lech, "|", out)


if __name__ == "__main__":
    main()
