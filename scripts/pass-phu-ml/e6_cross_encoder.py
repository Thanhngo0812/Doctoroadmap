"""E6 (vòng 2): tinh chỉnh cross-encoder trên nhãn D-01 (lượt A), chạy trên máy GPU của chủ dự án. Không gọi mô hình trả phí.

Đầu vào là `d01.jsonl` và `<doc>.jsonl` do `dung_du_lieu_e6.py` dựng.
- **Đoạn A:** "# Y # @ X @ : <câu định nghĩa của X>", tối đa `--toi-da-a` token. **Đoạn B:** các câu của cửa sổ định nghĩa Y, đã đánh dấu.
  Hết chỗ thì giữ câu theo thứ tự ưu tiên: câu neo có X, câu có X gần neo nhất, câu neo, câu có X khác, rồi câu gần neo. Câu giữ lại theo
  thứ tự gốc. Câu đầu tiên dài quá chỗ thì cắt quanh dấu X.
- **Chia:** bốn nhóm theo sách, cố định và cân số dòng. Mỗi nếp học trên ba nhóm, đoán nhóm còn lại (ngoài mẫu) và ba tài liệu đo.
- **Nhãn:** 5 lớp của D-01; điểm cạnh cứng là xác suất `can_de_hieu`.
- **Học:** đóng băng embedding từ, bf16 autocast, AdamW, warmup tuyến tính rồi giảm tuyến tính. Ghi dự đoán sau **mỗi** epoch, để chọn số epoch
  bằng AP ngoài mẫu trên D-01, không nhìn vàng.
Ra `<ra>/<lượt>/`: `ngoai-mau-nep<k>-e<epoch>.jsonl`, `<doc>-nep<k>-e<epoch>.jsonl` (mỗi dòng `id`, `p` 5 xác suất) và `nhat-ky.json`.
Nếp nào đã có đủ tệp thì bỏ qua, nên chạy lại sau khi đứt là chạy tiếp.
  python e6_cross_encoder.py --mo-hinh=vinai/phobert-base --tach-tu --luot=phobert-s1 --seed=1
  python e6_cross_encoder.py --mo-hinh=intfloat/multilingual-e5-base --luot=e5-s1 --seed=1
  thêm --thu=512 để chạy thử nhanh (512 dòng học, 1 epoch, 1 nếp)
"""
import argparse
import json
import random
import time
from pathlib import Path

import numpy as np
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer, get_linear_schedule_with_warmup

LABELS = ("can_de_hieu", "cong_cu", "khong", "nguoc", "khop_nham")
DEV_DOCS = ("doc-1", "xstk-ch3-1", "doc-4")


def read_jsonl(path):
    with open(path, encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def folds_by_book(rows, count):
    """Gán sách vào `count` nhóm: sách nhiều dòng trước, mỗi sách vào nhóm đang ít dòng nhất. Không phụ thuộc seed."""
    sizes = {}
    for row in rows:
        sizes[row["nhom"]] = sizes.get(row["nhom"], 0) + 1
    totals, assignment = [0] * count, {}
    for book in sorted(sizes, key=lambda b: (-sizes[b], b)):
        fold = min(range(count), key=lambda k: (totals[k], k))
        assignment[book] = fold
        totals[fold] += sizes[book]
    return assignment


class Encoder:
    def __init__(self, tokenizer, joined, max_len, max_a):
        self.tok, self.joined, self.max_len, self.max_a = tokenizer, joined, max_len, max_a
        self.cache = {}
        self.marker = tokenizer("@", add_special_tokens=False)["input_ids"]
        self.dropped = 0
        # Khuôn cặp của RoBERTa, chung cho PhoBERT và XLM-R: <s> A </s></s> B </s>. Tự ghép vì tokenizer của transformers 5 cho XLM-R không
        # còn `build_inputs_with_special_tokens`.
        self.cls, self.sep = tokenizer.cls_token_id, tokenizer.sep_token_id

    def ids(self, text):
        if text not in self.cache:
            self.cache[text] = self.tok(text, add_special_tokens=False)["input_ids"]
        return self.cache[text]

    def field(self, row, name):
        return row[name + "_tu"] if self.joined else row[name]

    def trim(self, ids, budget):
        """Cắt câu dài quanh lần đầu xuất hiện dấu X."""
        size = len(self.marker)
        at = next((i for i in range(len(ids) - size + 1) if ids[i:i + size] == self.marker), 0)
        start = max(0, min(at - budget // 3, len(ids) - budget))
        return ids[start:start + budget]

    def __call__(self, row):
        a_text = f"# {self.field(row, 'y_ten')} # @ {self.field(row, 'x_ten')} @ : {self.field(row, 'x_dinh_nghia')}"
        a_ids = self.ids(a_text)[:self.max_a]
        sentences = [list(self.ids(text)) for text in (row["cau_tu"] if self.joined else row["cau"])]
        budget = self.max_len - len(a_ids) - 4
        anchor, hits = row["cau_neo"], set(row["cau_co_x"])
        center = anchor if anchor is not None else min(hits, default=0)
        nearest = min(hits, key=lambda i: (abs(i - center), i)) if hits else None

        def rank(i):
            if i == anchor and i in hits:
                return 0
            if i == nearest:
                return 1
            if i == anchor:
                return 2
            return 3 if i in hits else 4
        keep, used = [], 0
        for i in sorted(range(len(sentences)), key=lambda i: (rank(i), abs(i - center), i)):
            if used + len(sentences[i]) <= budget:
                keep.append(i)
                used += len(sentences[i])
            elif not keep:
                sentences[i] = self.trim(sentences[i], budget)
                keep.append(i)
                used = len(sentences[i])
        self.dropped += int(len(keep) < len(sentences))
        b_ids = [token for i in sorted(keep) for token in sentences[i]]
        return [self.cls, *a_ids, self.sep, self.sep, *b_ids, self.sep]


def batches(lengths, size, rng, shuffle):
    """Lô theo độ dài gần nhau (đệm ít); khi học thì xáo trong từng khối rồi xáo thứ tự lô."""
    order = list(range(len(lengths)))
    if not shuffle:
        order.sort(key=lambda i: lengths[i])
        return [order[i:i + size] for i in range(0, len(order), size)]
    rng.shuffle(order)
    block = size * 50
    result = []
    for start in range(0, len(order), block):
        part = sorted(order[start:start + block], key=lambda i: lengths[i])
        result += [part[i:i + size] for i in range(0, len(part), size)]
    rng.shuffle(result)
    return result


def collate(encoded, index, pad_id, device):
    width = max(len(encoded[i]) for i in index)
    ids = torch.full((len(index), width), pad_id, dtype=torch.long)
    mask = torch.zeros((len(index), width), dtype=torch.long)
    for row, i in enumerate(index):
        ids[row, :len(encoded[i])] = torch.tensor(encoded[i])
        mask[row, :len(encoded[i])] = 1
    return ids.to(device), mask.to(device)


@torch.no_grad()
def predict(model, encoded, pad_id, device, size):
    model.eval()
    probs = [None] * len(encoded)
    for index in batches([len(e) for e in encoded], size, None, False):
        ids, mask = collate(encoded, index, pad_id, device)
        with torch.autocast(device_type=device.type, dtype=torch.bfloat16, enabled=device.type == "cuda"):
            logits = model(input_ids=ids, attention_mask=mask).logits
        for i, p in zip(index, torch.softmax(logits.float(), dim=-1).cpu().tolist()):
            probs[i] = [round(v, 5) for v in p]
    model.train()
    return probs


def write_predictions(path, rows, probs):
    path.write_text("".join(json.dumps({"id": r["id"], "p": p}) + "\n" for r, p in zip(rows, probs)), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--du-lieu", default=str(Path.home() / "e6/du-lieu"))
    ap.add_argument("--ra", default=str(Path.home() / "e6/ket-qua"))
    ap.add_argument("--mo-hinh", required=True)
    ap.add_argument("--luot", required=True)
    ap.add_argument("--tach-tu", action="store_true", help="dùng bản tách từ (PhoBERT)")
    ap.add_argument("--do-dai", type=int, default=256)
    ap.add_argument("--toi-da-a", type=int, default=64)
    ap.add_argument("--lo", type=int, default=16)
    ap.add_argument("--tich-luy", type=int, default=2)
    ap.add_argument("--lr", type=float, default=3e-5)
    ap.add_argument("--epoch", type=int, default=3)
    ap.add_argument("--warmup", type=float, default=0.06)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--so-nep", type=int, default=4)
    ap.add_argument("--nep", default="", help="chỉ chạy các nếp này, vd 0,1")
    ap.add_argument("--thu", type=int, default=0)
    ap.add_argument("--checkpointing", action="store_true")
    ap.add_argument("--luu-mo-hinh", action="store_true", help="lưu mô hình của nếp đầu tiên chạy (để đo tốc độ CPU)")
    args = ap.parse_args()

    out = Path(args.ra) / args.luot
    out.mkdir(parents=True, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    data = Path(args.du_lieu)
    train_rows = read_jsonl(data / "d01.jsonl")
    dev_rows = {doc: read_jsonl(data / f"{doc}.jsonl") for doc in DEV_DOCS}
    assignment = folds_by_book(train_rows, args.so_nep)
    folds = [int(k) for k in args.nep.split(",")] if args.nep else list(range(args.so_nep))
    epochs = args.epoch
    if args.thu:  # chạy thử: mỗi nhóm sách chỉ giữ `--thu` dòng đầu, để khỏi mã hoá cả tập
        folds, epochs = folds[:1], 1
        per_fold = {}
        for row in train_rows:
            per_fold.setdefault(assignment[row["nhom"]], []).append(row)
        train_rows = [row for rows in per_fold.values() for row in rows[:args.thu]]
        dev_rows = {doc: rows[:args.thu] for doc, rows in dev_rows.items()}

    tokenizer = AutoTokenizer.from_pretrained(args.mo_hinh)
    encoder = Encoder(tokenizer, args.tach_tu, args.do_dai, args.toi_da_a)
    started = time.time()
    train_encoded = [encoder(row) for row in train_rows]
    dev_encoded = {doc: [encoder(row) for row in rows] for doc, rows in dev_rows.items()}
    lengths = [len(e) for e in train_encoded]
    log_path = out / "nhat-ky.json"
    log = json.loads(log_path.read_text(encoding="utf-8")) if log_path.exists() else {"nep": {}}
    log.update({"tham_so": vars(args), "may": torch.cuda.get_device_name(0) if device.type == "cuda" else "cpu",
                "torch": torch.__version__, "chia": assignment, "dong_hoc": len(train_rows),
                "ma_hoa_giay": round(time.time() - started, 1), "do_dai_trung_vi": int(np.median(lengths)),
                "do_dai_p90": int(np.percentile(lengths, 90)), "ti_le_bo_cau": round(encoder.dropped / (len(train_rows) + sum(map(len, dev_rows.values()))), 4)})
    print(json.dumps({k: log[k] for k in ("may", "torch", "dong_hoc", "ma_hoa_giay", "do_dai_trung_vi", "do_dai_p90", "ti_le_bo_cau")}), flush=True)
    label_ids = [LABELS.index(row["nhan"]) for row in train_rows]

    for fold in folds:
        done = [out / f"ngoai-mau-nep{fold}-e{epochs}.jsonl"] + [out / f"{doc}-nep{fold}-e{epochs}.jsonl" for doc in DEV_DOCS]
        if not args.thu and all(path.exists() for path in done):
            print(f"nếp {fold}: đã xong, bỏ qua", flush=True)
            continue
        seed = args.seed * 100 + fold
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        rng = random.Random(seed)
        train_index = [i for i, row in enumerate(train_rows) if assignment[row["nhom"]] != fold]
        held_index = [i for i, row in enumerate(train_rows) if assignment[row["nhom"]] == fold]
        if args.thu:
            train_index, held_index = train_index[:args.thu], held_index[:args.thu]
        model = AutoModelForSequenceClassification.from_pretrained(args.mo_hinh, num_labels=len(LABELS), dtype=torch.float32).to(device)
        model.base_model.embeddings.word_embeddings.weight.requires_grad_(False)
        if args.checkpointing:
            model.gradient_checkpointing_enable()
        decay = [p for n, p in model.named_parameters() if p.requires_grad and not any(k in n for k in ("bias", "LayerNorm"))]
        no_decay = [p for n, p in model.named_parameters() if p.requires_grad and any(k in n for k in ("bias", "LayerNorm"))]
        optimizer = torch.optim.AdamW([{"params": decay, "weight_decay": 0.01}, {"params": no_decay, "weight_decay": 0.0}], lr=args.lr)
        steps_per_epoch = -(-len(train_index) // (args.lo * args.tich_luy))
        scheduler = get_linear_schedule_with_warmup(optimizer, int(args.warmup * steps_per_epoch * epochs), steps_per_epoch * epochs)
        if device.type == "cuda":
            torch.cuda.reset_peak_memory_stats()
        fold_log = {"dong_hoc": len(train_index), "dong_ngoai_mau": len(held_index), "epoch": []}
        model.train()
        for epoch in range(1, epochs + 1):
            epoch_started, losses = time.time(), []
            local = batches([lengths[i] for i in train_index], args.lo, rng, True)
            for step, index in enumerate(local, 1):
                rows = [train_index[i] for i in index]
                ids, mask = collate(train_encoded, rows, tokenizer.pad_token_id, device)
                target = torch.tensor([label_ids[i] for i in rows], device=device)
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
                    rate = step / (time.time() - epoch_started)
                    peak = torch.cuda.max_memory_allocated() / 2**30 if device.type == "cuda" else 0
                    print(f"nếp {fold} epoch {epoch} lô {step}/{len(local)} loss {np.mean(losses[-200:]):.4f} {rate:.2f} lô/giây "
                          f"bộ nhớ đỉnh {peak:.2f} GiB", flush=True)
            train_seconds = time.time() - epoch_started
            predict_started = time.time()
            held_rows = [train_rows[i] for i in held_index]
            write_predictions(out / f"ngoai-mau-nep{fold}-e{epoch}.jsonl", held_rows,
                              predict(model, [train_encoded[i] for i in held_index], tokenizer.pad_token_id, device, args.lo * 2))
            for doc, rows in dev_rows.items():
                write_predictions(out / f"{doc}-nep{fold}-e{epoch}.jsonl", rows,
                                  predict(model, dev_encoded[doc], tokenizer.pad_token_id, device, args.lo * 2))
            fold_log["epoch"].append({"epoch": epoch, "loss": round(float(np.mean(losses)), 4), "hoc_giay": round(train_seconds),
                                      "doan_giay": round(time.time() - predict_started),
                                      "bo_nho_dinh_gib": round(torch.cuda.max_memory_allocated() / 2**30, 2) if device.type == "cuda" else None})
            print(json.dumps({"nep": fold, **fold_log["epoch"][-1]}), flush=True)
        if args.luu_mo_hinh and not (out / "mo-hinh").exists():
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
