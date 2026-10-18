# W-14 — Tải sách lên, kiểm sớm, dự toán, hàng đợi, worker (bộ dựng giả)

**Nguồn chân lý:** [spec chức năng](../../doc/web-chuc-nang-spec.md), mục 4 (toàn bộ), 8 (trần khâu dựng); [ADR 0020](../../doc/adr/0020-khoa-hoc-la-don-vi-chia-se-du-lieu-hoc-theo-nguoi-va-cuon.md)
(dùng lại theo băm); [spec cơ sở dữ liệu](../../doc/web-co-so-du-lieu-spec.md), bảng `upload`, `build`, mục 6 (nhận việc); spec thiết kế, trang tải sách
và tiến trình dựng.
**Ai:** nhóm web · người soát kiểm · **Chi phí mô hình:** 0 USD (bộ dựng giả) · **Chặn bởi:** W-03, W-06 · **Trạng thái:** ready-for-agent

## Vì sao

Đây là đường đưa một giáo trình mới vào hệ thống. Vé này làm trọn đường đi bằng **bộ dựng giả** của W-13, để chạy được mà không tốn tiền và không chờ W-13
xong. W-15 nối bộ dựng thật.

## Cần làm

**`BuildService`:** `create_upload`, `get_upload`, `confirm_build`, `get_build`, `cancel_build`, `retry_build`, và phía worker `run_next_job`.

**Nhận tệp:**
- kiểm byte đầu PDF hay DOCX, ≤ `upload_max_mb` (10, gói Cloudinary miễn phí), PDF ≤ 400 trang, PDF không mã hoá;
- bắt buộc `rights_confirmed`;
- nếu trần lượt dựng đang bật (mặc định tắt ở bản demo): còn lượt trong tháng;
- **không** cần xác minh email (bản demo);
- tính SHA-256; tải lên Cloudinary qua `MediaStore` (`authenticated`, `public_id` ngẫu nhiên; PDF là `image` để cắt trang, DOCX là `raw`).

**Dùng lại:**
- đã có bản dựng `succeeded` cùng `doc_id` và `pipeline_version` thì tạo khoá học `ready` ngay: 0 USD, không trừ lượt;
- đang có bản dựng chạy dở cùng `doc_id` thì khoá học mới chờ chung bản đó.

**Luồng trạng thái** đúng spec mục 4: `reading` → (`rejected` | `awaiting_confirmation`) → `queued` → `running` → `succeeded` | `failed` | `cancelled`.
- Xác nhận thì trừ lượt (`counts_quota = true`).
- Không xác nhận trong 72 giờ thì hết hạn, không trừ lượt.
- Nếu trần dự toán bật: dự toán vượt trần thì `rejected` với `qua_du_toan`. Mặc định tắt; dự toán vẫn luôn hiện.

**Worker** (`web worker`):
- nhận việc bằng `FOR UPDATE SKIP LOCKED`; nhịp tim 30 giây;
- tải tệp gốc từ Cloudinary về thư mục tạm trước khi dựng, xoá bản tạm khi xong hay lỗi;
- cuối bước `learning_prep`: tải ảnh công thức và media đã xác nhận lên Cloudinary, ghi `media_asset`;
- việc định kỳ nhận lại bản dựng mất nhịp tim quá 10 phút, tối đa 1 lần;
- nếu trần khâu dựng toàn hệ thống bật: kiểm **trước** khi nhận việc;
- huỷ ở ranh giới bước;
- ghi chi mỗi bước vào sổ chi với `purpose = build`;
- xong thì khoá học `ready` với bản A10 mới nhất, và gửi thư "bản dựng xong" hay "bản dựng lỗi".

**HTTP:** `POST /uploads` (multipart), `GET /uploads/{id}`, `POST /uploads/{id}/build`, `GET /builds/{id}`, `POST /builds/{id}/cancel`, `POST /builds/{id}/retry`.

**Di trú:** `upload`, `build`, `media_asset`. Ràng buộc một bản dựng chạy dở cho mỗi `(doc_id, pipeline_version)`.

**Giao diện:**
- **trang "Tải giáo trình":**
  - kéo thả hay chọn tệp; hộp tick quyền dùng;
  - số lượt còn lại;
  - báo lỗi tệp ngay;
- **trang tiến trình:**
  - bốn bước có trạng thái;
  - vòng chờ GIF ở bước đang chạy;
  - dự toán với nút "Dựng lộ trình" và "Huỷ";
  - lỗi có nút "Thử lại" khi `retryable`;
  - rời trang rồi quay lại vẫn thấy đúng trạng thái;
  - trang hỏi `GET /builds/{id}` mỗi 3 giây.
- Thẻ khoá học đang dựng ở "Khoá học của tôi" hiện bước hiện tại.

## Tiêu chí nghiệm thu

Mỗi test thấy đỏ trước trên bản sai:
- [ ] Tệp đổi đuôi `.pdf` mà byte đầu không phải PDF thì `file_invalid`; 11 MB thì `file_too_large`, và `MediaStore` giả không nhận gì; PDF mã hoá thì
  `file_encrypted`.
- [ ] Bản dựng xong thì thư mục tạm không còn tệp gốc; `media_asset` có đủ ảnh công thức của bản dựng giả.
- [ ] Hai tài khoản tải cùng một tệp: bộ dựng giả chỉ chạy 1 lần; lần sau 0 USD, không trừ lượt; hai khoá trỏ cùng `doc_id`.
- [ ] Hai lần tải cùng tệp đồng thời trên PostgreSQL: chỉ một bản dựng chạy.
- [ ] Cấu hình mặc định: một tài khoản tải và dựng 5 cuốn liền không bị chặn.
- [ ] Bật `build_monthly_max = 3`: lượt thứ 4 trong tháng thì `quota_exceeded`, trước khi worker chạy bước nào; sang tháng mới theo đồng hồ giả thì được.
- [ ] Bật `build_max_estimate_usd = 3`: dự toán giả 3,5 USD thì `rejected`, `qua_du_toan`.
- [ ] Bật trần khâu dựng toàn hệ thống: chạm trần thì bản dựng nằm ở `queued`, không chạy.
- [ ] Hai worker nhận việc cùng lúc: mỗi bản dựng một worker.
- [ ] Mất nhịp tim quá 10 phút thì được nhận lại đúng 1 lần; lần sau `failed` với `loi_noi_bo`.
- [ ] Huỷ khi `running`: không bước nào bắt đầu sau cờ huỷ.
- [ ] Chưa xác minh email vẫn tải và dựng được.
- [ ] Ảnh chụp: trang tải, dự toán, đang dựng, lỗi bản quét, xong; cỡ 390 px và 1280 px.

## Ngoài vé

Bộ dựng thật (W-15). Dựng lại và phát hành bản mới.
