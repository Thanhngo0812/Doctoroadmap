# SA-33 — Phiên toàn lộ trình, phạm vi đã cũ, thẻ module ngoài phạm vi

**Nguồn chân lý:** [spec Pha B2](../../doc/pha-b2-spec.md), mục 1, 2 (`roadmap_page`), 3; [ADR 0017](../../doc/adr/0017-pham-vi-phien-la-noi-luu-neo-vao-khai-niem.md).
**Ai:** nhân viên · Claude kiểm · **Chi phí mô hình:** 0 USD (mô hình giả); lượt nhỏ nếu chủ dự án muốn thử thật · **Chặn bởi:** 32 ·
**Trạng thái:** ready-for-agent

## Vì sao

Trang lộ trình cần phiên chat không gắn module nào. Ngoài ra, khi đồ thị lên phiên bản mới, phiên module cũ phải trỏ đúng module mới, hoặc báo rõ là
module đã đổi. Không được lặng lẽ trỏ sang module khác.

## Cần làm

**Phạm vi lộ trình và phạm vi đã cũ** (hàm giải trả `module_id = null`):
- truy hồi không ưu tiên module;
- **thẻ lộ trình** thay thẻ module: số thứ tự, tên module, số khái niệm. Báo số token của thẻ trên doc-4;
- khối nhắc nền tắt;
- phạm vi đã cũ thêm `graph_card.scope_note` = "module này đã đổi".

**Thẻ module ngoài phạm vi** (`graph_card.module_cards[]`):
- mỗi khái niệm liên kết được mà nằm ngoài module đang mở có thẻ `{module_id, module_index, module_title}`;
- ở phạm vi module, thẻ ghi "nội dung ở module N"; ở phạm vi lộ trình, ghi "nằm ở module N";
- trợ lý vẫn trả lời, không từ chối.

**Danh sách `roadmap_page`:**
- mọi phiên lộ trình;
- cộng 5 phiên module gần nhất, kèm nhãn module đã giải;
- phiên đã cũ có ghi chú.

## Tiêu chí nghiệm thu

- [ ] Test, mỗi cái thấy đỏ trước:
  - phiên lộ trình truy hồi không ưu tiên module: hai đoạn cùng điểm thì không có đoạn nào được đẩy lên vì module;
  - phiên lộ trình không có khối nhắc nền;
  - phiên module hỏi về khái niệm của module khác thì vẫn trả lời, và có `module_cards` đúng module;
  - dùng cặp đồ thị tổng hợp của vé 31: phiên module tạo trên v1 mà module biến mất ở v2 thì `scope_note` có mặt và chạy như phiên lộ trình; module bị
    tách thì giải sang phần có Jaccard cao nhất;
  - `roadmap_page` có đủ phiên lộ trình, và chỉ 5 phiên module mới nhất.
- [ ] Báo số token thẻ lộ trình trên doc-4 (91 module) và doc-1. Nếu vượt khoảng 800 token, đề xuất cách thu gọn.
- [ ] Ví dụ JSON thật của `answer-2` ở phạm vi lộ trình, có `module_cards`, đính kèm báo cáo vé.
