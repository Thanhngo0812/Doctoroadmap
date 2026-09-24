from __future__ import annotations

from .identity import merge_and_break_cycles

# Cạnh ngầm (vé v2-06, spec v2 W20): định nghĩa của B dùng A mà không đoạn nào nhắc cả hai tên, nên luật "chunk căn cứ
# nhắc cả hai đầu" của pass chính không bao giờ tạo được cạnh đó. Đo trên vàng: 16/27 cạnh thiếu của doc-2 thuộc loại này.
# Căn cứ thay thế: một cụm nguyên văn trong đoạn định nghĩa của B mà việc hiểu nó cần A — kiểm chuỗi bằng mã.
IMPLICIT_KIND = "ngam"
IMPLICIT_CONFIDENCE = 0.6  # dưới `mach_trinh_bay` (0,7); hạng căn cứ 0 nên bị gỡ trước tiên khi khép chu trình


def _squash(text):
    return " ".join(str(text).split())


def implicit_candidates(order, edges, *, k):
    """{B: [A…]}: K khái niệm dạy ngay trước B, gần nhất trước, bỏ những A đã là tổ tiên của B trong đồ thị."""
    parents = {}
    for edge in edges:
        parents.setdefault(edge["target"], set()).add(edge["source"])
    ancestors = {}

    def ancestors_of(node):
        if node not in ancestors:
            seen, stack = set(), [node]
            while stack:
                for parent in parents.get(stack.pop(), ()):
                    if parent not in seen:
                        seen.add(parent)
                        stack.append(parent)
            ancestors[node] = seen
        return ancestors[node]

    result = {}
    for index, node in enumerate(order):
        window = order[max(0, index - k):index][::-1]
        known = ancestors_of(node)
        result[node] = [candidate for candidate in window if candidate not in known]
    return result


def validate_implicit_response(value, *, node_id, candidates, definition_text):
    if not isinstance(value, dict) or value.get("node_id") != node_id:
        raise ValueError("phán quyết sai node_id")
    if "confidence" in value:
        raise ValueError("mô hình không được trả confidence")
    rows = value.get("prerequisites")
    if not isinstance(rows, list):
        raise ValueError("prerequisites phải là danh sách")
    allowed, seen, text = set(candidates), set(), _squash(definition_text)
    for row in rows:
        if not isinstance(row, dict) or row.get("node_id") not in allowed:
            raise ValueError("tiên quyết không thuộc danh sách ứng viên")
        if row["node_id"] in seen:
            raise ValueError("tiên quyết bị lặp")
        seen.add(row["node_id"])
        if "confidence" in row:
            raise ValueError("mô hình không được trả confidence")
        quote = row.get("quote")
        if not isinstance(quote, str) or not _squash(quote) or _squash(quote) not in text:
            raise ValueError("quote không có nguyên văn trong đoạn định nghĩa của khái niệm đích")
        if not isinstance(row.get("reason"), str) or not row["reason"].strip():
            raise ValueError("tiên quyết thiếu reason")


def add_implicit_edges(existing, new):
    """Thêm cạnh ngầm, bỏ cạnh trùng cạnh có sẵn, rồi gỡ chu trình bằng hàm của A9 — cạnh ngầm hạng thấp nhất nên đi trước."""
    return merge_and_break_cycles([*existing, *new], {})
