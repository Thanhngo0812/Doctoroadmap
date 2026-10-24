# SA-70 — Bài giảng `lecture-3` bản 2: lời nhắc V5, chữ thô công thức, 8 ảnh, stream không lộ câu tự kiểm tra, ảnh trang không làm hỏng lần dựng

**Nguồn:** [spec bài giảng 3](../../doc/bai-giang-3-spec.md), mục 11 (chuẩn của vé này), mục 4 (lời nhắc nguyên văn) và mục 10; [spec trợ lý 3](../../doc/tro-ly-3-spec.md)
mục 9. Thử nghiệm 2026-10-23/24: script `tmp/claude-tools/chay_that_lecture3.py` (cờ `--prompt`, `--raw-formula`, `--max-images`, `--thinking`), so sánh mù ở
scratchpad `lecture3-so-sanh/`. Biên bản web lần 3, R-W08-2: `report/dieu-phoi-nghiem-thu-ba-nhom-lan3-2026-10-23.md`.

**Ai:** agent Sonnet cài · Claude nghiệm thu, chạy lượt thật và ghép · **Chi phí mô hình:** 0 USD khi cài (mô hình giả) · **Chặn bởi:** SA-69 (đã ghép
`973fa99`). Khối lời nhắc mục 2 của spec trợ lý đã lên `assistant-prompt-5` (dòng công thức, dòng quiz/tài liệu đã tạo) · **Trạng thái:** sẵn sàng

## Phạm vi tệp

Sửa hay thêm:
- `src/doc2roadmap/application/phase_b/lecture3.py`: lời nhắc V5 và luật công thức; stream dừng ở tiêu đề tự kiểm tra; `validation`
  (`pages_with_formula`, `thieu_anh_trang`, `formula_left`); `thinkingConfig` theo tham số và vào khoá cache;
- `src/doc2roadmap/application/phase_b/lecture_context3.py`: hàm thay `[formula]` bằng chữ thô, dùng chung với trợ lý;
- `src/doc2roadmap/application/phase_b/assistant_context.py`, `assistant.py`: dùng hàm chung cho đoạn tư liệu; luật công thức và phiên bản lời nhắc
  `assistant-prompt-5`; đếm `pages_with_formula` trước khi cắt;
- `src/doc2roadmap/domain/phase_b_limits.py`: khoá ở mục 10 (`lecture-prompt-4`, `lecture-context-4`, 8 ảnh, `lecture_thinking_level`);
- client mô hình trong `infrastructure/llm/phase_b.py`, nếu cần để truyền `thinkingConfig` cho `stream_text`;
- `src/doc2roadmap/composition_build.py`: bắt lỗi chụp ảnh trang trong `learning_prep` (spec mục 11.7);
- test mới, và sửa test khẳng định lời nhắc hay trần cũ (liệt kê từng cái).

**Không sửa:** `postcheck.py`, `documents.py`, quiz, `src/web/`.

## Tiêu chí nghiệm thu

Mọi test phải **đỏ trên mã cũ**. Ghi trong báo cáo cách đã thấy chúng đỏ.

- [ ] Bất biến 11–16 của spec bài giảng. Lời nhắc so với khối `text` đọc từ tệp spec.
- [ ] Trợ lý: đoạn tư liệu có `[formula: <raw_text>]` đúng thứ tự; `pages_with_formula` đếm trước khi cắt; lời nhắc so với khối `text` của spec trợ lý.
- [ ] **Chữ thô trên graph thật,** chỉ đọc: với doc-1 v8, xstk v68, naive-bayes v49, mọi đoạn có `[formula]` đều thay được hết (số chỗ thay bằng số
  `formula_refs`). Riêng xstk v68, khái niệm "Hệ số tương quan mẫu": tin nhắn gửi mô hình chứa `0,8165`.
- [ ] Bảng phá, gồm ít nhất:
  - lệch thứ tự chữ thô (đảo hai `formula_refs`);
  - thay cả trong `sources` hay trong chữ dùng chọn trang ảnh;
  - đếm trang sau khi cắt;
  - stream vẫn phát dòng tiêu đề tự kiểm tra;
  - stream giữ lại mọi dòng (không phát gì tới khi xong);
  - quên đưa mức suy nghĩ vào khoá cache.
- [ ] Cổng toàn repo xanh, cùng React test và build.

**Nghiệm thu của Claude sau khi ghép:** chạy thật 30 khái niệm cũ cộng 9 bài nhiều công thức, đối chiếu công thức với ảnh trang ở các bài từng vượt trần, đo giây tới
chữ đầu, báo chi. Cập nhật bàn giao mục 10 cho web: `delta` không còn chứa câu tự kiểm tra.

## Ngoài phạm vi

- Bật suy nghĩ mặc định: chờ đợt đánh giá tổng.
- Tài liệu `document-3`: vé 67, dùng lại hàm chữ thô của vé này.
- Lỗi tính số lẻ của flash-lite trong ví dụ tự nghĩ: giới hạn đã biết, ghi ở spec tài liệu.
