"""D-04a: xuất phiếu cạnh ngược thứ tự sách cho agentic, đúng định dạng `task/v4/D-04-dac-ta-nhan-canh-nguoc.md`. 0 USD, không gọi mô hình.

Cặp ngược là cạnh mà R17 (`soften_backward_edges`) làm mềm vì "ngược thứ tự sách". Cả hai nguồn chạy qua A10 thật, dừng ngay tại R17, nên vị trí
dạy và phép xếp "ngược" là của chính A10:
- **nguồn 1** (doc-1, xstk-ch3-1, doc-4): phát lại A9 → A10 như E4/E8 với cạnh pass phụ của LLM v3 và của E5 (`e5-a-hieu-chinh`); gộp trùng (X, Y);
- **nguồn 2** (16 sách học D-01, chưa chạy A8): cặp trong cửa sổ có nhãn lượt A `can_de_hieu` hoặc được E5 đề xuất (dự đoán ngoài mẫu chia theo
  sách, chính sách hiệu chỉnh như E5), nạp làm cạnh `requires` vào artifact danh tính rồi chạy A10 tới R17. Lấy mẫu tối đa 60 cặp mỗi sách, chia
  đều hai tầng cùng chương / khác chương, hạt giống cố định.
Không lấy sách `split = test` của `document-data/manifest.json` (T-01). Phiếu lặp 5%: cùng cặp, `phieu_id` khác, khối X trình bày trước khối Y.
Ghi `phieu.jsonl` (giao agentic), `khoa.jsonl` (Claude giữ), `dem.json`, `manifest.json` vào `tmp/d04-phieu/`. Chạy bằng tmp/venv-ml:
  tmp/venv-ml/Scripts/python.exe scripts/pass-phu-ml/xuat_phieu_d04.py [--ra=tmp/d04-phieu] [--toi-da=60] [--ti-le-lap=0.05]
"""
import hashlib
import json
import random
import sys
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
SEED = 20261015
BACKWARD = "ngược thứ tự sách"
ALLOWED = {"taught", "uncertain"}
DEV_DOCS = {"doc-1": "Toán học", "xstk-ch3-1": "Toán học", "doc-4": "Khoa học xã hội"}
DEV_SYSTEMS = ("llm-v3", "e5-a-hieu-chinh")
KEY_ONLY = ("nguon", "he", "pass", "confidence", "nhan_d01", "p_e5", "e5_de_xuat", "lap_cua")


class _StopAtR17(Exception):
    pass


def holdout_docs(manifest):
    return {book["id"] for book in manifest["books"] if book.get("split") == "test"}


def blind(doc):
    return "sach-" + hashlib.sha256(doc.encode()).hexdigest()[:12]


def phieu_id(doc, x, y, kind="goc"):
    return "p_" + hashlib.sha256(f"{doc}|{x}|{y}|{kind}".encode()).hexdigest()[:16]


def sample_pairs(pairs, cap, seed_key):
    """Tối đa `cap` cặp, chia đều hai tầng `cung_chuong`; tầng thiếu thì lấy bù từ tầng kia. Kết quả theo thứ tự ổn định."""
    rng = random.Random(seed_key)
    ordered = sorted(pairs, key=lambda pair: (pair["x"], pair["y"]))
    same = [pair for pair in ordered if pair["cung_chuong"]]
    other = [pair for pair in ordered if not pair["cung_chuong"]]
    rng.shuffle(same)
    rng.shuffle(other)
    half = cap // 2
    take_same = min(len(same), max(half, cap - len(other)))
    take_other = min(len(other), cap - take_same)
    return sorted(same[:take_same] + other[:take_other], key=lambda pair: (pair["x"], pair["y"]))


def card(doc, field, pair, *, x_first=False, kind="goc"):
    """Phiếu agentic đọc: không có trường nào của khoá. Khoảng cách chỉ ở khoá: cấp 1 của cây mục có khi là cả một phần sách (doc-4), nên
    `cung_chuong` dễ đọc sai, và số đo độ xa có thể kéo nhãn theo nó."""
    blocks = [("y", pair["y_block"]), ("x", pair["x_block"])]
    if x_first:
        blocks.reverse()
    return {"phieu": "D-04", "phieu_id": phieu_id(doc, pair["x"], pair["y"], kind), "doc_id": blind(doc), "linh_vuc": field,
            **dict(blocks)}


def key_row(doc, pair, card_row, original=None):
    return {"phieu_id": card_row["phieu_id"], "doc_id": doc, "x_id": pair["x"], "y_id": pair["y"],
            "cung_chuong": pair["cung_chuong"], "so_muc_giua": pair["so_muc_giua"],
            **{field: pair.get(field) for field in KEY_ONLY if field != "lap_cua"}, "lap_cua": original}


def with_repeats(items, rate, rng):
    """`items` là danh sách (doc, field, pair). Trả phiếu và khoá, gồm phiếu lặp (khối X trước khối Y), đã xáo."""
    cards, keys = [], []
    for doc, field, pair in items:
        row = card(doc, field, pair)
        cards.append(row)
        keys.append(key_row(doc, pair, row))
    count = int(round(rate * len(items)))
    for doc, field, pair in rng.sample(items, count):
        original = phieu_id(doc, pair["x"], pair["y"])
        row = card(doc, field, pair, x_first=True, kind="lap")
        cards.append(row)
        keys.append(key_row(doc, pair, row, original=original))
    order = list(range(len(cards)))
    rng.shuffle(order)
    return [cards[i] for i in order], [keys[i] for i in order]


# --- phần đọc artifact (cần src, underthesea) ---

def capture_r17(run):
    """Chạy `run()` (một lượt tới A10) và bắt đầu vào của R17; dừng A10 ngay sau R17."""
    import doc2roadmap.application.use_cases.build_roadmap as build_roadmap
    original, captured = build_roadmap.soften_backward_edges, {}

    def spy(edges, position):
        frame = sys._getframe(1).f_locals
        hard, soft = original(edges, position)
        captured.update(soft=[edge for edge in soft if edge.get("soft_reason") == BACKWARD], position=position,
                        ancestry=frame["ancestry"], chunk_by_id=frame["chunk_by_id"], nodes=frame["upstream"].payload["nodes"])
        raise _StopAtR17

    build_roadmap.soften_backward_edges = spy
    try:
        run()
    except _StopAtR17:
        pass
    finally:
        build_roadmap.soften_backward_edges = original
    if not captured:
        raise RuntimeError("A10 không tới R17")
    return captured


def describe(captured, x, y, tools):
    """Khối X, Y của phiếu và khoảng cách; None nếu một trong hai cửa sổ không dựng được."""
    nodes = {node["node_id"]: node for node in captured["nodes"]}
    chunks = list(captured["chunk_by_id"].values())
    window = {}
    for node_id in (x, y):
        sentences, anchor = tools.window_sentences(nodes[node_id], chunks, 4, 2)
        if not sentences:
            return None
        window[node_id] = (sentences, anchor)

    def block(node_id):
        node, (sentences, anchor) = nodes[node_id], window[node_id]
        anchor_chunk = captured["chunk_by_id"].get((node.get("anchor") or {}).get("chunk_id"))
        return {"ten": node["name"], "bi_danh": [name for name in tools.names(node)[1:] if name],
                "muc": list(anchor_chunk.section_path) if anchor_chunk else [],
                "cau": [{"i": i, "text": " ".join(sentence.split())} for i, sentence in enumerate(sentences)], "cau_neo": anchor}

    y_block = block(y)
    raw, words = tools.regexes(nodes[x]), tools.word_regexes(nodes[x])
    y_block["cau_co_ten_x"] = [i for i, sentence in enumerate(window[y][0]) if tools.found(raw, sentence) and tools.found_words(words, sentence)]
    ancestry, position = captured["ancestry"], captured["position"]
    same_chapter = bool(ancestry.get(x)) and bool(ancestry.get(y)) and ancestry[x][0] == ancestry[y][0]
    by_order = {chunk.order_index: chunk for chunk in chunks if getattr(chunk, "role", "noi_dung") == "noi_dung"}
    ends = {tuple(by_order[position[n][0]].section_path) for n in (x, y) if position[n][0] in by_order}
    between = {tuple(chunk.section_path) for order, chunk in by_order.items() if position[y][0] < order < position[x][0]} - ends
    return {"x": x, "y": y, "x_block": block(x), "y_block": y_block, "cung_chuong": same_chapter, "so_muc_giua": len(between)}


def tools_module():
    sys.path.insert(0, str(ROOT / "src"))
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    sys.path.insert(0, str(ROOT / "scripts/doc-lo-trinh"))
    import dung_bang_cap
    from doc2roadmap.domain.mentions import _names
    return SimpleNamespace(window_sentences=dung_bang_cap.window_sentences, regexes=dung_bang_cap.regexes,
                           word_regexes=dung_bang_cap.word_regexes, found=dung_bang_cap.found, found_words=dung_bang_cap.found_words,
                           names=_names)


def source_1(tools, versions):
    """Mọi cạnh R17 làm mềm vì ngược thứ tự sách, ở hai hệ của ba tài liệu phát triển; gộp trùng theo (X, Y)."""
    import phat_lai_e4 as e4
    from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore
    out, counts = [], {}
    for doc, field in DEV_DOCS.items():
        root, version, _, _ = e4.GOLD_DOCS[doc]
        secondary = JsonArtifactStore(Path(root)).load_graph(doc, version)
        versions[doc] = {"kho": root, "pass_phu_v3": version}
        merged, captured = {}, None
        for system in DEV_SYSTEMS:
            edges = (secondary.payload["secondary_edges"] if system == "llm-v3"
                     else json.loads(Path(f"tmp/pass-phu-ml/e4/{system}/{doc}-canh.json").read_text(encoding="utf-8")))
            captured = capture_r17(lambda: e4.replay(doc, edges, secondary=secondary))
            counts[f"{doc}|{system}"] = len(captured["soft"])
            for edge in captured["soft"]:
                row = merged.setdefault((edge["source"], edge["target"]), {"he": set(), "pass": set(), "confidence": None})
                row["he"].add(system)
                row["pass"].add("phu" if str(edge.get("session_id", "")).startswith("secondary") else "chinh")
                if edge.get("confidence") is not None:
                    row["confidence"] = max(row["confidence"] or 0, edge["confidence"])
        for (x, y), extra in sorted(merged.items()):
            pair = describe(captured, x, y, tools)
            if pair is None:
                counts[f"{doc}|bo_khong_cua_so"] = counts.get(f"{doc}|bo_khong_cua_so", 0) + 1
                continue
            out.append((doc, field, {**pair, "nguon": 1, "he": sorted(extra["he"]), "pass": sorted(extra["pass"]),
                                     "confidence": extra["confidence"]}))
    return out, counts


def e5_out_of_fold():
    """Xác suất ngoài mẫu của E5 trên dòng học D-01 (bỏ một sách), và cặp E5 đề xuất theo chính sách hiệu chỉnh, từng sách."""
    import numpy as np
    from sklearn.isotonic import IsotonicRegression
    import thi_nghiem_e5 as e5
    _, old_features = e5.e2b.load(e5.OLD_DOCS, "y-dinh-cung")
    train = e5.load_d01("a", False, 1.0, None, None)
    features = [c for c in old_features if c in train.columns]
    train[features] = train[features].apply(__import__("pandas").to_numeric, errors="coerce")
    oof = np.zeros(len(train))
    for book in sorted(train.doc.unique()):
        mask = (train.doc == book).to_numpy()
        _, oof[mask] = e5.e2b.fit_predict("lightgbm", train[~mask], train[mask], features)
    calibrated = IsotonicRegression(out_of_bounds="clip").fit(oof, train.nhan.to_numpy()).predict(oof)
    result = {}
    for book in sorted(train.doc.unique()):
        mask = (train.doc == book).to_numpy()
        rows = train[mask].assign(p=calibrated[mask], raw=oof[mask]).sort_values("raw", ascending=False)
        keep = int(round(float(rows.p.sum())))
        for rank, (x, y, p) in enumerate(zip(rows.x, rows.y, rows.p)):
            result[(book, x, y)] = (round(float(p), 4), rank < keep)
    return result


def source_2(tools, versions, holdout, cap):
    import pandas as pd
    import phat_lai_e4 as e4
    import xuat_phieu
    from doc2roadmap.application.use_cases.build_roadmap import BuildRoadmap
    scores = e5_out_of_fold()
    out, counts = [], {}
    for path in sorted(Path("tmp/pass-phu-ml/bang-d01").glob("*.csv")):
        doc = path.stem
        if doc in holdout:
            continue
        table = pd.read_csv(path)
        table = table[(table.loai == "thuc") & (table.trong_cua_so == 1)].drop_duplicates(["x", "y"])
        field = str(table.linh_vuc.iloc[0]) if len(table) else ""
        artifact = xuat_phieu.latest_identity("artifacts", doc)
        versions[doc] = {"kho": "artifacts", "danh_tinh": artifact.version}
        nodes = {node["node_id"]: node for node in artifact.payload["nodes"]}
        usable = lambda n: nodes.get(n, {}).get("learnable") and nodes[n].get("teaching_status") in ALLOWED  # noqa: E731
        proposed = {}
        for x, y, label in zip(table.x, table.y, table.nhan_a.fillna("")):
            p, chosen = scores.get((doc, x, y), (None, False))
            if (label == "can_de_hieu" or chosen) and usable(x) and usable(y) and x != y:
                proposed[(x, y)] = {"nhan_d01": label or None, "p_e5": p, "e5_de_xuat": chosen}
        edges = [{"source": x, "target": y, "edge_type": "requires"} for x, y in sorted(proposed)]
        upstream = SimpleNamespace(payload={**artifact.payload, "requires_edges": edges}, version=artifact.version,
                                   manifest=artifact.manifest, path=None)
        captured = capture_r17(lambda: BuildRoadmap(e4.MemoryStore("artifacts", 10_000)).execute(doc, upstream=upstream))
        backward = []
        for edge in captured["soft"]:
            pair = describe(captured, edge["source"], edge["target"], tools)
            if pair is not None:
                backward.append({**pair, **proposed[(edge["source"], edge["target"])], "nguon": 2, "he": ["d01"], "pass": [],
                                 "confidence": None})
        chosen = sample_pairs(backward, cap, f"{SEED}-{doc}")
        counts[doc] = {"de_xuat": len(edges), "nguoc": len(captured["soft"]), "nguoc_co_cua_so": len(backward),
                       "lay": len(chosen), "cung_chuong": sum(pair["cung_chuong"] for pair in chosen)}
        out += [(doc, field, pair) for pair in chosen]
    return out, counts


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    options = dict(arg[2:].split("=", 1) for arg in sys.argv[1:] if arg.startswith("--") and "=" in arg)
    out = Path(options.get("ra", "tmp/d04-phieu"))
    cap, rate = int(options.get("toi-da", "60")), float(options.get("ti-le-lap", "0.05"))
    holdout = holdout_docs(json.loads((ROOT / "document-data/manifest.json").read_text(encoding="utf-8")))
    tools, versions = tools_module(), {}
    first, first_counts = source_1(tools, versions)
    second, second_counts = source_2(tools, versions, holdout, cap)
    items = first + second
    if any(doc in holdout for doc, _, _ in items):
        raise RuntimeError("phiếu chứa sách T-01")
    cards, keys = with_repeats(items, rate, random.Random(SEED))
    out.mkdir(parents=True, exist_ok=True)
    for name, rows in (("phieu.jsonl", cards), ("khoa.jsonl", keys)):
        (out / name).write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    counts = {"nguon_1_canh_r17": first_counts, "nguon_2": second_counts,
              "phieu": {"tong": len(cards), "lap": sum(1 for k in keys if k["lap_cua"]),
                        "theo_nguon": dict(Counter(str(k["nguon"]) for k in keys if not k["lap_cua"])),
                        "theo_sach": dict(Counter(k["doc_id"] for k in keys if not k["lap_cua"]))}}
    (out / "dem.json").write_text(json.dumps(counts, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    manifest = {"phieu": "D-04", "hat_giong": SEED, "toi_da_moi_sach": cap, "ti_le_lap": rate, "artifact": versions,
                "sach_bo_qua_t01": sorted(holdout), "sha256": {name: sha256(out / name) for name in ("phieu.jsonl", "khoa.jsonl")}}
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(counts, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
