from __future__ import annotations

import json
import random
from datetime import datetime
from itertools import combinations
from pathlib import Path

from doc2roadmap.domain.canonical import digest, name_key


PAIR_LABELS = {"same", "parent_child", "related", "different", "uncertain"}


def gold_items(store, doc_ids, *, seed=42, random_count=100):
    rng, documents, items, outside, counts = random.Random(seed), {}, [], {}, {}
    for doc_id in sorted(set(doc_ids)):
        artifact = store.load_latest_canonical(doc_id)
        if artifact.payload.get("stage") != "nominations":
            raise ValueError(f"{doc_id}: cần artifact đề cử chưa phán để gán mù")
        candidates = store.load_latest_candidates(doc_id)
        if artifact.manifest["config"]["candidate_version"] != candidates.version:
            raise ValueError(f"{doc_id}: đề cử không khớp candidates mới nhất")
        chunks = store.load_chunks(doc_id, candidates.manifest["upstream_version"])
        sections = {c.chunk_id: c.section_path for c in chunks.result.chunks}
        raw = {e["candidate_id"]: e for e in candidates.payload["entities"]}
        nodes = {n["node_id"]: n for n in artifact.payload["nodes"] if not n["media_id"]}
        documents[doc_id] = {"candidate_version": candidates.version, "candidate_hash": digest(candidates.payload),
                             "canonical_version": artifact.version}
        counts[doc_id] = len(nodes)
        def item(group_ids, kind):
            groups = [{"group_id": id, "name_key": name_key(nodes[id]["name"]),
                       "members": [{"candidate_id": c, "name": raw[c]["name"],
                                    "node_type": raw[c]["node_type"], "aliases": raw[c].get("aliases", []),
                                    "evidence": raw[c].get("evidence", []),
                                    "section_paths": [sections[chunk_id] for chunk_id in sorted({r["chunk_id"]
                                        for r in raw[c].get("evidence", []) + raw[c].get("source_refs", [])})]}
                                   for c in nodes[id]["members"]],
                       "symbols": nodes[id]["symbols"]} for id in group_ids]
            identity = [doc_id, kind, [(g["name_key"], [m["candidate_id"] for m in g["members"]]) for g in groups]]
            return {"item_id": digest(identity), "doc_id": doc_id, "kind": kind, "groups": groups}
        nominated = {tuple(sorted((e["source"], e["target"]))) for e in artifact.payload["nominations"]["edges"]}
        items.extend(item(pair, "pair") for pair in sorted(nominated))
        items.extend(item([id], "group") for id, node in nodes.items() if len(node["members"]) > 1)
        outside[doc_id] = [item(pair, "pair") for pair in combinations(sorted(nodes), 2) if pair not in nominated]
        rng.shuffle(outside[doc_id])
    if not documents:
        raise ValueError("cần ít nhất một tài liệu")
    allocation = {doc: 0 for doc in documents}
    for _ in range(min(random_count, sum(map(len, outside.values())))):
        available = [doc for doc in documents if allocation[doc] < len(outside[doc])]
        doc = min(available, key=lambda doc: ((allocation[doc]+1)/max(counts[doc], 1), doc))
        allocation[doc] += 1
    for doc, count in allocation.items():
        items.extend(outside[doc][:count])
    rng.shuffle(items)
    return {"schema_version": 1, "documents": documents, "items": items,
            "seed": seed, "random_count": random_count,
            "sheet_id": digest([documents, seed, items])}


def write_gold_sheet(payload, path: Path):
    template = Path(__file__).parents[1] / "templates" / "a4-gold.html"
    data = json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(template.read_text(encoding="utf-8").replace("__PAYLOAD__", data), encoding="utf-8")


def load_gold(path: Path, store, *, expected=None, require_complete=False):
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1 or payload.get("blind_before_first_a4_run") is not True:
        raise ValueError("bộ vàng cần schema_version=1 và blind_before_first_a4_run=true")
    if not isinstance(payload.get("annotator"), str) or not payload["annotator"].strip():
        raise ValueError("thiếu người gán")
    try:
        datetime.fromisoformat(payload["annotated_at"].replace("Z", "+00:00"))
    except (KeyError, TypeError, ValueError, AttributeError) as error:
        raise ValueError("thời điểm gán không hợp lệ") from error
    if not isinstance(payload.get("documents"), dict) or not isinstance(payload.get("items"), list) or not payload["items"]:
        raise ValueError("bộ vàng thiếu documents/items")
    legacy = False
    if require_complete or payload.get("sheet_id"):
        if payload.get("seed") != 42 or payload.get("random_count") != 100:
            raise ValueError("bộ vàng chạy thật cần bảng đầy đủ với seed=42 và 100 cặp ngoài đồ thị")
        # Rebuild from frozen pre-judgment artifacts, not the latest complete A4 output.
        class FrozenNominations:
            def load_latest_canonical(self, doc_id):
                return store.load_canonical(doc_id, payload["documents"][doc_id]["canonical_version"])
            def load_latest_candidates(self, doc_id):
                return store.load_latest_candidates(doc_id)
            def load_chunks(self, doc_id, version):
                return store.load_chunks(doc_id, version)
        expected = gold_items(FrozenNominations(), payload["documents"])
        legacy = payload.get("sheet_id") == digest([expected["documents"], expected["seed"],
                                                    [i["item_id"] for i in expected["items"]]])
        if not legacy and payload.get("sheet_id") != expected["sheet_id"]:
            raise ValueError("sheet_id không khớp bảng gán mù nguồn")
    raw, frozen_nodes, source_sections = {}, {}, {}
    for doc, info in payload["documents"].items():
        candidates = store.load_latest_candidates(doc)
        if info.get("candidate_version") != candidates.version or info.get("candidate_hash") != digest(candidates.payload):
            raise ValueError(f"{doc}: bộ vàng không khớp candidates hiện hành")
        raw[doc] = {c["candidate_id"]: c for c in candidates.payload["entities"]}
        frozen = store.load_canonical(doc, info["canonical_version"])
        if frozen.payload.get("stage") != "nominations" or frozen.manifest["config"]["candidate_version"] != candidates.version:
            raise ValueError(f"{doc}: nguồn đề cử của bộ vàng không hợp lệ")
        frozen_nodes[doc] = {n["node_id"]: n for n in frozen.payload["nodes"] if not n["media_id"]}
        source_sections[doc] = {c.chunk_id: c.section_path for c in
            store.load_chunks(doc, candidates.manifest["upstream_version"]).result.chunks}
    if legacy:
        # Validate exactly what the annotator saw, without changing frozen labels or timestamps.
        for item in expected["items"]:
            for group in item["groups"]:
                node = frozen_nodes[item["doc_id"]][group["group_id"]]
                paths = [source_sections[item["doc_id"]][c] for c in node["source_chunk_ids"]]
                for member in group["members"]:
                    member["section_paths"] = paths
    seen = set()
    for item in payload["items"]:
        id = item.get("item_id", "<missing>")
        try:
            groups, doc, kind = item["groups"], item["doc_id"], item["kind"]
            identity = [doc, kind, [(g["name_key"], [m["candidate_id"] for m in g["members"]]) for g in groups]]
            if id != digest(identity) or id in seen or len(groups) != (2 if kind == "pair" else 1):
                raise ValueError("id trùng/sai hoặc số nhóm sai")
            for group in groups:
                if not group["members"]:
                    raise ValueError("nhóm rỗng")
                node = frozen_nodes[doc][group["group_id"]]
                if [m["candidate_id"] for m in group["members"]] != node["members"] or group["symbols"] != node["symbols"]:
                    raise ValueError("nhóm không khớp nguồn đề cử")
                for member in group["members"]:
                    original = raw[doc][member["candidate_id"]]
                    if member["name"] != original["name"] or name_key(original["name"]) != group["name_key"]:
                        raise ValueError("thành viên không khớp nhóm tên")
                    own_ids = sorted({r["chunk_id"] for r in original.get("evidence", []) + original.get("source_refs", [])})
                    if legacy:
                        own_ids = node["source_chunk_ids"]
                    if (any(member.get(k) != original.get(k, []) for k in ["node_type", "aliases", "evidence"])
                        or member["section_paths"] != [source_sections[doc][c] for c in own_ids]):
                        raise ValueError("bằng chứng thành viên không khớp nguồn")
            label = item["label"]
            if kind == "pair":
                if label not in PAIR_LABELS or (label == "parent_child" and
                    (type(item.get("child")) is not int or item["child"] not in [0, 1])):
                    raise ValueError("nhãn cặp/chiều cha-con không hợp lệ")
            elif kind == "group":
                if label not in {"one_entity", "homonym"}:
                    raise ValueError("nhãn nhóm không hợp lệ")
                if label == "homonym":
                    different = item.get("different_members", [])
                    ids = {m["candidate_id"] for m in groups[0]["members"]}
                    if not different or not set(different) < ids:
                        raise ValueError("cần chọn một phần thành viên đồng âm")
            else:
                raise ValueError("loại mục không hợp lệ")
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"mục {id}: {error}") from error
        seen.add(id)
    if expected is not None and seen != {i["item_id"] for i in expected["items"]}:
        raise ValueError("danh sách mục không đủ hoặc không khớp bảng gán")
    if expected is not None:
        expected_items = {i["item_id"]: i for i in expected["items"]}
        for item in payload["items"]:
            if item["groups"] != expected_items[item["item_id"]]["groups"]:
                raise ValueError(f"mục {item['item_id']}: bằng chứng/nhóm bị thay đổi so với bảng gán")
    return payload


def evaluate_canonical(artifact, gold, second=None, *, exclude_subtype_items=()):
    doc = artifact.payload["doc_id"]
    excluded = set(exclude_subtype_items)
    mapping = {c: n["node_id"] for n in artifact.payload["nodes"] for c in n["members"]}
    nominated = {frozenset((e["source"], e["target"])) for e in artifact.payload["nominations"]["edges"]}
    subtype = {(e["source"], e["target"]) for e in artifact.payload["edges"] if e["edge_type"] == "subtype_of"}
    tp = fp = fn = positives = captured = uncertain = parents = correct_parent = homonyms = 0
    annotated_pairs, parent_pairs, labels_by_pair = set(), set(), {}
    for item in gold["items"]:
        if item["doc_id"] != doc:
            continue
        if item["kind"] == "group":
            if item["label"] == "homonym" and len({mapping.get(m["candidate_id"]) for m in item["groups"][0]["members"]}) == 1:
                homonyms += 1
            continue
        if item["label"] == "uncertain":
            uncertain += 1
            continue
        a, b = item["groups"]
        x, y = mapping[a["members"][0]["candidate_id"]], mapping[b["members"][0]["candidate_id"]]
        positive, predicted = item["label"] == "same", x == y
        tp += positive and predicted; fp += predicted and not positive; fn += positive and not predicted
        positives += positive
        captured += positive and frozenset((a["group_id"], b["group_id"])) in nominated
        node_pair = frozenset((x, y))
        annotated_pairs.add(node_pair)
        labels_by_pair[node_pair] = item["label"]
        if item["label"] == "parent_child":
            pair = (x, y) if item["child"] == 0 else (y, x)
            parent_pairs.add(pair)
            if item["item_id"] not in excluded:
                parents += 1
                correct_parent += pair in subtype
    precision = tp/(tp+fp) if tp+fp else 0.
    recall = tp/(tp+fn) if tp+fn else 0.
    subtype_correct = sum(edge in parent_pairs for edge in subtype)
    subtype_incorrect = sum(frozenset(edge) in annotated_pairs and edge not in parent_pairs for edge in subtype)
    relations_2a_on_gold = {label: 0 for label in ("same", "parent_child", "related", "different")}
    for edge in artifact.payload["edges"]:
        if edge["edge_type"] == "subtype_of" or "2a" not in edge.get("origins", []):
            continue
        label = labels_by_pair.get(frozenset((edge["source"], edge["target"])))
        if label in relations_2a_on_gold:
            relations_2a_on_gold[label] += 1
    result = {"canonical_version": artifact.version, "tp": tp, "fp": fp, "fn": fn,
              "precision": precision, "recall": recall,
              "f1": 2*precision*recall/(precision+recall) if precision+recall else 0.,
              "nomination_recall": captured/positives if positives else None,
              "uncertain_count": uncertain, "homonyms_merged": homonyms,
              "subtype_recall": correct_parent/parents if parents else None,
              "subtype_incorrect": subtype_incorrect,
              "subtype_precision": subtype_correct/(subtype_correct+subtype_incorrect)
                                   if subtype_correct+subtype_incorrect else None,
              "relations_2a_on_gold": relations_2a_on_gold}
    if second:
        def labels(payload):
            return {i["item_id"]: (i["label"], i.get("child") if i["label"] == "parent_child" else None)
                    for i in payload["items"] if i["doc_id"] == doc}
        a, b = labels(gold), labels(second)
        common = sorted(a.keys() & b.keys())
        if common:
            values = set(a[i] for i in common) | set(b[i] for i in common)
            agreement = sum(a[i] == b[i] for i in common)/len(common)
            chance = sum(sum(a[i] == label for i in common)*sum(b[i] == label for i in common) for label in values)/len(common)**2
            kappa = (agreement-chance)/(1-chance) if chance < 1 else None
        else:
            agreement = kappa = None
        result["agreement"] = {"count": len(common), "fraction": agreement, "kappa": kappa}
    return result
