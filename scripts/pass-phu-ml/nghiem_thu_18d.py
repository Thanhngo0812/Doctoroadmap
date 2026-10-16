"""Vé 18d: nghiệm thu stage pass phụ không LLM của sản phẩm so với E5 nghiên cứu (lượt `e5-d01-a`, chính sách hiệu chỉnh). 0 USD.

Với mỗi tài liệu vàng: chạy `BuildSecondaryMLEdges` trên artifact pass chính đã dùng trong nghiên cứu, ghi vào kho thử riêng; rồi so
- điểm từng chiều ứng viên với `tmp/pass-phu-ml/diem/e5-d01-a/<doc>.csv` (chênh tối đa);
- số dương ước lượng và ngưỡng với `nguong.json` (nghiên cứu tính trên cặp LLM đã hỏi, sản phẩm trên cặp chưa bị cạnh pass chính tỉa);
- tập cạnh (X, Y) với cạnh của bộ lắp nghiên cứu `tmp/pass-phu-ml/e4/e5-a-hieu-chinh/<doc>-canh.json`;
- E4 (phát lại A9 → A10 → chấm) với dòng `e5-a-hieu-chinh` của `tmp/pass-phu-ml/ket-qua/sua-y.jsonl` (sau khi sửa bộ khớp, mục 8.11); tiêu chí ±0,03 trên Q7, Q7b, bao đóng P, R.
In số đếm và số đo, không in văn bản giáo trình. Chạy từ gốc repo:
  .venv/Scripts/python.exe scripts/pass-phu-ml/nghiem_thu_18d.py [doc ...] [--kho=tmp/v4-18d]
"""
import csv
import json
import sys
from pathlib import Path
from time import perf_counter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from phat_lai_e4 import replay, score_payload, summary  # noqa: E402  (đặt src vào sys.path)
from doc2roadmap.application.use_cases.build_secondary_ml_edges import BuildSecondaryMLEdges  # noqa: E402
from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore  # noqa: E402
from doc2roadmap.infrastructure.secondary_model import LightGBMSecondaryScorer  # noqa: E402
from doc2roadmap.infrastructure.secondary_tokenizer import VietnameseWordTokenizer  # noqa: E402

MAIN = {"doc-1": ("artifacts/v3-r12-final-evaluation", 1), "xstk-ch3-1": ("artifacts", 41), "doc-4": ("artifacts", 7)}
METRICS = ("Q7", "Q7b", "bao_dong_P", "bao_dong_R")
RESEARCH = Path("tmp/pass-phu-ml")


def run(doc, root):
    source, version = MAIN[doc]
    main_artifact = JsonArtifactStore(Path(source)).load_graph(doc, version)
    store = JsonArtifactStore(root / doc)
    store.load_chunks = JsonArtifactStore(Path("artifacts")).load_chunks
    stage = BuildSecondaryMLEdges(store, LightGBMSecondaryScorer(), VietnameseWordTokenizer())
    started = perf_counter()
    artifact, reused = stage.execute(doc, upstream=main_artifact)
    return artifact, perf_counter() - started, reused


def compare(doc, artifact):
    payload = artifact.payload
    product = {}
    for row in payload["secondary_log"]:
        left, right = row.get("score_left_to_right"), row.get("score_right_to_left")
        pair_id = row["pair_id"]
        product.setdefault(pair_id, {})["lr"] = left
        product[pair_id]["rl"] = right
    with open(RESEARCH / f"diem/e5-d01-a/{doc}.csv", encoding="utf-8") as handle:
        research = {(r["pair_id"], r["x"], r["y"]): float(r["score"]) for r in csv.DictReader(handle)}
    pairs = {(p["pair_id"]): p for p in payload.get("suspected_pairs", [])}
    worst, compared = 0.0, 0
    for row in payload["secondary_log"]:
        for key, direction in (("score_left_to_right", 0), ("score_right_to_left", 1)):
            value = row.get(key)
            if value is None:
                continue
            pair = pairs.get(row["pair_id"])
            if pair is None:
                continue
            x, y = (pair["left"], pair["right"]) if direction == 0 else (pair["right"], pair["left"])
            if (row["pair_id"], x, y) in research:
                worst = max(worst, abs(research[row["pair_id"], x, y] - value))
                compared += 1
    saved = json.loads((RESEARCH / "diem/e5-d01-a/nguong.json").read_text(encoding="utf-8"))["tai_lieu"][doc]
    edges_research = {(e["source"], e["target"]) for e in json.loads(
        (RESEARCH / f"e4/e5-a-hieu-chinh/{doc}-canh.json").read_text(encoding="utf-8"))}
    edges_product = {(e["source"], e["target"]) for e in payload["secondary_edges"]}
    return {"diem_so_sanh": compared, "diem_lech_toi_da": worst,
            "k_san_pham": payload["stats"]["expected_positive_count"], "k_nghien_cuu": saved["so_duong_uoc_luong"],
            "nguong_san_pham": payload["stats"]["threshold"], "nguong_nghien_cuu": saved["nguong_hieu_chinh"],
            "canh_san_pham": len(edges_product), "canh_nghien_cuu": len(edges_research),
            "canh_chung": len(edges_product & edges_research)}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    options = dict(arg[2:].split("=", 1) for arg in sys.argv[1:] if arg.startswith("--") and "=" in arg)
    root = Path(options.get("kho", "tmp/v4-18d"))
    docs = [arg for arg in sys.argv[1:] if not arg.startswith("--")] or list(MAIN)
    reference = {}
    for line in open(RESEARCH / "ket-qua/sua-y.jsonl", encoding="utf-8"):
        row = json.loads(line)
        if row["phuong_an"] == "e5-a-hieu-chinh":
            reference[row["doc"]] = row
    passed = True
    for doc in docs:
        artifact, seconds, reused = run(doc, root)
        result = {"doc": doc, "giay": round(seconds, 1), "dung_lai_cache": reused, **compare(doc, artifact)}
        edges = artifact.payload["secondary_edges"]
        payload, _ = replay(doc, edges)
        e4 = summary(score_payload(doc, payload, root / "e4", "san-pham-ml"), payload, len(edges))
        result["e4"] = {k: e4[k] for k in METRICS}
        result["e4_nghien_cuu"] = {k: reference[doc][k] for k in METRICS}
        result["lech"] = {k: round(e4[k] - reference[doc][k], 3) for k in METRICS}
        result["dat"] = all(abs(v) <= 0.03 for v in result["lech"].values())
        passed &= result["dat"]
        print(json.dumps(result, ensure_ascii=False), flush=True)
    print("ĐẠT" if passed else "CHƯA ĐẠT")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
