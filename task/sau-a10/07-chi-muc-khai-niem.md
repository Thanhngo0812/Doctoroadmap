# SA-07 — Chỉ mục khái niệm

**Nguồn chân lý:** [spec Pha B](../../doc/pha-b-spec.md), mục 4 và 6; [báo cáo trợ lý](../../report/nghien-cuu-tro-ly-hoi-dap-do-thi-2026-10-11.md),
mục 3.2, câu hỏi H7.
**Ai:** nhân viên · Claude kiểm · **Chi phí mô hình:** embedding, ước dưới 0,01 USD cho sáu cuốn; dry-run trước · **Chặn bởi:** 01, 02 ·
**Trạng thái:** ready-for-agent

## Vì sao

Người học hay hỏi mà không gọi đúng tên khái niệm, kiểu "cái phép biến ma trận thành bậc thang là gì". Khớp theo tên thì không bắt được. Vector A6
có sẵn nhưng embed với task `SEMANTIC_SIMILARITY`, không hợp để so câu hỏi với khái niệm.

## Cần làm

**Lập chỉ mục:**
- Mỗi tài liệu có một chỉ mục vector khái niệm: embed `display_name` cộng mô tả A5 của mọi khái niệm học được.
- Mô hình `gemini-embedding-001`, 768 chiều, task tài liệu truy hồi.
- Chỉ mục khoá theo phiên bản đồ thị, mô hình embedding và văn bản đầu vào.

**Tra theo mô tả:** `lookup_concept` (vé 02) thêm nhánh này. Khi không khớp tên nào, embed câu hỏi bằng task truy vấn tương ứng, rồi trả tối đa
3 ứng viên vượt ngưỡng, đánh dấu `match = mo_ta`. Ngưỡng nằm trong cấu hình.

**Lệnh CLI:**
- lập chỉ mục, có `--dry-run` (số token, USD) và `--allow-spend`;
- tra khái niệm bằng một câu hỏi.

Mọi lời gọi embedding ghi sổ chi Pha B.

**Nhánh so sánh:** một cờ cho phép dùng vector A6 thay chỉ mục mới, để vé 23 so hai cách.

## Tiêu chí nghiệm thu

- [ ] Dry-run sáu cuốn báo số token và USD. Chạy thật xong thì lần chạy lại không gọi embedding.
- [ ] Test với embedding giả tất định:
  - câu hỏi không chứa tên khái niệm nhưng gần mô tả thì liên kết đúng;
  - câu hỏi có tên thì nhánh tên thắng;
  - dưới ngưỡng thì không trả gì.
- [ ] Mỗi lời gọi embedding có một dòng trong sổ chi.

## Ngoài vé

Hai việc không thuộc vé này:
- đo độ chính xác liên kết trên bộ câu hỏi thử (vé 23);
- embed lại chunk.
