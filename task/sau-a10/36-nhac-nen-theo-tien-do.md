# SA-36 — Trợ lý nhắc khái niệm nền theo tiến độ

**Nguồn chân lý:** [spec Pha B2](../../doc/pha-b2-spec.md), mục 3 (khối nhắc khái niệm nền); [ADR 0019](../../doc/adr/0019-tien-do-hoc-khong-chan-nhan-gan-luc-doc.md).
**Ai:** nhân viên · Claude kiểm · **Chi phí mô hình:** 0 USD · **Chặn bởi:** 33, 34 · **Trạng thái:** ready-for-agent

## Vì sao

Luật cũ nhắc tiên quyết mà không biết người học đã học chưa. Có tiến độ rồi, trợ lý chỉ nên nhắc những tiên quyết người học chưa đánh dấu.

## Cần làm

- **Phạm vi module:** khối nhắc khái niệm nền nhắc tối đa 3 tiên quyết Hasse **chưa** đánh dấu đã học, kèm câu trích. Giữ ba luật cũ: không nhắc lại
  trong cùng phiên, không có ở câu từ chối, tắt được.
- **Phạm vi lộ trình hay đã cũ:** không có khối nhắc.
- **Phiên mở lại:** danh sách đã nhắc giữ theo phiên.

## Tiêu chí nghiệm thu

- [ ] Test, mỗi cái thấy đỏ trước:
  - khái niệm có 3 tiên quyết, người học đã học 2, thì khối nhắc chỉ có tiên quyết còn lại;
  - học hết tiên quyết thì không có khối nhắc;
  - nhắc một lần rồi hỏi lại trong cùng phiên thì không nhắc lại;
  - phiên lộ trình không có khối nhắc;
  - câu từ chối không có khối nhắc.
