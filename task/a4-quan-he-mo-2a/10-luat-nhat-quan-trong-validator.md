# 10 — Luật nhất quán trong validator

**What to build:** `validate_partition` bắt đầu ra tự mâu thuẫn và báo lỗi, để cơ chế thử lại sẵn có bắt mô hình phán
lại. Luật R1, R2 và tập đồng nhất lấy đúng như ticket 09.

## Vì sao đặt trong `validate_partition`, không đặt trong `split_relation_edges`

`split_relation_edges` chỉ loại từng quan hệ, nên lần gộp sai vẫn đứng. Mâu thuẫn giữa quan hệ và phân hoạch là lỗi của
**cả đầu ra**. Nó phải đi đường của lỗi phân hoạch: thử lại một lần, rồi mới hoãn cụm.

**Blocked by:** 09 — Kế hoạch đợt 2

**Status:** done — 2026-09-14

- [x] Thêm lớp lỗi `ContradictionError(ValueError)` trong `domain/canonical_decisions.py`. Code thử lại hiện có vẫn bắt
      được nó vì nó là `ValueError`, còn ticket 12 thì phân biệt được nó để đếm riêng.
- [x] Hằng `IDENTITY_EDGE_TYPES` = {`same_as`, `equivalent_to`, `identical_to`, `synonym_of`, `alias_of`}. So sau
      `normalize_edge_type`; `edge_type` không phải chuỗi thì bỏ qua ở bước này, để `split_relation_edges` loại như cũ.
- [x] Trong `validate_partition`, sau phần kiểm cấu trúc, xét mọi quan hệ có **cả hai đầu** nằm trong `nodes`:
  - **R1:** hai nhóm khác nhau, cùng một node, kiểu không thuộc tập đồng nhất ⇒ mâu thuẫn;
  - **R2:** hai nhóm ở hai node khác nhau, kiểu thuộc tập đồng nhất ⇒ mâu thuẫn.
- [x] Gom **mọi** mâu thuẫn của đầu ra vào **một** `ContradictionError`, để lượt thử lại sửa hết một lần. Mỗi mâu thuẫn ghi
      id hai nhóm, kiểu quan hệ và cách sửa. Ví dụ R1: *"g_3 và g_7 cùng node nhưng có quan hệ g_3 subtype_of g_7: quan
      hệ nghĩa là hai node riêng — tách hai nhóm hoặc bỏ quan hệ"*. Ví dụ R2: *"g_2 equivalent_to g_5 nhưng nằm hai node:
      cùng một thực thể thì chung node"*.
- [x] Không đổi:
  - quan hệ tới nhóm lạ hoặc nhóm `deferred`, và quan hệ đồng nhất trong cùng node, vẫn do `split_relation_edges` loại
    riêng như hiện nay;
  - kiểm "cùng node" trong `split_relation_edges` giữ lại làm lớp phòng thủ.
- [x] **Test.** Mỗi test phải hỏng khi bỏ đúng guard của nó; nộp danh sách đột biến đã thử:
  - R1 với `subtype_of`, `precedes`, `example_of` trong cùng node ⇒ `ContradictionError`;
  - R2 với `equivalent_to` giữa hai node, và với kiểu viết khác chữ (`Same_As`) ⇒ `ContradictionError`;
  - `same_as` trong cùng node ⇒ không lỗi, và `split_relation_edges` loại nó;
  - quan hệ tới nhóm `deferred` ⇒ không lỗi ở validate;
  - hai mâu thuẫn trong một đầu ra ⇒ một lỗi nêu đủ cả hai;
  - seam với trọng tài giả: lần đầu mâu thuẫn, lần thử lại tách đúng ⇒ phân hoạch lần hai được áp và nhật ký giữ lỗi của
    lần đầu;
  - seam: mâu thuẫn cả hai lần ⇒ cả cụm `deferred`, không gộp gì.
- [x] Toàn bộ test xanh, chặn mạng.

## Bằng chứng hoàn tất

- R1 và R2 được kiểm sau khuôn phân hoạch; lỗi liệt kê đủ mọi mâu thuẫn, đầu mút lạ/deferred và kiểu không phải chuỗi vẫn
  đi qua lớp loại quan hệ cũ. Seam giả xác nhận lần hai hợp lệ được áp; mâu thuẫn hai lần hoãn trọn cụm.
- Đột biến đã chạy thật: vô hiệu R1 làm đỏ cả ba ca `subtype_of`, `precedes`, `example_of`; vô hiệu R2 làm đỏ cả hai ca
  `equivalent_to`, `Same_As`. Khôi phục guard xong, 70 test domain+A4 xanh và toàn suite 294 test xanh.
