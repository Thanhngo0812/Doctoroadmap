"""Resolve canonical review IDs and preserve human constraints through model conflicts."""
from itertools import combinations, product

from .canonical import digest
from .canonical_decisions import guarded_components
from .identity import _names, _normalized, VERIFY_RELATIONS


def shared_names(left, right):
    names = lambda node: {_normalized(name) for name in _names(node)} - {""}
    return bool(names(left) & names(right))


def validate_merge_verification(value, *, pair_id):
    if not isinstance(value, dict) or value.get("pair_id") != pair_id:
        raise ValueError("xác minh sai pair_id")
    if value.get("relation") not in VERIFY_RELATIONS:
        raise ValueError("relation ngoài tập đóng")
    if not isinstance(value.get("reason"), str) or not value["reason"].strip():
        raise ValueError("xác minh thiếu reason")


def review_constraints(review, previous, initial_nodes):
    initial_by_id = {node["node_id"]: node for node in initial_nodes}
    nodes = {node["node_id"]: node for node in [*initial_nodes, *previous.get("nodes", [])]}
    redirects = previous.get("redirects", {})
    member_groups = {member: node["node_id"] for node in initial_nodes for member in node["members"]}

    def groups(node_id):
        original, seen = node_id, set()
        while node_id in redirects:
            if node_id in seen:
                raise ValueError(f"vòng chuyển hướng id duyệt {original}")
            seen.add(node_id)
            node_id = redirects[node_id]
        if node_id not in nodes:
            raise ValueError(f"id duyệt không thuộc canonical hiện hành: {original}")
        # Keep the reviewed side's A3 members when its old group still exists. A
        # redirect may now land in a merged node containing BOTH reviewed sides.
        source = initial_by_id.get(original, nodes[node_id])
        result = {member_groups[member] for member in source["members"] if member in member_groups}
        if not result:
            raise ValueError(f"id duyệt không còn thành viên trong ứng viên A3: {original}")
        return result

    same, different = set(), set()
    for pair, decision in review.items():
        if decision not in {"Đồng ý gộp", "Không gộp", "Là hai nghĩa khác nhau", "Không chắc"}:
            raise ValueError(f"quyết định duyệt không hợp lệ: {decision}")
        if len(pair) != 2:
            raise ValueError("mỗi quyết định duyệt cần hai id khác nhau")
        left, right = [groups(node_id) for node_id in sorted(pair)]
        if decision == "Đồng ý gộp":
            same.update(tuple(sorted(pair)) for pair in combinations(left | right, 2))
        else:
            if left & right:
                raise ValueError("quyết định không gộp trỏ về cùng một nhóm; cần duyệt lại sau khi tách ứng viên")
            different.update(tuple(sorted(pair)) for pair in product(left, right))
    if same & different:
        raise ValueError("quyết định người duyệt tự mâu thuẫn cùng/khác")
    return sorted(same), sorted(different)


def reviewed_components(ids, same, different, human_same, human_different):
    blocks, conflicts = guarded_components(ids, human_same, human_different)
    if conflicts:
        raise ValueError("quyết định người duyệt tự mâu thuẫn bắc cầu")
    owner = {key: index for index, block in enumerate(blocks) for key in block}
    blocked = {(min(owner[a], owner[b]), max(owner[a], owner[b])) for a, b in human_different}
    model_same = {(owner[a], owner[b]) for a, b in same
                  if owner[a] != owner[b] and tuple(sorted((owner[a], owner[b]))) not in blocked}
    model_different = {(owner[a], owner[b]) for a, b in different if owner[a] != owner[b]}
    merged, conflicts = guarded_components(list(range(len(blocks))), model_same,
                                           [*model_different, *blocked])
    expand = lambda component: sorted(key for index in component for key in blocks[index])
    return [expand(component) for component in merged], [expand(component) for component in conflicts]


def reserve_node_ids(nodes, previous):
    """A retired ID remains a redirect even if its old anchor reappears after a split."""
    retired = previous.get("redirects", {})
    for node in nodes:
        original = node["node_id"]
        if original in retired:
            revision = 1
            while True:
                node_id = "node_" + digest([original, node["anchor_candidate_id"], "retired", revision])[:24]
                if node_id not in retired:
                    node["node_id"] = node_id
                    break
                revision += 1
