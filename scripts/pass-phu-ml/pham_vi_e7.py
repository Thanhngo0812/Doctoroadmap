"""E7 (vòng 2), khảo sát phạm vi: với cặp hợp đồng cho phép mà tên X không có trong cửa sổ của Y, mỗi bộ sinh ứng viên bắt được bao nhiêu cạnh vàng
"X ngoài cửa sổ" của phép quy lỗi, và sinh bao nhiêu cặp. 0 USD, không gọi mô hình.

Bốn bộ sinh:
- `chunk`: tên X (khớp theo ranh giới từ) có trong chunk neo hay chunk dạy của Y, ngoài cửa sổ;
- `mot_phan_ten`: một phần tên X có trong cửa sổ: tiền tố, hậu tố từ 2 âm tiết, hoặc tên bỏ từ chung đầu ("sự", "tính", "cái"…);
- `cap_luong`: cặp nghi ngờ sẵn có của luồng (`suspected_pairs`);
- hợp của các bộ trên.
Cần bảng `tmp/pass-phu-ml/bang/<doc>.csv` (`--tach-tu`) và bảng cạnh của `quy_loi_thuong_nguon.py --tach-tu`. Chạy bằng tmp/venv-ml:
  tmp/venv-ml/Scripts/python.exe scripts/pass-phu-ml/pham_vi_e7.py
"""
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

sys.argv.append("--tach-tu")
sys.path.insert(0, "src")
sys.path.insert(0, "scripts/pass-phu-ml")
import dung_bang_cap as dbc  # noqa: E402
from phat_lai_e4 import GOLD_DOCS  # noqa: E402
from doc2roadmap.domain.canonical import alias_kind  # noqa: E402
from doc2roadmap.domain.mentions import _mention_normalize, _names  # noqa: E402
from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore  # noqa: E402

GENERIC = {"sự", "tính", "cái", "các", "những", "phép", "việc"}
DOCS = ("doc-1", "xstk-ch3-1", "doc-4")


def partial_forms(node):
    """Phần tên đủ dài để khớp riêng: tiền tố và hậu tố từ 2 âm tiết của tên từ 3 âm tiết, và tên bỏ từ chung đầu."""
    forms = set()
    for value in _names(node):
        value = " ".join((value or "").split())
        if not value or alias_kind(value) == "symbol":
            continue
        words, full = value.split(), _mention_normalize(value)
        parts = []
        if len(words) >= 3:
            parts += [" ".join(words[:k]) for k in range(2, len(words))]
            parts += [" ".join(words[k:]) for k in range(1, len(words) - 1)]
        if len(words) >= 2 and _mention_normalize(words[0]) in GENERIC:
            parts.append(" ".join(words[1:]))
        forms |= {p for p in parts if _mention_normalize(p) != full and not all(_mention_normalize(w) in GENERIC for w in p.split())}
    return sorted(forms)


def named_in(raw, word, sentences, normalized):
    return any(any(p.search(n) for p in raw) and dbc.found_words(word, s) for s, n in zip(sentences, normalized))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    total = defaultdict(int)
    for doc in DOCS:
        root, version, _, _ = GOLD_DOCS[doc]
        artifact = JsonArtifactStore(Path(root)).load_graph(doc, version)
        payload, config = artifact.payload, artifact.manifest["config"]
        chunk_root = Path(root) if (Path(root) / "chunks" / doc / f"v{config['chunks_version']}").exists() else Path("artifacts")
        chunks = JsonArtifactStore(chunk_root).load_chunks(doc, config["chunks_version"]).result.chunks
        chunk_by_id = {chunk.chunk_id: chunk for chunk in chunks}
        nodes = {node["node_id"]: node for node in payload["nodes"]}
        table = pd.read_csv(f"tmp/pass-phu-ml/bang/{doc}.csv")
        gold = pd.read_csv(f"tmp/pass-phu-ml/quy-loi/{doc}-canh.csv")
        gold_outside = {(r.x, r.y) for r in gold.itertuples() if str(r.nguyen_nhan_thuong_nguon).startswith("x_ngoai")}
        inside = {(r.x, r.y) for r in table.itertuples() if r.x_trong_ywin_tu > 0}
        pairs = {frozenset((p["left"], p["right"])) for p in payload.get("suspected_pairs", [])}
        targets = [y for y, n in nodes.items() if n.get("teaching_status") not in dbc.NOT_TARGET and n.get("learnable")]
        learnable = [x for x, n in nodes.items() if n.get("learnable")]
        raw = {x: dbc.regexes(nodes[x]) for x in learnable}
        word = {x: dbc.word_regexes(nodes[x]) for x in learnable}
        forms = {x: [(dbc.regexes({"name": f}), dbc.word_regexes({"name": f})) for f in partial_forms(nodes[x])] for x in learnable}
        made = defaultdict(set)
        for y in targets:
            window, _ = dbc.window_sentences(nodes[y], chunks, config.get("definition_before", 4), config.get("definition_after", 2))
            if not window:
                continue
            window_norm = [_mention_normalize(s) for s in window]
            chunk_ids = set(nodes[y].get("defining_chunk_ids", [])) | {(nodes[y].get("anchor") or {}).get("chunk_id")}
            chunk_sentences = [chunk_by_id[c].text[sp.start:sp.end] for c in chunk_ids if c in chunk_by_id
                               for sp in dbc.SPLITTER.split(chunk_by_id[c].text)]
            chunk_norm = [_mention_normalize(s) for s in chunk_sentences]
            for x in learnable:
                if x == y or (x, y) in inside:
                    continue
                if named_in(raw[x], word[x], chunk_sentences, chunk_norm):
                    made["chunk"].add((x, y))
                if any(named_in(rf, wf, window, window_norm) for rf, wf in forms[x]):
                    made["mot_phan_ten"].add((x, y))
                if frozenset((x, y)) in pairs:
                    made["cap_luong"].add((x, y))
        made["chunk_hoac_mot_phan"] = made["chunk"] | made["mot_phan_ten"]
        made["hop"] = made["chunk_hoac_mot_phan"] | made["cap_luong"]
        print(f"{doc}: cạnh vàng ngoài cửa sổ {len(gold_outside)}")
        for key in ("chunk", "mot_phan_ten", "cap_luong", "chunk_hoac_mot_phan", "hop"):
            caught = len(made[key] & gold_outside)
            print(f"  {key:20s} bắt {caught:2d}/{len(gold_outside)} | sinh {len(made[key]):6d} cặp")
            total[(key, "bat")] += caught
            total[(key, "sinh")] += len(made[key])
        total["vang"] += len(gold_outside)
    print("tổng:", {f"{k[0]}_{k[1]}" if isinstance(k, tuple) else k: v for k, v in total.items()})


if __name__ == "__main__":
    main()
