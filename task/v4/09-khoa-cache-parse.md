# v4-09 — Khoá cache parse theo mọi tuỳ chọn docling làm đổi đầu ra

**Nguồn chân lý:** [R-03](../../report/nghien-cuu-v4-a1-docling-2026-10-04.md) mục 1, [đo A1 lượt 1](../../report/v4-10-do-a1-tai-may-2026-10-05.md) ·
**Ai:** nhân viên · **Phụ thuộc:** — · **Chi phí mô hình:** 0

**Trạng thái:** soạn 2026-10-05. Phải xong **trước** mọi vé đổi cấu hình A1.

## Vì sao (Claude, 2026-10-05)

- `IngestDocument` tra cache parse bằng `parser_config` gồm: `adapter` (phiên bản docling và bộ đọc), `adapter_version`, `image_scale`, và
  `strip_lines` khi có (`application/use_cases/ingest_document.py`).
- Các tuỳ chọn làm đổi đầu ra đều không có trong khoá:
  - `do_ocr`;
  - engine OCR: hiện docling tự chọn theo gói đã cài (`OcrAutoOptions`), nên đổi môi trường là đổi engine;
  - `bitmap_area_threshold`, `force_full_page_ocr`;
  - `do_table_structure`, chế độ TableFormer;
  - mô hình bố cục;
  - cách chia đoạn trang để parse song song (vé 10 lượt 2).
- Hệ quả: đổi một tuỳ chọn thì luồng **âm thầm dùng lại parse cũ**. Số đo trước và sau sửa vì vậy sai, và parse cũ nằm dưới cấu hình mới.

## Việc cần làm

1. **Một nguồn cho cấu hình pipeline.** `DoclingParser` nhận cấu hình pipeline (dataclass hoặc dict đóng băng) và dựng converter từ đó.
   Converter không còn tự đặt tuỳ chọn ở nhiều chỗ. Mặc định phải đúng cấu hình hiện tại:
   - `images_scale=2.0`, `generate_picture_images=True`;
   - OCR bật, bảng ACCURATE, bố cục heron;
   - số luồng theo docling.
2. **Khoá cache.** `parser_config` thêm một trường `pipeline`, ghi các tuỳ chọn làm đổi đầu ra. Theo đúng mẫu `heading_scheme`: **chỉ ghi các
   tuỳ chọn khác mặc định**, để băm của mọi tài liệu cũ giữ nguyên. Không mất cache parse cũ, không mất chunk, không phải chạy lại khâu LLM nào.
3. **Engine OCR ghi đích danh.**
   - Khi OCR bật, dùng engine cụ thể thay cho tự chọn (hiện là RapidOCR, backend torch) và ghi vào khoá.
   - Nếu đổi engine làm khác đầu ra trên tài liệu cũ thì giữ "tự chọn" làm mặc định cho tài liệu cũ, còn engine đích danh là tuỳ chọn mới.
     Báo lại kết quả kiểm này.
4. **Số luồng không vào khoá.** Lượt đo 1 cho thấy 4 và 8 luồng ra đầu ra y hệt ở cả bốn tầng trên 4 tài liệu. Nhưng manifest parse phải ghi
   số luồng đã dùng, để truy được khi có khác biệt.
5. **CLI:** `ingest` có cờ cho từng tuỳ chọn trên. Mặc định không đổi.

## Nghiệm thu

- **Test:**
  - cấu hình mặc định cho đúng `parser_config_hash` như trước; dùng băm của một artifact cũ trong repo làm mốc;
  - đổi `do_ocr`, chế độ bảng hay engine OCR thì băm đổi và cache **không** được dùng lại;
  - đổi số luồng thì băm không đổi, manifest ghi số luồng.
  - Test "cache không dùng lại" phải đỏ trên mã hiện tại.
- **Dry-run** `ingest` trên một tài liệu đã có parse, cấu hình mặc định: báo "tái dùng", không parse lại.
- Báo một con số: số artifact parse cũ còn dùng lại được, phải là tất cả.
