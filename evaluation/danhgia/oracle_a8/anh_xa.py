"""Ánh xạ ngược trạng thái dạy: bốn giá trị vàng G3 sang sáu giá trị của máy.

Chiều xuôi (nháp) nằm ở `evaluation/giao-thuc/anh-xa-trang-thai.json`: `taught` <- {day_o_day, day_qua_vi_du}, `mentioned_only` <- {chi_nhac},
`prior_knowledge` <- {kien_thuc_nen}. Chiều ngược chọn **một** giá trị máy cho mỗi giá trị vàng, và phải đi ngược lại được chiều xuôi
(test `test_anh_xa_nguoc_la_nghich_dao_cua_chieu_xuoi`):

| vàng | máy | lý do |
|---|---|---|
| `day_o_day` | `taught` | dạy ở đây |
| `day_qua_vi_du` | `taught` | máy không có giá trị riêng cho "dạy qua ví dụ"; chiều xuôi cũng gộp vào `taught` |
| `chi_nhac` | `mentioned_only` | chỉ nhắc; A10 đưa ra khỏi dãy học nhưng vẫn là tiên quyết tiềm năng |
| `kien_thuc_nen` | `prior_knowledge` | kiến thức nền; A10 loại khỏi dãy, cạnh đi qua nó được co lại |
| `null` (tranh chấp trạng thái) | `uncertain` | vàng chưa chốt trạng thái; A10 vẫn xếp (uncertain ở trong dãy) |

`unchecked` và `not_subject_matter` không bao giờ là đầu ra của oracle: vàng không có khái niệm "không thuộc môn" (loại khỏi kho chốt).
"""

MAY_TU_VANG = {
    "day_o_day": "taught",
    "day_qua_vi_du": "taught",
    "chi_nhac": "mentioned_only",
    "kien_thuc_nen": "prior_knowledge",
    None: "uncertain",
}
# trạng thái máy mà node có câu neo (anchor) và chunk dạy
CO_NEO = {"taught"}


def sang_may(trang_thai_vang):
    if trang_thai_vang not in MAY_TU_VANG:
        raise ValueError(f"trạng thái vàng {trang_thai_vang!r} không có trong ánh xạ ngược; phải thuộc {sorted(map(str, MAY_TU_VANG))}")
    return MAY_TU_VANG[trang_thai_vang]
