# W-09 — Trợ lý và phiên chat

**Nguồn chân lý:** [spec Pha B2](../../doc/pha-b2-spec.md), mục 1–3, 8, 10 (`session-1`, `turn-1`, `answer-2`); [spec chức năng](../../doc/web-chuc-nang-spec.md),
mục 1 (công cụ buộc phía máy chủ, SSE), 7 (giới hạn tần suất), 8; [ADR 0017](../../doc/adr/0017-pham-vi-phien-la-noi-luu-neo-vao-khai-niem.md); spec thiết
kế, khung chat.
**Ai:** nhóm web · người soát kiểm · **Chi phí mô hình:** 0 USD (mô hình giả và phát lại) · **Chặn bởi:** W-07, SA-32, SA-33, SA-42 · **Trạng thái:**
ready-for-agent

## Vì sao

Trợ lý là phần "agent" của đề tài. Người học cần phiên chat ở trang lộ trình (phiên toàn lộ trình) và ở trang học (phiên của module), mở lại được phiên
cũ, và thấy trả lời hiện dần.

## Cần làm

**Gateway:** `create_session`, `list_sessions`, `rename_session`, `delete_session`, `list_turns`, `ask_stream`.
- **Phạm vi do web gửi:** `{kind: roadmap}` từ trang lộ trình; `{kind: module, node_ids}` từ trang học, với `node_ids` lấy từ đồ thị đã phát hành phía máy
  chủ, không tin danh sách do trình duyệt gửi.
- `ask_stream` truyền `owner`, `doc_id`, `graph_version` vào use case trợ lý. Công cụ của trợ lý chỉ nhận các giá trị này từ gateway.
- **Giới hạn tần suất:** `assistant_turns_per_minute` (10) mỗi người, đếm bằng `rate_limit_event`.

**HTTP:**
- `GET/POST /courses/{cid}/sessions` (lọc `roadmap_page`, `module:<id>`, `all`);
- `PATCH/DELETE /courses/{cid}/sessions/{sid}`;
- `GET /courses/{cid}/sessions/{sid}/turns`;
- `POST /courses/{cid}/sessions/{sid}/turns` trả **SSE**: sự kiện tiến trình gọi công cụ, chữ trả lời, rồi đối tượng `answer-2` cuối cùng.
- `client_turn_id` do trình duyệt sinh. Gửi lại cùng mã (mạng chập chờn) thì không tạo lượt thứ hai.

**Giao diện:**
- **khung chat** dùng chung cho hai trang: danh sách phiên (tiêu đề, ngày, câu hỏi cuối), nút "Phiên mới", đổi tên, xoá có xác nhận;
- **lượt:** câu hỏi; trả lời hiện dần; trích dẫn bấm được (mở trang sách); thẻ "nội dung ở module N — mở module"; ghi chú "module này đã đổi" khi phạm vi đã
  cũ;
- **tiến trình gọi công cụ** ("đang tìm trong sách…") hiện bằng dòng nhỏ;
- `status = daily_limit` hiện câu của mã và dải hết trần (W-16 làm phần dải);
- trang lộ trình có bộ lọc "tất cả".

## Tiêu chí nghiệm thu

Mỗi test thấy đỏ trước trên bản sai:
- [ ] Thành viên B không liệt kê, không đọc lượt, không gửi câu hỏi vào phiên của A cùng khoá (`not_found`).
- [ ] Một kịch bản mô hình giả có lời gọi công cụ mang `owner` lạ trong tham số: công cụ vẫn chạy với `owner` của gateway; kho không có bản ghi nào của
  `owner` lạ.
- [ ] Phạm vi module với `node_ids` do trình duyệt gửi khác đồ thị: máy chủ dùng `node_ids` của đồ thị đã phát hành.
- [ ] Gửi lại cùng `client_turn_id` thì chỉ một lượt được lưu, và chỉ một lần gọi mô hình.
- [ ] Lượt thứ 11 trong một phút thì `rate_limited`.
- [ ] Trần ngày tính chung mọi khoá: chi ở khoá A làm khoá B trả `daily_limit` (đồng hồ giả, sổ chi bộ nhớ).
- [ ] Xoá phiên thì tài liệu do phiên tạo vẫn còn trong thư viện (bất biến 4 của Pha B2, kiểm lại qua HTTP).
- [ ] Ảnh chụp khung chat ở hai trang, phiên đã cũ, `daily_limit`; cỡ 390 px và 1280 px.

## Ngoài vé

Báo lỗi câu trả lời (W-19). Dời phiên giữa phạm vi (ngoài phạm vi Pha B2).
