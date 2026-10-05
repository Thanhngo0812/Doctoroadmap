"""Đặc trưng ngữ nghĩa cho bảng cặp E0: embedding tại máy bằng bộ mã hoá cỡ BERT (mặc định `intfloat/multilingual-e5-base`). 0 USD.

Văn bản giáo trình không rời máy: mô hình tải một lần từ Hugging Face rồi chạy CPU. Bộ mã hoá cỡ BERT được phép cho cả seminar (thầy trả lời
2026-10-02) và không phải LLM sinh văn bản. Mỗi dòng có hướng X→Y nhận:
- `sem_tenx_neoy`: cosine(tên X, câu neo của Y) — X có là phần cốt lõi trong định nghĩa của Y;
- `sem_neox_neoy`: cosine(câu neo X, câu neo Y) — hai định nghĩa gần nhau tới đâu;
- `sem_tenx_teny`: cosine(tên X, tên Y);
- `sem_caux_neoy`: cosine(câu của cửa sổ Y có tên X gần neo nhất, câu neo Y) — câu nhắc X có thuộc phần định nghĩa không (trống nếu không có);
- `sem_tenx_cuasoy_max`, `sem_tenx_cuasoy_tb`: cosine lớn nhất và trung bình giữa tên X và các câu của cửa sổ Y;
- `sem_neox_cuasoy_max`: cosine lớn nhất giữa câu neo X và các câu của cửa sổ Y.
e5 cần tiền tố; mọi chuỗi dùng "query: " vì phép so là đối xứng. Ghi `tmp/pass-phu-ml/bang/<doc>-ngu-nghia.csv`, ghép vào bảng theo (pair_id, x, y).
Chạy từ gốc repo: .venv/Scripts/python.exe scripts/pass-phu-ml/dac_trung_ngu_nghia.py [doc ...] [--mo-hinh=intfloat/multilingual-e5-base]
"""
import csv
import sys
from pathlib import Path

import torch
from transformers import AutoModel, AutoTokenizer

sys.path.insert(0, "src")
sys.path.insert(0, "scripts/pass-phu-ml")
from dung_bang_cap import DOCS, found, regexes, window_sentences  # noqa: E402
from doc2roadmap.domain.secondary import select_secondary_pairs  # noqa: E402
from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore  # noqa: E402


class Encoder:
    def __init__(self, name):
        torch.set_num_threads(12)
        self.tokenizer = AutoTokenizer.from_pretrained(name)
        self.model = AutoModel.from_pretrained(name).eval()
        self.cache = {}

    def __call__(self, texts):
        missing = sorted({text for text in texts if text not in self.cache}, key=len)
        for start in range(0, len(missing), 32):
            batch = missing[start:start + 32]
            tokens = self.tokenizer(["query: " + text for text in batch], padding=True, truncation=True, max_length=256,
                                    return_tensors="pt")
            with torch.no_grad():
                hidden = self.model(**tokens).last_hidden_state
            mask = tokens["attention_mask"].unsqueeze(-1).float()
            vectors = torch.nn.functional.normalize((hidden * mask).sum(1) / mask.sum(1), dim=-1)
            for text, vector in zip(batch, vectors):
                self.cache[text] = vector
        return torch.stack([self.cache[text] for text in texts]) if texts else torch.zeros((0, 1))


def build(doc, encoder):
    root, version, _, _ = DOCS[doc]
    artifact = JsonArtifactStore(Path(root)).load_graph(doc, version)
    payload, config = artifact.payload, artifact.manifest["config"]
    chunks_version = config["chunks_version"]
    chunk_root = Path(root) if (Path(root) / "chunks" / doc / f"v{chunks_version}").exists() else Path("artifacts")
    chunks = JsonArtifactStore(chunk_root).load_chunks(doc, chunks_version).result.chunks
    before, after = config.get("definition_before", 4), config.get("definition_after", 2)
    nodes = payload["nodes"]
    node_by_id = {node["node_id"]: node for node in nodes}
    del payload["decision_log"]
    pairs, _ = select_secondary_pairs(nodes, payload.get("suspected_pairs", []), payload.get("pair_cluster_ledger", []), [],
                                      route=payload["routing"]["route"])
    windows = {node_id: window_sentences(node, chunks, before, after) for node_id, node in node_by_id.items()}
    patterns = {node_id: regexes(node) for node_id, node in node_by_id.items()}
    name = {node_id: " ".join(node["name"].split()) for node_id, node in node_by_id.items()}
    anchor = {node_id: " ".join(((node.get("anchor") or {}).get("sentence") or node["name"]).split()) for node_id, node in node_by_id.items()}
    texts = list(name.values()) + list(anchor.values()) + [" ".join(s.split()) for rows, _ in windows.values() for s in rows]
    encoder([text for text in texts if text])

    def vector(text):
        return encoder([text])[0]

    window_vectors = {node_id: encoder([" ".join(s.split()) for s in rows]) for node_id, (rows, _) in windows.items() if rows}
    rows = []
    for pair in pairs:
        for x, y in ((pair["left"], pair["right"]), (pair["right"], pair["left"])):
            nx_, ax, ay = vector(name[x]), vector(anchor[x]), vector(anchor[y])
            sentences, anchor_index = windows[y]
            hits = [i for i, sentence in enumerate(sentences) if found(patterns[x], sentence)]
            nearest = min(hits, key=lambda i: abs(i - (anchor_index or 0))) if hits else None
            row = {"pair_id": pair["pair_id"], "x": x, "y": y,
                   "sem_tenx_neoy": float(nx_ @ ay), "sem_neox_neoy": float(ax @ ay), "sem_tenx_teny": float(nx_ @ vector(name[y])),
                   "sem_caux_neoy": "" if nearest is None else float(window_vectors[y][nearest] @ ay)}
            if y in window_vectors:
                to_name, to_anchor = window_vectors[y] @ nx_, window_vectors[y] @ ax
                row.update(sem_tenx_cuasoy_max=float(to_name.max()), sem_tenx_cuasoy_tb=float(to_name.mean()),
                           sem_neox_cuasoy_max=float(to_anchor.max()))
            else:
                row.update(sem_tenx_cuasoy_max="", sem_tenx_cuasoy_tb="", sem_neox_cuasoy_max="")
            rows.append(row)
    return rows


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    options = dict(arg[2:].split("=", 1) for arg in sys.argv[1:] if arg.startswith("--") and "=" in arg)
    encoder = Encoder(options.get("mo-hinh", "intfloat/multilingual-e5-base"))
    for doc in [arg for arg in sys.argv[1:] if not arg.startswith("--")] or ["doc-1", "nhap-mon-ml", "xstk-ch3-1", "doc-4"]:
        rows = build(doc, encoder)
        path = Path("tmp/pass-phu-ml/bang") / f"{doc}-ngu-nghia.csv"
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        print(f"{doc}: {len(rows)} dòng, {len(encoder.cache)} chuỗi đã mã hoá", flush=True)


if __name__ == "__main__":
    main()
