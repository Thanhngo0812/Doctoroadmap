# 01 — Fixture ghi cho báo cáo DOCX (bản có ảnh) và slide

**What to build:** Hai tài liệu mới chạy được trong bộ test dưới một giây, không cần Docling thật —
y như hai giáo trình đã có fixture.

Ghi fixture Docling cho:

- **Báo cáo DOCX, bản hiện tại** — user vừa dán **3 ảnh PNG raster** vào ruột (`word/media/` có
  image1–3.png, tổng ~790 KB) đúng để thử đường trích ảnh. File đã đổi so với bản vòng 9 phân tích
  (sha256 mở đầu `5c46fa3d`, bản cũ `11cd54e7`) — fixture ghi từ **bản mới**, và mọi số đo vòng 9
  có thể lệch nhẹ, đó là chuyện chờ đợi được. Ingest lại bản mới đo được: 269/396 node giữ,
  **3 node figure**, 30 chunk.
- **Slide Naive Bayes** — 224/224 node, 36 trang, có OCR.

## Đầu ra khám phá bắt buộc

Fixture là ảnh chụp `DoclingDocument`, **độc lập với cổng trích ảnh đang chặn DOCX**. Ghi xong phải
trả lời: các mục picture trong DoclingDocument của DOCX **có mang dữ liệu ảnh của 3 PNG raster
không**? Câu trả lời quyết định tầm với của ticket 03 (trích thẳng từ document, hay cần đường khác)
— ghi rõ vào phần Note của ticket này khi đóng.

**Blocked by:** None — can start immediately.

**Status:** done

- [x] Fixture DOCX ghi từ bản file hiện tại (có 3 PNG), đặt cạnh hai fixture giáo trình
- [x] Fixture slide ghi từ PDF hiện tại
- [x] Test phát lại: nạp fixture → adapter → cây node, so được với chạy thật (cùng cơ chế
      round-trip đã dùng cho hai fixture cũ)
- [x] Ghi lại cỡ tệp thật của hai fixture (không ước lượng — bài học vòng 6)
- [x] Trả lời câu hỏi khám phá: picture item của DOCX có/không mang dữ liệu ảnh raster
- [x] Toàn bộ test hiện có vẫn xanh — fixture mới chưa được phép đổi hành vi nào
