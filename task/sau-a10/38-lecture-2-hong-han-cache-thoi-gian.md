# SA-38 — Bài giảng `lecture-2`: bài hỏng hẳn, bản ghi hỏng, cache, thời gian

**Nguồn chân lý:** [spec Pha B2](../../doc/pha-b2-spec.md), mục 6.2, 6.3, 6.4, 10; [ADR 0018](../../doc/adr/0018-bai-giang-khong-hien-ban-lui-stream-sau-cong.md).
**Ai:** nhân viên · Claude kiểm · **Chi phí mô hình:** 0 USD (mô hình giả và phát lại) · **Chặn bởi:** SA-30 (K6 dò sai, không cache bài hỏng, TTFT) ·
**Trạng thái:** ready-for-agent

## Vì sao

Chủ dự án quyết bản lùi trích câu không bao giờ hiện cho người học. Khi bài hỏng hẳn, người học vẫn cần thứ để học tiếp: phần mã dựng đã kiểm, lời
nhắn, và đường về sách. Bài hỏng không được nằm vĩnh viễn trong cache. Một lần bấm cũng không được bắt người học chờ tới 3 × 60 giây.

## Cần làm

- **Hợp đồng `lecture-2`:**
  - `status` ∈ {`ready`, `generating`, `no_source`, `failed`}; bỏ `fallback`;
  - thêm đối tượng `failure`: `reason_code`, `retryable`, `read_page`, `ask_assistant`.

  Vé này chưa đổi phần tiên quyết; phần đó thuộc vé 40.
- **Bài hỏng hẳn:**
  - giữ mọi phần mã dựng của `skeleton`;
  - `reason_code` ∈ {`kiem_noi_dung`, `loi_mang`, `het_thoi_gian`, `tran_he_thong`, `khong_co_mo_hinh`};
  - `retryable` là true với `loi_mang`, `het_thoi_gian`, `tran_he_thong`;
  - `read_page` lấy từ câu định nghĩa, nếu không có thì từ chunk dạy đầu.
- **Không đường nào trả câu do TextRank chọn cho người học.**
  - Hàm trích câu chỉ còn làm mốc so sánh cho vé 21, và không nối vào use case bài giảng.
  - Chế độ không có mô hình (trang xem thử ngoại tuyến) trả `failed` với `khong_co_mo_hinh`.
- **Bản ghi hỏng:**
  - `kiem_noi_dung` được ghi nhớ 24 giờ;
  - `loi_mang` và `het_thoi_gian` được ghi nhớ 60 giây;
  - `tran_he_thong` được ghi nhớ tới hết ngày.

  Chỉ bài `ready` vào cache chung. Khoá gồm phiên bản luật kiểm và prompt. Đọc bản ghi hỏng thì 0 lời gọi mô hình.
- **Thời gian:**
  - trần cả lần bấm `lecture_click_timeout_seconds` (30);
  - tầng gọi mạng thử lại 1 lần trên đường người học đang chờ, 2 lần khi tải trước;
  - lần sinh lại dùng `lecture_retry_temperature`, mặc định 0.

## Tiêu chí nghiệm thu

- [ ] Test, mỗi cái thấy đỏ trước:
  - mô hình giả trả đầu ra vi phạm cả hai lần thì `status = failed`, `reason_code = kiem_noi_dung`, vẫn có `skeleton` đầy đủ, và không có ý nào là câu
    trích tự chọn;
  - bấm lại trong 24 giờ thì 0 lời gọi; sau 24 giờ (đồng hồ giả), hoặc đổi phiên bản luật, thì sinh lại;
  - lỗi mạng thì `retryable = true`, ghi nhớ 60 giây, sau đó sinh lại được;
  - mô hình giả chậm vượt 30 giây thì `het_thoi_gian`, không chờ thêm;
  - đường người học đang chờ thử lại tầng mạng đúng 1 lần, đường tải trước đúng 2 lần;
  - bài `failed` không bao giờ có trong cache như bài `ready`;
  - không có mô hình thì `khong_co_mo_hinh`;
  - không đường nào trả `status = fallback`.
- [ ] Phát lại 0 USD 12 bài của nhóm 2 qua `lecture-2`. Báo số `ready`, số `failed`, và `reason_code` của từng bài hỏng.
- [ ] Ví dụ JSON thật của một bài `failed` đính kèm báo cáo vé.
