# 04 — Cấu trúc mục kiểu sách toán

**Nguồn chân lý:** [spec v3](../../doc/v3-lo-trinh-doc-duoc-spec.md), R2 · **Ai:** nhân viên · **Phụ thuộc:** 03 · **Chi phí mô hình:** 0

**Trạng thái:** chờ giao

## Việc cần làm
- Nhận tiêu đề mục dạng "3C Matrices", "Section 3C …" là cấp mục dưới "Chapter 3".
- Mục đánh số kết quả ("3.36 definition: …", "5.1 definition: operator", "Định lý 2.1.", "Ví dụ 3.") là **khối** nằm trong mục,
  không mở section mới.
- Vùng `bai_tap` ("Exercises 3B") đóng khi gặp tiêu đề mục kế tiếp.
- Tự nhận theo mẫu, không cờ theo tài liệu; `--heading-scheme vn-textbook` giữ nguyên.

## Tệp liên quan
`domain/chunking.py` (`_heading_number_level`, `_false_heading_reason`, `_chapter_sequences`).

## Nghiệm thu
- Test cây mục cho mẫu Axler (Chapter 3 → 3A/3B/3C → khối "3.36 definition") và cho "Exercises 3B" đóng trước "3C".
- **Tôi kiểm:** nhập lại doc-2 (không tốn tiền), đọc cây mục chương 3: nội dung "Matrices" phải nằm dưới "3C", không dưới
  "Exercises 3B". Hash chunk của doc-1, xstk, doc-4 không đổi (luật không kích hoạt) — nếu đổi phải báo.

## Bổ sung sau kiểm thử vé 03 (Claude, 2026-09-26)

- **Nghiệm thu thêm cho doc-2**, sau khi tính lại vai trò trên cây mới: chunk `bai_tap` chỉ còn phần nằm dưới chính các tiêu đề
  Exercises (hiện khoảng 161 chunk); 564 chunk đang treo dưới "Exercises nX" là nội dung dạy (ví dụ "3.132 matrix of T′ is transpose
  of matrix of T", "6.42 Riesz representation theorem") phải về `noi_dung`. Không mục kết quả đánh số nào mang `bai_tap`.
- **Phần cuối sách:** thêm vai trò `cuoi_sach` (spec v3 R1) cho tiêu đề "Photo Credits", "Index", "Symbol Index", "References",
  "Bibliography", "Tài liệu tham khảo"; mỗi mẫu một test. "Photo Credits" của doc-2 phải ra `cuoi_sach`, không phải `noi_dung`.
- **Luật "chương có số luôn mở lại vùng nội dung"** (vé 03) hiện không có test nào đỏ khi tắt nó. Thêm test (một chương có số nằm dưới
  tiêu đề `mo_dau` hoặc `de_cuong` vẫn là `noi_dung`); hoặc, nếu cây mới khiến luật thừa, bỏ luật kèm test chứng minh.
