# SA-69 — Trợ lý `answer-3`: sửa sau lượt chạy thật (phạm vi công cụ, lộ lời nhắc)

**Nguồn:** [spec trợ lý 3](../../doc/tro-ly-3-spec.md), mục 8 (chuẩn của vé này) và mục 2. Lượt chạy thật 2026-10-24: 32 ca, 36 lượt, 0,072 USD; script
`tmp/claude-tools/chay_that_tro_ly.py`.

**Ai:** agent Sonnet cài · Claude nghiệm thu, chạy lại các ca hỏng và ghép · **Chi phí mô hình:** 0 USD khi cài (mô hình giả) · **Chặn bởi:** SA-66 (đã ghép
`ba4350f`) · **Trạng thái:** sẵn sàng. **Gấp:** web W-09 nhận `answer-3`; quiz và tài liệu do trợ lý tạo đang hỏng trên main.

## Vì sao

SA-66 bỏ mã module khỏi ngữ cảnh. Mô hình thật vì thế truyền `scope` dạng chữ người đọc ("module 4", "module 1: Giảm trùng lắp thông tin"). `make_quiz` và
`make_document` không hiểu nên hỏng cả hai. Test của SA-66 dùng mô hình giả truyền mã có sẵn, nên không bắt được.

## Phạm vi tệp

Sửa hay thêm:
- `src/doc2roadmap/application/phase_b/assistant.py`: khai báo `make_quiz`, `make_document` (mô tả `scope`, `scope` thôi bắt buộc); phân giải phạm vi trước khi
  gọi hai công cụ;
- `src/doc2roadmap/application/phase_b/assistant_context.py`: lời nhắc theo spec mục 2 (thêm hai dòng cuối);
- `src/doc2roadmap/domain/phase_b_limits.py`: `assistant_prompt_version` = `assistant-prompt-4`;
- test mới, và sửa test khẳng định lời nhắc cũ.

**Không sửa:** `quiz.py`, `documents.py`, bài giảng, `postcheck.py`, `src/web/`.

## Tiêu chí nghiệm thu

Mọi test phải **đỏ trên mã cũ** (main `ba4350f`). Ghi trong báo cáo cách đã thấy chúng đỏ.

- [ ] Bất biến 12 và 13 ở mục "Quyết định kiểm thử" của spec, qua use case với mô hình giả:
  - đủ các dạng `scope`: `"module 4"`, `["module 1: <tên>"]`, `"Module 4"`, mã `module_004`, tên module, tên khái niệm, `"module này"`, chuỗi rỗng, thiếu
    `scope`, chuỗi lạ;
  - khẳng định trên **lần làm quiz và tài liệu thật được tạo** (phạm vi, `node_ids`), không chỉ trên đối số đã phân giải;
  - phiên phạm vi lộ trình mà thiếu `scope`: quiz lộ trình; tài liệu lộ trình vượt 5 module thì `scope_too_large` như cũ.
- [ ] Hai ca thật nay qua được, chạy trên graph thật, chỉ đọc, mô hình giả phát lại đúng đối số mô hình thật đã gửi:
  - nhap-mon-ml v50, phiên module thứ 4: `make_quiz({"n": 3, "scope": ["module 4"]})` → quiz 3 câu (hay ít hơn nếu ngân hàng thiếu), phạm vi module thứ 4;
  - doc-6 v29, phiên module thứ 1: `make_document({"request": "…", "scope": ["module 1: Giảm trùng lắp thông tin"]})` → tài liệu, không lỗi phạm vi.
- [ ] Lời nhắc so với khối `text` đọc từ tệp spec (đã có test; cập nhật để nó đọc bản mới).
- [ ] Bảng phá, gồm ít nhất:
  - bỏ bước phân giải (truyền nguyên chữ);
  - đánh số module từ 0;
  - bỏ dự phòng "module đang mở";
  - để `scope` bắt buộc trong khai báo.
- [ ] Cổng toàn repo xanh, cùng React test và build.

**Nghiệm thu của Claude sau khi ghép:** chạy thật lại ca n13 (quiz), n19 (tài liệu), n20 (đòi in lời nhắc) bằng `chay_that_tro_ly.py`, đọc kết quả.

## Ngoài phạm vi

- Chữ thô công thức và ảnh trang cho trợ lý: vé 70.
- Sai số module trong lời trả lời: theo dõi ở đợt đánh giá tổng.
- Tài liệu `document-3`: vé 67.
