"""Vé 17i: thử prompt phán cụm sửa cho chuỗi gộp trên đúng các cụm đã phán. Tốn tiền nhỏ (mỗi cụm một lời, flash-lite).

Lỗi đo được ở lượt đầu: prompt `partition-gop` để mô hình (1) ghi quan hệ `synonym` giữa hai node tách rời, luật R2 không bắt vì chỉ nhận
`synonym_of`; (2) dùng `subtype_of` cho hai tên của cùng một khái niệm (bản dịch, đồng nghĩa). Script hỏi lại mỗi lời phán cụm hợp lệ của
canonical chuỗi gộp bằng prompt sửa, rồi so cặp nhóm cùng/khác giữa lời cũ và lời mới, in tên để Claude đọc.
Chạy từ gốc repo (cần .env có khoá):
  .venv/Scripts/python.exe scripts/gop-khau/thu_prompt_gop.py <doc> [...] [--loai=merge|repair] [--che-do=sua-don|sua-lo|cu-don]
      [--kho=tmp/v4-17i/artifacts] [--ra=tmp/v4-17i/thu-prompt]
`sua-don`: prompt sửa, mỗi cụm/mục một lời; `sua-lo`: prompt sửa, giữ đúng lô phán sửa cũ; `cu-don`: prompt cũ, mỗi mục một lời; `cu-lo`: prompt cũ, lô cũ (đo nhiễu lặp lại).
"""
import glob
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from itertools import combinations
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, str(Path(__file__).resolve().parent))
from doc2roadmap.application.canonical_prompt import PARTITION_SCHEMA  # noqa: E402
from doc2roadmap.application.use_cases.canonical_repairs import BATCH_INSTRUCTION, BATCH_SCHEMA  # noqa: E402
from doc2roadmap.config import Settings  # noqa: E402
from doc2roadmap.infrastructure.llm.gemini import GeminiEntityExtractor  # noqa: E402

PROMPT = """Partition exact-name groups using verbatim A3 evidence. Merge if and only if two groups denote the same concept: the same
definition and the same set of objects, differing only in their names. Different names include synonyms, symbols, initialisms and
abbreviations, singular/plural, spelling variants and translations (for example an English term and its Vietnamese equivalent).
Evidence that presents one name as another name of the other ("X (Y)", "X hay Y", "X còn gọi là Y", "Y là viết tắt của X") means merge.
A single sentence often defines several DIFFERENT concepts; sharing an evidence sentence or a similar draft is not identity.
Keep separate: a special case or narrower kind of the other (it denotes a strict subset of its objects), equality established by a
proposition, different propositions, and different kinds of objects. For a special case propose subtype_of from the special case to its
general concept; never use subtype_of between two names of one concept.
Never put synonym, alias, abbreviation, translation, same_as or any other identity relation between separate nodes: two names of one
concept belong in one node.
Every group occurs exactly once in nodes or deferred. Use group_id, never names as IDs.
Between separate nodes, propose an open relation only when cited evidence states it. Use a short
snake_case edge_type and cite source chunk IDs. Never propose requires, illustrates or tabulates.
Do not choose canonical names, types, aliases or descriptions. Uncertain identity means keep separate
or deferred. Return only JSON with nodes, relations, deferred."""


OLD_PROMPT = Path("src/doc2roadmap/application/prompts/a4/partition-gop.txt").read_text(encoding="utf-8")
V3_PROMPT = Path("src/doc2roadmap/application/prompts/a4/partition.txt").read_text(encoding="utf-8")


def pairs(value, groups):
    owner = {gid: i for i, node in enumerate(value.get("nodes", [])) for gid in node.get("groups", [])}
    return {frozenset((a, b)): (a in owner and b in owner and owner[a] == owner[b]) for a, b in combinations(groups, 2)}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    options = dict(arg[2:].split("=", 1) for arg in sys.argv[1:] if arg.startswith("--") and "=" in arg)
    root, out = options.get("kho", "tmp/v4-17i/artifacts"), Path(options.get("ra", "tmp/v4-17i/thu-prompt"))
    out.mkdir(parents=True, exist_ok=True)
    settings = Settings()
    model = GeminiEntityExtractor(settings.gemini_api_key.get_secret_value() if settings.gemini_api_key else None,
                                  settings.merge_model_id, timeout_seconds=settings.gemini_timeout_seconds,
                                  max_retries=settings.gemini_max_retries, temperature=settings.extraction_temperature,
                                  max_output_tokens=settings.extraction_max_output_tokens, transport=settings.llm_transport,
                                  vertex_project=settings.vertex_project, vertex_location=settings.vertex_location)
    from ten_nhom import group_name_map  # noqa: E402
    kind, mode = options.get("loai", "merge"), options.get("che-do", "sua-don")
    tokens = [0, 0]
    for doc in [arg for arg in sys.argv[1:] if not arg.startswith("--")]:
        version = sorted(glob.glob(f"{root}/canonical/{doc}/v*"), key=lambda p: int(p.split("v")[-1]))[-1]
        canonical = json.load(open(version + "/canonical.json", encoding="utf-8"))
        names = group_name_map(root, doc)
        units = []  # (đầu vào gửi đi theo chế độ, danh sách (nhóm, phân hoạch cũ))
        if kind == "merge":
            for row in [r for r in canonical["decision_log"] if r.get("stage") == "merge" and r.get("valid")]:
                units.append((("don", row["input"]), [([g["group_id"] for g in row["input"]["groups"]], row["output"])]))
        else:
            for row in [r for r in canonical["decision_log"] if r.get("stage") == "repair" and r.get("valid")]:
                if "items" not in row["output"]:  # mục hỏng trong lô đã được hỏi lại riêng
                    units.append((("don", row["input"]), [([g["group_id"] for g in row["input"]["groups"]], row["output"])]))
                    continue
                old = {item["item_id"]: item["partition"] for item in row["output"]["items"]}
                items = [(item, old[item["item_id"]]) for item in row["input"]["items"] if item["item_id"] in old]
                if mode in ("sua-lo", "cu-lo"):
                    units.append((("lo", {"items": [i for i, _ in items]}),
                                  [([g["group_id"] for g in i["groups"]], o) for i, o in items]))
                else:
                    for item, partition in items:
                        data = {key: value for key, value in item.items() if key != "item_id"}
                        units.append((("don", data), [([g["group_id"] for g in item["groups"]], partition)]))
        if "chi-cap" in options:  # chỉ giữ lời phán chứa cả hai nhóm của ít nhất một cặp "A|B;C|D"
            wanted = [set(pair.split("|")) for pair in options["chi-cap"].split(";")]
            units = [unit for unit in units
                     if any(pair <= {names.get(g) for groups, _ in unit[1] for g in groups} for pair in wanted)]
        prompt = {"cu-don": OLD_PROMPT, "cu-lo": OLD_PROMPT, "v3-don": V3_PROMPT}.get(mode, PROMPT)

        def ask(unit):
            (shape, data), parts = unit
            schema = BATCH_SCHEMA if shape == "lo" else PARTITION_SCHEMA
            text = prompt + BATCH_INSTRUCTION if shape == "lo" else prompt
            reply = model.start_session(text).ask_json(json.dumps(data, ensure_ascii=False, sort_keys=True), response_schema=schema)
            value = reply.payload
            if shape == "lo":
                by_id = {row.get("item_id"): row.get("partition", {}) for row in value.get("items", [])}
                values = [by_id.get(item["item_id"], {}) for item in data["items"]]
            else:
                values = [value]
            return values, getattr(reply, "usage", None) or {}

        with ThreadPoolExecutor(4) as pool:
            answers = list(pool.map(ask, units))
        changed, kept_relations = [], []
        for (_, parts), (values, usage) in zip(units, answers):
            tokens[0] += int(usage.get("promptTokenCount", 0))
            tokens[1] += int(usage.get("candidatesTokenCount", 0)) + int(usage.get("thoughtsTokenCount", 0))
            for (groups, old_value), value in zip(parts, values):
                old, new = pairs(old_value, groups), pairs(value, groups)
                for pair in old:
                    if old[pair] != new[pair]:
                        a, b = sorted(pair)
                        changed.append({"cu": "cung" if old[pair] else "khac", "moi": "cung" if new[pair] else "khac",
                                        "a": names.get(a, a), "b": names.get(b, b)})
                for edge in value.get("relations", []):
                    kept_relations.append({"edge_type": edge.get("edge_type"), "a": names.get(edge.get("source")),
                                           "b": names.get(edge.get("target"))})
        (out / f"{doc}-{kind}-{mode}.json").write_text(json.dumps({"doi": changed, "quan_he": kept_relations}, ensure_ascii=False, indent=1),
                                         encoding="utf-8")
        print(f"== {doc} {kind} {mode}: {len(units)} lời, {len(changed)} cặp đổi")
        for row in changed:
            print(f"  {row['cu']} -> {row['moi']}: {row['a']} | {row['b']}")
        identity_like = [r for r in kept_relations if any(w in (r["edge_type"] or "").casefold()
                                                          for w in ("synonym", "alias", "abbrev", "acronym", "translat", "same"))]
        print("  quan hệ dạng đồng nhất còn lại:", identity_like)
    print("USD", round((tokens[0] * 0.25 + tokens[1] * 1.5) / 1e6, 4))


if __name__ == "__main__":
    main()
