# 04 — Neo định nghĩa (C8 v3)

**Nguồn chân lý:** spec v2, W11–W13

**What to build:** mỗi khái niệm có một câu neo nguyên văn nơi tài liệu dạy nó, và một trạng thái là thuộc tính của khái
niệm. Thay stage `teaching` v2.

**Blocked by:** vé 10 — T2 (tài liệu N1) và T3 (nhãn khái niệm mù trên N1). Có thể viết mã và chạy trên dữ liệu phát
triển trước; cổng chỉ chấm được khi có nhãn N1.

**Status:** ready (viết mã); cổng chờ T3

## Cổng nhận (khoá trước khi chạy trên N1)

1. **Q9 — câu neo đúng:** kiểm tay 50 khái niệm ngẫu nhiên trên ≥ 3 tài liệu (vé 10, T4): câu neo là nơi tài liệu dạy
   khái niệm ≥ 90%.
2. **Loại khái niệm trên N1 (nhãn mù):** loại đúng ≥ 80% khái niệm phải loại; loại nhầm ≤ 2% khái niệm phải giữ.
3. **Không làm mất vàng:** 0 đầu cạnh vàng của hai chương phát triển bị loại.
4. Báo kèm (bằng chứng phát triển, không phải cổng): nhãn `doc-3` đã khoá, và ba tài liệu cổng A của C8.

## Acceptance

- [ ] Tách câu và chọn ứng viên (W11) là hàm thuần có test.
- [ ] Prompt `a10/teaching.txt` v3, schema, kiểm câu trích bằng mã, kiểm tín hiệu tường minh cho `prior_knowledge`.
- [ ] Đổi sổ đăng ký hash prompt có chủ đích; README prompt ghi v3.
- [ ] Sửa spec provenance và `spec-addendum.md` A3–A5 (neo định nghĩa) cùng commit.
