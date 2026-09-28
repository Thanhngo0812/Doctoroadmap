# 11b — Tên khái niệm có nội dung: căn cứ rộng hơn dòng nhãn, chống trùng tên

**Nguồn chân lý:** [spec v3](../../doc/v3-lo-trinh-doc-duoc-spec.md), R9 (bổ sung 2026-09-28) · **Ai:** nhân viên · **Phụ thuộc:** 11 ·
**Chi phí mô hình:** vài lời gọi (≈ 0,005 USD cho kho phát triển)

**Trạng thái (2026-09-28):** đã triển khai, test và chạy lại sáu tài liệu. doc-1 có tên hiển thị hợp lệ cho 7/8 nhãn cần kiểm; `Định lý 4` giữ nhãn cũ kèm cảnh báo `display_name quá dài`, đúng đường fallback của vé. Không nhận tên trùng với khái niệm khác. [Báo cáo](../../report/ket-qua-v3-05b-09b-11b-vertex-2026-09-28.md).

## Vì sao (kiểm thử vé 11, 2026-09-28)
- "Định lý 4" → "Ma trận chuyển cơ sở", "Định lý 7" → "Hạng của hệ véc tơ": tên hiển thị **trùng tên khái niệm có sẵn** trong sách.
- "Tính chất 3", "Tính chất 4", "Định lý 6" còn nhãn số: câu neo chỉ là dòng nhãn ("✸ Tính chất 3 ."), mệnh đề nằm ở câu ngay sau.
- "Tính chất 1" → "Tính chất cơ bản của định thức": đúng luật nhưng quá chung, vì nội dung nằm trong công thức.

## Việc cần làm
- Khi câu neo không đủ từ nội dung (chỉ là dòng nhãn), căn cứ gồm câu neo và một–hai câu kế tiếp trong cùng chunk; luật kiểm từ giữ
  nguyên, áp trên phạm vi đó.
- `display_name` không được trùng tên, alias hay `display_name` của khái niệm khác trong tài liệu (so sau chuẩn hoá). Trùng → hỏi lại một
  lần kèm tên bị trùng; vẫn trùng → giữ nhãn cũ và ghi cảnh báo.

## Tệp liên quan
`domain/anchors.py` (`validate_display_name`), `application/use_cases/name_concept_labels.py`, `prompts/a10/display_name.txt`.

## Nghiệm thu
- Test: căn cứ mở rộng khi câu neo chỉ là dòng nhãn; trùng tên khái niệm khác bị bác và hỏi lại; fixture ở ít nhất hai ngôn ngữ ngoài vi/en.
- **Tôi kiểm:** đọc doc-1 ("Tính chất 1–4", "Định lý 4, 6, 7") và các nhãn số của tài liệu khác nếu có.

## Kiểm thử (Claude, 2026-09-28) — **đạt**

- **Test:** đột biến "tắt chặn trùng tên" và "tắt căn cứ mở rộng" đều làm test đỏ. Fixture tiếng Nhật và tiếng Pháp.
- **Trùng tên:** sau chuẩn hoá, không `display_name` nào trùng tên, alias hay tên hiển thị của khái niệm khác, trên cả sáu tài liệu.
  Năm tài liệu kia không có nhãn số cần đặt tên.
- **Đọc doc-1, theo văn bản gốc:**
  - Đúng:
    - "Tính chất 3" → "Công thức khai triển định thức theo hàng i";
    - "Tính chất 4" → "… theo cột j";
    - "Định lý 5" → "dim W ≤ dim V".
  - Chấp nhận:
    - "Tính chất 2" → "Đổi chỗ hai hàng hay hai cột": thiếu vế "thì định thức đổi dấu";
    - "Định lý 7" → "Hạng ma trận của hệ đối với một cơ sở": gọi tên đại lượng thay vì mệnh đề "hạng hệ = hạng ma trận";
    - "Tính chất 1" → "Tính chất cơ bản của định thức": nội dung chỉ nằm trong công thức, nên chung chung nhưng có căn cứ;
    - "Định lý 4" giữ nhãn và có cảnh báo, đúng đường fallback.
  - **Sai lạc:** "Định lý 6" → "không gian con của không gian véc tơ".
    - Tên lấy từ giả thiết ("Giả sử U và W là các không gian con của không gian véc tơ hữu hạn chiều V").
    - Kết luận là công thức số chiều, đã mất thành `[formula]`.
    - Người đọc sẽ tưởng đây là bài "Không gian con".
- **Ghi nhận, chưa mở vé:** khi sửa prompt đặt tên lần tới, yêu cầu tên nêu điều kết quả khẳng định. Nếu điều đó chỉ nằm trong công thức
  không đọc được thì không đặt tên (giữ nhãn).
