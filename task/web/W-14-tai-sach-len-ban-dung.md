# W-14 — Tải sách lên, xác nhận, kiểm sớm, hàng đợi, worker và usage thực (bộ dựng giả)

**Nguồn chân lý:** [spec chức năng](../../doc/web-chuc-nang-spec.md), mục 4 (toàn bộ), 8 (trần khâu dựng); [ADR 0020](../../doc/adr/0020-khoa-hoc-la-don-vi-chia-se-du-lieu-hoc-theo-nguoi-va-cuon.md)
(dùng lại theo băm); [spec cơ sở dữ liệu](../../doc/web-co-so-du-lieu-spec.md), bảng `upload`, `build`, mục 6 (nhận việc); spec thiết kế, trang tải sách
và tiến trình dựng.
**Ai:** lõi phụ trách backend/worker; nhóm web phụ trách React và tích hợp · người soát kiểm · **Chi phí mô hình:** 0 USD (bộ dựng giả) · **Chặn bởi:** W-03, W-06; mốc backend cần sửa W-25 · **Trạng thái:** backend `5b24ece` chưa đạt; React còn chờ.

**Soát 2026-10-21:** 35 test W-14 cũ chạy lại đạt, nhưng hai ca PG độc lập tái hiện confirm ghi đè cancel thành queued và cancel khi publication vẫn ghi succeeded/course ready/gửi thư thành công. Chưa ghép backend/schema; sửa theo [W-25](W-25-dong-bo-xac-nhan-huy-va-ket-thuc-ban-dung.md), giữ usage thực/lease fence và tuyến migration đã chốt. Web có thể chuẩn bị React theo hợp đồng, nhận mốc backend đã sửa/soát đạt trước cổng cuối; chưa đóng W-14 đầu-cuối. Xem [phán xét/bằng chứng](../../report/dieu-phoi-nghiem-thu-w07-w14-w24-va-ke-hoach-2026-10-21.md).

**Kế hoạch sau W-06, 2026-10-21:** khi W-06 được ghi ghép, lõi chuẩn bị backend/worker và hợp đồng để web tích hợp sau ưu tiên W-07.
Đây vẫn là một vé đầu-cuối; backend riêng xong chưa đóng vé. Xem
[kế hoạch và điểm kiểm](../../report/dieu-phoi-nghiem-thu-w06-va-ke-hoach-2026-10-21.md).
W-06 đã có `course`/`membership`, `module_count`, PDF mẫu `source_public_id`; W-14 bổ sung FK `course.build_id → build.id` khi tạo build,
nối nguồn upload và metadata graph, kiểm dùng lại cùng tài liệu. Không sửa migration W-06. **Tuyến đã chốt 2026-10-21:** giữ `w14_0006` nối `w06_0005`, W-14 ghép trước rồi W-11 nối bằng `w11_0007`. Chỉ ghép sau khi mốc cụ thể được soát đạt và cổng xanh; có thể nghiệm thu mốc backend/schema riêng nếu hoàn chỉnh, chưa đóng vé W-14 đầu-cuối khi React còn thiếu.
Giữ bộ dựng/MediaStore/Mailer giả, test usage giả khác 0 để kiểm sổ chi thực; không gọi mô hình hay dùng ngân sách phục hồi cũ.

## Vì sao

Đây là đường đưa một giáo trình mới vào hệ thống. Vé này làm trọn đường đi bằng **bộ dựng giả** của W-13, để chạy được mà không tốn tiền và không chờ W-13
xong. W-15 nối bộ dựng thật.

## Cần làm

**Đồng bộ quyết định chủ dự án 2026-10-19** từ spec chức năng mục 4 và W-13: thả/chọn tệp rồi xác nhận mới dựng; không tính/hiện dự toán hoặc chi phí
cho người dùng. Ghi usage/chi phí từ kết quả chạy vào DB phía máy chủ, kể cả lỗi/huỷ. Báo cáo giao diện và API không được dùng lại luồng dự toán cũ.

**`BuildService`:** `create_upload`, `get_upload`, `confirm_build`, `get_build`, `cancel_build`, `retry_build`, và phía worker `run_next_job`.

**Nhận tệp:**
- kiểm byte đầu PDF hay DOCX, ≤ `upload_max_mb` (10, gói Cloudinary miễn phí), PDF ≤ `build_max_pages` khi bật (mặc định không giới hạn theo spec chức năng), PDF không mã hoá;
- bắt buộc `rights_confirmed`;
- nếu trần lượt dựng đang bật (mặc định tắt ở bản demo): còn lượt trong tháng;
- **không** cần xác minh email (bản demo);
- tính SHA-256; tải lên Cloudinary qua `MediaStore` (`authenticated`, `public_id` ngẫu nhiên; PDF là `image` để cắt trang, DOCX là `raw`).

**Dùng lại:**
- đã có bản dựng `succeeded` cùng `doc_id` và `pipeline_version` thì tạo khoá học `ready` ngay: 0 USD, không trừ lượt;
- đang có bản dựng chạy dở cùng `doc_id` thì khoá học mới chờ chung bản đó.

**Luồng trạng thái** đúng spec mục 4: sau kiểm tệp là `awaiting_confirmation` → xác nhận → `queued` → worker `reading` → (`rejected` | `running`) →
`succeeded` | `failed` | `cancelled`. Kiểm chữ/bản quét/ngôn ngữ thuộc `reading`, trước bước có tiền.
- Xác nhận thì trừ lượt (`counts_quota = true`).
- Không xác nhận trong 72 giờ thì hết hạn, không trừ lượt.
- Không có bước tính dự toán, `build_max_estimate_usd` hay lỗi `qua_du_toan` trong luồng này.

**Worker** (`web worker`):
- nhận việc bằng `FOR UPDATE SKIP LOCKED`; nhịp tim 30 giây;
- tải tệp gốc từ Cloudinary về thư mục tạm trước khi dựng, xoá bản tạm khi xong hay lỗi;
- cuối bước `learning_prep`: tải ảnh công thức và media đã xác nhận lên Cloudinary, ghi `media_asset`;
- việc định kỳ nhận lại bản dựng mất nhịp tim quá 10 phút, tối đa 1 lần;
- nếu trần khâu dựng toàn hệ thống bật: kiểm **trước** khi nhận việc;
- huỷ ở ranh giới bước;
- ghi chi mỗi bước vào sổ chi với `purpose = build`;
- Nối `build_document_runner(settings, recorder=callback)`/bộ dựng giả với callback nhận `BuildResult`: ghi kết quả và usage thực vào PostgreSQL của
  web cùng `build_id`/người yêu cầu ở mọi kết thúc. SQLite `builds.sqlite3` của CLI W-13 không thay DB web. Không cộng lại chi lịch sử của artifact/cache;
  giữ cờ `usage_complete` khi thiếu token. Đối chiếu [báo cáo W-13](../../report/w13-dung-mot-cuon-2026-10-19.md) và port `application/ports/build.py`.
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
  - chọn tệp, xác nhận bằng nút "Dựng lộ trình" trước khi xếp hàng; nút "Huỷ" theo trạng thái, không hiện dự toán/chi phí;
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
- [ ] Trước xác nhận, bộ dựng chưa được gọi; xác nhận mới xếp hàng. API cho người dùng và giao diện không có trường dự toán/chi phí; test thấy đỏ trên
  luồng cũ còn dự toán.
- [ ] Kết quả thành công/lỗi/huỷ của bộ dựng giả được ghi PostgreSQL cùng đúng `build_id`/người yêu cầu. Kiểm lại bằng truy vấn độc lập: số chi/usage
  khớp kết quả, giữ `usage_complete=false` khi thiếu số, cache không bị tính chi cũ lần nữa. Không lấy số 0 USD làm đủ bằng chứng, dùng usage giả khác 0.
- [ ] Bật trần khâu dựng toàn hệ thống: chạm trần thì bản dựng nằm ở `queued`, không chạy.
- [ ] Hai worker nhận việc cùng lúc: mỗi bản dựng một worker.
- [ ] Mất nhịp tim quá 10 phút thì được nhận lại đúng 1 lần; lần sau `failed` với `loi_noi_bo`.
- [ ] Huỷ khi `running`: không bước nào bắt đầu sau cờ huỷ.
- [ ] Chưa xác minh email vẫn tải và dựng được.
- [ ] Ảnh chụp: trang tải/xác nhận, đang dựng, lỗi bản quét, xong; cỡ 390 px và 1280 px; không có dự toán/chi phí cho người dùng.

## Ngoài vé

Bộ dựng thật (W-15). Dựng lại và phát hành bản mới.
