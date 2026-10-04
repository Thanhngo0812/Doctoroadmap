"""Báo cáo phút và USD theo khâu cho một tài liệu (vé v4-02). Chỉ đọc manifest, không gọi mô hình, 0 USD.

Lần chuỗi từ artifact cuối (mặc định bản graph mới nhất) ngược về cụm, rồi canonical (A4/A5), candidates (A3) và chunks (A1/A2).
- Số đo mới của v4-02 nằm ở `manifest.stats`: `runtime_seconds`, `model_calls`, `input_tokens`, `output_tokens`, `embedding_model_calls`,
  `embedding_input_tokens`, `token_usage_complete`, `measurement_history_complete`. Embedding được trừ khỏi tổng trước khi áp giá LLM.
- Artifact cũ (v3) không có các trường này: token lấy từ trường cũ của từng khâu, thời gian ghi "chưa đo". Không suy thời gian từ
  `created_at` và không coi trường thiếu là 0.
- Giá LLM lấy từ `PRICING_USD_PER_MILLION` trong mã. Mã chưa khoá giá embedding, nên USD embedding chỉ tính khi truyền `--gia-embedding`.
Chạy từ gốc repo:
  .venv/Scripts/python.exe scripts/do-chi-phi/bao_cao.py <doc> [--phien-ban=<v>] [--goc=artifacts] [--gia-embedding=<USD/1M>] [--json=<tệp>]
  .venv/Scripts/python.exe scripts/do-chi-phi/bao_cao.py --tu-kiem
"""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "src")
from doc2roadmap.application.prerequisite_prompt import PRICING_USD_PER_MILLION  # noqa: E402

NEW_FIELDS = ("model_calls", "input_tokens", "output_tokens", "embedding_model_calls", "embedding_input_tokens")
NAMES = (("a6-a7-topic-graph", "A6 cụm"), ("mention-map", "A6 nhắc tên"), ("provenance-refinement", "A7 nguồn gốc"),
         ("a10-teaching-anchor", "C8 neo"), ("a10-identity", "A9'' danh tính"), ("a8-main-pass", "A8 pass chính"),
         ("a8-secondary-pass", "A8 pass phụ"), ("a9-", "A9 kiểm đồ thị"), ("a10-concept-labels", "tên khái niệm"),
         ("a10-book-anchored-sequence", "A10 lộ trình"), ("a10-module-titles", "tên module"))


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def label(manifest, fallback):
    algorithm = str(manifest.get("config", {}).get("algorithm_id", ""))
    return next((name for prefix, name in NAMES if algorithm.startswith(prefix)), fallback or algorithm or "?")


def measure(manifest):
    """Số đo của một artifact: ưu tiên trường mới; artifact cũ thì gom token từ trường cũ."""
    stats = manifest.get("stats", {})
    if "usage_responses" in stats:  # chỉ có từ v4-02; A7 cũ cũng có `model_calls` nên không dùng trường đó để nhận diện
        row = {key: stats.get(key, 0) for key in NEW_FIELDS}
        row.update(runtime_seconds=stats.get("runtime_seconds"), kind="mới",
                   complete=bool(stats.get("token_usage_complete", True)) and bool(stats.get("measurement_history_complete", True)))
        return row
    pools = [stats, manifest.get("module_title_metrics", {})]
    cost = manifest.get("cost_summary") or {}
    if cost.get("input_tokens") is not None and not any(key.endswith("_input_tokens") for key in stats):
        pools = [{"input_tokens": cost.get("input_tokens", 0), "output_tokens": cost.get("output_tokens", 0),
                  "llm_calls": stats.get("llm_calls", 0)}]
    def total(suffix):
        return sum(value for pool in pools for key, value in pool.items()
                   if isinstance(value, (int, float)) and not isinstance(value, bool)
                   and (key == suffix[1:] or key.endswith(suffix)) and "total" not in key)
    calls = sum(value for pool in pools for key, value in pool.items()
                if isinstance(value, int) and not isinstance(value, bool) and key.endswith("calls")
                and not any(word in key for word in ("deferred", "retried", "invalid")))
    return {"model_calls": calls, "input_tokens": total("_input_tokens"), "output_tokens": total("_output_tokens"),
            "embedding_model_calls": None, "embedding_input_tokens": None,
            "runtime_seconds": stats.get("runtime_seconds"), "kind": "cũ", "complete": False}


def usd(row, embedding_price):
    llm_input = row["input_tokens"] - (row["embedding_input_tokens"] or 0)
    value = llm_input / 1e6 * PRICING_USD_PER_MILLION["input"] + row["output_tokens"] / 1e6 * PRICING_USD_PER_MILLION["output"]
    if embedding_price is not None and row["embedding_input_tokens"]:
        value += row["embedding_input_tokens"] / 1e6 * embedding_price
    return value


def chain(root, doc, version):
    """Danh sách (khâu, kiểu artifact, phiên bản, manifest) từ A1 tới artifact cuối."""
    graph = root / "graph" / doc
    if version is None:
        version = max(int(path.name[1:]) for path in graph.iterdir() if path.name.startswith("v"))
    rows, current = [], version
    while current is not None and (graph / f"v{current}" / "manifest.json").exists():
        manifest = read(graph / f"v{current}" / "manifest.json")
        rows.append((label(manifest, manifest.get("stage")), "graph", current, manifest))
        if manifest.get("stage") == "clusters":
            break
        config = manifest.get("config", {})
        current = (manifest.get("upstream_version") or config.get("edges_version") or config.get("main_version")
                   or config.get("provenance_version"))
    rows.reverse()
    if not rows or rows[0][3].get("stage") != "clusters":
        return rows, "chuỗi đồ thị không về tới cụm trong kho này (có thể nằm ở kho khác)"
    config = rows[0][3]["config"]
    early = []
    canonical_path = root / "canonical" / doc / f"v{config.get('canonical_version')}" / "manifest.json"
    if canonical_path.exists():
        canonical = read(canonical_path)
        early.append(("A4/A5 gộp, mô tả", "canonical", config.get("canonical_version"), canonical))
        candidates_path = root / "candidates" / doc / f"v{canonical.get('upstream_version')}" / "manifest.json"
        if candidates_path.exists():
            candidates = read(candidates_path)
            early.insert(0, ("A3 trích khái niệm", "candidates", canonical.get("upstream_version"), candidates))
            chunks_path = root / "chunks" / doc / f"v{candidates.get('upstream_version')}" / "manifest.json"
            if chunks_path.exists():
                early.insert(0, ("A1/A2 đọc PDF, cắt đoạn", "chunks", candidates.get("upstream_version"), read(chunks_path)))
    return early + rows, None


def report(root, doc, version, embedding_price):
    rows, note = chain(root, doc, version)
    table, totals = [], {"usd": 0.0, "seconds": 0.0, "seconds_missing": 0}
    for name, kind, number, manifest in rows:
        row = measure(manifest)
        cost = usd(row, embedding_price)
        totals["usd"] += cost
        if row["runtime_seconds"] is None:
            totals["seconds_missing"] += 1
        else:
            totals["seconds"] += row["runtime_seconds"]
        extra = {}
        if kind == "chunks":
            extra = {key: manifest.get(key) for key in ("page_count", "parse_runtime_seconds", "parse_reused")}
        table.append({"khau": name, "artifact": f"{kind} v{number}", "phut": None if row["runtime_seconds"] is None
                      else round(row["runtime_seconds"] / 60, 2), "loi_goi": row["model_calls"],
                      "token_vao": row["input_tokens"], "token_ra": row["output_tokens"],
                      "embedding_loi_goi": row["embedding_model_calls"], "embedding_token": row["embedding_input_tokens"],
                      "usd": round(cost, 4), "so_do": row["kind"], "du": row["complete"], **extra})
    return {"doc_id": doc, "root": str(root), "rows": table, "usd": round(totals["usd"], 4),
            "phut_da_do": round(totals["seconds"] / 60, 2), "khau_chua_do_thoi_gian": totals["seconds_missing"],
            "gia_llm": PRICING_USD_PER_MILLION, "gia_embedding": embedding_price, "ghi_chu": note}


def show(result):
    print(f"# {result['doc_id']} ({result['root']}) — giá LLM {result['gia_llm']} USD/1M token")
    if result["ghi_chu"]:
        print("  lưu ý:", result["ghi_chu"])
    print(f"  {'khâu':<24} {'artifact':<16} {'phút':>7} {'lời gọi':>8} {'token vào':>12} {'token ra':>11} {'USD':>9}  số đo")
    for row in result["rows"]:
        minutes = "chưa đo" if row["phut"] is None else f"{row['phut']:.2f}"
        flag = row["so_do"] + ("" if row["du"] else (", thiếu" if row["so_do"] == "mới" else ""))
        pages = f" | {row['page_count']} trang, parse {row['parse_runtime_seconds']}s" if row.get("page_count") else ""
        print(f"  {row['khau']:<24} {row['artifact']:<16} {minutes:>7} {row['loi_goi'] or 0:>8} {row['token_vao'] or 0:>12,} "
              f"{row['token_ra'] or 0:>11,} {row['usd']:>9.3f}  {flag}{pages}")
    print(f"  CỘNG: {result['usd']:.2f} USD; {result['phut_da_do']:.1f} phút đã đo; {result['khau_chua_do_thoi_gian']} khâu chưa đo thời gian")


def self_test():
    """Một manifest có số đo mới: embedding phải bị trừ trước khi áp giá LLM; trường thiếu không thành 0 phút."""
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        stats = {"runtime_seconds": 120.0, "model_calls": 10, "input_tokens": 3_000_000, "output_tokens": 100_000,
                 "embedding_model_calls": 4, "embedding_input_tokens": 1_000_000, "usage_responses": 10,
                 "token_usage_complete": True, "measurement_history_complete": True}
        (root / "graph" / "d" / "v1").mkdir(parents=True)
        (root / "graph" / "d" / "v1" / "manifest.json").write_text(json.dumps(
            {"stage": "clusters", "config": {"algorithm_id": "a6-a7-topic-graph-v3"}, "stats": stats}), encoding="utf-8")
        (root / "graph" / "d" / "v2").mkdir(parents=True)
        (root / "graph" / "d" / "v2" / "manifest.json").write_text(json.dumps(
            {"stage": "mentions", "upstream_version": 1, "config": {"algorithm_id": "mention-map-v4"}, "stats": {}}), encoding="utf-8")
        result = report(root, "d", None, None)
        expected = 2_000_000 / 1e6 * PRICING_USD_PER_MILLION["input"] + 100_000 / 1e6 * PRICING_USD_PER_MILLION["output"]
        assert abs(result["rows"][0]["usd"] - round(expected, 4)) < 1e-9, result["rows"][0]
        assert result["rows"][0]["phut"] == 2.0 and result["rows"][1]["phut"] is None
        assert result["khau_chua_do_thoi_gian"] == 1
    print("tự kiểm: đạt")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    options = dict(arg[2:].split("=", 1) for arg in sys.argv[1:] if arg.startswith("--") and "=" in arg)
    if "--tu-kiem" in sys.argv:
        self_test()
        return
    doc = next(arg for arg in sys.argv[1:] if not arg.startswith("--"))
    result = report(Path(options.get("goc", "artifacts")), doc,
                    int(options["phien-ban"]) if "phien-ban" in options else None,
                    float(options["gia-embedding"]) if "gia-embedding" in options else None)
    show(result)
    if "json" in options:
        Path(options["json"]).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
