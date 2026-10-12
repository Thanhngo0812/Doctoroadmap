"""E6 (vòng 2): đo tốc độ cross-encoder trên CPU, vì sản phẩm chạy pass phụ trên CPU. 0 USD.

Nạp mô hình đã tinh chỉnh (`--luu-mo-hinh` của `e6_cross_encoder.py`, chép về máy), mã hoá ứng viên của một tài liệu đúng như lúc học, rồi
đoán trên CPU. In số cặp mỗi giây và số phút cho cả tài liệu. `--int8`: đo thêm bản lượng tử hoá động int8 (các lớp Linear) và độ lệch điểm
so với bản fp32 (lệch tuyệt đối lớn nhất, tương quan hạng Spearman). Chạy bằng `tmp/venv-e6` (torch bản CPU, transformers; tách khỏi
`tmp/venv-ml` để không đổi phiên bản gói mà bảng vòng 1 dựa vào):
  tmp/venv-e6/Scripts/python.exe scripts/pass-phu-ml/e6_toc_do_cpu.py --mo-hinh=<thư mục> [--tach-tu] [--tai-lieu=doc-4] [--int8]
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

sys.path.insert(0, str(Path(__file__).resolve().parent))
from e6_cross_encoder import Encoder, predict, read_jsonl  # noqa: E402


def timed(model, encoded, pad_id, size):
    started = time.time()
    probs = predict(model, encoded, pad_id, torch.device("cpu"), size)
    return np.array([p[0] for p in probs]), time.time() - started


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mo-hinh", required=True)
    ap.add_argument("--tach-tu", action="store_true")
    ap.add_argument("--tai-lieu", default="doc-4")
    ap.add_argument("--do-dai", type=int, default=256)
    ap.add_argument("--toi-da-a", type=int, default=64)
    ap.add_argument("--lo", type=int, default=32)
    ap.add_argument("--int8", action="store_true")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    rows = read_jsonl(Path("tmp/pass-phu-ml/e6/du-lieu") / f"{args.tai_lieu}.jsonl")
    tokenizer = AutoTokenizer.from_pretrained(args.mo_hinh)
    started = time.time()
    encoder = Encoder(tokenizer, args.tach_tu, args.do_dai, args.toi_da_a)
    encoded = [encoder(row) for row in rows]
    encode_seconds = time.time() - started
    model = AutoModelForSequenceClassification.from_pretrained(args.mo_hinh).eval()
    result = {"tai_lieu": args.tai_lieu, "cap": len(rows), "luong_cpu": torch.get_num_threads(), "ma_hoa_giay": round(encode_seconds, 1)}
    scores, seconds = timed(model, encoded, tokenizer.pad_token_id, args.lo)
    result["fp32"] = {"giay": round(seconds, 1), "cap_moi_giay": round(len(rows) / seconds, 1), "phut_ca_tai_lieu": round((seconds + encode_seconds) / 60, 2)}
    if args.int8:
        quantized = torch.ao.quantization.quantize_dynamic(model, {torch.nn.Linear}, dtype=torch.qint8)
        int8_scores, seconds = timed(quantized, encoded, tokenizer.pad_token_id, args.lo)
        ranks = lambda values: np.argsort(np.argsort(values))  # noqa: E731
        result["int8"] = {"giay": round(seconds, 1), "cap_moi_giay": round(len(rows) / seconds, 1),
                          "phut_ca_tai_lieu": round((seconds + encode_seconds) / 60, 2),
                          "lech_lon_nhat": round(float(np.abs(int8_scores - scores).max()), 4),
                          "spearman": round(float(np.corrcoef(ranks(scores), ranks(int8_scores))[0, 1]), 4)}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
