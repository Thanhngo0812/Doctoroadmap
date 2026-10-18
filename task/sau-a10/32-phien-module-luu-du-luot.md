# SA-32 — Phiên module lưu đủ lượt; trợ lý hỏi theo phiên

**Nguồn chân lý:** [spec Pha B2](../../doc/pha-b2-spec.md), mục 2, 3, 10 (`session-1`, `turn-1`, `answer-2`); [ADR 0017](../../doc/adr/0017-pham-vi-phien-la-noi-luu-neo-vao-khai-niem.md).
**Ai:** nhân viên · Claude kiểm · **Chi phí mô hình:** 0 USD (mô hình giả và phát lại) · **Chặn bởi:** 31 · **Trạng thái:** ready-for-agent

## Vì sao

Hiện phiên chỉ giữ 3 lượt cuối, nên người học không mở lại được cuộc trò chuyện cũ. Mỗi câu hỏi phải tự gửi `current_module_id`, và không có danh sách
phiên. Trang học cần mỗi module có danh sách phiên riêng.

## Cần làm

**Use case phiên:**
- `create_session(owner, doc_id, scope)`;
- `list_sessions(owner, doc_id, filter)`. Vé này làm hai bộ lọc `module:<module_id>` và `all`; bộ lọc `roadmap_page` làm ở vé 33;
- `rename_session`;
- `delete_session`;
- `list_turns(owner, session_id)`.

Mọi use case kiểm `owner`.

**Lượt `turn-1`:**
- Lưu **mọi** lượt, kèm `answer` là đối tượng `answer-2`.
- Ngữ cảnh gửi mô hình vẫn chỉ là 3 lượt cuối, ≤ 1.000 token.

**Tiêu đề do luật:**
- Sau lượt có trả lời đầu tiên, đặt `display_name` của khái niệm liên kết đầu tiên.
- Không có khái niệm liên kết thì lấy câu hỏi, cắt ở ranh giới từ, ≤ 60 ký tự.
- Không bao giờ ghi đè tiêu đề có `title_source = learner`.

**Trợ lý `answer-2`:**
- Yêu cầu gồm `session_id`, không còn `current_module_id`.
- Module đang mở lấy từ phạm vi của phiên, qua hàm giải của vé 31.
- Vé này chỉ phục vụ phạm vi module còn giải được. Phạm vi lộ trình và phạm vi đã cũ để vé 33; tới lúc đó, use case báo lỗi rõ ràng.

**Phiên cũ** (bản ghi phiên kiểu cũ trong kho thử) không cần chuyển đổi. Ghi rõ trong báo cáo vé.

**CLI:** lệnh tạo, liệt kê, đổi tên, xoá phiên và xem lượt; lệnh hỏi nhận `--session-id`.

## Tiêu chí nghiệm thu

- [ ] Test, mỗi cái thấy đỏ trước:
  - 5 lượt hỏi thì `list_turns` trả đủ 5, nhưng ngữ cảnh gửi mô hình ở lượt 5 chỉ có lượt 2–4;
  - tiêu đề do luật được đặt sau lượt đầu, theo khái niệm liên kết;
  - người học đổi tên rồi hỏi tiếp thì tiêu đề không bị ghi đè;
  - xoá phiên thì `list_turns` trả rỗng, và phiên không còn trong danh sách;
  - `owner` khác bị từ chối ở mọi use case;
  - trợ lý dùng module lấy từ phạm vi phiên: kịch bản có hai module, kiểm truy hồi ưu tiên đúng module.
- [ ] Hai yêu cầu cùng `client_turn_id` vẫn chỉ tạo một lượt (single-flight như cũ).
- [ ] Phát lại 0 USD 6 câu trợ lý đã ghi qua đường phiên mới. Báo trạng thái trước và sau.
- [ ] Ví dụ JSON thật của `session-1` và `turn-1` đính kèm báo cáo vé.
