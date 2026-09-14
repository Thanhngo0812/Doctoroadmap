# 03 — Trích ảnh mọi định dạng và `missing_image` bắt buộc (F36)

**What to build:** User ingest báo cáo DOCX có 3 ảnh PNG dán trong ruột và **nhìn thấy ảnh được
trích** — định danh băm, lưu kho, tham chiếu trong chunk — y như ảnh PDF. Hình nào không lấy được
byte (logo DrawingML cần LibreOffice) thì hệ thống **tự nói ra** bằng cảnh báo `missing_image` kèm
lý do, không phải một dòng stderr của thư viện trôi mất.

## Cơ chế lỗi đang sửa

Trích ảnh và cả cảnh báo `missing_image` đang nằm trong cổng *"file là PDF"* — cái cờ sinh ra để bật
bộ sửa glyph, bị dùng luôn làm proxy định dạng. Một cờ làm hai việc không liên quan. Hệ quả đo được:
DOCX có 3 node figure, `image_id` cả ba đều rỗng, `images_extracted: 0`, cảnh báo: không dòng nào.

## Việc

- Cờ sửa-glyph chỉ còn chi phối sửa glyph. Trích ảnh chạy cho **mọi** định dạng nguồn.
- Node hình có byte ⇒ băm, lưu, tham chiếu — đường PDF hiện hành, không đổi hành vi PDF.
- Node hình không lấy được byte ⇒ dấu `[figure]` vẫn vào văn bản **và bắt buộc** một cảnh báo
  `missing_image` kèm vị trí (trang nếu có).
- ADR 0002 bổ sung: *dấu vết không có tham chiếu là trạng thái suy giảm hợp lệ duy nhất khi byte
  không lấy được, và bắt buộc kèm cảnh báo* — không bao giờ im lặng.
- README ghi LibreOffice là phụ thuộc tuỳ chọn cho DOCX chứa hình vẽ DrawingML.
- **Nhích `adapter_version` một lần — cú nhích duy nhất của cả đợt** (ticket 04 và 07 cũng đổi
  adapter nhưng không nhích nữa). Lưu ý hệ quả: ingest thật giữa chừng đợt sẽ đóng băng cây parse
  nửa-mới; đối chiếu cuối đợt (ticket 09) mới là lần ingest có giá trị.

**Blocked by:** 01 — cần fixture DOCX bản có ảnh, và câu trả lời khám phá về dữ liệu picture.
02 — số vàng phải có trước để cú dịch chuyển của ticket này nhìn thấy được.

**Status:** done

- [x] Trên fixture DOCX: mỗi node figure hoặc có định danh ảnh + tham chiếu, hoặc có một dòng
      `missing_image` — **không tồn tại** dấu `[figure]` mà không có gì đi kèm
- [x] 3 ảnh PNG dán ruột được trích (nếu khám phá ở 01 xác nhận dữ liệu có trong document); ghi lại
      con số thật trích được / cảnh báo — đây là câu user hỏi, trả lời bằng số
- [x] Chunk DOCX chứa hình có `image_refs` trỏ đúng vị trí dấu, cùng hệ toạ độ với các tham chiếu khác
- [x] I24 giữ: đổi tập tham chiếu ảnh mà văn bản không đổi ⇒ định danh chunk không đổi
- [x] Hành vi PDF không đổi: số vàng ba tài liệu PDF đứng yên ở mọi cột
- [x] Số vàng DOCX cập nhật đúng cú dịch dự đoán: tham chiếu ảnh 0 → (số trích được), cảnh báo thêm
      `missing_image` cho phần còn lại
- [x] Có test: node hình có byte ⇒ ref; node hình không byte ⇒ marker + cảnh báo; cả hai trên cùng
      một tài liệu
- [x] `adapter_version` nhích đúng một, ADR 0002 và README cập nhật
