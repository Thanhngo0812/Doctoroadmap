"""Chấm bảng chấm mù v3 (`tao_bang_v3.py`): so cạnh dư của đồ thị cũ và đồ thị mới theo phán quyết người, kèm Wilson 95%.

Với mỗi đồ thị (`cu`, `moi`), trên các cặp mà đồ thị đó có cạnh:
  - "không làm sai thứ tự học" = người chọn đúng chiều máy (trực tiếp hoặc qua khái niệm khác);
  - "không cần thứ tự"; "ngược chiều"; "không chắc" tách riêng, không tính vào mẫu số.
Thêm độ tin của lần chấm (cạnh vàng được xác nhận đúng chiều) và mức vàng bỏ sót (cặp ngẫu nhiên người thấy có thứ tự).

`--moi-cuoi=<graph.json>`: chấm phía `moi` theo **cạnh hiển thị của đồ thị cuối**, không theo đồ thị tạm lúc sinh bảng.
- Bảng 2026-10-01 sinh từ pass chính + pilot của lượt ba sửa vé 12. Trong hai chương vàng, pilot đã hỏi đúng mọi cặp mà pass phụ đầy đủ hỏi.
- Đồ thị cuối có thể khác chút: luật A9 trên toàn đồ thị, hoặc đường đi qua khái niệm ngoài chương làm một cạnh thành thừa khi rút gọn.
- Script báo số cạnh hiển thị của đồ thị cuối không có trong bảng. Khác 0 thì ghi rõ khi báo kết quả.

Chạy từ gốc repo:
  .venv/Scripts/python.exe scripts/cham-mu/cham_bang_v3.py <bảng đã điền .xlsx> <khoá .json> [--moi-cuoi=<graph.json>]
"""
import json
import math
import sys
from pathlib import Path

import openpyxl

sys.path.insert(0, "src")
from doc2roadmap.domain.sequence import transitive_reduction  # noqa: E402


def wilson(k, n, z=1.96):
    if not n:
        return None, None
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0.0, centre - half), min(1.0, centre + half)


def ratio(k, n):
    low, high = wilson(k, n)
    return f"{k}/{n}" + (f" = {k / n:.0%} (Wilson 95% {low:.0%}–{high:.0%})" if n else "")


def answers(sheet_path, labels):
    code = {text: key for key, text in labels.items()}
    rows = list(openpyxl.load_workbook(sheet_path, read_only=True)["Cặp"].iter_rows(values_only=True))[1:]
    found = {}
    for row in rows:
        if row and row[0] is not None and row[5]:
            if row[5] not in code:
                raise ValueError(f"cặp {row[0]}: phán quyết {row[5]!r} ngoài sáu lựa chọn")
            found[int(row[0])] = code[row[5]]
    return found


def judge(item, answer, direction):
    """Phán quyết người so với một chiều máy [a, b]."""
    if answer == "khong_chac":
        return "unsure"
    if answer == "khong_can_thu_tu":
        return "none"
    first = item["x"] if answer.startswith("x_truoc_y") else item["y"]
    if first != direction[0]:
        return "reversed"
    return "agree_direct" if answer.endswith("truc_tiep") else "agree_indirect"


def final_directions(key, graph_path):
    """Chiều cạnh hiển thị của đồ thị cuối trên từng cặp của bảng; và số cạnh dư hiển thị không có trong bảng."""
    payload = json.loads(Path(graph_path).read_text(encoding="utf-8"))
    identity = payload.get("identity_map", {})
    gold_file = json.loads(Path(key["inputs"]["gold"]["path"]).read_text(encoding="utf-8"))
    targets = {identity.get(t, t) for t in gold_file["targets"]}
    gold = {(identity.get(e["prerequisite"], e["prerequisite"]), identity.get(e["target"], e["target"])) for e in gold_file["edges"]}
    shown = {(identity.get(a, a), identity.get(b, b)) for a, b in transitive_reduction(payload["requires_edges"])}
    shown = {(a, b) for a, b in shown if a != b and a in targets and b in targets}
    in_sheet = {frozenset(item["pair"]) for item in key["items"]}
    missing = [pair for pair in shown - gold if frozenset(pair) not in in_sheet]
    directions = {}
    for item in key["items"]:
        a, b = item["pair"]
        directions[item["item"]] = [a, b] if (a, b) in shown else ([b, a] if (b, a) in shown else None)
    return directions, missing


def main(sheet_path, key_path, final_graph=None):
    sys.stdout.reconfigure(encoding="utf-8")
    key = json.loads(Path(key_path).read_text(encoding="utf-8"))
    found = answers(sheet_path, key["labels"])
    print(f"# {key['doc_id']}: {len(found)}/{len(key['items'])} cặp đã chấm")
    if final_graph:
        directions, missing = final_directions(key, final_graph)
        for item in key["items"]:
            if item["category"] == "du":
                item["moi"] = directions[item["item"]]
        print(f"  phía `moi` chấm theo đồ thị cuối {final_graph}; cạnh dư hiển thị của đồ thị cuối không có trong bảng: {len(missing)}")
    for graph in ("cu", "moi"):
        tally = dict.fromkeys(("agree_direct", "agree_indirect", "none", "reversed", "unsure", "unanswered"), 0)
        for item in key["items"]:
            if item["category"] != "du" or not item.get(graph):
                continue
            answer = found.get(item["item"])
            tally["unanswered" if answer is None else judge(item, answer, item[graph])] += 1
        judged = tally["agree_direct"] + tally["agree_indirect"] + tally["none"] + tally["reversed"]
        print(f"  cạnh dư đồ thị {graph}: {tally}")
        print(f"    không làm sai thứ tự học {ratio(tally['agree_direct'] + tally['agree_indirect'], judged)}"
              f" · không cần thứ tự {ratio(tally['none'], judged)} · ngược chiều {ratio(tally['reversed'], judged)}")
    gold = [judge(item, found[item["item"]], item["vang"]) for item in key["items"]
            if item["category"] == "vang" and item["item"] in found]
    confirmed = sum(result in ("agree_direct", "agree_indirect") for result in gold)
    print(f"  độ tin: cạnh vàng được xác nhận đúng chiều {ratio(confirmed, len(gold))}")
    randoms = [found[item["item"]] for item in key["items"] if item["category"] == "ngau_nhien" and item["item"] in found]
    ordered = sum(answer not in ("khong_can_thu_tu", "khong_chac") for answer in randoms)
    print(f"  vàng bỏ sót: cặp ngẫu nhiên người thấy có thứ tự {ratio(ordered, len(randoms))}")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    final = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--moi-cuoi=")), None)
    main(args[0], args[1], final)
