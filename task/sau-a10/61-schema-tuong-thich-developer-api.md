# SA-61 — Schema gửi Gemini tương thích Developer API (`additionalProperties` bị từ chối)

**Nguồn:** SA-60 (`report/pha-b-sa60-2026-10-22.md`): mọi lượt trợ lý qua Developer API trả HTTP 400 vì khai báo công cụ có `additionalProperties`; Vertex thì
nhận. Claude đã kiểm ngày 2026-10-22 rằng `additionalProperties` có ở:
- khai báo công cụ của trợ lý: `application/phase_b/assistant.py`, `_declaration`;
- schema đầu ra JSON của quiz: `application/phase_b/quiz.py`.

**Ai:** agent Sonnet cài · Claude nghiệm thu · **Chi phí mô hình:** 0 USD khi cài; một lượt thử thật rất nhỏ trên Developer API nếu cần, dry-run và xin duyệt
riêng · **Chặn bởi:** không · **Trạng thái:** sẵn sàng

## Vì sao

Sản phẩm dự định chạy Gemini Developer API. SA-60 cũng cho thấy embedding qua Developer API nhanh hơn Vertex khoảng 18 lần (0,63 s so với 11,4 s). Hiện
trợ lý không chạy được trên Developer API, và có thể cả các khâu dùng đầu ra JSON có schema (quiz, bài giảng, tên module, tài liệu).

## Cần làm

- **Phía ứng dụng giữ nguyên schema.** `_check_args` dựa vào `additionalProperties: False` để bắt tham số lạ.
- **Adapter Gemini** (`infrastructure/llm/`) lọc các khoá Developer API không nhận, **chỉ khi** gửi qua Developer API. Lọc cả khai báo công cụ lẫn
  `response_schema`, đệ quy qua schema con. Vertex giữ nguyên request như hiện tại.
- Lập danh sách khoá phải lọc theo tài liệu chính thức của Gemini API. Ghi nguồn vào báo cáo; không đoán.
- Kiểm mọi chỗ gửi schema: trợ lý, quiz (sinh và kiểm), bài giảng, tên module, tài liệu.

## Bổ sung 2026-10-24 (Claude, trước khi giao)

- **Giao sau SA-68.** Hôm nay có thêm nhiều chỗ gửi lược đồ hay cấu hình mới, phải phủ hết:
  - quiz-3: lược đồ sinh câu, lược đồ giải mù kèm `thinkingConfig`;
  - bài giảng: `thinkingConfig` khi `lecture_thinking_level` được đặt;
  - trợ lý: ảnh trang trong tin nhắn;
  - tài liệu `document-3`.
- **Kiểm theo tài liệu chính thức** xem Developer API có nhận `thinkingConfig.thinkingLevel` và `responseJsonSchema` như Vertex không; ghi nguồn.
- **Ngoài lõi, việc của người điều phối** (ghi ở bàn giao mục 10), cần trước hôm đổi transport cho demo:
  - nới chốt "WayFinder web requires DOC2ROADMAP_LLM_TRANSPORT=vertex" trong `src/web/backend/wayfinder/composition.py`;
  - thêm `DOC2ROADMAP_GEMINI_API_KEY` vào `src/web/.env` và đổi `DOC2ROADMAP_LLM_TRANSPORT`.

  Web chạy bằng `wayfinder.cli --env-file src/web/.env` từ worktree. Lõi chỉ đọc tệp `.env` ở thư mục đang đứng, nên không thấy `.env` tổng của repo; mọi khoá
  `DOC2ROADMAP_*` của web phải nằm trong `src/web/.env`.

## Tiêu chí nghiệm thu

- [ ] Test với transport giả, ghi lại thân request:
  - qua Developer API, không còn khoá bị cấm ở bất kỳ mức nào của schema;
  - qua Vertex, thân request giống hệt trước khi sửa.

  Test phải đỏ trên mã cũ.
- [ ] `_check_args` vẫn từ chối tham số lạ; test cũ xanh.
- [ ] Bản ghi phát lại SA-55 và mốc SA-56 vẫn khớp. Nếu bản ghi chứa thân request theo transport, giải thích vì sao.
- [ ] Test Pha B, test kiến trúc và cổng toàn repo xanh.
- [ ] Tuỳ chọn: một lượt thử thật rất nhỏ trên Developer API (một câu hỏi trợ lý, một module quiz), sau khi dry-run và chủ dự án duyệt.
