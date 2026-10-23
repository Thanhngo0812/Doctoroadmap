# SA-66 — Trợ lý `answer-3`: gia sư tự nhiên, ngữ cảnh lấy trước, kiểm chỉ ghi log

**Nguồn:** [spec trợ lý 3](../../doc/tro-ly-3-spec.md) (chuẩn của vé này); [ADR 0026](../../doc/adr/0026-tro-ly-3-gia-su-tu-nhien.md). Bản thử 2026-10-23: trang so
sánh `Desktop\bai-giang-thu\so-sanh-tro-ly.html`, script `tmp/claude-tools/proto_tro_ly.py`. Chủ dự án: "nâng cấp toàn diện từ prompt, môi trường trợ lý để nó
trở nên chuẩn và cực kỳ tốt".

**Ai:** agent Sonnet cài · Claude nghiệm thu, chạy lượt thật và ghép · **Chi phí mô hình:** 0 USD khi cài (mô hình giả). Lượt thật do Claude chạy, chủ dự án đã
duyệt chi · **Chặn bởi:** SA-64 ghép. SA-64 có cổng `PageImages` và `body_md` của bài giảng; cả hai vé cùng đụng `get_lecture` · **Trạng thái:** chờ SA-64

## Phạm vi tệp

Sửa hay thêm:
- `src/doc2roadmap/application/phase_b/assistant.py`: ngữ cảnh lấy trước, lời nhắc, vòng công cụ, stream, trạng thái, `validation`, hợp đồng `answer-3`;
- `src/doc2roadmap/domain/phase_b_limits.py`: các khoá ở spec mục 7;
- `src/doc2roadmap/composition_phase_b.py`: nối cổng ảnh trang và làm nóng chứng thực;
- client mô hình có công cụ trong `infrastructure/llm/`, nếu cần cho stream có ảnh;
- trang xem thử và CLI phần trợ lý;
- test mới, và sửa test trợ lý cũ khẳng định hành vi bị bỏ (liệt kê từng cái).

**Không sửa:**
- `postcheck.py`, `documents.py`;
- quiz;
- bài giảng;
- `src/web/`.

## Tiêu chí nghiệm thu

Mọi test phải **đỏ trên mã cũ** hoặc trên bản sai. Ghi trong báo cáo cách đã thấy chúng đỏ.

- [ ] 11 bất biến ở mục "Quyết định kiểm thử" của spec. Lời nhắc so với khối `text` đọc từ tệp spec.
- [ ] **Ngữ cảnh lấy trước trên graph thật,** chỉ đọc, tìm kiếm BM25 không cần tiền:
  - câu "Muốn học trị riêng và véctơ riêng thì mình cần học những gì trước?" (doc-1 v8) có phần lộ trình với số module;
  - câu "Trong bảng mẫu hai chiều, đại lượng tần số đồng thời có ý nghĩa là gì?" (xstk v68) có đoạn định nghĩa tần số đồng thời.
- [ ] **Danh sách test trợ lý cũ đã sửa,** kèm lý do: hậu kiểm xoá câu, `KHONG_DU`, khối ngoài sách, 5 vòng. Không xoá test để cho xanh.
- [ ] Bảng phá, gồm ít nhất:
  - còn gọi `check_text`;
  - trả rỗng khi có `KHONG_DU`;
  - bỏ tư liệu lấy trước;
  - lịch sử chỉ có câu hỏi;
  - không gửi ảnh khi có `[formula]`;
  - để `validation` lọt ra;
  - quên trần chi của `make_quiz`;
  - vòng cuối không buộc trả lời.
- [ ] Cổng toàn repo xanh, cùng React test và build.
- [ ] Báo cáo kèm JSON `answer-3` và chuỗi sự kiện của một câu hỏi từ mô hình giả.

**Nghiệm thu của Claude sau khi ghép:** chạy thật lại 12 câu của bản thử, cộng khoảng 20 câu của gói 19a, qua use case mới. Claude tự đọc từng câu, đo giây tới
chữ đầu ở câu thứ hai trở đi (mục tiêu p50 ≤ 3 giây trên Vertex), và báo chi.

## Ngoài phạm vi

- Tài liệu do người học yêu cầu: cùng bệnh hậu kiểm, vé riêng sau.
- Web.
- SA-23.
- Developer API.
