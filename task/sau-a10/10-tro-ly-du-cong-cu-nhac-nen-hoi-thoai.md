# SA-10 — Trợ lý: đủ công cụ, nhắc khái niệm nền, hội thoại nhiều lượt

**Nguồn chân lý:** [spec Pha B](../../doc/pha-b-spec.md), mục 10 (bước 1, 3, 6), bất biến 4, 11;
[báo cáo trợ lý](../../report/nghien-cuu-tro-ly-hoi-dap-do-thi-2026-10-11.md), mục 3.3, 3.5, 3.8.
**Ai:** nhân viên · Claude kiểm · **Chi phí mô hình:** lượt thử khoảng 20 câu, dưới 0,2 USD, dry-run trước · **Chặn bởi:** 09 ·
**Trạng thái:** ready-for-agent

## Vì sao

Mục tiêu 4 của đề cương yêu cầu trợ lý "chủ động nhắc lại các khái niệm nền dựa trên đồ thị". Người học cũng cần hỏi tiếp được, hỏi lộ trình,
hỏi quan hệ, hỏi hình. Vé này hoàn thiện trợ lý cho phần hỏi đáp.

## Cần làm

**Thêm bốn công cụ tra cứu** của vé 02 vào agent: `get_module_info`, `path_to`, `traverse`, `get_media`.

**Ghi chú module:** khái niệm thuộc module sau module đang mở thì ghi "học kỹ ở module N", do mã gắn.

**Khối nhắc khái niệm nền** do mã sinh, theo bảng luật ở báo cáo trợ lý, mục 3.5:

| trường hợp | nhắc gì |
|---|---|
| khái niệm được hỏi thuộc module sau | các tiên quyết Hasse nằm giữa module đang mở và module đó |
| khái niệm thuộc module đang mở | tiên quyết ở module trước, một dòng, kèm nút "vì sao?" |
| tiên quyết bị sách trình bày sau | ghi "sách trình bày ở phần sau" |
| câu hỏi đang hỏi chính khái niệm nền đó | không nhắc |

Bốn luật chống làm phiền:
- tối đa 1 khối mỗi câu trả lời, tối đa 3 khái niệm, đặt ở cuối;
- không nhắc lại cùng khái niệm trong một phiên;
- không nhắc ở câu từ chối hay câu nối tiếp ngắn;
- có cờ tắt.

**Hội thoại nhiều lượt:**
- Phiên lưu trong kho Pha B: `doc_id`, module đang mở, tập khái niệm đã nhắc, 3 lượt gần nhất (chỉ câu hỏi và câu trả lời, trần 1.000 token).
- Câu nối tiếp không liên kết được khái niệm nào thì mượn khái niệm của lượt trước.

**Hợp đồng:**
- sự kiện `graph_card` (ghi chú module, khối nhắc nền);
- `media` trong `final`, chỉ media `confirmed`.

**Sổ chi:** đo tỉ lệ gọi công cụ sai theo từng công cụ.

## Tiêu chí nghiệm thu

- [ ] Test kịch bản nhiều lượt, mỗi cái thấy đỏ trước:
  - lượt 2 "còn cái kia thì sao?" mượn đúng khái niệm;
  - lịch sử không quá 3 lượt;
  - khối nhắc không lặp khái niệm trong phiên, không có ở câu từ chối, và tắt được.
- [ ] Test công cụ qua lời gọi của mô hình giả:
  - `path_to` trả kết quả đã gộp;
  - `traverse` không bao giờ trả cạnh mở kiểu `requires`;
  - `get_media` chỉ trả media `confirmed`.
- [ ] Lượt thật khoảng 20 câu trộn các loại, trên doc-1 và nhap-mon-ml, sau dry-run và chủ dự án duyệt. Báo:
  - USD mỗi câu;
  - số vòng;
  - giây chờ ở p50 và p90;
  - tỉ lệ gọi công cụ sai theo từng công cụ.

  **Nếu tỉ lệ gọi công cụ sai quá 10% thì báo chủ dự án** (thông tin, không phải cổng dừng); không tự đổi mô hình.

## Ngoài vé

Hai việc không thuộc vé này:
- `get_lecture`, `make_quiz`, `make_document` (vé 14, 17, 18);
- đánh giá bốn cấu hình (vé 23).
