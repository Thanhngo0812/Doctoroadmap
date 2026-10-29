"""DG-21 phần C, bước chấm: chấm các cặp ứng viên pass phụ bằng cross-encoder `intfloat/multilingual-e5-base` đã học ở DG-20 (nếp 0), rồi hiệu chỉnh.

Claude chạy ở môi trường có `torch` + `transformers` (như `ce_hoc.py`, `ce_do_cpu.py`). Đầu vào là tệp do `python -m danhgia cap-ce` xuất; đầu ra là tệp
điểm có sẵn (`DiemCoSanScorer`): dòng đầu schema `diem-co-san-1`, mỗi dòng sau `{id, dac_trung_sha, p, xac_suat}` theo đúng thứ tự tệp cặp.
`p` = softmax[can_de_hieu] làm tròn 5 chữ số (như `ngoai-mau-*.jsonl` mà bộ hiệu chỉnh đã học); `xac_suat` = isotonic của `ce-hieu-chinh.json`.
  python ce_cham.py --cap=CAP.jsonl --mo-hinh=<...>/e5-dg20/mo-hinh --hieu-chinh=ce-hieu-chinh.json --ra=DIEM.jsonl [--lo=16] [--thu-nho]
`--thu-nho`: chỉ 64 cặp đầu, ghi `<ra>.thu-nho` (kiểm nhanh đường chạy; không dùng làm kết quả). Cần `e6_cross_encoder.py` cùng thư mục (hoặc `scripts/pass-phu-ml/`).
Phần thuần (đọc cặp, hiệu chỉnh, ghi tệp điểm) không cần `torch`: xem `ghi_diem`.
"""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

SCHEMA = "diem-co-san-1"
SO_THU_NHO = 64


def doc_cap(tep):
    return [json.loads(d) for d in Path(tep).read_text(encoding="utf-8").splitlines() if d.strip()]


def hieu_chinh(p, diem, xac_suat):
    return np.interp(p, diem, xac_suat).tolist()


def ghi_diem(duong, cap, p, bo_hieu_chinh, dau):
    """Ghi tệp điểm. Thiếu hay thừa điểm so với cặp là lỗi."""
    if len(cap) != len(p):
        raise ValueError(f"{len(cap)} cặp nhưng {len(p)} điểm")
    xac_suat = hieu_chinh(p, bo_hieu_chinh["diem"], bo_hieu_chinh["xac_suat"])
    dong = [json.dumps({"schema": SCHEMA, **dau}, ensure_ascii=False)]
    dong += [json.dumps({"id": c["id"], "dac_trung_sha": c["dac_trung_sha"], "p": float(v), "xac_suat": float(x)}) for c, v, x in zip(cap, p, xac_suat)]
    Path(duong).write_text("".join(d + "\n" for d in dong), encoding="utf-8", newline="\n")


def cham_bang_mo_hinh(cap, thu_muc_mo_hinh, lo):
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pass-phu-ml"))
    from e6_cross_encoder import LABELS, Encoder, predict

    may = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tok = AutoTokenizer.from_pretrained(thu_muc_mo_hinh)
    mo_hinh = AutoModelForSequenceClassification.from_pretrained(thu_muc_mo_hinh, dtype=torch.float32).to(may).eval()
    ma_hoa = Encoder(tok, False, 256, 64)          # đúng cách cắt, độ dài 256 và đánh dấu @/# lúc học (ce_hoc.py)
    da_ma_hoa = [ma_hoa(c) for c in cap]
    xac_suat = predict(mo_hinh, da_ma_hoa, tok.pad_token_id, may, lo)
    return [p[LABELS.index("can_de_hieu")] for p in xac_suat], {"may": torch.cuda.get_device_name(0) if may.type == "cuda" else "cpu",
                                                              "torch": torch.__version__}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cap", required=True)
    ap.add_argument("--mo-hinh", required=True)
    ap.add_argument("--hieu-chinh", required=True)
    ap.add_argument("--ra", required=True)
    ap.add_argument("--lo", type=int, default=16)
    ap.add_argument("--thu-nho", action="store_true")
    args = ap.parse_args()
    cap = doc_cap(args.cap)
    ra = args.ra
    if args.thu_nho:
        cap, ra = cap[:SO_THU_NHO], args.ra + ".thu-nho"
    bo_hieu_chinh = json.loads(Path(args.hieu_chinh).read_text(encoding="utf-8"))
    bat_dau = time.time()
    p, may = cham_bang_mo_hinh(cap, args.mo_hinh, args.lo)
    dau = {"mo_hinh": "intfloat/multilingual-e5-base:dg20-nep0", "sha256_mo_hinh": hashlib.sha256((Path(args.mo_hinh) / "model.safetensors").read_bytes()).hexdigest(),
           "sha256_hieu_chinh": hashlib.sha256(Path(args.hieu_chinh).read_bytes()).hexdigest(), "so_cap": len(cap), "giay": round(time.time() - bat_dau, 1),
           "thu_nho": args.thu_nho, **may}
    ghi_diem(ra, cap, p, bo_hieu_chinh, dau)
    print("đã ghi", ra, "cặp", len(cap), "giây", dau["giay"])


if __name__ == "__main__":
    main()
