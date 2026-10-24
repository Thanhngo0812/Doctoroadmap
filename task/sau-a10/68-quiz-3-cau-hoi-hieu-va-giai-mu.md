# SA-68 — Quiz `quiz-3`: câu hỏi kiểm hiểu và vận dụng, giữ lại nhờ một lần giải mù có suy nghĩ

**Nguồn:** [spec quiz 3](../../doc/quiz-3-spec.md) (chuẩn của vé này); [ADR 0028](../../doc/adr/0028-quiz-3-cau-hoi-hieu-va-giai-mu.md). Bản thử 2026-10-24:
`tmp/claude-tools/proto_quiz.py` (bản cũ), `proto_quiz3.py` (sinh + giải mù), `kiem_lai_quiz3.py` (giải mù ở bốn mức suy nghĩ); kết quả ở scratchpad
`quiz-baseline/`, `quiz-v3/`.

**Ai:** agent Sonnet cài · Claude nghiệm thu, chạy lượt thật và ghép · **Chi phí mô hình:** 0 USD khi cài (mô hình giả) · **Chặn bởi:** SA-70 ghép (hàm chữ thô công
thức dùng chung, trần ảnh). Có thể chạy song song với SA-67 nếu khác tệp, nhưng giao từng agent một · **Trạng thái:** chờ SA-70

## Phạm vi tệp

Sửa hay thêm:
- `src/doc2roadmap/application/phase_b/quiz.py`: sinh ngân hàng `quiz-3`, giải mù, sinh bù một lượt, lọc câu điền khuyết, hợp đồng nộp bài;
- một tệp ngữ cảnh mới cho quiz, nếu cần;
- `src/doc2roadmap/domain/phase_b_limits.py`: khoá ở spec mục 8;
- `src/doc2roadmap/composition_phase_b.py`: nối cổng ảnh trang, mô hình giải có suy nghĩ, sinh song song;
- client mô hình trong `infrastructure/llm/phase_b.py`, nếu cần cho `thinkingConfig` và ảnh trong lời gọi JSON;
- CLI `phase-b quiz`, `submit` và trang xem thử phần quiz, nếu đang đọc trường cũ;
- test mới, và sửa test quiz cũ khẳng định hành vi bị bỏ (liệt kê từng cái).

**Không sửa:** `postcheck.py`, `documents.py`, bài giảng, trợ lý (trừ khi tóm tắt kết quả `make_quiz` cần đổi), `src/web/`.

## Tiêu chí nghiệm thu

Mọi test phải **đỏ trên mã cũ**. Ghi trong báo cáo cách đã thấy chúng đỏ.

- [ ] 10 bất biến ở mục "Quyết định kiểm thử" của spec. Lời nhắc so với khối `text` đọc từ tệp spec.
- [ ] Test graph thật của spec, chỉ đọc.
- [ ] Danh sách test quiz cũ đã sửa, kèm lý do: trích nguyên văn, cấm công thức, 3 phương án, luật Q1–Q8, `quiz_verify` cũ. Không xoá test để cho xanh.
- [ ] Bảng phá, gồm ít nhất:
  - gửi đáp án hay giải thích cho người giải;
  - không đổi lại thứ tự phương án khi so đáp án;
  - giữ câu `ambiguous`;
  - bỏ suy nghĩ ở bước giải;
  - sinh bù hơn một lượt;
  - còn luật cấm công thức;
  - để lý do của người giải lọt ra người học.
- [ ] Cổng toàn repo xanh, cùng React test và build.
- [ ] Báo cáo kèm JSON một lần làm quiz và kết quả nộp bài `quiz-3` từ mô hình giả.

**Nghiệm thu của Claude sau khi ghép:** chạy thật 12 khái niệm của bản thử qua use case mới. Claude tự giải và đọc từng câu, đối chiếu công thức với ảnh trang,
đếm câu sai còn lọt, đo thời gian một lần làm quiz module, báo chi. Cập nhật bàn giao mục 10 cho web: 4 phương án, LaTeX, `contract_version` `quiz-3`.

## Ngoài phạm vi

- Web.
- Sinh sẵn ngân hàng khi dựng sách.
- `high` ở bước giải, mô hình mạnh hơn.
- Dọn mã `quiz-2`.
