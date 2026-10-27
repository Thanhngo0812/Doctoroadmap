"""DG-20 phần C: học cross-encoder `intfloat/multilingual-e5-base` cho pass phụ (M3), 4 phần theo cuốn, chạy trên máy GPU trong `~/e6/venv`. 0 USD.

Dùng lại nguyên bộ mã hoá và vòng học của E6 (`e6_cross_encoder.py`, phải nằm cùng thư mục): đoạn A "# Y # @ X @ : <định nghĩa X>", đoạn B là các câu của cửa sổ Y
có đánh dấu, độ dài 256, đóng băng embedding từ, bf16 autocast, AdamW 3e-5, warmup 6%, lô 16 x tích luỹ 2, 3 epoch, 5 nhãn D-01 (điểm cạnh cứng = p[can_de_hieu]).
Khác E6:
- chỉ D-01, KHÔNG đọc tài liệu phát triển (thư mục dữ liệu chỉ cần `d01.jsonl`);
- chia 4 phần theo `chia-4-phan.json` (4 cuốn mỗi phần, seed 20261027) thay vì cân số dòng, để LightGBM và logistic chấm trên đúng 4 phần này;
- seed mỗi nếp = 20261027 + nếp; ghi dự đoán ngoài mẫu sau MỖI epoch (`ngoai-mau-nep<k>-e<epoch>.jsonl`); nếp đã đủ tệp thì bỏ qua (chạy lại để tiếp tục);
- `--luu-mo-hinh-nep=0` (mặc định) lưu mô hình nếp 0 sau epoch cuối để đo phút CPU (`ce_do_cpu.py`).
  cd ~/dg20 && ~/e6/venv/bin/python ce_hoc.py --du-lieu=~/dg20/du-lieu --ra=~/dg20/ket-qua --luot=e5-dg20
  thêm --thu-nho để kiểm nhanh (256 dòng mỗi phần, 1 epoch, 1 nếp, ra thư mục `<luot>-thu-nho`)
"""
import argparse
import json
import random
import sys
import time
from pathlib import Path

import numpy as np
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer, get_linear_schedule_with_warmup

sys.path.insert(0, str(Path(__file__).resolve().parent))
from e6_cross_encoder import LABELS, Encoder, batches, collate, predict, read_jsonl, write_predictions  # noqa: E402

SEED = 20261027


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--du-lieu", default=str(Path.home() / "dg20/du-lieu"), help="thư mục chứa d01.jsonl (chỉ D-01)")
    ap.add_argument("--chia", default=str(Path(__file__).with_name("chia-4-phan.json")))
    ap.add_argument("--ra", default=str(Path.home() / "dg20/ket-qua"))
    ap.add_argument("--luot", default="e5-dg20")
    ap.add_argument("--mo-hinh", default="intfloat/multilingual-e5-base")
    ap.add_argument("--do-dai", type=int, default=256)
    ap.add_argument("--toi-da-a", type=int, default=64)
    ap.add_argument("--lo", type=int, default=16)
    ap.add_argument("--tich-luy", type=int, default=2)
    ap.add_argument("--lr", type=float, default=3e-5)
    ap.add_argument("--epoch", type=int, default=3)
    ap.add_argument("--warmup", type=float, default=0.06)
    ap.add_argument("--nep", default="", help="chỉ chạy các nếp này, vd 0,1")
    ap.add_argument("--luu-mo-hinh-nep", type=int, default=0, help="nếp lưu mô hình để đo CPU; -1 là không lưu")
    ap.add_argument("--thu-nho", action="store_true")
    ap.add_argument("--checkpointing", action="store_true")
    args = ap.parse_args()

    chia = json.loads(Path(args.chia).read_text(encoding="utf-8"))
    assert chia["seed"] == SEED and len(chia["phan"]) == 4 and all(len(p) == 4 for p in chia["phan"])
    fold_of = {book: k for k, books in enumerate(chia["phan"]) for book in books}
    out = Path(args.ra).expanduser() / (args.luot + ("-thu-nho" if args.thu_nho else ""))
    out.mkdir(parents=True, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    rows = read_jsonl(Path(args.du_lieu).expanduser() / "d01.jsonl")
    assert {r["nhom"] for r in rows} <= set(fold_of), "có cuốn ngoài 16 cuốn D-01"
    assert {r["nguon"] for r in rows} == {"d01"}
    folds = [int(k) for k in args.nep.split(",")] if args.nep else [0, 1, 2, 3]
    epochs = args.epoch
    if args.thu_nho:  # mỗi phần chỉ giữ 256 dòng đầu, 1 epoch, 1 nếp
        per = {}
        for r in rows:
            per.setdefault(fold_of[r["nhom"]], []).append(r)
        rows = [r for part in per.values() for r in part[:256]]
        folds, epochs = folds[:1], 1

    tokenizer = AutoTokenizer.from_pretrained(args.mo_hinh)
    encoder = Encoder(tokenizer, False, args.do_dai, args.toi_da_a)
    started = time.time()
    encoded = [encoder(r) for r in rows]
    lengths = [len(e) for e in encoded]
    label_ids = [LABELS.index(r["nhan"]) for r in rows]
    log_path = out / "nhat-ky.json"
    log = json.loads(log_path.read_text(encoding="utf-8")) if log_path.exists() else {"nep": {}}
    log.update({"tham_so": vars(args), "may": torch.cuda.get_device_name(0) if device.type == "cuda" else "cpu", "torch": torch.__version__,
                "chia": chia["phan"], "dong": len(rows), "ma_hoa_giay": round(time.time() - started, 1),
                "do_dai_trung_vi": int(np.median(lengths)), "do_dai_p90": int(np.percentile(lengths, 90))})
    print(json.dumps({k: log[k] for k in ("may", "torch", "dong", "ma_hoa_giay", "do_dai_trung_vi", "do_dai_p90")}), flush=True)

    for fold in folds:
        if all((out / f"ngoai-mau-nep{fold}-e{e}.jsonl").exists() for e in range(1, epochs + 1)) and not args.thu_nho:
            print(f"nếp {fold}: đã xong, bỏ qua", flush=True)
            continue
        seed = SEED + fold
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        rng = random.Random(seed)
        train_index = [i for i, r in enumerate(rows) if fold_of[r["nhom"]] != fold]
        held_index = [i for i, r in enumerate(rows) if fold_of[r["nhom"]] == fold]
        assert not {rows[i]["nhom"] for i in train_index} & {rows[i]["nhom"] for i in held_index}, "rò rỉ cuốn giữa học và ngoài mẫu"
        model = AutoModelForSequenceClassification.from_pretrained(args.mo_hinh, num_labels=len(LABELS), dtype=torch.float32).to(device)
        model.base_model.embeddings.word_embeddings.weight.requires_grad_(False)
        if args.checkpointing:
            model.gradient_checkpointing_enable()
        decay = [p for n, p in model.named_parameters() if p.requires_grad and not any(k in n for k in ("bias", "LayerNorm"))]
        no_decay = [p for n, p in model.named_parameters() if p.requires_grad and any(k in n for k in ("bias", "LayerNorm"))]
        optimizer = torch.optim.AdamW([{"params": decay, "weight_decay": 0.01}, {"params": no_decay, "weight_decay": 0.0}], lr=args.lr)
        steps = -(-len(train_index) // (args.lo * args.tich_luy))
        scheduler = get_linear_schedule_with_warmup(optimizer, int(args.warmup * steps * epochs), steps * epochs)
        if device.type == "cuda":
            torch.cuda.reset_peak_memory_stats()
        fold_log = {"dong_hoc": len(train_index), "dong_ngoai_mau": len(held_index), "cuon_ngoai_mau": chia["phan"][fold], "epoch": []}
        model.train()
        for epoch in range(1, epochs + 1):
            t0, losses = time.time(), []
            local = batches([lengths[i] for i in train_index], args.lo, rng, True)
            for step, index in enumerate(local, 1):
                idx = [train_index[i] for i in index]
                ids, mask = collate(encoded, idx, tokenizer.pad_token_id, device)
                target = torch.tensor([label_ids[i] for i in idx], device=device)
                with torch.autocast(device_type=device.type, dtype=torch.bfloat16, enabled=device.type == "cuda"):
                    logits = model(input_ids=ids, attention_mask=mask).logits
                loss = torch.nn.functional.cross_entropy(logits.float(), target)
                (loss / args.tich_luy).backward()
                losses.append(loss.item())
                if step % args.tich_luy == 0 or step == len(local):
                    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                    optimizer.step()
                    scheduler.step()
                    optimizer.zero_grad(set_to_none=True)
                if step % 200 == 0:
                    print(f"nếp {fold} epoch {epoch} lô {step}/{len(local)} loss {np.mean(losses[-200:]):.4f} {step / (time.time() - t0):.2f} lô/giây", flush=True)
            t_train = time.time() - t0
            t1 = time.time()
            held = [rows[i] for i in held_index]
            write_predictions(out / f"ngoai-mau-nep{fold}-e{epoch}.jsonl", held,
                              predict(model, [encoded[i] for i in held_index], tokenizer.pad_token_id, device, args.lo * 2))
            fold_log["epoch"].append({"epoch": epoch, "loss": round(float(np.mean(losses)), 4), "hoc_giay": round(t_train), "doan_giay": round(time.time() - t1),
                                      "bo_nho_dinh_gib": round(torch.cuda.max_memory_allocated() / 2**30, 2) if device.type == "cuda" else None})
            print(json.dumps({"nep": fold, **fold_log["epoch"][-1]}), flush=True)
        if fold == args.luu_mo_hinh_nep and not (out / "mo-hinh").exists():
            model.save_pretrained(out / "mo-hinh")
            tokenizer.save_pretrained(out / "mo-hinh")
        log["nep"][str(fold)] = fold_log
        log_path.write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
        del model, optimizer
        if device.type == "cuda":
            torch.cuda.empty_cache()
    log_path.write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
