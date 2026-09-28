# 11 — Tên khái niệm có nội dung

**Nguồn chân lý:** [spec v3](../../doc/v3-lo-trinh-doc-duoc-spec.md), R9 · **Ai:** nhân viên · **Phụ thuộc:** 05 · **Chi phí mô hình:** ≈ 0,02 USD / tài liệu

**Trạng thái:** chờ giao

## Việc cần làm
- Nhận nhãn đánh số và từ chung bằng bằng chứng trong tài liệu, không bằng danh sách từ *(sửa 2026-09-26 theo spec v3 R9)*: **họ nhãn**
  là tiền tố (một–hai từ; với chữ viết không cách từ, một–hai ký tự) đi với ít nhất hai số khác nhau trong tên khái niệm hoặc tiêu đề
  của cùng tài liệu ("Tính chất 1", "Tính chất 3"; "Theorem 4", "Theorem 7"; "定理 2", "定理 5").
- Tên đúng bằng tiền tố của một họ nhãn ("Định lý", "Theorem" đứng một mình) là từ chung: không là khái niệm, loại ở bước neo
  (`not_subject_matter`, lý do "từ chung").
- Tên là một phần tử của họ nhãn nhận `display_name` ngắn sinh từ câu neo, viết bằng ngôn ngữ của tài liệu; mã kiểm từ nội dung có trong
  câu neo (chữ viết không cách từ: kiểm theo chuỗi con); nhãn cũ thành alias. `node_id`, `name` gốc giữ nguyên — bộ vàng không đổi. A10
  hiển thị `display_name`.

## Tệp liên quan
`domain/anchors.py` hoặc use case riêng sau neo, `application/use_cases/build_roadmap.py` (hiển thị).

## Nghiệm thu
- Test nhận diện họ nhãn và từ chung trên tên tổng hợp ở tiếng Việt, tiếng Anh và ít nhất hai ngôn ngữ khác (một chữ viết không cách
  từ); tiền tố chỉ đi với một số không thành họ nhãn; test kiểm từ của `display_name`.
- **Tôi kiểm:** doc-1 không còn "Tính chất 1…4", "Định lý 4…7" trên lộ trình; doc-2 không còn "Definition", "Theorem".

## Kiểm thử (Claude, 2026-09-28) — đạt về mã; kết quả chưa đạt → vé 11b

- Đột biến 2/2 bị bắt: họ nhãn chỉ cần một số; tên hiển thị không cần căn cứ câu neo.
- Đọc doc-1: "Tính chất 2" → "Đổi chỗ hai hàng hay hai cột" (tốt). Nhưng "Định lý 4" → "Ma trận chuyển cơ sở" và "Định lý 7" → "Hạng của
  hệ véc tơ" **trùng tên khái niệm có sẵn**, người học sẽ nhầm; "Tính chất 1" → "Tính chất cơ bản của định thức" quá chung (công thức nằm
  trong `[formula]`). Ba nhãn còn số ("Tính chất 3", "Tính chất 4", "Định lý 6") có câu neo chỉ là dòng nhãn, mệnh đề nằm ở câu ngay sau.
  → vé [11b](11b-ten-khai-niem-can-cu-va-trung.md).
