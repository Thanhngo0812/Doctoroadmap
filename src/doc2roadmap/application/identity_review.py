"""Shared verification schema and human merge-review input for canonical."""
from doc2roadmap.domain.identity import VERIFY_RELATIONS

VERIFY_SCHEMA = {"type": "object", "properties": {
    "pair_id": {"type": "string"}, "relation": {"type": "string", "enum": list(VERIFY_RELATIONS)},
    "reason": {"type": "string"}}, "required": ["pair_id", "relation", "reason"]}
# Quyết định của người duyệt (T5) thắng phán của mô hình. Chỉ "Đồng ý gộp" cho gộp; "Không chắc" thì giữ tách.
HUMAN_VERDICT = {"Đồng ý gộp": "same", "Không gộp": "different", "Là hai nghĩa khác nhau": "sense_split",
                 "Không chắc": "different"}


def load_identity_review(path, *, doc_id):
    """Đọc quyết định duyệt danh tính (T5) của một tài liệu: {"doc_id", "decisions": [{"left", "right", "decision"}]}."""
    import json
    from pathlib import Path

    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("doc_id") != doc_id:
        raise ValueError(f"tệp duyệt danh tính của doc_id {data.get('doc_id')!r}, không phải {doc_id!r}")
    review = {}
    for row in data.get("decisions", []):
        if row.get("decision") not in HUMAN_VERDICT:
            raise ValueError(f"quyết định {row.get('decision')!r} ngoài {sorted(HUMAN_VERDICT)}")
        review[frozenset((row["left"], row["right"]))] = row["decision"]
    return review

