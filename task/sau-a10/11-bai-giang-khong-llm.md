# SA-11 — Bài giảng không LLM: khung do mã dựng và trích câu

**Nguồn chân lý:** [ADR 0011](../../doc/adr/0011-noi-dung-hoc-sinh-khi-can-cache-theo-ngu-canh.md); [spec Pha B](../../doc/pha-b-spec.md), mục 8
(phần do mã dựng, trường hợp đặc biệt) và 13 (hợp đồng `lecture-1`); [báo cáo bài giảng](../../report/nghien-cuu-bai-giang-theo-khai-niem-2026-10-11.md),
mục 4.2, 5; V11 trong `doc/pipeline-seminar-chuan-V1-V13-v2.md`.
**Ai:** nhân viên · Claude kiểm · **Chi phí mô hình:** 0 USD · **Chặn bởi:** 02 · **Trạng thái:** ready-for-agent

## Vì sao

Phần lớn giá trị của một bài giảng có sẵn trong đồ thị: vị trí, định nghĩa nguyên văn, khái niệm nền kèm câu trích "vì sao", hình. Làm phần này
trước thì có ba cái lợi:
- bấm khái niệm là có bài, 0 USD;
- có bản lùi khi lời gọi LLM hỏng;
- có mốc không LLM (V11) để so trong đánh giá.

## Cần làm

**Use case bài giảng, chế độ không LLM**, trả hợp đồng `lecture-1`. Có hai phần.

**Phần khung do mã dựng:**
- vị trí: module, k/m, khái niệm trước và sau;
- câu định nghĩa nguyên văn, kèm trang và tham chiếu công thức;
- tiên quyết hiển thị (Hasse, tối đa 3), kèm câu trích "vì sao" và ghi chú thứ tự: "đã học ở module m", "cùng module, ngay trước", "sách trình bày
  ở phần sau";
- media `confirmed`;
- dòng "học để làm gì": tối đa 3 khái niệm học sau, chỉ tên.

**Phần thân trích câu:**
- TextRank trên chunk dạy và chunk định nghĩa, chọn k câu theo thứ tự xuất hiện; tất định.
- `status = fallback`, kèm cảnh báo `ban_trich_cau`.

**Trường hợp đặc biệt:** không có chunk dạy và cũng không có chunk định nghĩa thì không dựng thân. Khi đó `status = no_source`, kèm các đoạn có nhắc
tên lấy từ `mention_map`.

**Lệnh CLI:** bài giảng cho một khái niệm, hoặc cho một danh sách khái niệm (dùng để chấm).

## Tiêu chí nghiệm thu

- [ ] Chạy cho mọi khái niệm của sáu cuốn, 0 USD. Báo:
  - mili giây mỗi bài;
  - số ca `no_source` (xstk có 1 ca đã biết);
  - số bài có cảnh báo `thieu_cong_thuc`.
- [ ] Test, mỗi cái thấy đỏ trước:
  - câu định nghĩa nằm nguyên văn trong chunk;
  - tiên quyết chỉ lấy từ Hasse, tối đa 3, và có câu trích;
  - cạnh ngược thứ tự sách mang đúng ghi chú;
  - chỉ media `confirmed` được hiện;
  - `no_source` đúng ca;
  - TextRank chạy hai lần cho cùng kết quả.
- [ ] Đủ các trường bắt buộc của hợp đồng `lecture-1`; đính kèm một ví dụ JSON thật cho nhóm web.
- [ ] Claude đọc 10 bài trải đều sáu cuốn và ghi phán xét vào vé.

## Ngoài vé

Phần LLM viết (vé 12) và stream (vé 13).
