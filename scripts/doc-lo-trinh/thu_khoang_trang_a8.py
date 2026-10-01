"""Thử nghiệm 0 USD (kiểm thử vé 12, lượt cửa sổ −4…+2, 2026-10-01): câu trích chỉ lệch khoảng trắng có làm mất cạnh không?

Mô hình hay chép câu nhiều dòng thành một dòng ("nếu hệ thức\\n[formula]\\nchỉ xảy ra" → "nếu hệ thức [formula] chỉ xảy ra"), nên phép so
nguyên văn bác cạnh đúng (`quote_outside_evidence_chunk`, `quote_outside_definition_window`). Script không gọi mô hình. Với mỗi đề xuất bị
bác vì câu trích, nó tìm trong cửa sổ định nghĩa, chunk neo và chunk được dẫn một đoạn **chỉ khác khoảng trắng**. Thấy thì thay câu trích
bằng đúng đoạn ấy và cho qua lại đúng `validate_main_proposals`. Không nhận diễn đạt khác.

Pilot pass phụ được chấm lại xấp xỉ: mỗi thứ tự hỏi lấy lần thử cuối, nắn câu trích, rồi đòi hai thứ tự cùng `create`, cùng chiều, cùng loại.
Chạy từ gốc repo:
  .venv/Scripts/python.exe scripts/doc-lo-trinh/thu_khoang_trang_a8.py [--chi-tiet]
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "scripts/doc-lo-trinh")
from thu_cua_so_rong_a8 import fmt, grade, reduced  # noqa: E402
from doc2roadmap.application.use_cases.a8_score import load_gold  # noqa: E402
from doc2roadmap.domain.global_validation import validate_graph_rules  # noqa: E402
from doc2roadmap.domain.prerequisites import definition_window, validate_main_proposals  # noqa: E402
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore  # noqa: E402

CASES = (("doc-1", "doc-1-10-12-vang.json"), ("doc-2", "doc-2-98-115-vang.json"))
EVALUATION = Path("artifacts/v3-r12-window-evaluation")
OLD_FINAL = Path("artifacts/v3-05b-a9v10-evaluation")
QUOTE_ERRORS = {"quote_outside_evidence_chunk", "quote_outside_definition_window", "definition_chunk_not_cited"}
LOST = {"rejected", "deferred_after_retry", "downgraded_to_cong_cu"}


def snap(quote, texts):
    """Đoạn trong `texts` chỉ khác `quote` ở khoảng trắng (kể cả xuống dòng); không có thì None."""
    tokens = str(quote).split()
    if not tokens:
        return None
    pattern = re.compile(r"\s+".join(re.escape(token) for token in tokens))
    for text in texts:
        match = pattern.search(text)
        if match:
            return match.group(0)
    return None


def sources(operation, nodes, chunk_by_id, chunks, before, after):
    target = nodes.get(operation.get("target"))
    anchor = ((target or {}).get("anchor") or {}).get("chunk_id")
    texts = [definition_window(target, chunks, before=before, after=after)] if target else []
    texts += [chunk_by_id[chunk_id].text for chunk_id in [*operation.get("chunk_ids", []), anchor] if chunk_id in chunk_by_id]
    return texts


def replay_main(payload, chunks, before, after):
    chunk_by_id = {chunk.chunk_id: chunk for chunk in chunks}
    nodes = {node["node_id"]: node for node in payload["nodes"]}
    sessions = {session["session_id"]: session for session in payload["main_sessions"]}
    edges, recovered = [dict(edge) for edge in payload["main_edges"]], []
    for row in payload["executor_log"]:
        operation = dict(row.get("operation") or {})
        if row.get("error") not in QUOTE_ERRORS or row.get("status") not in LOST or not operation.get("quote"):
            continue
        fixed = snap(operation["quote"], sources(operation, nodes, chunk_by_id, chunks, before, after))
        if fixed is None or fixed == operation["quote"]:
            continue
        operation["quote"] = fixed
        accepted, _, _, _ = validate_main_proposals(
            {"edges": [operation], "flags": []}, sessions[row["session_id"]], payload["nodes"], chunks,
            payload["mention_map"], existing_edges=edges, require_kind=True, definition_before=before, definition_after=after)
        for edge in accepted:
            edges = [old for old in edges if (old["source"], old["target"]) != (edge["source"], edge["target"])] + [edge]
            recovered.append(edge)
    return edges, recovered


def replay_pilot(pilot, main_edges, nodes, chunks, before, after):
    """Hai thứ tự của một cặp phải cùng tạo cạnh, cùng chiều, cùng loại, như `reconcile_pair_verdicts`."""
    chunk_by_id = {chunk.chunk_id: chunk for chunk in chunks}
    deferred = {row["pair_id"] for row in pilot.get("secondary_log", []) if row.get("status") == "deferred"}
    verdicts = {}
    for row in pilot["decision_log"]:
        texts = [row.get("raw_text")] + [attempt.get("raw_text") for attempt in reversed(row.get("attempts") or [])]
        output = None
        for raw in texts:
            try:
                output = json.loads(raw) if raw else None
            except ValueError:
                output = None
            if isinstance(output, dict) and output.get("pair_id"):
                break
        if not isinstance(output, dict) or output.get("pair_id") not in deferred:
            continue
        if output.get("decision") == "create" and output.get("quote"):
            fixed = snap(output["quote"], sources(output, nodes, chunk_by_id, chunks, before, after))
            if fixed is None:
                output = {"decision": "invalid"}
            else:
                output = {**output, "quote": fixed}
        verdicts.setdefault(output.get("pair_id"), []).append(output)
    edges = list(pilot["secondary_edges"])
    recovered = []
    for pair_id, rows in verdicts.items():
        if len(rows) < 2 or any(row.get("decision") != "create" for row in rows[:2]):
            continue
        first, second = rows[:2]
        if any(first.get(key) != second.get(key) for key in ("prerequisite", "target", "prerequisite_kind")):
            continue
        session = {"session_id": f"replay:{pair_id}", "allowed_node_ids": pair_id.split("|")}
        candidate = {key: first.get(key) for key in ("target", "prerequisite", "prerequisite_kind", "evidence_kind",
                                                       "chunk_ids", "quote", "reason")}
        try:
            accepted, _, _, _ = validate_main_proposals(
                {"edges": [candidate], "flags": []}, session, list(nodes.values()), chunks, {}, existing_edges=main_edges + edges,
                require_kind=True, definition_before=before, definition_after=after)
        except (KeyError, TypeError, ValueError):
            continue
        edges += accepted
        recovered += accepted
    return edges, recovered


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    base, evaluation, old_store = JsonArtifactStore(Path("artifacts")), JsonArtifactStore(EVALUATION), JsonArtifactStore(OLD_FINAL)
    for doc_id, gold_file in CASES:
        artifact = evaluation.load_graph(doc_id, 1)
        payload, pilot = artifact.payload, evaluation.load_graph(doc_id, 2).payload
        config = artifact.manifest["config"]
        before, after = config.get("definition_before", 4), config.get("definition_after", 2)
        chunks = base.load_chunks(doc_id, config["chunks_version"]).result.chunks
        nodes = {node["node_id"]: node for node in payload["nodes"]}
        gold, identity = load_gold(Path("artifacts/a8-gold") / gold_file), payload.get("identity_map", {})
        old = old_store.load_graph(doc_id, 6).payload
        old_present = {node["node_id"] for node in [*old["nodes"], *old.get("mentioned_nodes", [])]}
        main_edges, main_recovered = replay_main(payload, chunks, before, after)
        pilot_edges, pilot_recovered = replay_pilot(pilot, main_edges, nodes, chunks, before, after)
        rows = [("đồ thị cuối luồng cũ, rút gọn", grade(reduced(old["requires_edges"]), gold, old.get("identity_map", {}), old_present))]
        for label, main_set, pilot_set in (("lượt chạy thật (cửa sổ −4…+2)", payload["main_edges"], pilot["secondary_edges"]),
                                           ("+ gộp khoảng trắng khi so câu trích", main_edges, pilot_edges)):
            structural = validate_graph_rules(payload["nodes"], [*main_set, *pilot_set], [], type_aliases={})
            rows.append((label, grade(reduced(structural["requires_edges"]), gold, identity, set(nodes))))
        print(f"# {doc_id}: chính +{len(main_recovered)} cạnh, pilot +{len(pilot_recovered)} cạnh qua được khi gộp khoảng trắng")
        for label, (direct, closure) in rows:
            print(f"  {label:<40} trực tiếp {fmt(direct):<16} bao đóng {fmt(closure)}")
        if "--chi-tiet" in sys.argv:
            for edge in main_recovered + pilot_recovered:
                kind = "cứng" if not edge.get("soft") else "mềm"
                print(f"    + [{kind}] {nodes[edge['source']]['name']} → {nodes[edge['target']]['name']}: {edge.get('quote', '')[:70]!r}")


if __name__ == "__main__":
    main()
