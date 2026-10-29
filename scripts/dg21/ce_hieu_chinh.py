"""DG-21 phần C, bước hiệu chỉnh: isotonic cho điểm cross-encoder, học trên dự đoán NGOÀI MẪU epoch 3 của 4 nếp DG-20 (`ngoai-mau-nep<k>-e3.jsonl`).

Điểm = p[can_de_hieu] (cột 0 của `p`), nhãn dương = `nhan == can_de_hieu` của `d01.jsonl` (chỉ D-01). Ghi `evaluation/mo-hinh/dg21/ce-hieu-chinh.json`
(điểm, xác suất, SHA-256 các tệp đầu vào). Chạy được trên laptop (numpy + scikit-learn), không cần `torch`.
  tmp/venv-ml/Scripts/python.exe scripts/dg21/ce_hieu_chinh.py --ngoai-mau=<thư mục có ngoai-mau-nep*-e3.jsonl> --du-lieu=<d01.jsonl> [--ra=...]
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from sklearn.isotonic import IsotonicRegression

GOC = Path(__file__).resolve().parents[2]
EPOCH = 3
SO_NEP = 4
NHAN_DUONG = "can_de_hieu"


def doc_jsonl(tep):
    return [json.loads(d) for d in Path(tep).read_text(encoding="utf-8").splitlines() if d.strip()]


def hieu_chinh_tu_ngoai_mau(ngoai_mau, nhan_theo_id, so_nep=SO_NEP, epoch=EPOCH):
    """Isotonic trên p[can_de_hieu] ngoài mẫu của mọi nếp. `ngoai_mau`: {nếp: [{"id", "p"}]}; `nhan_theo_id`: {id: nhãn}. Mỗi dòng có đúng một nhãn."""
    diem, nhan = [], []
    thay = set()
    for nep in range(so_nep):
        for r in ngoai_mau[nep]:
            if r["id"] in thay:
                raise ValueError(f"id {r['id']} xuất hiện ở hai nếp: dự đoán ngoài mẫu phải rời nhau")
            thay.add(r["id"])
            diem.append(r["p"][0])
            nhan.append(int(nhan_theo_id[r["id"]] == NHAN_DUONG))
    iso = IsotonicRegression(out_of_bounds="clip").fit(np.asarray(diem), np.asarray(nhan))
    return {"diem": [float(v) for v in iso.X_thresholds_], "xac_suat": [float(v) for v in iso.y_thresholds_], "so_dong": len(diem),
            "so_duong": int(sum(nhan)), "epoch": epoch, "so_nep": so_nep}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    options = dict(a[2:].split("=", 1) for a in sys.argv[1:] if a.startswith("--") and "=" in a)
    thu_muc = Path(options["ngoai-mau"])
    du_lieu = Path(options["du-lieu"])
    ra = Path(options.get("ra", GOC / "evaluation/mo-hinh/dg21/ce-hieu-chinh.json"))
    tep = [thu_muc / f"ngoai-mau-nep{k}-e{EPOCH}.jsonl" for k in range(SO_NEP)]
    ngoai_mau = {k: doc_jsonl(t) for k, t in enumerate(tep)}
    nhan = {r["id"]: r["nhan"] for r in doc_jsonl(du_lieu)}
    ket_qua = hieu_chinh_tu_ngoai_mau(ngoai_mau, nhan)
    ket_qua["sha256_dau_vao"] = {t.name: hashlib.sha256(t.read_bytes()).hexdigest() for t in tep}
    ket_qua["sha256_d01"] = hashlib.sha256(du_lieu.read_bytes()).hexdigest()
    ket_qua["cach"] = "isotonic trên p[can_de_hieu] ngoài mẫu epoch 3 của 4 nếp DG-20; nội suy tuyến tính, kẹp hai đầu"
    ra.parent.mkdir(parents=True, exist_ok=True)
    ra.write_text(json.dumps(ket_qua, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print("đã ghi", ra, "dòng", ket_qua["so_dong"], "dương", ket_qua["so_duong"], "mốc", len(ket_qua["diem"]))


if __name__ == "__main__":
    main()
