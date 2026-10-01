"""Thử nghiệm 0 USD (kiểm thử vé 12, 2026-10-01): chấm lại đề xuất **đã có** của A8 dưới cửa sổ định nghĩa rộng hơn.

A8 v5 bác đề xuất `can_de_hieu` khi câu trích nằm ngoài cửa sổ "câu neo + hai câu sau". Gần như mọi câu bị bác lại nằm **trước** câu neo,
trong chính chunk neo: câu giả thiết của định nghĩa ("Giả sử K là một trường.", "Suppose A is an m-by-n matrix."). Script này không gọi
mô hình. Nó lấy nguyên các thao tác bị bác/hạ cấp trong `executor_log` của pass chính và trong các lần thử của pilot pass phụ, cho qua đúng
`validate_main_proposals` (pass chính) hoặc kiểm câu trích (pilot) với cửa sổ mở thêm `--truoc` câu phía trước (mặc định 4), rồi chấm:
  - hai đầu thuộc đích vàng, cùng bản đồ danh tính mới (như `cham_main_a8_v3.py`), trực tiếp và theo bao đóng;
  - **đường cơ sở đúng** cho quyết định chạy pass phụ là đồ thị cuối của luồng cũ (A8 chính + phụ cũ → A9), không phải riêng pass chính
    cũ; so sau luật A9 và rút gọn bắc cầu (đúng các cạnh hiện ở dòng "cần:").
Là cận dưới: mô hình chưa từng được xem cửa sổ rộng. Chạy từ gốc repo:
  .venv/Scripts/python.exe scripts/doc-lo-trinh/thu_cua_so_rong_a8.py [--truoc=4] [--chi-tiet]
"""
import json
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, "src")
import doc2roadmap.domain.prerequisites as prerequisites  # noqa: E402
from doc2roadmap.application.use_cases.a8_score import load_gold, merge_gold  # noqa: E402
from doc2roadmap.domain.anchors import heading_chunks  # noqa: E402
from doc2roadmap.domain.global_validation import validate_graph_rules  # noqa: E402
from doc2roadmap.domain.gold_scoring import score_edges, transitive_closure  # noqa: E402
from doc2roadmap.domain.sentence_splitter import UnicodeSentenceSplitter  # noqa: E402
from doc2roadmap.domain.sequence import transitive_reduction  # noqa: E402
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore  # noqa: E402

# (tài liệu, pass chính cũ, pass chính v5, đồ thị cuối luồng cũ trong kho thử, bộ vàng)
CASES = (("doc-1", 4, 42, 6, "doc-1-10-12-vang.json"), ("doc-2", 4, 34, 6, "doc-2-98-115-vang.json"))
OLD_FINAL_STORE = Path("artifacts/v3-05b-a9v10-evaluation")
PILOT_STORE = Path("artifacts/v3-r12-secondary-pilot")
RECOVERABLE = {"quote_outside_definition_window", "definition_chunk_not_cited"}
LOST = {"rejected", "deferred_after_retry", "downgraded_to_cong_cu"}


def widened(before):
    """Như `prerequisites.definition_window`, chỉ mở thêm `before` câu trước câu neo trong cùng chunk."""
    def window(node, chunks):
        anchor = node.get("anchor") or {}
        chunk = next((row for row in chunks if row.chunk_id == anchor.get("chunk_id")), None)
        sentence = anchor.get("sentence")
        if chunk is None or not isinstance(sentence, str) or not sentence:
            return ""
        text = unicodedata.normalize("NFC", chunk.text)
        start = text.find(unicodedata.normalize("NFC", sentence), max(0, int(anchor.get("char_start", 0)) - 8))
        if start < 0:
            start = text.find(unicodedata.normalize("NFC", sentence))
        if start < 0:
            return ""
        spans = UnicodeSentenceSplitter().split(text)
        index = next((i for i, span in enumerate(spans) if span.start <= start < span.end), None)
        if index is None:
            return ""
        first = spans[max(0, index - before)].start
        result = text[first:spans[min(index + 2, len(spans) - 1)].end]
        heading = heading_chunks(node, [chunk]).get(chunk.chunk_id)
        if heading and heading[1] <= first:
            result = heading[0] + "\n" + result
        return result
    return window


def grade(edges, gold, identity, present):
    representative = lambda node_id: identity.get(node_id, node_id)  # noqa: E731
    targets = {representative(node_id) for node_id in gold["targets"]} & present
    gold_edges = {(representative(a), representative(b)) for a, b in merge_gold([gold], mode="union")}
    gold_edges = {(a, b) for a, b in gold_edges if a != b and a in targets and b in targets}
    predicted = {(representative(edge["source"]), representative(edge["target"])) for edge in edges if not edge.get("soft")}
    predicted = {(a, b) for a, b in predicted if a != b and a in targets and b in targets}
    return score_edges(predicted, gold_edges), score_edges(transitive_closure(predicted), transitive_closure(gold_edges))


def fmt(score):
    return f"P {score['true_positive']}/{score['predicted']} R {score['true_positive']}/{score['gold']}"


def reduced(edges):
    return [{"source": source, "target": target}
            for source, target in transitive_reduction([edge for edge in edges if not edge.get("soft")])]


def replay_main(payload, chunks, window):
    prerequisites.definition_window = window
    sessions = {session["session_id"]: session for session in payload["main_sessions"]}
    edges, recovered = [dict(edge) for edge in payload["main_edges"]], []
    for row in payload["executor_log"]:
        operation = row.get("operation") or {}
        if row.get("error") not in RECOVERABLE or row.get("status") not in LOST \
                or operation.get("prerequisite_kind") != "can_de_hieu":
            continue
        accepted, _, _, _ = prerequisites.validate_main_proposals(
            {"edges": [operation], "flags": []}, sessions[row["session_id"]], payload["nodes"], chunks,
            payload["mention_map"], existing_edges=edges, require_kind=True)
        for edge in accepted:
            edges = [old for old in edges if (old["source"], old["target"]) != (edge["source"], edge["target"])] + [edge]
            recovered.append(edge)
    return edges, recovered


def replay_pilot(pilot, nodes, chunks, window):
    edges, recovered = [dict(edge) for edge in pilot["secondary_edges"]], []
    for row in pilot["decision_log"]:
        for attempt in row.get("attempts") or []:
            if attempt.get("error") != "quote_outside_definition_window":
                continue
            try:
                output = json.loads(attempt["raw_text"])
            except (KeyError, TypeError, ValueError):
                continue
            target = nodes.get(output.get("target"))
            if (output.get("decision") == "create" and output.get("prerequisite_kind") == "can_de_hieu" and target
                    and output.get("quote") and output["quote"] in window(target, chunks)):
                pair = (output["prerequisite"], output["target"])
                edges = [old for old in edges if (old["source"], old["target"]) != pair] + [{"source": pair[0], "target": pair[1]}]
                recovered.append({"source": pair[0], "target": pair[1], "quote": output["quote"]})
                break
    return edges, recovered


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    before = int(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--truoc=")), "4"))
    original_window = prerequisites.definition_window
    store, pilots, old_store = JsonArtifactStore(Path("artifacts")), JsonArtifactStore(PILOT_STORE), JsonArtifactStore(OLD_FINAL_STORE)
    for doc_id, old_main_version, new_version, old_final_version, gold_file in CASES:
        artifact = store.load_graph(doc_id, new_version)
        payload = artifact.payload
        chunks = store.load_chunks(doc_id, artifact.manifest["config"]["chunks_version"]).result.chunks
        nodes = {node["node_id"]: node for node in payload["nodes"]}
        gold = load_gold(Path("artifacts/a8-gold") / gold_file)
        identity, present = payload.get("identity_map", {}), set(nodes)
        pilot = pilots.load_graph(doc_id, 1).payload
        old_final = old_store.load_graph(doc_id, old_final_version).payload
        old_present = {node["node_id"] for node in [*old_final["nodes"], *old_final.get("mentioned_nodes", [])]}
        print(f"# {doc_id} (hai đầu thuộc đích vàng)")
        rows = [("pass chính cũ (v4)", grade(store.load_graph(doc_id, old_main_version).payload.get("main_edges", []),
                                            gold, identity, present)),
                ("đồ thị cuối luồng cũ, sau rút gọn", grade(reduced(old_final["requires_edges"]), gold,
                                                            old_final.get("identity_map", {}), old_present))]
        for label, window in ((f"cửa sổ gốc −0…+2", original_window), (f"cửa sổ −{before}…+2", widened(before))):
            main_edges, main_recovered = replay_main(payload, chunks, window)
            pilot_edges, pilot_recovered = replay_pilot(pilot, nodes, chunks, window)
            prerequisites.definition_window = original_window
            rows.append((f"pass chính, {label}", grade(main_edges, gold, identity, present)))
            structural = validate_graph_rules(payload["nodes"], [*main_edges, *pilot_edges], [], type_aliases={})
            rows.append((f"chính + pilot qua luật A9, sau rút gọn, {label}",
                         grade(reduced(structural["requires_edges"]), gold, identity, present)))
            if "--chi-tiet" in sys.argv and main_recovered:
                for edge in main_recovered + pilot_recovered:
                    print(f"    + {nodes[edge['source']]['name']} → {nodes[edge['target']]['name']}: {edge.get('quote', '')[:80]!r}")
        for label, (direct, closure) in rows:
            print(f"  {label:<58} trực tiếp {fmt(direct):<16} bao đóng {fmt(closure)}")


if __name__ == "__main__":
    main()
