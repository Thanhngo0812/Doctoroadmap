# 03 — Vai trò vùng văn bản

**Nguồn chân lý:** [spec v3](../../doc/v3-lo-trinh-doc-duoc-spec.md), R1 · **Ai:** nhân viên · **Phụ thuộc:** — · **Chi phí mô hình:** 0

**Trạng thái:** đã cài đặt và kiểm chứng (2026-09-26), chờ reviewer nghiệm thu

## Việc cần làm
- `Section` mang `role` ∈ `noi_dung`, `bai_tap`, `de_cuong`, `mo_dau`, `hanh_chinh`; chunk thừa hưởng vai trò section của nó.
- Luật thuần theo mẫu tiêu đề và vị trí (danh sách mẫu trong spec v3 R1); trang mục lục đã phát hiện (`_toc_runs`) là `de_cuong`;
  mọi thứ trước tiêu đề chương có số đầu tiên là `mo_dau` trừ khi tiêu đề nói khác.
- Lưu vào artifact chunks (thêm trường, cấu hình chunk đổi → tăng `CHUNK_ALGORITHM_ID`); cung cấp hàm `chunk_roles(chunks)` cho các
  stage sau.
- **Tái dùng:** vai trò tính lại được từ cây section có sẵn mà không nhập lại PDF (ghi rõ cách).

## Tệp liên quan
`domain/chunking.py`, `domain/models.py` (`Section`, `Chunk`), `application/use_cases/ingest_document.py`.

## Nghiệm thu
- Test mỗi mẫu tiêu đề (tiếng Việt, tiếng Anh, có/không dấu; "Exercises 3B", "Câu hỏi ôn tập", "Nội dung môn học", "Preface",
  "Lời nói đầu", "Mục lục"); test vùng `bai_tap` đóng khi gặp tiêu đề cùng cấp; test phần trước chương đầu là `mo_dau`.
- **Tôi kiểm:** vai trò trên doc-1 (đề cương học phần, "Bài tập chương n", "Đề số n"), doc-2 (Preface, "Exercises nX"), doc-6
  ("Nội dung môn học", slide "Nội dung" lặp), nhap-mon-ml ("MỞ ĐẦU") — liệt kê section theo vai trò và đọc.

## Kiểm thử của nhân viên

Test từng mẫu có/không dấu, kế thừa con/đóng vùng cùng cấp, phần trước chương có số, TOC, roundtrip và nâng metadata
đều xanh; đã thấy đỏ trước sửa. `CHUNK_ALGORITHM_ID=section-id-v9-roles`; có `chunk_roles(chunks)`.
Tái tính không cần PDF bằng `assign_section_roles(sections, chunks)`; công cụ
`scripts/doc-lo-trinh/vai_tro_vung.py --doc-id X --save` ghi version mới (không ghi đè), giữ nguyên ID/text/offset.
Đã ghi doc-1 chunks v6, doc-2 v2, doc-6 v3, nhap-mon-ml v3, doc-3 v2, naive-bayes v2.

Đã đọc các section chỉ định. **Lưu ý cho vé 04:** doc-2 có 725 chunk kế thừa bài tập do cây cũ nhận sai mục dạng
`1B`, `3C`; chưa được dùng số đó để loại nội dung thật. Stage ghim chunk cũ không tự chuyển version.
Danh sách, số lượng và cách tái dùng: [báo cáo](../../report/v3-01-03-10-ket-qua-2026-09-26.md).
