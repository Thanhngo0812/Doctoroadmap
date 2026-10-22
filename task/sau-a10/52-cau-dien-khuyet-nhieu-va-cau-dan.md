# SA-52 — Câu điền khuyết: nhiễu không nằm trong câu, không khoét giữa thuật ngữ khác, nhiễu không là ký hiệu, bỏ câu dẫn kết bằng dấu hai chấm

**Nguồn chân lý:** [spec Pha B](../../doc/pha-b-spec.md), mục 9, luật Q3–Q6; [SA-50](50-quiz-dien-khuyet-kiem-luat-va-cau-thieu.md);
[soát 2026-10-22](../../report/soat-pha-b-46-47-49-50-51-2026-10-22.md), mục SA-50.

**Ai:** Claude cài (chủ dự án giao 2026-10-21: Claude hoàn thành Pha B) · người soát độc lập kiểm trước khi ghép · **Chi phí mô hình:** 0 USD ·
**Chặn bởi:** không · **Trạng thái:** sẵn sàng

## Vì sao

Phát lại mọi module của sáu cuốn ở chế độ không gọi mô hình cho 713 câu điền khuyết. Cách đo và ví dụ ở báo cáo soát.

1. **Nhiễu nằm sẵn trong câu dẫn: 187/713 câu (26%).** Ví dụ xstk-ch3-1: "Người ta gọi kỳ vọng M(X) là ___, ký hiệu là μ và phương sai D(X) là phương
   sai tổng thể", nhiễu "Phương sai tổng thể". Người học loại được nhiễu mà không cần hiểu bài. Gốc: `_cloze_bank` chọn danh sách nhiễu một lần cho cả
   khái niệm, trước khi chọn câu trích, và không đối chiếu với câu.
2. **Khoét trống giữa một thuật ngữ khác: 13 câu.** Ví dụ doc-1: "Kết ___: A ∪ (B ∪ C) = (A ∪ B) ∪ C", đáp án "Hợp". "Kết hợp" là khái niệm khác, nên
   câu dạy sai liên hệ. `_blank_concept_aliases` chỉ kiểm ranh giới từ; mã chỉ có ngoại lệ viết tay cho "Hiệu" trong "kí hiệu".
3. **Q6, nhiễu là ký hiệu: 9 câu,** cùng nhiễu `Mm×n` (doc-1 v8, module_010). Q6 ghi "đáp án và câu nhiễu không bao giờ là công thức"; nhánh điền
   khuyết không kiểm chữ của phương án.
4. **Câu dẫn thiếu lọt lưới: 38 câu kết bằng dấu hai chấm.** Ví dụ "Các phép toán hợp, ___ và hiệu có các tính chất sơ cấp sau đây:". Regex
   `INCOMPLETE_CLOZE_LEAD_IN` chỉ nhận vài mẫu cố định, có tính từ chen giữa là lọt.
5. **Test cache không chống lùi phiên bản.** Mutation đổi `LOCAL_RULES_VERSION` về bản trước sống sót, vì test tự ép phiên bản bằng monkeypatch trước
   khi tra cache.

## Cần làm

- **Chọn nhiễu theo từng câu trích.** Bỏ nhiễu có tên hay alias xuất hiện trong câu trích; so theo ranh giới từ, không phân biệt hoa thường. Sau khi
  bỏ mà không còn đủ hai nhiễu hợp lệ thì bỏ câu, mã `cloze.distractor_in_stem`.
- **Không khoét trống trong thuật ngữ dài hơn.** Chỗ khớp alias của đáp án nằm trong tên hay alias dài hơn của một khái niệm khác trong graph thì bỏ câu,
  mã `cloze.blank_inside_longer_term`. Giữ ngoại lệ "Hiệu" trong "kí hiệu", vì "kí hiệu" không phải tên khái niệm trong graph.
- **Q6 cho phương án.** Bỏ nhiễu có ký hiệu toán: một trong `× = ∪ ∩ ∈ ∉ ∑ ∫ √ ≤ ≥ ≠ ± → ⊂ ⊃ ⊆ ^`. Đáp án là ký hiệu thì bỏ khái niệm khỏi nhánh điền
  khuyết. Mã `cloze.notation_option`. Luật "chữ cái liền chữ số" có trong bản vé đầu đã bỏ khi cài (2026-10-22): luật đó bắt nhầm tên khái niệm hợp lệ
  như "Chính quy hóa L2".
- **Câu trích kết bằng dấu hai chấm:** bỏ, dùng mã có sẵn `cloze.incomplete_lead_in`. Câu như vậy dẫn vào danh sách hay công thức không hiện. Chấp nhận
  mất một số câu vẫn trả lời được; báo số câu mất.
- **Đổi `LOCAL_RULES_VERSION` thành `quiz-local-rules-v4`** để ngân hàng cũ không trở lại từ cache. Khoá cache dùng chung cho câu LLM, nên ngân hàng LLM
  cũng sinh lại khi có người làm quiz. Không chạy sinh lại chủ động.
- **Sửa test cache:** ghi bản cache bằng khoá tính với chuỗi phiên bản cũ ghi cứng `quiz-local-rules-v3`, rồi tra bằng hằng số thật đang chạy, không
  monkeypatch.

## Tiêu chí nghiệm thu

- [ ] **Mỗi luật một test, thấy đỏ trên mã hiện hành rồi mới xanh,** dùng đồ thị tổng hợp:
  - nhiễu nằm trong câu bị bỏ, và câu có nhiễu khác đủ điều kiện vẫn tạo được;
  - khoét giữa thuật ngữ dài hơn;
  - phương án ký hiệu;
  - câu kết bằng dấu hai chấm.
- [ ] **Thử sửa sai bỏ từng luật mới đều bị bắt.** Lùi `LOCAL_RULES_VERSION` về `quiz-local-rules-v3` cũng bị bắt.
- [ ] **Phát lại 0 USD mọi module của sáu cuốn:**
  - bốn số đếm trên về 0;
  - báo số câu và khái niệm có câu trước và sau, cùng số khái niệm mất câu điền khuyết;
  - đọc tận một mẫu câu sau sửa.
- [ ] **Test quiz, hợp đồng, SA-45/46/50 và kiến trúc xanh;** cổng toàn repo qua runner xanh.

## Ngoài vé

- Không sửa đường sinh LLM.
- Không sửa neo hay tên khái niệm của Pha A. Khái niệm đặt tên bằng ký hiệu (`Mm×n`) báo cho phiên pha A.
- Không cải tổ cách chọn câu trích.
- Không chạy có tiền.
