# SA-67 — Tài liệu `document-3`: viết tự nhiên theo yêu cầu, tư liệu rộng, kiểm chỉ ghi log

**Nguồn:** [spec tài liệu 3](../../doc/tai-lieu-3-spec.md) (chuẩn của vé này); [ADR 0027](../../doc/adr/0027-tai-lieu-3-viet-tu-nhien.md). Bản thử 2026-10-24:
`tmp/claude-tools/proto_tai_lieu.py` (`--baseline`, `--v3`), `tmp/claude-tools/lap_tai_lieu.py`; kết quả ở scratchpad `tai-lieu-*`.

**Ai:** agent Sonnet cài · Claude nghiệm thu, chạy lượt thật và ghép · **Chi phí mô hình:** 0 USD khi cài (mô hình giả) · **Chặn bởi:** SA-70 ghép (hàm chữ thô công
thức dùng chung, trần ảnh) · **Trạng thái:** chờ SA-70

## Phạm vi tệp

Sửa hay thêm:
- `src/doc2roadmap/application/phase_b/documents.py`: luồng `document-3` theo spec mục 1–6;
- một tệp ngữ cảnh mới cho tài liệu, nếu cần (gom tư liệu, tin nhắn, `validation`), theo mẫu `assistant_context.py`;
- `src/doc2roadmap/domain/phase_b_limits.py`: khoá ở spec mục 7;
- `src/doc2roadmap/composition_phase_b.py`: nối cổng ảnh trang, tìm kiếm, stream cho `document()`;
- `src/doc2roadmap/application/phase_b/assistant.py`: chỉ phần tóm tắt kết quả `make_document`, nếu hợp đồng mới cần;
- CLI `phase-b document` và trang xem thử phần tài liệu, nếu đang đọc trường cũ;
- test mới, và sửa test tài liệu cũ khẳng định hành vi bị bỏ (liệt kê từng cái).

**Không sửa:** `postcheck.py`, bài giảng, quiz, `src/web/`.

## Tiêu chí nghiệm thu

Mọi test phải **đỏ trên mã cũ**. Ghi trong báo cáo cách đã thấy chúng đỏ.

- [ ] 10 bất biến ở mục "Quyết định kiểm thử" của spec. Lời nhắc so với khối `text` đọc từ tệp spec.
- [ ] Test graph thật của spec (xstk v68, module thứ 4–6), chỉ đọc, tìm kiếm BM25 không cần tiền.
- [ ] Danh sách test tài liệu cũ đã sửa, kèm lý do: trích nguyên văn, `outside_document_blocks`, hậu kiểm, `no_valid_citations`. Không xoá test để cho xanh.
- [ ] Bảng phá, gồm ít nhất:
  - còn gọi `check_text`;
  - chỉ lấy đoạn tìm được, bỏ đoạn định nghĩa của từng khái niệm;
  - quên chữ thô công thức;
  - không gửi ảnh khi có công thức;
  - để `validation` lọt ra;
  - bỏ kiểm `scope_too_large` trước lời gọi;
  - trả `failed` khi có chữ mà lỗi giữa chừng.
- [ ] Cổng toàn repo xanh, cùng React test và build.
- [ ] Báo cáo kèm JSON `document-3` và chuỗi sự kiện của một tài liệu từ mô hình giả.

**Nghiệm thu của Claude sau khi ghép:** chạy thật 6 yêu cầu của bản thử, cộng ca n19 của trợ lý, qua use case mới. Claude đọc từng tài liệu, đối chiếu công thức
với ảnh trang, đo giây tới chữ đầu, báo chi.

## Ngoài phạm vi

- Web.
- Dọn `postcheck.py` và mã `document-2`.
- Bật suy nghĩ hay lời gọi kiểm lại.
- Quiz (vé 68).
