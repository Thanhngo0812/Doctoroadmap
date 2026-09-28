# 09b — Tên module: phần phụ có nghĩa, không lặp tên nền; tên nền lấy từ cây mục đã sửa

**Nguồn chân lý:** [spec v3](../../doc/v3-lo-trinh-doc-duoc-spec.md), R7 (bổ sung 2026-09-28) · **Ai:** nhân viên · **Phụ thuộc:** 09 ·
**Chi phí mô hình:** hỏi lại các module vi phạm (≈ 0,01 USD cho kho phát triển)

**Trạng thái (2026-09-28):** đã triển khai, test và chạy lại sáu tài liệu trên A9 v10. Không còn tên module trùng trong cả sáu; doc-1 và doc-2 không có phần phụ lặp nguyên tên nền hay `(1/1)`. Vẫn còn tên nền chung như `Chapter 1`/`Chapter 9` ở doc-2 và tiêu đề dài do cây mục, ngoài phạm vi luật phần phụ của vé. [Báo cáo](../../report/ket-qua-v3-05b-09b-11b-vertex-2026-09-28.md).

## Vì sao (kiểm thử vé 09, 2026-09-28)
Tên không còn trùng, nhưng phần phụ hay lặp tên nền ("2.1 Ma trận — Ma trận", "5.2 Dạng toàn phương trên không gian R n — trên không gian
R n"), hay chỉ là mẩu tên ("2.1 Ma trận — thực", "Vector — space", "Matrix — multiplication"); có cả "Jordan basis — Jordan basis" và
"(1/1)". doc-2 có nhiều tên nền "Chapter n" vì cây mục cũ bị vỡ.

## Việc cần làm
- Luật kiểm phần phụ, không dùng danh sách từ:
  - không trùng và không là chuỗi con của tên nền (sau chuẩn hoá), tên nền cũng không là chuỗi con của nó;
  - nếu mọi từ chỉ lấy từ **một** tên khái niệm thì phải là trọn tên đó, không là mẩu của nó;
  - phải có ít nhất một chữ cái.
- Vi phạm → hỏi lại một lần kèm lý do. Vẫn sai → dùng trọn tên của một–hai khái niệm tiêu biểu của module (khái niệm đầu module và khái
  niệm có nhiều cạnh ra nhất trong module). Chỉ dùng "(k/n)" khi hết cách, và không bao giờ in "(1/1)".
- Tài liệu có đồ thị dựng trên version chunks cũ (doc-2): đường dẫn mục dùng để đặt tên lấy từ cây đã sửa, bằng đúng phép chuyển theo văn
  bản của vé 14b (chỉ để hiển thị; ID, vai trò, cạnh giữ nguyên).

## Tệp liên quan
`domain/module_titles.py` (`grounded_suffix`, `common_content_title`), `application/use_cases/name_modules.py`, `prompts/a10/module_title.txt`.

## Nghiệm thu
- Test từng luật kiểm (lặp tên nền, mẩu tên, không chữ cái, "(1/1)"), trên tiêu đề tổng hợp ở ít nhất hai ngôn ngữ ngoài vi/en.
- **Tôi kiểm:** đọc lại toàn bộ tên module doc-1, doc-2 và một tài liệu khác.
