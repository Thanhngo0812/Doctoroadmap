# 03 — Vai trò vùng văn bản

**Nguồn chân lý:** [spec v3](../../doc/v3-lo-trinh-doc-duoc-spec.md), R1 · **Ai:** nhân viên · **Phụ thuộc:** — · **Chi phí mô hình:** 0

**Trạng thái:** **đạt**, kèm hai điều kiện chuyển sang vé 04 — Claude kiểm thử 2026-09-26 (mục cuối)

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

## Kiểm thử (Claude, 2026-09-26) — đạt, hai điều kiện chuyển sang vé 04

- Đọc diff: luật thuần theo mẫu tiêu đề và vị trí; vai trò tính lại được từ cây đã lưu mà không đổi ID/text/offset;
  `refresh_chunk_roles` ghi version mới, không ghi đè.
- Test xanh. Đột biến 4/5 bị bắt: bỏ mẫu Exercises; con không kế thừa vai trò cha; phần trước chương đầu không thành `mo_dau`; mục
  lục đã phát hiện không thành `de_cuong`. **Sống sót một đột biến:** tắt luật "chương có số luôn mở lại vùng nội dung" mà không
  test nào đỏ; trên sáu tài liệu hiện có, luật này cũng không đổi vai trò nào. Đây là chốt chặn chưa từng thấy đỏ → điều kiện 1.
- Bản chunks mới không làm lệch cache: dry-run sáu tài liệu, mọi stage A6 tới pass chính A8 vẫn "tái dùng".
- Đọc vai trò:
  - **doc-1** đúng: bìa → `mo_dau`; "Mục lục", "ĐỀ CƯƠNG CHI TIẾT HỌC PHẦN" → `de_cuong`; "10. Hình thức và tiêu chuẩn đánh giá
    sinh viên" → `hanh_chinh`; "Bài tập chương 2–5", "Đề thi tham khảo", "Đề số 1–8" → `bai_tap`. Chỗ nhỏ: "9. Tài liệu tham khảo"
    thành `mo_dau` và "Tài liệu tham khảo" cuối sách thành `bai_tap` (kế thừa) — đều nằm ngoài nội dung dạy nên không hại.
  - **doc-6** đúng: "Nội dung môn học" và sáu slide "Nội dung" lặp → `de_cuong`; trang bìa lặp → `mo_dau`; các mục đánh số →
    `noi_dung`.
  - **nhap-mon-ml** đúng: "MỤCLỤC" → `de_cuong`; "MỞĐẦU", tập thể tác giả, tài liệu đọc → `mo_dau`. Lưu ý cho vé 05: trước khi loại
    vùng này khỏi neo, kiểm xem có khái niệm nào chỉ được định nghĩa trong MỞ ĐẦU không.
  - **doc-2**: vai trò đúng theo cây, nhưng cây sai, như nhân viên đã báo. 564/725 chunk `bai_tap` thực ra là nội dung dạy của mục
    kế sau bị treo dưới "Exercises nX" (ví dụ "3.132 matrix of T′ is transpose of matrix of T", "6.42 Riesz representation
    theorem"); chỉ 161 chunk nằm dưới chính các tiêu đề Exercises. "Photo Credits" (8 chunk) cũng đang mang `bai_tap` → điều kiện 2.
- **Điều kiện, ghi vào vé 04:** (1) thêm test cho luật chương có số, hoặc bỏ luật nếu cây mới không cần nó; (2) sau khi sửa cây, doc-2
  chỉ còn khoảng 161 chunk `bai_tap`, không mục kết quả đánh số nào mang `bai_tap`, và phần cuối sách không thành `noi_dung`.

## Rà soát đa ngôn ngữ (Claude, 2026-09-26)

Luật theo mẫu tiêu đề tiếng Việt/tiếng Anh (`ROLE_PATTERNS`, tìm chương đầu bằng "chương|chapter") trái nguyên tắc đa ngôn ngữ của spec
v3. Cách tính vai trò được thay ở vé [14](14-vai-tro-cau-truc-da-ngon-ngu.md); giao diện `role`, `chunk_roles` và cách ghi version
chunks giữ nguyên, nên các vé 05, 06, 07 không phải chờ.
