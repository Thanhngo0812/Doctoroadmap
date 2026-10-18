# SA-40 — Bài giảng gợi lại tiên quyết, câu nối, khối "Tiếp theo"

**Nguồn chân lý:** [spec Pha B2](../../doc/pha-b2-spec.md), mục 6 (phần mã dựng, phần LLM viết, K10–K12), 10 (`lecture-2`); [ADR 0018](../../doc/adr/0018-bai-giang-khong-hien-ban-lui-stream-sau-cong.md); [nghiên cứu bài giảng](../../report/nghien-cuu-bai-giang-tien-quyet-goi-mo-xu-ly-hong-2026-10-18.md), mục 4.
**Ai:** nhân viên · Claude kiểm · **Chi phí mô hình:** 0 USD (mô hình giả); lượt thật ở vé 43 · **Chặn bởi:** 39 · **Trạng thái:** ready-for-agent

## Vì sao

Chủ dự án muốn bài giảng "làm người ta biết có tính tiên quyết": gợi lại phần trước, gợi mở phần sau.
- Lượt thật ngày 2026-10-15: 3/12 bài có tiên quyết nhưng 0/3 có ý nhắc nền.
- `used_later` chỉ là danh sách tên, và nằm trong số khối bị cắt đầu tiên khi ngữ cảnh dài.

## Cần làm

**Phần mã dựng** (`skeleton`, 0 USD):
- **`prerequisites[]`:** tối đa 3 tiên quyết Hasse, mỗi tiên quyết có:
  - `recall`, gồm `node_id`, `name`, `module_index`, `module_title`, `order_note`, `definition`. `definition` là câu neo kèm trích dẫn;
  - `bridge`, null cho tới khi có câu nối đạt.
- **`next_up[]`:** tối đa 2 khái niệm theo cạnh `requires` đi ra, ưu tiên module gần nhất phía sau.
  - Mỗi mục có `quote` và `citation` của cạnh.
  - Đồ thị không có câu trích cạnh thì chỉ có tên và module.
- Bỏ `used_later` khỏi hợp đồng và khỏi prompt.

**Phần LLM viết:**
- **`bridges` thay `prereq_notes`:** một câu nối cho mỗi tiên quyết có nhãn `Q#`, lược đồ `{prereq, text, sources, quote}`.
- **Tiên quyết `legacy_excerpt`** (nhap-mon-ml, naive-bayes) không được gửi để viết câu nối.
- **Prompt:** nói rõ câu nối trung tính, không nói về người học; lấy giới hạn từ `BSettings`.

**Luật kiểm:**

| # | luật | khi hỏng |
|---|---|---|
| K10 | mỗi tiên quyết có `Q#` có một câu nối đạt | không sinh lại; tiên quyết đó chỉ có `recall`; đếm |
| K11 | `sources` đúng `Q#` của chính tiên quyết đó; `quote` nguyên văn; `text` có tên hoặc alias của tiên quyết | bỏ câu nối |
| K12 | `text` ≤ `bridge_max_chars`; không có cụm trong `bridge_forbidden_phrases` | bỏ câu nối |

**Câu nối là ý LLM,** nên chỉ gửi sau cổng, với `section_kind = cau_noi`.

**Chẩn đoán:** đếm câu nối đạt và câu nối bị bỏ theo từng luật, ở dòng chẩn đoán của SA-26.

## Tiêu chí nghiệm thu

- [ ] Test với mô hình giả, mỗi cái thấy đỏ trước:
  - khái niệm có 2 tiên quyết có `Q#` mà mô hình trả đủ 2 câu nối hợp lệ thì cả hai có `bridge`;
  - câu nối trích nhãn `Q#` của tiên quyết khác bị bỏ (K11);
  - câu nối không nêu tên tiên quyết bị bỏ (K11);
  - câu nối có "như bạn đã học" bị bỏ (K12);
  - câu nối dài quá trần bị bỏ (K12);
  - thiếu câu nối thì tiên quyết chỉ có `recall`, và **không** có lời gọi sinh lại (K10);
  - tiên quyết `legacy_excerpt` không có trong ngữ cảnh gửi mô hình;
  - với A → B, bài của A có B trong `next_up`, còn bài của B không có A;
  - `next_up` ở đồ thị không có câu trích thì không có trường `quote`;
  - `used_later` và `prereq_notes` không còn trong hợp đồng.
- [ ] Đổi `bridge_max_chars` thì prompt và luật đổi theo.
- [ ] Chạy 0 USD (mô hình giả hoặc không có mô hình) phần mã dựng cho mọi khái niệm của sáu cuốn. Báo:
  - số khái niệm có tiên quyết;
  - số tiên quyết có `Q#`, tức gửi được để viết câu nối, tách theo cuốn;
  - số khái niệm có `next_up`.
- [ ] Ví dụ JSON thật của `lecture-2` có `recall`, `bridge` và `next_up`, từ một kịch bản phát lại, đính kèm báo cáo vé.
