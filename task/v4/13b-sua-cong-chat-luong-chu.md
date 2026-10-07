# v4-13b — Sửa cổng chất lượng chữ: bắt chữ bị thay hệ chữ, không tự đổi bộ đọc đã chỉ định, tài liệu T10

**Nguồn chân lý:** [kiểm thử vé 12–14](../../report/kiem-thu-ve-12-13-14-a1-mo-rong-2026-10-08.md) mục 3 · [vé 13](13-a1-bo-doc-chu-tieng-viet.md) ·
**Ai:** nhân viên · **Phụ thuộc:** vé 13 (mã chưa commit) · **Chi phí mô hình:** 0

**Trạng thái:** soạn 2026-10-08. Không chặn việc gán nhãn D-01.

## Vì sao (Claude, 2026-10-08)

Kiểm thử vé 13 tái hiện hai lỗi của cổng chất lượng chữ.

1. **Bỏ sót chữ bị thay bằng chữ Kirin.**
   - docling-parse đọc d01-11 thành "Ký kӃt và thӵc hiӋn hӧp đӗng". Âm tiết hợp lệ chỉ 0,28, nhưng cổng không cảnh báo gì.
   - Cùng dạng lỗi ở d01-05, 06, 13, 15, 16. Bảng đo của vé 13 cho các cuốn này 0,38–0,46.
   - Cây sạch đang ghim của d01-05 (pypdfium2) cũng có 694 chữ Kirin trông như chữ Latin ("сủа", "nghiệт"), dồn ở trang 145, 108, 85.
2. **Tự đổi bộ đọc đã chỉ định.**
   - Lệnh tái lập T10 của xstk (`--pdf-backend docling-parse --pdf-text-policy legacy`) khi dry-run ra "selected: pypdfium2, cần parse mới",
     thay vì dùng lại parse v2 đã khoá.
   - Lượt chưa parse (`quality=None`) bị coi là sạch.

## Việc cần làm

### 1. Bắt chữ bị thay hệ chữ

- Thêm chỉ số **tỉ lệ chữ cái ngoài hệ Latin và Hy Lạp**, tính sau NFKC để `µ` thành `μ`. Tính cho cả tài liệu và cho từng trang có từ 100 chữ cái
  trở lên.
- Số Claude đo trên mẫu trang của `do_chu_v413.py`:

  | văn bản | tỉ lệ chữ ngoài Latin/Hy Lạp |
  |---|---|
  | docling-parse: d01-05, 06, 11, 13, 15, 16 | 13–18% |
  | docling-parse: d01-01 | 0,76% (đã bị chốt ký tự lạ bắt) |
  | pypdfium2: mọi tài liệu (mẫu trang) | ≤ 0,37% |
  | pypdfium2, cây ghim d01-05: trang 145, 108, 85 | 2,2–2,8% (chữ Kirin trông như Latin, lỗi thật) |
- Chọn ngưỡng trên **bảng đầy đủ**:
  - mức tài liệu cho 21 tài liệu × 2 bộ đọc;
  - mức trang trên cây ghim của mọi tài liệu trong kho.

  Báo số trang bị bắt nhầm ở sách sạch.
- Ngưỡng cũ (âm tiết dưới 0,80 *và* tách từ 1% trở lên) giữ nguyên. Xem thêm có nên dùng riêng chỉ số âm tiết thấp ở mức tài liệu không; mọi bản
  sạch đều từ 0,78 trở lên.
- Không sửa artifact D-01 đã ghim. Chỉ 39/5.541 phiếu có câu dính chữ Kirin, không tên khái niệm nào bị dính, nên không đáng chạy lại khâu trả
  tiền. Chỉ ghi vào báo cáo.

### 2. Bộ đọc đã chỉ định rõ thì không tự đổi

- `ingest --pdf-backend` không truyền thì là **tự chọn**: dùng pypdfium2, được đổi bộ đọc khi chữ hỏng.
- Truyền giá trị rõ thì là **ghim**:
  - không parse bằng bộ đọc kia;
  - nếu có cảnh báo: thoát mã khác 0, in chỉ số, gợi ý thử bộ đọc kia hoặc dùng cờ lý do;
  - nếu có `--allow-text-quality-reason`: dùng đúng bộ đọc ghim.
- Dry-run: lượt chưa có cây thì ghi "chưa đo", không được chọn như một bản sạch.
- Khoá cache không đổi. Chế độ tự chọn hay ghim không vào khoá; bộ đọc thật vẫn vào khoá như vé 09.

### 3. Tài liệu T10

- Bảng khoá trong `T10-cau-hinh-khoa.md` và đầu ra của `scripts/khoa-cau-hinh/tao_bang.py` thêm `--pdf-text-policy legacy` cho xstk và doc-4, cho khớp
  với `CONTEXT.md`.
- Các bước trả tiền của xstk giờ bị cổng chặn vì chữ VNI thật ở trang 3. Lệnh T10 của xstk phải ghi rõ `--allow-text-quality-reason "<lý do>"`.
  - Không làm sạch xstk, vì phải giữ nguyên văn bản đã khoá.
  - Hỏi chủ dự án câu chữ của lý do.

### 4. Việc nhỏ

- Cổng xét cả loại nút `title`; bỏ `heading`, vì loại này không tồn tại.
- Thay bảng số trong báo cáo v4-13 bằng số đo sau khi sửa nhận diện VNI.

## Nghiệm thu

- **Test**, phải đỏ trên mã hiện tại và xanh sau khi sửa:
  - câu thật "a) Ký kӃt và thӵc hiӋn hӧp đӗng vӟi chӫ vұt thӇ…" phải bị cổng cảnh báo;
  - kho giả có parse docling-parse đã lưu, mang cảnh báo VNI. Gọi `ingest` với bộ đọc ghim là docling-parse:
    - không có cờ lý do: thoát lỗi, và không parse bằng pypdfium2;
    - có cờ lý do: dùng lại parse đã lưu, không parse mới;
  - dry-run không chọn lượt chưa đo.
- **Bảng ngưỡng** theo mục 1, kèm số trang bị bắt nhầm.
- **Dry-run lệnh T10 của xstk** (có cờ lý do) phải báo dùng lại parse v2.
- Toàn bộ test xanh. Kiểm khoá cache như vé 09: mọi manifest parse giữ nguyên `parser_config_hash`.
- Báo cáo `report/v4-13b-...md`.
