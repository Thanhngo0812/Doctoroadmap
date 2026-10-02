"""Mô phỏng 0 USD: pass phụ chạy song song theo lô "hỏi trước, chốt theo thứ tự" thì tốn thêm bao nhiêu lời gọi và nhanh hơn bao nhiêu.

Pass phụ hiện chạy **từng cặp một** (2 lời gọi song song cho hai thứ tự), vì hai thứ phụ thuộc cạnh đã tạo trước đó:
  - `select_secondary_pairs` cắt cặp đã có cạnh trực tiếp hoặc đường đi rõ;
  - hồ sơ (`pair_dossier`) cho mô hình xem đường đi hiện có giữa hai khái niệm.
Cách song song giữ **đúng kết quả của cách chạy tuần tự**:
  1. lấy B cặp tiếp theo còn phải hỏi theo ảnh chụp cạnh hiện tại, hỏi cả B cặp cùng lúc (2B lời gọi);
  2. chốt theo đúng thứ tự cũ, mỗi cặp kiểm lại với cạnh đã chốt. Bị cắt thì bỏ kết quả. Đường đi trong hồ sơ đổi thì dừng lô, lô sau bắt đầu
     từ cặp đó với ảnh chụp mới.
  Lời gọi lặp lại cùng đầu vào là cache hit (`run_model_jobs` khoá theo hash đầu vào), nên không tính hai lần.
Script dựng lại đúng thứ tự tuần tự và cạnh mỗi cặp đã tạo từ nhật ký lượt thật, kiểm phép dựng khớp nhật ký, rồi đo với nhiều cỡ lô.
Chạy từ gốc repo:  .venv/Scripts/python.exe scripts/doc-lo-trinh/thu_song_song_pass_phu.py
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, "src")
from doc2roadmap.domain.secondary import _either_path, select_secondary_pairs  # noqa: E402

ROOT = Path("artifacts/v3-r12-final-evaluation")
SIZES = (1, 4, 8, 16, 32, 50, 100, None)  # None = hỏi mọi cặp còn lại trong một lô (kiểu batch job)


def load(doc):
    main = json.loads((ROOT / "graph" / doc / "v1" / "graph.json").read_text(encoding="utf-8"))
    finished = ROOT / "graph" / doc / "v2" / "graph.json"
    if finished.exists():
        secondary = json.loads(finished.read_text(encoding="utf-8"))
        label = "trọn"
    else:
        checkpoint = next((ROOT / "checkpoints" / "graph" / doc).glob("secondary-*.json"))
        secondary = json.loads(checkpoint.read_text(encoding="utf-8"))
        label = f"dở, {len(secondary['completed_secondary_pairs'])} cặp đã xong"
    return main, secondary, label


def signature(path):
    return None if not path else tuple((edge["source"], edge["target"]) for edge in path)


def simulate(doc):
    main, secondary, label = load(doc)
    nodes, ledger, route = main["nodes"], main.get("pair_cluster_ledger", []), main["routing"]["route"]
    order, _ = select_secondary_pairs(nodes, main.get("suspected_pairs", []), ledger, [], route=route)
    logged = {row["pair_id"]: row["status"] for row in secondary["secondary_log"]}
    order = [pair for pair in order if pair["pair_id"] in logged]
    created = defaultdict(list)
    for edge in secondary["secondary_edges"]:
        created[edge["session_id"].removeprefix("secondary_")].append(edge)

    def askable(pair, edges):
        return bool(select_secondary_pairs(nodes, [pair], ledger, edges, route=route)[0])

    # Kiểm phép dựng: cắt/hỏi theo tuần tự phải khớp nhật ký.
    edges, mismatch, asked_sequential = list(main["main_edges"]), 0, 0
    for pair in order:
        ask = askable(pair, edges)
        mismatch += ask == logged[pair["pair_id"]].startswith("pruned")
        if ask:
            asked_sequential += 1
            edges += created[pair["pair_id"]]
    rows = []
    for size in SIZES:
        size = size or len(order)
        edges, index, rounds, asked, used = list(main["main_edges"]), 0, 0, set(), set()
        while index < len(order):
            snapshot, window, cursor = list(edges), [], index
            while cursor < len(order) and len(window) < size:
                pair = order[cursor]
                if askable(pair, snapshot):
                    window.append((pair["pair_id"], signature(_either_path(snapshot, pair["left"], pair["right"]))))
                cursor += 1
            asked.update(window)
            rounds += bool(window)
            position = index
            while position < cursor:
                pair = order[position]
                if not askable(pair, edges):
                    position += 1
                    continue
                key = (pair["pair_id"], signature(_either_path(edges, pair["left"], pair["right"])))
                if key not in asked:
                    break
                used.add(key)
                edges += created[pair["pair_id"]]
                position += 1
            index = position
        rows.append((size, rounds, len(asked), len(used)))
    return label, len(order), mismatch, asked_sequential, rows


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    for doc in sys.argv[1:] or ("doc-3", "nhap-mon-ml", "doc-1", "doc-2"):
        label, pairs, mismatch, sequential, rows = simulate(doc)
        print(f"# {doc} ({label}): {pairs} cặp theo thứ tự, {sequential} cặp phải hỏi; dựng lại lệch nhật ký: {mismatch}")
        for size, rounds, asked, used in rows:
            waste = (asked - used) / used if used else 0
            print(f"  lô {size:>4} cặp ({2 * size:>4} lời gọi song song): {rounds:>5} lượt chờ "
                  f"(nhanh ×{sequential / rounds:5.1f}) | lời gọi {2 * asked:>6} so với {2 * used:>6} → thừa {waste:6.1%}")


if __name__ == "__main__":
    main()
