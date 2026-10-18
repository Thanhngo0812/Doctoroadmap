# SA-42 — Trần chi theo ngày: người học và hệ thống

**Nguồn chân lý:** [spec Pha B2](../../doc/pha-b2-spec.md), mục 8; đợt tra hỏi 2026-10-18, Q5 và Q29.
**Ai:** nhân viên · Claude kiểm · **Chi phí mô hình:** 0 USD (mô hình giả, đồng hồ giả) · **Chặn bởi:** 32, 38 · **Trạng thái:** ready-for-agent

## Vì sao

Spec Pha B chỉ có trần cho mỗi tin nhắn và mỗi chức năng. Khi có nhiều người học, cần thêm hai trần:
- trần theo người học, cho phần chi riêng của họ;
- trần hệ thống, cho nội dung dùng chung.

Hết trần thì phần 0 USD vẫn chạy.

## Cần làm

**Trần người học:**
- `learner_daily_max_usd` (0,20);
- chỉ tính `purpose` ∈ {`assistant`, `document`} của người học, đọc từ sổ chi;
- kiểm trước mỗi lời gọi có tiền: chi hôm nay cộng ước của lời gọi không được vượt trần;
- `make_document` trong một lượt trợ lý tính chung trần;
- hết trần thì:
  - trợ lý trả `status = daily_limit` kèm câu do mã viết;
  - tài liệu trả `failed`, `reason = daily_limit`.

**Trần hệ thống:**
- `system_daily_max_usd` (5,0) cho `lecture`, `quiz_gen`, `quiz_verify`;
- hết trần thì:
  - bài giảng mới trả `failed`, `reason_code = tran_he_thong`, ghi nhớ tới hết ngày (vé 38);
  - quiz dùng ngân hàng sẵn có và câu điền khuyết;
- bài giảng và ngân hàng đã có vẫn trả bình thường.

**Chung:**
- "Ngày" theo `spend_day_timezone`, qua port đồng hồ của vé 31.
- **Sổ chi:** mọi dòng `assistant` và `document` phải có `learner_id`. Thiếu thì ghi sổ báo lỗi, không ghi dòng không có chủ.

## Tiêu chí nghiệm thu

- [ ] Test với đồng hồ giả, mỗi cái thấy đỏ trước:
  - chi hôm nay 0,19 USD, mà lời gọi ước 0,02 USD, thì bị chặn trước khi gọi mô hình, kèm `daily_limit`, 0 lời gọi;
  - sang ngày mới thì gọi được;
  - chi của người học khác không tính vào trần của người này;
  - trần hệ thống chạm thì bài giảng mới trả `tran_he_thong`, còn bài đã cache vẫn trả `ready`;
  - trần hệ thống chạm thì quiz không gọi sinh mới, chỉ dùng ngân hàng sẵn có hoặc câu điền khuyết;
  - dòng sổ chi `assistant` thiếu `learner_id` thì ghi sổ báo lỗi.
- [ ] Đổi hai trần trong `BSettings` thì hành vi đổi theo.
