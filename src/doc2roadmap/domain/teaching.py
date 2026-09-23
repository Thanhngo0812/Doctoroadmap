from __future__ import annotations

from collections import deque

VERDICTS = ("teaches", "mentions_only", "prior_knowledge", "not_subject_matter", "uncertain")
# Hai câu hỏi độc lập (v2). v1 gộp chúng vào một trường, và một nhãn trong hình vừa "không phải kiến thức môn học"
# vừa "được nêu tên mà không dạy" — mô hình chọn vế sau cho 7/8 ca và rác lọt qua. Nay luật loại chỉ đọc `kind`.
KINDS = ("concept", "course_logistics", "example_detail", "non_subject", "uncertain")
ROLES = ("teaches", "mentions", "prior_knowledge", "uncertain")
NON_SUBJECT_KINDS = {"course_logistics", "example_detail", "non_subject"}
# Chỉ hai trạng thái này bị đưa ra khỏi stage. Node "chỉ được nhắc" vẫn giữ: provenance có thể chỉ trỏ vào một
# câu liệt kê trong khi tài liệu dạy nó ở nơi khác (`Neural Networks` của doc-3), nên loại nó là mất chủ đề chính.
EXCLUDED_STATUSES = {"prior_knowledge", "not_subject_matter"}


def _squash(text):
    return " ".join(str(text).split())


def validate_teaching_response(value, *, node_id, chunk_id, chunk_text):
    if not isinstance(value, dict) or value.get("node_id") != node_id or value.get("chunk_id") != chunk_id:
        raise ValueError("phán quyết sai node_id hoặc chunk_id")
    if value.get("kind") not in KINDS:
        raise ValueError("kind ngoài năm giá trị cho phép")
    if value.get("role") not in ROLES:
        raise ValueError("role ngoài bốn giá trị cho phép")
    if "confidence" in value:
        raise ValueError("mô hình không được trả confidence")
    if not isinstance(value.get("reason"), str) or not value["reason"].strip():
        raise ValueError("phán quyết thiếu reason")
    claims = value["kind"] in NON_SUBJECT_KINDS or (
        value["kind"] == "concept" and value["role"] in {"teaches", "prior_knowledge"})
    if claims:
        quote = value.get("quote")
        if not isinstance(quote, str) or not _squash(quote):
            raise ValueError(f"kind {value['kind']} / role {value['role']} cần quote")
        if _squash(quote) not in _squash(chunk_text):
            raise ValueError("quote không có trong đoạn")


def verdict_of(value):
    """Thứ này là gì quyết định việc loại, trước khi xét đoạn làm gì với nó."""
    if value["kind"] in NON_SUBJECT_KINDS:
        return "not_subject_matter"
    if value["kind"] == "uncertain":
        return "uncertain"
    return {"teaches": "teaches", "mentions": "mentions_only", "prior_knowledge": "prior_knowledge",
            "uncertain": "uncertain"}[value["role"]]


def teaching_status(rows):
    """Gộp phán quyết từng đoạn của một node thành trạng thái của node.

    Thứ tự ưu tiên cố định: có một đoạn dạy là đủ giữ node; rồi `uncertain` (giữ, vì chưa đủ căn cứ để loại);
    rồi hai trạng thái bị loại; cuối cùng là "chỉ được nhắc". Vị trí dạy lấy từ các đoạn thật sự dạy.
    """
    verdicts = {row["verdict"] for row in rows}
    teaching = sorted((row for row in rows if row["verdict"] == "teaches"),
                      key=lambda row: (row["order_index"], row["chunk_id"]))
    if teaching:
        status = "taught"
    elif "uncertain" in verdicts:
        status = "uncertain"
    elif "prior_knowledge" in verdicts:
        status = "prior_knowledge"
    elif "not_subject_matter" in verdicts:
        status = "not_subject_matter"
    elif rows:
        status = "mentioned_only"
    else:
        status = "unchecked"
    return {
        "teaching_status": status,
        "teaching_chunk_ids": [row["chunk_id"] for row in teaching],
        "teaching_order_index": teaching[0]["order_index"] if teaching else None,
        "teaching_conflict": bool(teaching) and bool(verdicts & EXCLUDED_STATUSES),
    }


def bypass_excluded(edges, excluded):
    """Bỏ node bị loại khỏi DAG mà không làm mất ràng buộc học trước: a → x → b thành a → b.

    Chỉ đi xuyên qua node bị loại, nên cạnh thêm vào đúng bằng phần khả đạt mà việc bỏ node làm mất. Đầu vào là
    DAG đã qua A9 nên phép co không thể sinh chu trình.
    """
    excluded = set(excluded)
    children = {}
    for edge in edges:
        children.setdefault(edge["source"], set()).add(edge["target"])
    kept = [edge for edge in edges if edge["source"] not in excluded and edge["target"] not in excluded]
    present = {(edge["source"], edge["target"]) for edge in kept}
    added = []
    for source in sorted({edge["source"] for edge in edges} - excluded):
        queue = deque((child, [child]) for child in sorted(children.get(source, ())) if child in excluded)
        seen = {child for child, _ in queue}
        while queue:
            node, path = queue.popleft()
            for child in sorted(children.get(node, ())):
                if child in excluded:
                    if child not in seen:
                        seen.add(child)
                        queue.append((child, path + [child]))
                elif (source, child) not in present:
                    present.add((source, child))
                    added.append({"source": source, "target": child, "edge_type": "requires", "via_excluded": path})
    return kept + added, added
