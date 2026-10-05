"""Lắp cạnh pass phụ không LLM từ điểm của bộ phân loại, rồi phát lại A9 → A10 và chấm trên vàng (E4). 0 USD.

Đi đúng luồng của pass phụ v3, chỉ thay lời gọi mô hình bằng điểm:
- cặp lấy bằng `select_secondary_pairs`, xét theo thứ tự `pair_id`; trước mỗi cặp tỉa lại bằng cạnh đã có (cạnh cứng trực tiếp hoặc đường
  tường minh), như v3;
- mỗi cặp chọn chiều có điểm cao hơn, tạo cạnh khi điểm ≥ ngưỡng;
- **căn cứ và câu trích chọn bằng luật, không sinh văn bản:**
  - tên X (tên hoặc bí danh) có trong cửa sổ định nghĩa của Y → cạnh cứng `can_de_hieu`, `trong_dinh_nghia`, câu trích là câu của cửa sổ có tên X,
    gần câu neo nhất;
  - không có thì, nếu cho phép cạnh mềm, tìm chunk mà mention map có cả X và Y → `cong_cu`, `mach_trinh_bay`, câu trích là câu của chunk đó
    có tên X (ưu tiên câu có cả tên Y);
  - mọi đề xuất đi qua `validate_main_proposals` với `require_kind=True`, cùng cửa sổ (−before…+after) như v3; đề xuất trượt kiểm thì thử câu
    kế tiếp, hết câu thì không tạo cạnh.
Điểm đọc từ CSV (`pair_id,x,y,score`), hoặc từ một luật dựng sẵn:
  --luat=cua-so    điểm 1 khi tên X có trong cửa sổ định nghĩa của Y.
Chạy từ gốc repo:
  .venv/Scripts/python.exe scripts/pass-phu-ml/lap_canh.py <doc> (--diem=<csv> (--nguong=<t> | --nguong-tu=<nguong.json> [--chinh-sach=ti-le|hieu-chinh])
      | --luat=cua-so)
      [--chi-cung] [--tach-tu] [--nhan=<tên>]
  `--tach-tu` (chạy bằng tmp/venv-ml, cần underthesea): tên tiên quyết trong câu trích phải khớp theo ranh giới từ tiếng Việt.
"""
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "scripts/pass-phu-ml")
from dung_bang_cap import found, found_words, regexes, word_regexes  # noqa: E402
from phat_lai_e4 import GOLD_DOCS, replay, score_payload, summary  # noqa: E402
from doc2roadmap.domain.prerequisites import definition_window, merge_main_proposals, validate_main_proposals  # noqa: E402
from doc2roadmap.domain.secondary import select_secondary_pairs  # noqa: E402
from doc2roadmap.domain.sentence_splitter import UnicodeSentenceSplitter  # noqa: E402
from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore  # noqa: E402

SPLITTER = UnicodeSentenceSplitter()


def sentences(text):
    return [text[span.start:span.end] for span in SPLITTER.split(text)]


def hard_quotes(x_patterns, target, chunks, before, after, word_patterns=None):
    """Câu của cửa sổ định nghĩa của đích có tên tiên quyết, xếp theo khoảng cách tới câu neo. Có `word_patterns` thì tên còn phải khớp
    theo ranh giới từ tiếng Việt (không lọt giữa từ ghép)."""
    window = definition_window(target, chunks, before=before, after=after)
    rows = sentences(window)
    anchor = (target.get("anchor") or {}).get("sentence", "").split("\n")[0][:60]
    anchor_index = next((i for i, row in enumerate(rows) if anchor and anchor in row), 0)
    hits = [(abs(i - anchor_index), i, row) for i, row in enumerate(rows)
            if found(x_patterns, row) and (word_patterns is None or found_words(word_patterns, row))]
    return [row for _, _, row in sorted(hits)]


def soft_quotes(x_patterns, y_patterns, x, y, mention_map, chunk_by_id):
    """(chunk, câu) trong các chunk nhắc cả hai đầu; câu có cả hai tên trước, rồi câu có tên tiên quyết."""
    result = []
    for chunk_id in sorted(chunk_id for chunk_id, rows in mention_map.items() if x in rows and y in rows and chunk_id in chunk_by_id):
        for row in sentences(chunk_by_id[chunk_id].text):
            has_x, has_y = found(x_patterns, row), found(y_patterns, row)
            if has_x:
                result.append((0 if has_y else 1, chunk_by_id[chunk_id].order_index, chunk_id, row))
    return [(chunk_id, row) for _, _, chunk_id, row in sorted(result)]


def assemble(doc, scores, threshold, *, allow_soft=True, secondary=None, words=False):
    root, version, _, _ = GOLD_DOCS[doc]
    secondary = secondary or JsonArtifactStore(Path(root)).load_graph(doc, version)
    payload, config = secondary.payload, secondary.manifest["config"]
    chunks_version = config["chunks_version"]
    chunk_root = Path(root) if (Path(root) / "chunks" / doc / f"v{chunks_version}").exists() else Path("artifacts")
    chunks = JsonArtifactStore(chunk_root).load_chunks(doc, chunks_version).result.chunks
    chunk_by_id = {chunk.chunk_id: chunk for chunk in chunks}
    before, after = config.get("definition_before", 4), config.get("definition_after", 2)
    nodes = payload["nodes"]
    node_by_id = {node["node_id"]: node for node in nodes}
    mention_map, ledger, route = payload["mention_map"], payload.get("pair_cluster_ledger", []), payload["routing"]["route"]
    patterns = {node_id: regexes(node) for node_id, node in node_by_id.items()}
    word_patterns = {node_id: word_regexes(node) for node_id, node in node_by_id.items()} if words else {}
    pairs, _ = select_secondary_pairs(nodes, payload.get("suspected_pairs", []), ledger, [], route=route)
    main_edges = list(payload.get("main_edges", []))
    edges, stats = [], {"cap": len(pairs), "bi_tia": 0, "duoi_nguong": 0, "khong_can_cu": 0, "cung": 0, "mem": 0}
    for pair in pairs:
        current = main_edges + edges
        askable, _ = select_secondary_pairs(nodes, [pair], ledger, current, route=route)
        if not askable:
            stats["bi_tia"] += 1
            continue
        options = sorted(((scores(pair["pair_id"], x, y), x, y) for x, y in ((pair["left"], pair["right"]), (pair["right"], pair["left"]))),
                         reverse=True)
        value, x, y = options[0]
        if value is None or value < threshold:
            stats["duoi_nguong"] += 1
            continue
        session = {"session_id": "secondary_" + pair["pair_id"], "allowed_node_ids": [pair["left"], pair["right"]]}
        candidates = [{"prerequisite_kind": "can_de_hieu", "evidence_kind": "trong_dinh_nghia", "quote": quote,
                       "chunk_ids": [(node_by_id[y].get("anchor") or {}).get("chunk_id")]}
                      for quote in hard_quotes(patterns[x], node_by_id[y], chunks, before, after, word_patterns.get(x))]
        if allow_soft:
            candidates += [{"prerequisite_kind": "cong_cu", "evidence_kind": "mach_trinh_bay", "quote": quote, "chunk_ids": [chunk_id]}
                           for chunk_id, quote in soft_quotes(patterns[x], patterns[y], x, y, mention_map, chunk_by_id)]
        accepted = None
        for candidate in candidates:
            output = {"edges": [{"target": y, "prerequisite": x, **candidate,
                                 "reason": f"pass phụ không LLM: điểm {value:.3f}; căn cứ {candidate['evidence_kind']}"}], "flags": []}
            proposals, _, _, retry = validate_main_proposals(output, session, nodes, chunks, mention_map, existing_edges=current,
                                                              require_kind=True, definition_before=before, definition_after=after)
            if proposals and not retry:
                accepted = proposals
                break
        if not accepted:
            stats["khong_can_cu"] += 1
            continue
        edges, _ = merge_main_proposals(accepted, edges)
        stats["cung" if accepted[0].get("prerequisite_kind") == "can_de_hieu" else "mem"] += 1
    return edges, stats, secondary


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    options = dict(arg[2:].split("=", 1) for arg in sys.argv[1:] if arg.startswith("--") and "=" in arg)
    doc = next(arg for arg in sys.argv[1:] if not arg.startswith("--"))
    if options.get("luat") == "cua-so":
        root, version, _, _ = GOLD_DOCS[doc]
        artifact = JsonArtifactStore(Path(root)).load_graph(doc, version)
        chunks_version = artifact.manifest["config"]["chunks_version"]
        chunk_root = Path(root) if (Path(root) / "chunks" / doc / f"v{chunks_version}").exists() else Path("artifacts")
        chunks = JsonArtifactStore(chunk_root).load_chunks(doc, chunks_version).result.chunks
        node_by_id = {node["node_id"]: node for node in artifact.payload["nodes"]}
        patterns = {node_id: regexes(node) for node_id, node in node_by_id.items()}
        words = {node_id: word_regexes(node) for node_id, node in node_by_id.items()} if "--tach-tu" in sys.argv else None
        config = artifact.manifest["config"]
        cache = {}

        def scores(pair_id, x, y):
            if y not in cache:
                cache[y] = sentences(definition_window(node_by_id[y], chunks, before=config.get("definition_before", 4),
                                                       after=config.get("definition_after", 2)))
            return 1.0 if any(found(patterns[x], s) and (words is None or found_words(words[x], s)) for s in cache[y]) else 0.0
        threshold = 0.5
    else:
        table = {}
        with open(options["diem"], encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                table[row["pair_id"], row["x"], row["y"]] = float(row["score"])

        def scores(pair_id, x, y):
            return table.get((pair_id, x, y))
        threshold = float(options.get("nguong", "nan"))
    if "nguong-tu" in options:  # ngưỡng do E2b chọn trên tài liệu học, ghi trong nguong.json
        key = {"ti-le": "nguong_ti_le", "hieu-chinh": "nguong_hieu_chinh"}.get(options.get("chinh-sach"), "nguong")  # chính sách của E2b
        threshold = json.loads(Path(options["nguong-tu"]).read_text(encoding="utf-8"))["tai_lieu"][doc][key]
    edges, stats, secondary = assemble(doc, scores, threshold, allow_soft="--chi-cung" not in sys.argv, words="--tach-tu" in sys.argv)
    label = options.get("nhan", options.get("luat", "diem"))
    out = Path(options.get("ra", "tmp/pass-phu-ml/e4"))
    (out / label).mkdir(parents=True, exist_ok=True)
    (out / label / f"{doc}-canh.json").write_text(json.dumps(edges, ensure_ascii=False), encoding="utf-8")
    payload, _ = replay(doc, edges, secondary=secondary)
    result = summary(score_payload(doc, payload, out, label), payload, len(edges))
    print(json.dumps({"doc": doc, "phuong_an": label, "lap_canh": stats, **result}, ensure_ascii=False))


if __name__ == "__main__":
    main()
