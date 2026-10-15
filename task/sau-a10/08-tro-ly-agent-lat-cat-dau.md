# SA-08 — Trợ lý agent, lát cắt đầu: port gọi công cụ, vòng lặp có trần

**Nguồn chân lý:** [ADR 0012](../../doc/adr/0012-tro-ly-la-agent-goi-cong-cu.md); [spec Pha B](../../doc/pha-b-spec.md), mục 7, 10 và 13 (hợp đồng
`answer-1`), bất biến 9, 15; [báo cáo trợ lý](../../report/nghien-cuu-tro-ly-hoi-dap-do-thi-2026-10-11.md), mục 2.9, 3.8, 3.9.
**Ai:** nhân viên · Claude kiểm · **Chi phí mô hình:** lượt thử nhỏ khoảng 10 câu hỏi, dưới 0,1 USD, dry-run trước · **Chặn bởi:** 01, 02, 03 ·
**Trạng thái:** ready-for-agent

**Điều kiện riêng:** phần adapter Gemini, bộ điều phối và CLI mà nhân viên đang sửa dở phải được commit trước khi bắt đầu.

## Vì sao

Đây là lát cắt mỏng nhất của trợ lý mà vẫn đi hết đường: hỏi một câu, agent gọi công cụ, rồi trả lời có nhãn nguồn. Các vé 09, 10, 14, 17, 18
cùng xây trên lát cắt này.

## Cần làm

**Port mô hình hội thoại có công cụ (mới):**
- Một lượt nhận chỉ dẫn hệ thống, lịch sử, danh sách công cụ và chế độ `AUTO` hoặc `NONE`.
- Port trả luồng sự kiện: mẩu chữ, lời gọi công cụ, kết thúc kèm usage (gồm token suy nghĩ).
- Phiên giữ kín phần riêng của nhà cung cấp, cụ thể là thought signature của Gemini 3, và gửi lại đúng trong lượt.

**Adapter cho port:**
- adapter Gemini, cho cả Developer API lẫn Vertex;
- mô hình giả theo kịch bản cho test;
- ghi và phát lại phiên, như bộ phát lại LLM hiện có.

**Use case trợ lý:**
- **Ngữ cảnh mồi** do mã lắp: thẻ module đang mở; tối đa 2 khái niệm liên kết được, kèm "vì sao đứng ở đây"; tối đa 4 đoạn truy hồi có ưu tiên module.
- **Ba công cụ:** `search_document`, `lookup_concept`, `why_here`.
- **Vòng lặp có trần:** tối đa 5 vòng công cụ và khoảng 0,01 USD mỗi tin nhắn. Vòng cuối, hoặc vòng sắp vượt trần, đặt `NONE`.
- **Lỗi công cụ** trả thông báo có cấu trúc cho mô hình và được đếm vào tỉ lệ gọi công cụ sai.
- **Sự kiện:** `progress`, `tool_call` (`by = model`), `delta`, `final`.
- **Câu trả lời:** Markdown có nhãn nguồn.
- **Hợp đồng `answer-1` bản tối thiểu:** `status` ∈ {`answered`, `budget_exhausted`, `error`}, kèm `usage` và `tool_calls`.
- **Sổ chi:** mỗi lời gọi một dòng.
- **Phạm vi tìm:** chỉ trong tài liệu; chỉ dẫn hệ thống cấm dùng web.

**Lệnh CLI hỏi một câu:** nhận tài liệu, module đang mở, câu hỏi; in sự kiện và JSON cuối. Có `--dry-run` (ước token từ ngữ cảnh mồi, không gọi)
và `--allow-spend`.

## Tiêu chí nghiệm thu

- [ ] Test với mô hình giả theo kịch bản, mỗi cái thấy đỏ trước:
  - mô hình trả lời ngay thì đúng 1 lời gọi;
  - mô hình gọi công cụ thì kết quả công cụ có trong đầu vào vòng kế và trong nhật ký;
  - mô hình gọi công cụ mãi thì dừng ở vòng 5, vòng cuối `NONE`, `status = budget_exhausted` kèm phần đã có;
  - chạm trần USD thì ép vòng cuối;
  - tên công cụ sai hoặc tham số sai thì mô hình nhận lỗi có cấu trúc, và lỗi được đếm.
- [ ] Test adapter trên phiên đã ghi: thought signature được gửi lại trong lượt.
- [ ] Lượt thật khoảng 10 câu trên doc-6 và naive-bayes, sau dry-run và chủ dự án duyệt. Báo:
  - USD mỗi câu;
  - TTFT và tổng giây, ở p50 và p90;
  - số vòng;
  - số lần gọi công cụ sai.

  Ghi lại phản hồi để làm test phát lại.
- [ ] Test kiến trúc vẫn xanh.

## Ngoài vé

Ba việc không thuộc vé này:
- hậu kiểm trích dẫn và từ chối (vé 09);
- bốn công cụ còn lại, nhắc khái niệm nền, hội thoại nhiều lượt (vé 10);
- tạo nội dung (vé 14, 17, 18).
