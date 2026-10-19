# v4-13 — A1 cho tài liệu tiếng Việt: bộ đọc chữ mặc định pypdfium2 và lưới an toàn chất lượng chữ có hành động

**Nguồn chân lý:** [kiểm rộng 16 cuốn](../../report/v4-10-buoc-2b-kiem-rong-16-cuon-2026-10-05.md) mục Tóm tắt 1 ·
[vé 09](09-khoa-cache-parse.md) (bộ đọc nằm trong khoá cache) ·
**Ai:** nhân viên · **Phụ thuộc:** vé 09 (đã xong) · **Chi phí mô hình:** 0

**Trạng thái:** soạn 2026-10-05, chủ dự án duyệt cùng ngày. Làm trước hoặc song song vé 14. Vé 14 có thành công thì docling vẫn còn cho sách
có công thức và bảng, và lưới an toàn ở đây áp cho mọi bộ đọc.

**Cập nhật nhân viên, 2026-10-06:** đã triển khai mặc định, fallback, cổng chất lượng trước chi tiền, cờ xác nhận có lý do,
và cờ tái lập backend cũ. Đã đo 21 tài liệu × 2 bộ đọc, kiểm cache 44/44, dry-run d01-01 tái dùng parse sạch v2.
Toàn bộ lượt kiểm thử: 880 xanh; 14 test trọng điểm chạy lại xanh sau chỉnh cuối (gồm chốt model của vé 12).
Chi mô hình mới 0 USD. Báo cáo: [v4-13](../../report/v4-13-bo-doc-chu-va-cong-chat-luong-2026-10-06.md).
Cổng phát hiện 7 sách D-01 cần xử lý/xác nhận chữ lỗi; điều đó chặn nghiệm thu đủ 16 sách của vé 12, không được tự bỏ cổng.

## Vì sao (Claude, 2026-10-05)

- **docling-parse, bộ đọc chữ mặc định của `ingest`, đã đọc hỏng 2 giáo trình tiếng Việt:**
  - doc-4: tách vỡ âm tiết ("Ph ươ ng pháp"); dự án đã chuyển doc-4 sang pypdfium2;
  - d01-01 (Toán cao cấp 2): giải mã font sai, chữ thành "T'p c¡c ph†p bi,n Œi tuy,n t‰nh cıa V".
- **pypdfium2 đọc sạch mọi tài liệu tiếng Việt đã thử:** 16 cuốn D-01 và doc-1, doc-4, xstk.
- **`_text_quality` trong `ingest` đã bắt được d01-01:** manifest chunk v1 ghi "Lớp text có thể hỏng font: 97507 chữ cái đọc được, 0.02% có
  dấu". Nhưng đó **chỉ là cảnh báo trong manifest**. Luồng chạy tiếp và không ai thấy; A2 → A9'' (tốn tiền) có thể đã chạy trên chữ rác.
- Đồ án giờ chỉ làm tiếng Việt, nên đặt mặc định cho tiếng Việt là hợp lý.

## Việc cần làm

### 1. Đo trước khi đổi (0 USD)

- Với mọi PDF tiếng Việt đang có, đọc chữ bằng cả hai bộ đọc trên toàn bộ hoặc một mẫu trang cố định:
  - doc-1, doc-4, doc-6, xstk, naive-bayes;
  - 16 cuốn `document-data/train/`. **Không mở `document-data/test/`.**
  - Bộ đọc chữ có tầng riêng, không cần chạy mô hình bố cục: docling-parse ở mức trang, pypdfium2 qua `get_textpage`.
- Tính trên mỗi phần chữ:
  - các chỉ số sẵn có của `_text_quality`;
  - **tỉ lệ âm tiết tiếng Việt hợp lệ**: token từ 2 chữ cái trở lên, sau NFC, viết thường, coi "ƣ" như "ư", khớp mẫu phụ âm đầu + vần + phụ âm cuối;
    mẫu tham khảo ở mục 2;
  - tỉ lệ ký tự "lạ" của chữ hỏng (†, ‰, ı, Œ, ¡, ⁄…);
  - tỉ lệ token một chữ cái.
- Số Claude đã đo:

  | văn bản | tỉ lệ âm tiết hợp lệ |
  |---|---|
  | d01-01, docling-parse | 0,32 |
  | doc-4, docling-parse | 0,71 |
  | doc-4, pypdfium2 | 0,99 |
  | 16 cuốn D-01, pdfium | 0,85–0,999 |

  Cuốn CNTT và hoá thấp vì có thuật ngữ tiếng Anh và tên hoá chất. Khoảng cách giữa hỏng và sạch còn hẹp (0,71 so với 0,85), nên **phải chọn
  ngưỡng trên bảng đầy đủ** và có thể kết hợp nhiều chỉ số.
- Báo bảng: tài liệu × bộ đọc × chỉ số. Có cuốn nào docling-parse **tốt hơn** pypdfium2 không? Ví dụ chữ bảng, dấu cách, chữ ghép.

### 2. Đổi mặc định và giữ tài liệu cũ

- `ingest --pdf-backend` mặc định thành `pypdfium2`. `docling-parse` vẫn chọn được bằng cờ.
- Định danh bộ đọc trong khoá cache giữ nguyên (`docling:2.114.0` và `docling:2.114.0+pypdfium2`), nên artifact cũ không đổi khoá.
- Mọi chỗ ghi lệnh cho tài liệu cũ không cờ phải ghi rõ `--pdf-backend docling-parse`: xstk, doc-1… trong `T10-cau-hinh-khoa.md`, `CONTEXT.md`,
  script và vé. Nếu không, chạy lại theo khuôn cũ sẽ ra parse mới, chunk mới, kéo theo chạy lại khâu tốn tiền.
- Mẫu âm tiết tham khảo (Claude dùng để đo):
  `^(ngh|ng|gh|gi|kh|nh|ph|qu|th|tr|ch|[bcdđghklmnpqrstvx])?[nguyên âm có dấu]{1,3}(ch|ng|nh|[cmnpt])?$`.

### 3. Lưới an toàn có hành động

Ngay sau parse, trước khi cắt chunk:
- Tính các chỉ số ở mục 1 trên cây vừa parse (chữ của nút văn bản, tiêu đề, danh sách; bỏ công thức và bảng). Tính thêm **theo trang**, để bắt
  hỏng cục bộ: vài trang dùng font khác, dòng đầu trang mã VNI như "BOÄ MOÂN TOAÙN" ở d01-02.
- **Không đạt ngưỡng:**
  1. tự parse lại bằng bộ đọc kia;
  2. giữ bản có chất lượng tốt hơn;
  3. ghi cả hai bộ số và lý do chọn vào manifest. Bộ đọc thật sự dùng nằm trong khoá cache, như vé 09.
- **Cả hai bộ đọc đều không đạt** (ví dụ font mã cũ VNI hay TCVN3 không có bảng ToUnicode): `ingest` **thoát mã khác 0** và in rõ:
  - chỉ số;
  - các trang tệ nhất;
  - gợi ý: chuyển mã, OCR, hoặc cờ cho phép chạy tiếp có ghi lý do.
- Các lệnh tốn tiền sau đó (`label-roles`, `a3`, `roadmap`) **từ chối chạy** trên chunk có cảnh báo chất lượng chữ chưa được xác nhận, trừ khi
  truyền cờ cho phép. Cảnh báo không được chỉ nằm im trong manifest.
- **Ngoài phạm vi vé này:** bộ chuyển mã VNI/TCVN3 sang Unicode. Ghi lại nếu gặp nhiều.

## Nghiệm thu

- **Test:**
  - chỉ số tách đúng ba mẫu chữ (sạch, vỡ âm tiết "Ph ươ ng pháp", hỏng font "T'p c¡c ph†p");
  - bộ đọc giả trả chữ hỏng → `ingest` chuyển bộ đọc và ghi manifest. Test này phải **đỏ trên mã hiện tại**;
  - cả hai bộ đọc giả đều hỏng → thoát mã khác 0;
  - lệnh tốn tiền từ chối chunk có cảnh báo chưa xác nhận;
  - tài liệu cũ: khoá parse giữ nguyên, kiểm lại như cách vé 09 kiểm 30/30.
- **Bảng đo** của mục 1, kèm ngưỡng đã chọn và lý do.
- **Dry-run** `ingest` trên d01-01 với bộ đọc docling-parse: lưới an toàn phải bắt và chuyển sang pypdfium2. Dùng bản có sẵn trong kho, không
  parse lại tốn thời gian nếu tránh được.
- Báo cáo `report/v4-13-...md`.
