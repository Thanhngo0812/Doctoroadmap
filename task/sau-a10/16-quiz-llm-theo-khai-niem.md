# SA-16 — Quiz LLM theo khái niệm

**Nguồn chân lý:** [ADR 0011](../../doc/adr/0011-noi-dung-hoc-sinh-khi-can-cache-theo-ngu-canh.md); [spec Pha B](../../doc/pha-b-spec.md), mục 9,
bất biến 5, 6, 8; [báo cáo quiz](../../report/nghien-cuu-quiz-tu-kiem-tra-2026-10-11.md), mục 3.1–3.6, 3.8.
**Ai:** nhân viên · Claude kiểm · **Chi phí mô hình:** lượt thử 2 module, dưới 0,05 USD, dry-run trước · **Chặn bởi:** 15 ·
**Trạng thái:** ready-for-agent

## Vì sao

Câu điền khuyết chỉ đo mức nhớ, và phủ kém ở sách toán. Chủ dự án chốt hai điều:
- quiz do LLM sinh khi người học bấm "làm quiz";
- câu hiện dần, câu nào xong trước hiện trước.

## Cần làm

**Đơn vị sinh là khái niệm.** Mỗi khái niệm có một ngân hàng 2 câu, ở hai mức Bloom do mã gán theo `node_type` (báo cáo, mục 3.1).

**Ngữ cảnh mỗi lời gọi**, theo spec mục 9:
- thẻ module;
- thẻ khái niệm và mức Bloom;
- câu neo và chunk dạy;
- mô tả A5, ghi "chỉ để hiểu, không trích";
- tối đa 3 tiên quyết;
- tối đa 4 ứng viên câu nhiễu do mã chọn;
- tối đa 2 chunk bài tập;
- một câu mẫu viết tay;
- nhắc nhiệm vụ.

**Luật kiểm:** Q1–Q8 cộng K5. Đáp án và câu nhiễu không bao giờ là công thức.

**Lời gọi kiểm giải mù**, mỗi khái niệm một lời gọi:
- Mô hình nhận câu đã xáo, không đánh dấu đáp án.
- Chọn khác đáp án, hoặc thấy hơn một phương án đúng, thì bỏ câu.
- Câu nhiễu "đúng theo nguồn" thì bỏ câu. Câu nhiễu "nguồn không nói" thì gắn cờ, và thay bằng ứng viên khác nếu còn.

**Đường lùi:** khái niệm không còn câu thì sinh lại 1 lần; vẫn hỏng thì dùng câu điền khuyết của vé 15, không đủ điều kiện thì bỏ khái niệm. Câu
hỏng không chặn cả bộ.

**Song song theo khái niệm:**
- Sự kiện `item_ready` gửi ngay khi một câu sẵn sàng, đã bỏ đáp án. Sự kiện `done` gửi khi xong.
- Lần làm chọn 1 câu mỗi khái niệm, xoay vòng biến thể.

**Cache và cấu hình:**
- Ngân hàng cache chung theo khoá khái niệm, gồm `context_hash`, prompt, lược đồ, prompt kiểm, mô hình và cấu hình.
- Nhiệt độ 0 cho cả lời gọi sinh lẫn lời gọi kiểm.
- Sổ chi ghi hai mục đích `quiz_gen` và `quiz_verify`.
- Lệnh CLI có `--dry-run` và `--allow-spend`.

## Tiêu chí nghiệm thu

- [ ] Test với mô hình giả theo kịch bản, mỗi cái thấy đỏ trước:
  - lời gọi kiểm chọn phương án khác thì bỏ câu;
  - câu nhiễu "đúng theo nguồn" thì bỏ câu;
  - "nguồn không nói" thì gắn cờ hoặc thay câu nhiễu;
  - phương án là công thức thì bỏ;
  - đáp án lộ qua độ dài thì sinh lại;
  - một khái niệm hỏng hết vẫn không chặn các khái niệm khác;
  - câu đầu được gửi trước khi khái niệm chậm nhất xong (kịch bản có độ trễ);
  - lần sau dùng lại ngân hàng, không gọi mô hình.
- [ ] Lượt thật trên 2 module (doc-1, doc-4), sau dry-run và chủ dự án duyệt. Báo:
  - USD mỗi module;
  - giây tới câu đầu và tới câu cuối;
  - tỉ lệ bỏ câu theo từng luật và theo lời gọi kiểm;
  - tỉ lệ khái niệm còn ít nhất 1 câu.

  Ghi lại phản hồi để phát lại.

## Ngoài vé

Hai việc không thuộc vé này:
- chấm người và đo độ chính xác của lời gọi kiểm (vé 22);
- gửi ảnh công thức cho mô hình.
