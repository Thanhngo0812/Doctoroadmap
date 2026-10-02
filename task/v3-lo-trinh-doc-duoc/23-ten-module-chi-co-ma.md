# 23 — Tên module chỉ có mã mục thì thêm tên khái niệm

**Nguồn chân lý:** [spec v3](../../doc/v3-lo-trinh-doc-duoc-spec.md) R7 (tên module có nghĩa), bảng kiểm R11 (`ten-nen-chi-co-ma`) ·
**Ai:** nhân viên · **Phụ thuộc:** — · **Chi phí mô hình:** gần 0 (chỉ hỏi lại module bị đổi tên; tên tối đa 128 token)

**Trạng thái:** chờ chủ dự án quyết: làm trước khi khoá T10, hay sau tập giữ lại.

## Vì sao (Claude, 2026-10-03)
- doc-2 (`v3-r12-final-evaluation` v8) có 5/53 module mà tên chỉ là mã: "Chapter 3", "6B", "7C", "Chapter 7", "Chapter 8". Người học không
  biết "6B" là gì, trong khi bên trong là Orthonormal list, Orthonormal basis, Gram-Schmidt procedure…
- `prepare_module_titles` đã tìm phần tên còn thiếu ở mục lục đầu sách và ở dòng đầu của mục. Không tìm được thì chỉ gắn cờ
  `numbering_only_title` và **giữ nguyên mã làm tên**.
- Module trải nhiều mục lấy tên mục chung sâu nhất. Nếu đó là chương mà tên chương chỉ có mã thì ra "Chapter 7" (module này chứa Cholesky
  factorization, Singular value decomposition…).
- Năm tài liệu còn lại có 0 tên kiểu này. Lỗi gắn với kiểu tách tiêu đề của docling ("Chapter 3" và tên chương thành hai khối), nên sách
  khác cũng có thể gặp.

## Việc cần làm
- Khi tên nền của module chỉ có mã (mục nằm trong `numbering_flags`, hoặc tên khớp trọn `section_code`), đưa module vào nhóm cần đặt tên
  (`needs_model`) như module bị chia của vé 09d: giữ mã làm tiền tố, mô hình chọn 1–3 tên khái niệm **nguyên vẹn** nối sau
  ("6B — Orthonormal basis · Gram-Schmidt procedure").
- Không đổi module, dãy học hay cạnh. Chỉ đổi `title` của module có tên nền chỉ có mã. Module khác giữ nguyên tên (tái dùng như 09d).
- Đổi config hash của bước tên module.
- Không thêm danh sách từ của ngôn ngữ nào: nhận mã bằng `section_code` và họ đánh số của chính tài liệu, như hiện nay.

## Nghiệm thu
- **Test**, fixture ở hai ngôn ngữ ngoài vi/en: mục chỉ có mã, không có mục lục → tên gồm mã và ít nhất một tên khái niệm nguyên vẹn. Test
  phải đỏ trên mã hiện tại.
- **Chạy lại bước tên module** sáu tài liệu trên kho cuối, tái dùng tên cũ:
  - `kiem_doc_duoc.py`: `ten-nen-chi-co-ma` = 0 ở doc-2, các loại khác không tăng;
  - mọi module khác giữ nguyên tên;
  - báo chi (một con số).
- **Chạy lại** `kiem_tuong_duong_chuoi.py` với đích `module_titles` mới; tôi sinh lại bảng khoá.
- **Tôi kiểm:** đọc năm tên mới của doc-2.
