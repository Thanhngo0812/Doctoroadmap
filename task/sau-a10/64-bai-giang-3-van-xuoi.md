# SA-64 — Bài giảng `lecture-3`: văn xuôi tự nhiên, tư liệu rộng, thấy ảnh trang

**Nguồn:** [spec bài giảng 3](../../doc/bai-giang-3-spec.md) (chuẩn của vé này); [ADR 0025](../../doc/adr/0025-bai-giang-3-van-xuoi-tu-nhien.md); giữ ADR 0024 và
ADR 0019. Bản thử 2026-10-23: so sánh ở `Desktop\bai-giang-thu\so-sanh.html`, script ở `tmp/claude-tools/proto_bai_giang.py`. Thay SA-63: SA-63 đã dừng,
chính sách "luôn hiện" của nó nằm trong vé này.

**Ai:** agent Sonnet cài · Claude nghiệm thu, chạy lượt thật và ghép · **Chi phí mô hình:** 0 USD khi cài (mô hình giả). Lượt thật sau khi cài do Claude chạy;
chủ dự án đã duyệt, "trần lên 100 luôn miễn là phải tốt" · **Chặn bởi:** không. SA-65 làm ảnh trang; vé này cài cổng `PageImages` và adapter đọc, nên chạy
được trước SA-65 · **Ghép:** Claude ghi cửa ghép ở mục 10 bàn giao · **Trạng thái:** sẵn sàng

## Phạm vi tệp

Sửa hay thêm:
- module use case bài giảng mới trong `src/doc2roadmap/application/phase_b/`; cổng `PageImages` trong `application/ports/`;
- adapter đọc ảnh trang trong `src/doc2roadmap/infrastructure/artifacts/`;
- `src/doc2roadmap/domain/phase_b_limits.py`: các khoá mới ở spec mục 10;
- client Gemini cho đầu ra chữ có stream và ảnh (`infrastructure/llm/`);
- `src/doc2roadmap/composition_phase_b.py`: chỉ phần nối use case mới;
- công cụ `get_lecture` trong `application/phase_b/assistant.py`: chỉ phần đọc bài;
- trang xem thử `src/doc2roadmap/presentation/preview/`, CLI `phase_b` (lệnh bài giảng);
- test mới trong `tests/`.

**Không sửa:**
- `lectures.py` (mã `lecture-2`); chỉ được import hàm dựng phần mã dựng, như vị trí, định nghĩa, `recall`, `next_up`, nhãn người học;
- quiz, phần khác của trợ lý;
- `src/web/`;
- `composition_build.py` (SA-62 đang chờ ghép; ảnh trang lúc dựng thuộc SA-65).

## Định dạng ảnh trang (SA-65 ghi, vé này đọc)

`artifact_dir/phase_b/page_images/<doc_id>/parse-v<N>/index.json`:

```json
{"schema_version": 1, "doc_id": "doc-1", "parse_version": 3, "scale": 1.5, "format": "jpeg",
 "pages": {"37": {"file": "pages/p037.jpg", "sha256": "…"}}}
```

Trang đánh số từ 1, khớp `chunk.page`. Adapter trả `None` nếu không có index hay không có trang đó.

## Cần làm

Theo spec mục 1–10, gồm:
- gom tư liệu `lecture-context-3`;
- ảnh trang khi có `[formula]`;
- lời nhắc nguyên văn mục 4, cộng dòng khuôn câu tự kiểm tra;
- gọi mô hình chữ có stream, nhiệt độ 1,0, 4.096 token;
- hợp đồng `lecture-3`, sự kiện `delta`;
- tách câu tự kiểm tra;
- log `validation` không gửi người học;
- cache;
- chính sách lỗi ADR 0024;
- trang xem thử Markdown kèm KaTeX. Thư viện JS ghim phiên bản; trang vẫn chỉ chạy localhost như vé 24.

## Tiêu chí nghiệm thu

Mọi test phải **đỏ trên mã cũ** hoặc trên bản sai. Ghi trong báo cáo cách đã thấy chúng đỏ.

- [ ] 10 bất biến ở mục "Quyết định kiểm thử" của spec, mỗi bất biến một test hay hơn.
- [ ] **Lời nhắc nguyên văn:** test so lời nhắc hệ thống với bản trong spec. So với chuỗi đọc từ tệp spec, không so với hằng số của chính mã.
- [ ] **Gom tư liệu trên graph thật**, chỉ đọc, 0 USD:
  - với khái niệm "Hệ phương trình có nghiệm duy nhất" (doc-1 v8), tư liệu có đoạn chứa "Ví dụ 30";
  - với "Bất đẳng thức Cauchy-Schwarz", tư liệu có đoạn trang 62 và cần ảnh trang.

  Đọc graph từ `C:/Users/ngoco/Desktop/Doctoroadmap/artifacts`, không ghi.
- [ ] Bảng phá trong báo cáo, gồm ít nhất các phép sau:
  - quên gửi ảnh khi có `[formula]`;
  - gửi ảnh khi không có `[formula]`;
  - để `validation` lọt ra người học;
  - chặn bài vì nhãn lạ;
  - không tách câu tự kiểm tra;
  - không sinh lại khi đầu ra rỗng;
  - nhiệt độ 0;
  - gom tư liệu bỏ qua đoạn có tên khái niệm ở tiêu đề.
- [ ] Test Pha B, test kiến trúc, và cổng toàn repo qua `scripts/w05_run_tests.py` xanh, cùng React test và build.
- [ ] **Báo cáo kèm JSON hợp đồng `lecture-3`** của một bài từ mô hình giả, và chuỗi sự kiện stream của nó.

**Nghiệm thu của Claude sau khi ghép:**
- chạy thật khoảng 30 khái niệm của sáu cuốn qua use case mới, và tự đọc;
- so với bản thử, đặt cạnh nhau ở trang so sánh;
- báo chi và giây tới chữ đầu, giây tới xong bài.

## Ngoài phạm vi

- Ảnh trang lúc dựng và lệnh chụp bù (SA-65).
- Web (người điều phối).
- Dọn mã `lecture-2`.
- Rà trợ lý (vé sau).
