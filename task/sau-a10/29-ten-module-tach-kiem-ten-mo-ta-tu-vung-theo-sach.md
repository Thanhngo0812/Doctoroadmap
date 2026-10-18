# SA-29 — Tên module: tách kiểm tên và mô tả, từ vựng mô tả lấy từ chính cuốn sách

**Nguồn chân lý:** [soát SA-25–28](../../report/kiem-thu-pha-b-sa25-28-2026-10-18.md), mục 4 (quyết định của Claude); [báo cáo SA-28](../../report/pha-b-sa28-2026-10-18.md);
[spec Pha B](../../doc/pha-b-spec.md), mục 2.
**Ai:** nhân viên · Claude kiểm và đọc lại toàn bộ · **Chi phí mô hình:** bước 1 là 0 USD (từ cache). Bước 3 ước 0,15–0,25 USD cho sáu cuốn, dry-run trước,
chủ dự án duyệt · **Chặn bởi:** không · **Trạng thái:** ready-for-agent

## Vì sao

SA-28 đổi prompt để mô tả viết thành câu. Kết quả:
- **đường lùi tăng từ 8/160 lên 135/160,** trong đó 122 module mang cờ `vocabulary`;
- **tên và mô tả rơi cùng nhau,** nên mất cả những tên LLM tốt;
- các đồ thị tên mới này đang là bản mặc định.

Claude phát lại 160 phản hồi đã ghi, 0 USD, script `scripts/pha-b/kiem_lai_tu_vung_sa28.py`:
- chỉ kiểm riêng tên thì **144/160** đạt;
- mở rộng từ vựng của mô tả bằng âm tiết của đoạn dạy, cộng âm tiết có ở ít nhất max(3, 2% số đoạn) của cuốn, thì **82/160** đạt;
- phần còn hỏng chủ yếu do mô tả tự xưng: "module" 42 lần, "nội dung" 31 lần.

## Cần làm

**1. Tách kiểm tên khỏi kiểm mô tả** (0 USD).
- Tên qua luật tên thì giữ, dù mô tả hỏng. Luật tên gồm: hình thức, `generic_title`, trùng, mảnh tên, từ vựng tên.
- Mô tả hỏng thì dùng khuôn. Ghi `description_source = template` và cờ `description_<luật>`, ví dụ `description_vocabulary`.
- Chạy lại sáu cuốn từ cache. Prompt và đầu vào không đổi, nên phải ra **0 lời gọi**. Ghi phiên bản đồ thị mới.

**2. Từ vựng mô tả và luật mượn từ.**
- **Từ vựng của mô tả** = từ vựng hiện có, cộng hai nguồn:
  - âm tiết của các đoạn dạy (`teaching_chunk_ids`) của mọi khái niệm trong module;
  - âm tiết xuất hiện ở ít nhất max(3, `naming_common_chunk_ratio` × số đoạn) đoạn của chính cuốn, với `naming_common_chunk_ratio` = 0,02 đặt ở
    `BSettings`.

  Không dùng danh sách từ viết tay. Từ vựng của tên giữ như cũ.
- **Luật "không mượn từ module kề" bằng mã.** Một âm tiết bị coi là mượn khi đủ cả hai điều kiện:
  - nó có trong tên hay bí danh khái niệm của module ±1;
  - nó không có trong tên, bí danh, mô tả A5 hay đoạn dạy của module đích.

  Câu mô tả có âm tiết mượn thì bị loại. Cờ `description_borrowed`.
- **Prompt:**
  - cấm mô tả tự xưng ("module này", "chương này", "bài này", "nội dung"); câu mô tả bắt đầu thẳng bằng điều được dạy;
  - gửi cho mô hình phần từ vựng nội dung (tên, bí danh, mô tả A5, tiêu đề, âm tiết đoạn dạy). Không gửi cả tập âm tiết tần suất, để không tăng token;
  - nói rõ: từ thông dụng của sách được phép.

**3. Lượt thật sáu cuốn.** Dry-run báo số lời gọi và USD. Chạy sau khi chủ dự án duyệt.

## Tiêu chí nghiệm thu

- [ ] Test, mỗi cái thấy đỏ trên mã hiện tại rồi mới xanh:
  - tên tốt kèm mô tả có từ ngoài từ vựng thì giữ tên LLM, và mô tả là khuôn có cờ `description_vocabulary`;
  - mô tả dùng một âm tiết chỉ có ở đoạn dạy của module thì qua;
  - mô tả dùng một âm tiết có ở ≥ 2% số đoạn của cuốn thì qua;
  - mô tả dùng tên khái niệm của module kề mà module đích không có thì bị loại, cờ `description_borrowed`;
  - prompt có câu cấm tự xưng;
  - đổi `naming_common_chunk_ratio` thì tập từ vựng đổi theo.
- [ ] Bước 1 chạy từ cache: 0 lời gọi; báo số tên LLM giữ được ở mỗi cuốn (đích khoảng 144/160).
- [ ] Phát lại 0 USD 160 phản hồi SA-28 qua luật mới (bước 2, chưa đổi prompt). Báo số mô tả đạt; phải khớp phép đo của Claude (82/160) hoặc giải thích
  chỗ lệch.
- [ ] Lượt thật bước 3 sau dry-run và duyệt. Báo cho từng cuốn:
  - tên LLM, mô tả LLM, mô tả khuôn;
  - số cờ theo từng luật;
  - USD và phút.
- [ ] Ngoài tên và mô tả, artifact không đổi gì (so như vé 05).
- [ ] Claude đọc lại toàn bộ tên và mô tả, ghi phán xét vào vé.

## Ngoài vé

Đánh giá tên bằng người chấm (vé 20).
