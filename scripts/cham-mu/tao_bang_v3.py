"""Bảng chấm mù v3 (kiểu T15): đặt đầu đối đầu cạnh dư của đồ thị cũ và đồ thị mới trên hai chương vàng phát triển.

Vì sao: trên hai chương vàng, luồng mới (vé 12) và luồng cũ ngang nhau trong nhiễu đo; bộ vàng không phân định được. Người chấm mù thì
phân định được, đặc biệt câu hỏi "cạnh này có cần không" (T1, T11: lỗi chính là thừa ràng buộc).

Mỗi tài liệu trộn bốn loại cặp, đảo chiều ngẫu nhiên, người chấm không biết nguồn:
  - `du`: cạnh hiển thị (rút gọn bắc cầu của cạnh cứng) của đồ thị cũ và/hoặc mới, hai đầu thuộc đích vàng, không phải cạnh vàng trực
    tiếp. Khoá ghi chiều của từng đồ thị, `cu` / `moi`, có thể cả hai;
  - `vang`: mẫu cạnh vàng trực tiếp, đo độ tin của chính lần chấm;
  - `ngau_nhien`: cặp hai đích không có đường đi ở cả hai đồ thị và không phải cạnh vàng, đo mức vàng bỏ sót.
Khuôn sheet và sheet Khái niệm lấy từ bảng gán vàng A1 (`tao_bang.concept_sheet`) như T1/T11, để người chấm quen. Seed, số mẫu ghi dưới đây
**trước** khi có đồ thị cuối. Mặc định ghi vào `tmp/cham-mu-v3`; bảng thật dùng `--ra=artifacts/a8-gold`.
Chạy từ gốc repo:
  .venv/Scripts/python.exe scripts/cham-mu/tao_bang_v3.py --cu-doc-1=<graph.json> --moi-doc-1=<graph.json>
      --cu-doc-2=<graph.json> --moi-doc-2=<graph.json> [--ra=<thư mục>]
"""
import hashlib
import json
import random
import sys
from pathlib import Path

import openpyxl
from openpyxl.styles import Alignment, Font
from openpyxl.worksheet.datavalidation import DataValidation

sys.path.insert(0, "src")
sys.path.insert(0, "scripts/cham-mu")
from tao_bang import GUIDE, LABELS, concept_sheet  # noqa: E402
from doc2roadmap.domain.gold_scoring import transitive_closure  # noqa: E402
from doc2roadmap.domain.sequence import transitive_reduction  # noqa: E402

SEED = 20261001
# (tài liệu, chương vàng, số cạnh vàng lấy mẫu, số cặp ngẫu nhiên) — ghi trước khi có đồ thị cuối của vé 12
CASES = (("doc-1", "10-12", 5, 8), ("doc-2", "98-115", 5, 8))


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def displayed(graph_path, targets):
    """Cạnh hiển thị: rút gọn bắc cầu của cạnh cứng, qua bản đồ danh tính của chính đồ thị, hai đầu thuộc đích vàng."""
    payload = json.loads(Path(graph_path).read_text(encoding="utf-8"))
    identity = payload.get("identity_map", {})
    edges = {(identity.get(a, a), identity.get(b, b)) for a, b in transitive_reduction(payload["requires_edges"])}
    edges = {(a, b) for a, b in edges if a != b}
    return {(a, b) for a, b in edges if a in targets and b in targets}, edges, identity


def build(doc, chapter, gold_sample, random_sample, old_path, new_path, rng):
    gold_path = Path(f"artifacts/a8-gold/{doc}-{chapter}-vang.json")
    gold_file = json.loads(gold_path.read_text(encoding="utf-8"))
    new_payload_identity = json.loads(Path(new_path).read_text(encoding="utf-8")).get("identity_map", {})
    targets = {new_payload_identity.get(t, t) for t in gold_file["targets"]}
    gold = {(new_payload_identity.get(e["prerequisite"], e["prerequisite"]), new_payload_identity.get(e["target"], e["target"]))
            for e in gold_file["edges"]}
    gold = {pair for pair in gold if pair[0] != pair[1] and pair[0] in targets and pair[1] in targets}
    old_scope, old_all, _ = displayed(old_path, targets)
    new_scope, new_all, _ = displayed(new_path, targets)
    sheet_path, header, body, by_node = concept_sheet(doc, chapter)

    pairs = {}
    for label, scope in (("cu", old_scope), ("moi", new_scope)):
        for a, b in scope - gold:
            pairs.setdefault(frozenset((a, b)), {})[label] = [a, b]
    gold_items = rng.sample(sorted(gold), min(gold_sample, len(gold)))
    reach = set(transitive_closure(old_all)) | set(transitive_closure(new_all))
    candidates = sorted((a, b) for a in sorted(targets & set(by_node)) for b in sorted(targets & set(by_node))
                        if a < b and (a, b) not in reach and (b, a) not in reach and (a, b) not in gold and (b, a) not in gold)
    randoms = rng.sample(candidates, min(random_sample, len(candidates)))

    items = []
    for key, directions in sorted(pairs.items(), key=lambda row: sorted(row[0])):
        a, b = sorted(key)
        items.append({"category": "du", "pair": [a, b], **{name: directions.get(name) for name in ("cu", "moi")}})
    items += [{"category": "vang", "pair": list(pair), "vang": list(pair)} for pair in gold_items]
    items += [{"category": "ngau_nhien", "pair": list(pair)} for pair in randoms]
    for item in items:
        a, b = item["pair"]
        item["x"], item["y"] = (b, a) if rng.random() < 0.5 else (a, b)
    missing = sorted({node for item in items for node in (item["x"], item["y"])} - set(by_node))
    if missing:
        raise ValueError(f"{doc}: {len(missing)} khái niệm không có trong sheet Khái niệm, ví dụ {missing[0]}")
    rng.shuffle(items)
    for index, item in enumerate(items, 1):
        item["item"] = index
    counts = {"du_chi_cu": sum(1 for i in items if i["category"] == "du" and i.get("cu") and not i.get("moi")),
              "du_chi_moi": sum(1 for i in items if i["category"] == "du" and i.get("moi") and not i.get("cu")),
              "du_ca_hai": sum(1 for i in items if i["category"] == "du" and i.get("moi") and i.get("cu")),
              "vang": len(gold_items), "ngau_nhien": len(randoms)}
    return items, counts, (sheet_path, header, body, by_node, gold_path)


def write(out_dir, doc, items, counts, sources, old_path, new_path):
    sheet_path, header, body, by_node, gold_path = sources
    name_col, place_col = header.index("Tên (dùng để chọn)"), header.index("Nơi dạy")
    workbook = openpyxl.Workbook()
    guide = workbook.active
    guide.title = "Hướng dẫn"
    for line in GUIDE:
        guide.append([line])
    guide["A1"].font = Font(bold=True, size=13)
    guide.column_dimensions["A"].width = 110
    sheet = workbook.create_sheet("Cặp")
    sheet.append(["STT", "Khái niệm X", "Khái niệm Y", "Nơi dạy X", "Nơi dạy Y", "Phán quyết", "Ghi chú"])
    for item in items:
        x, y = by_node[item["x"]], by_node[item["y"]]
        sheet.append([item["item"], x[name_col], y[name_col], x[place_col], y[place_col], None, None])
    for cell in sheet[1]:
        cell.font = Font(bold=True)
    for column, width in zip("ABCDEFG", (6, 34, 34, 42, 42, 32, 40)):
        sheet.column_dimensions[column].width = width
    for row in sheet.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    choices = workbook.create_sheet("_lua_chon")
    for label in LABELS.values():
        choices.append([label])
    choices.sheet_state = "hidden"
    validation = DataValidation(type="list", formula1=f"=_lua_chon!$A$1:$A${len(LABELS)}", allow_blank=True)
    sheet.add_data_validation(validation)
    validation.add(f"F2:F{len(items) + 1}")
    concepts = workbook.create_sheet("Khái niệm")
    concepts.append(list(header))
    for row in body:
        concepts.append(list(row))
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"cham-mu-v3-{doc}.xlsx"
    workbook.save(out)
    key = {"doc_id": doc, "seed": SEED, "labels": LABELS, "counts": counts,
           "inputs": {"graph_cu": {"path": str(old_path), "sha256": sha256(old_path)},
                      "graph_moi": {"path": str(new_path), "sha256": sha256(new_path)},
                      "gold": {"path": str(gold_path), "sha256": sha256(gold_path)},
                      "concept_sheet": {"path": str(sheet_path), "sha256": sha256(sheet_path)}},
           "sheet": {"path": str(out), "sha256": sha256(out)}, "items": items}
    key_path = out_dir / f"cham-mu-v3-{doc}-khoa.json"
    key_path.write_text(json.dumps(key, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out, key_path


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    options = dict(arg[2:].split("=", 1) for arg in sys.argv[1:] if arg.startswith("--") and "=" in arg)
    out_dir = Path(options.get("ra", "tmp/cham-mu-v3"))
    rng = random.Random(SEED)
    for doc, chapter, gold_sample, random_sample in CASES:
        old_path, new_path = Path(options[f"cu-{doc}"]), Path(options[f"moi-{doc}"])
        items, counts, sources = build(doc, chapter, gold_sample, random_sample, old_path, new_path, rng)
        out, key_path = write(out_dir, doc, items, counts, sources, old_path, new_path)
        print(f"{doc}: {len(items)} cặp {counts} → {out} | khoá {key_path}")


if __name__ == "__main__":
    main()
