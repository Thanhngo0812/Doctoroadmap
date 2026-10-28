"""Đo phút CPU của cross-encoder cho 1.000 cặp (chi phí nếu đưa vào sản phẩm), đặt cạnh LightGBM. Cần torch, transformers và mô hình nếp 0 do `ce_hoc.py` lưu.
  python ce_do_cpu.py --mo-hinh=<ra>/e5-dg20/mo-hinh --du-lieu=<thư mục có d01.jsonl> [--so-cap=1000] [--luong=<số luồng CPU>]
Ép chạy CPU, fp32, lô 16, độ dài tối đa 256, một lô khởi động rồi đo; in giây mã hoá và giây suy luận cho `--so-cap` cặp, và phút cho 1.000 cặp (mã hoá cộng suy luận).
Trên laptop chưa có torch: cài bản CPU vào một venv riêng, hoặc chạy trên CPU của máy GPU và ghi rõ số luồng.
"""
import argparse
import json
import sys
import time
from pathlib import Path

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

sys.path.insert(0, str(Path(__file__).resolve().parent))
from e6_cross_encoder import Encoder, batches, collate, read_jsonl  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mo-hinh", required=True)
    ap.add_argument("--du-lieu", required=True)
    ap.add_argument("--so-cap", type=int, default=1000)
    ap.add_argument("--luong", type=int, default=0)
    args = ap.parse_args()
    if args.luong:
        torch.set_num_threads(args.luong)
    rows = read_jsonl(Path(args.du_lieu).expanduser() / "d01.jsonl")[:args.so_cap]
    tok = AutoTokenizer.from_pretrained(args.mo_hinh)
    model = AutoModelForSequenceClassification.from_pretrained(args.mo_hinh, dtype=torch.float32).eval()
    enc = Encoder(tok, False, 256, 64)
    t0 = time.time()
    encoded = [enc(r) for r in rows]
    t_enc = time.time() - t0
    device = torch.device("cpu")
    order = batches([len(e) for e in encoded], 16, None, False)
    with torch.no_grad():
        ids, mask = collate(encoded, order[0], tok.pad_token_id, device)
        model(input_ids=ids, attention_mask=mask)  # khởi động
        t1 = time.time()
        for index in order:
            ids, mask = collate(encoded, index, tok.pad_token_id, device)
            model(input_ids=ids, attention_mask=mask)
    t_inf = time.time() - t1
    kq = {"so_cap": len(rows), "luong": torch.get_num_threads(), "ma_hoa_giay": round(t_enc, 1), "suy_luan_giay": round(t_inf, 1),
          "phut_cho_1000_cap": round((t_enc + t_inf) / len(rows) * 1000 / 60, 2), "torch": torch.__version__}
    print(json.dumps(kq))


if __name__ == "__main__":
    main()
