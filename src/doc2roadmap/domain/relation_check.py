from __future__ import annotations

# C10: một cạnh `requires` A → B chỉ còn là ràng buộc cứng khi định nghĩa hoặc phát biểu của B, trong chính các đoạn
# được đưa ra, **dùng** A. Tiêu chí ấy làm năm lựa chọn loại trừ nhau: dùng A là `requires`; không dùng mà vẫn giúp
# học (động cơ, ví dụ, nối qua một định lý) là `supports`; chiều ngược là `reversed`.
VERDICTS = ("requires", "supports", "reversed", "unrelated", "unresolved")
QUOTED = {"requires", "supports", "reversed"}
HARD = {"requires", "unresolved", "unchecked"}


def _squash(text):
    return " ".join(str(text).split())


def edge_id(edge):
    return f"{edge['source']}->{edge['target']}"


def validate_relation_response(value, *, edge_id, passages):
    if not isinstance(value, dict) or value.get("edge_id") != edge_id:
        raise ValueError("phán quyết sai edge_id")
    if value.get("verdict") not in VERDICTS:
        raise ValueError("verdict ngoài năm giá trị cho phép")
    if "confidence" in value:
        raise ValueError("mô hình không được trả confidence")
    if not isinstance(value.get("reason"), str) or not value["reason"].strip():
        raise ValueError("phán quyết thiếu reason")
    if value["verdict"] in QUOTED:
        quote = value.get("quote")
        if not isinstance(quote, str) or not _squash(quote):
            raise ValueError(f"verdict {value['verdict']} cần quote")
        if not any(_squash(quote) in _squash(text) for text in passages):
            raise ValueError("quote không có trong hồ sơ")


def apply_relation_verdicts(edges, verdicts):
    """Chia cạnh theo phán quyết. Cạnh chưa được kiểm hoặc chưa đủ căn cứ vẫn là ràng buộc cứng: bước kiểm chỉ được
    phép gỡ một ràng buộc khi có câu trích chứng minh, không được gỡ vì thiếu câu trả lời."""
    result = {"requires": [], "recommended": [], "rejected": []}
    for edge in edges:
        verdict = verdicts.get(edge_id(edge), {"verdict": "unchecked"})
        row = {**edge, "relation_check": verdict["verdict"]}
        if verdict.get("reason"):
            row["relation_reason"] = verdict["reason"]
        if verdict["verdict"] in HARD:
            result["requires"].append(row)
        elif verdict["verdict"] == "supports":
            result["recommended"].append(row)
        else:
            result["rejected"].append(row)
    return result
