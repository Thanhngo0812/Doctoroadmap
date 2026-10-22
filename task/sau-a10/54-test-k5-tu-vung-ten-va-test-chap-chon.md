# SA-54 — Test cho K5 và luật từ vựng của tên module; ổn định hai test kho JSON chập chờn

**Nguồn chân lý:** [spec B2](../../doc/pha-b2-spec.md), mục 6, K5; [spec Pha B](../../doc/pha-b-spec.md), mục tên module; [SA-29](29-ten-module-tach-kiem-ten-mo-ta-tu-vung-theo-sach.md);
[soát 2026-10-22](../../report/soat-pha-b-46-47-49-50-51-2026-10-22.md), phụ lục "kiểm lại các chỗ canh giữ cũ".

**Ai:** agent Sonnet cài · Claude nghiệm thu · **Chi phí mô hình:** 0 USD · **Chặn bởi:** không · **Trạng thái:** sẵn sàng

## Vì sao

Ngày 2026-10-22, Claude chạy lại các mutation cũ trên mã hiện hành với toàn bộ 343 test Pha B. Kết quả có hai chỗ canh giữ chưa test nào bảo vệ, và
hai test cho kết quả sai khi máy nặng tải:

1. **K5, chống bịa ký hiệu toán trong bài giảng.** Thay `if not _symbols_valid(item["text"], cited_texts):` trong `_valid_item` của
   `application/phase_b/lectures.py` bằng `if False:` mà mọi test vẫn xanh. Không test nào gọi tới `_symbols_valid`.
2. **Luật từ vựng của tên module.** Bỏ nhánh `return 'vocabulary'` trong `_validate_title` của `application/phase_b/naming.py` mà mọi test vẫn xanh.
   SA-29 tách kiểm tên khỏi kiểm mô tả; nhánh của mô tả có test (`test_bad_description_keeps_valid_llm_title_and_marks_only_description_fallback`),
   nhánh của tên thì không.
3. **Hai test chập chờn khi máy nặng tải:**
   - `tests/unit/application/test_phase_b_budget_sa48.py::test_two_lecture_nodes_share_the_system_reservation_and_cached_result_stays_available[json]`;
   - `test_assistant_sessions_share_learner_reservation_before_streaming[json]`.

   Cả hai chờ luồng bằng mốc thời gian 0,5–2 giây trên kho JSON. Chúng làm cổng SA-53 lần đầu đỏ giả (`KeyError: 'a'`, lỗi trong `Thread` bị nuốt), và
   làm hai mutation không liên quan trông như bị bắt. Chạy riêng thì đạt 20/20 lần.
4. **Các khe thiếu test của SA-52 và SA-53**, do người soát độc lập tìm thấy
   ([soát 52–53](../../report/soat-pha-b-52-53-sonnet-2026-10-22.md)). Mỗi khe dưới đây là một mutation sống sót:
   - `_term_in` trong `application/phase_b/quiz.py` bỏ ranh giới từ;
   - nhiễu chỉ lộ trong câu qua alias: `distractor_terms.get(value, [value])` đổi thành `[value]`, hoặc bỏ ghi `distractor_terms` ở nhánh nhiễu dự
     phòng lấy từ module;
   - bỏ ký tự `^` khỏi `CLOZE_NOTATION`;
   - SA-53, `application/phase_b/lectures.py`: chưa có test khoá kịch bản câu nối đầu của tiên quyết a bị K6 loại lúc stream, còn câu nối sau của a được
     phát. Đầu ra hiện đúng nhờ `_merge_emitted`, nhưng không có test giữ.

## Cần làm

- **Test K5:** bài giảng tổng hợp có một ý chứa ký hiệu toán không có trong nguồn được trích. Ý đó bị bỏ, ghi `dropped_by_rule["K5"]`. Ý cùng ký hiệu
  nhưng có trong nguồn thì được giữ.
- **Test từ vựng của tên:** mô hình giả trả tên module có một từ không nằm trong từ vựng của module (từ của nội dung module cộng từ chức năng). Tên bị loại
  với cờ `vocabulary` và đi đường lùi. Tên có đủ từ trong từ vựng thì được giữ. Không sửa luật, không sửa mô tả.
- **Ổn định hai test chập chờn:** thay các mốc `join(timeout=...)` hay `wait(timeout=...)` dùng để đoán thứ tự bằng sự kiện đồng bộ rõ ràng. Lỗi xảy ra
  bên trong luồng phải được bắt và nêu ra trong assertion, không để thành `KeyError` mù. Giữ nguyên điều test kiểm: giữ chỗ ngân sách dùng chung, một
  lượt bị chặn khi hết trần.
- **Test cho các khe của SA-52:**
  - nhiễu "Tam" không bị coi là có trong câu chứa "Tam giác";
  - nhiễu chỉ xuất hiện trong câu qua alias của nó thì bị loại, ở cả nhánh nhiễu thường lẫn nhánh dự phòng;
  - nhiễu chứa `^` bị bỏ.
- **Test cho khe của SA-53:** kịch bản stream câu nối `[a₁ bị K6 loại, a₂ hợp lệ]`. `a₂` đã phát phải có trong final, trong cache và trong
  `prerequisites[].bridge`; không có sự kiện nào rút lại `a₂`.
- **Không sửa mã sản phẩm.** Nếu thấy test chập chờn hay một khe thiếu test là do lỗi thật của mã, dừng lại và ghi vào mục "Câu hỏi" của báo cáo.

## Tiêu chí nghiệm thu

- [ ] Hai test mới xanh trên mã hiện hành. Thay `_symbols_valid` bằng `if False:` thì test K5 đỏ. Bỏ nhánh `return 'vocabulary'` của `_validate_title` thì
  test tên đỏ. Ghi kết quả mutation vào báo cáo.
- [ ] Hai test đã ổn định chạy 30 lần liên tiếp, trong lúc một tiến trình khác chạy song song làm máy nặng tải: 0 lần đỏ. Ghi cách tạo tải.
- [ ] Hai test đó vẫn bắt được mutation gốc của SA-48: `DailySpendGuard.reserve` và `release` thành no-op thì đỏ.
- [ ] Mỗi mutation sống sót trong mục 4 giờ làm ít nhất một test mới đỏ. Ghi bảng mutation vào báo cáo. Test của SA-53 phải đỏ khi bỏ
  `_merge_emitted` ở nhánh final; nếu không đỏ được thì giải thích vì sao.
- [ ] Test Pha B và kiến trúc xanh; cổng toàn repo qua runner xanh.

## Ngoài vé

- Không đổi luật K5, luật từ vựng hay ngưỡng nào.
- Không sửa kho JSON hay kho PostgreSQL.
- Không chạy có tiền.
