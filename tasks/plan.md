# Kế hoạch W-13 — dựng một cuốn ở lõi

Ngày: 2026-10-19. Người dùng giao lập kế hoạch, sau đó cho đúng ba subagent Luna triển khai; agent chính tích hợp và nghiệm thu.

## Phạm vi và quyết định

- `build_document` gọi trực tiếp use case, không chạy CLI con. Chuỗi đã được phiên Pha A xác nhận: bộ đọc nhẹ → kiểm sớm → label-roles → A3/A3′ → A4/A5 tiếng Việt → roadmap/A10/tên module → A12/chỉ mục khái niệm/ảnh công thức PDF.
- Bốn bước công khai: `doc_reading`, `concepts`, `graph`, `learning_prep`. `label-roles` bắt buộc đầu concepts; A3 và A3′ chạy song song. Huỷ ở ranh giới bước; thử lại tận dụng cache/checkpoint hiện có.
- Quyết định trực tiếp của người dùng thay phần dự toán trong vé/spec: không tính/hiển thị dự toán. Luồng web là thả tệp → xác nhận → dựng. Giữ dry-run nội bộ chỉ đọc thật và kiểm đầu vào/kế hoạch phụ thuộc, không gọi mô hình, không tạo graph, không bịa số downstream.
- Ghi chi phí từ usage thực tế vào DB kể cả khi lỗi/huỷ; giữ cờ thiếu usage nếu không có đủ số token, không giả số 0. Checkout chưa có web/PostgreSQL; cung cấp callback ghi kết quả cho W-14 và SQLite stdlib cho CLI cục bộ, không đưa phụ thuộc DB vào application.
- Mọi chạy nghiệm thu 0 USD: mock, cache, cấm mạng. Cache miss dừng và báo trước khi có chi. Không mở `document-data/test/` hay sửa mã Pha A hiện hành.
- Web truyền Settings với transport vertex cho cả sinh/embedding; lõi nhận cấu hình, không khoá transport, không tự fallback. Không bắt buộc API key ở đường Vertex/dry-run.
- Kiểm sớm: chất lượng chữ (`chu_loi`), bản quét (`ban_quet`), tiếng Việt (`ngon_ngu_khong_ho_tro`). Không truyền lý do bỏ qua chất lượng chữ. Hiệu chỉnh ngưỡng bằng sáu cuốn phát triển và tài liệu tiếng Anh/ảnh do test tạo.
- Vàng: chủ dự án xác nhận bổ sung cho gọi trực tiếp `Canonicalize.execute(..., a4_gold_coverage="none", gold_sheet_id=None)`, không đọc fixture hay kiểm artifact các cuốn khác. CLI a4 cũ thuộc Pha A giữ nguyên.

## Phụ thuộc và chia việc

Hợp đồng BuildRunner/BuildResult/BuildPipeline (agent chính) → ba nhánh độc lập → tích hợp + DB + kiểm thử đột biến + báo cáo (agent chính).

1. Luna 1: application orchestrator, kiểm sớm, huỷ/thử lại và test hành vi; chỉ sở hữu `application/use_cases/build_document.py`, `tests/unit/application/test_build_document.py`.
2. Luna 2: adapter gọi trực tiếp Pha A/B, composition nhận Settings, chốt chặn chi và số usage; chỉ sở hữu `composition_build.py`, `application/build_usage.py`, `tests/unit/application/test_build_pipeline.py` (nếu cần thêm tệp phải báo trước).
3. Luna 3: CLI build và FakeBuildRunner chép artifact, test CLI/hợp đồng; sở hữu `presentation/cli/build.py`, thay đổi nhỏ `presentation/cli/main.py`, `infrastructure/artifacts/fake_build_runner.py`, `tests/unit/presentation/test_build_cli.py`, `tests/unit/infrastructure/test_fake_build_runner.py`.
4. Agent chính: hợp đồng `application/ports/build.py`, SQLite recorder/test, hiệu chỉnh trên sáu cuốn, kiểm thử tích hợp/đột biến, báo cáo và đồng bộ đúng các đoạn tài liệu W-13 liên quan.

## Nghiệm thu

- Mỗi nhánh chạy test riêng với `.venv/Scripts/python.exe -m pytest <test>`; agent chính chạy lại các test W-13, các test lân cận CLI/canonical/roadmap/Pha B và kiểm import/compile các tệp mới.
- Bỏ/đổi thứ tự label-roles, bỏ kiểm sớm, đổi Vertex sang Developer API phải làm assertion độc lập thất bại. Huỷ trong concepts chặn graph; lỗi graph/thử lại không tăng số lời gọi bước đã cache.
- Chạy CLI dry-run trên PDF doc-6 bằng thư mục artifact tạm, 0 lời gọi mạng, không ghi graph. Cache-only pipeline dừng ở miss trước mọi chi; ghi chính xác giới hạn nếu không thể dựng hoàn tất từ cache của bộ đọc nhẹ.
- Lưu DB được truy vấn độc lập sau chạy; lỗi/huỷ cũng có bản ghi; không có estimate trong kết quả sản phẩm.
- Không commit/push vì workspace có thay đổi của các phiên khác; không hoàn nguyên các thay đổi đó.

## Rủi ro

| Rủi ro | Xử lý |
|---|---|
| Hàm composition cũ tự nạp Settings và đang thuộc phiên Pha A | Composition mới trong tệp riêng, truyền phụ thuộc rõ ràng; không sửa hàm cũ. |
| Cache doc-6 thuộc bộ đọc/chunk cũ | Không dùng để giả chứng minh đường cuốn mới; cache miss phải dừng ở chốt chi. |
| Nhãn vai trò tạo phiên bản chunk mới | Giữ identity/text/offset và test thứ tự; dùng load_role_chunks theo hợp đồng Pha A. |
| Nhà cung cấp không trả token embedding | Ghi phần đã đo cùng cờ incomplete; không gọi giá token ước là hoá đơn chính xác. |
| PostgreSQL/web chưa có trong checkout | Port callback + SQLite CLI được nghiệm thu; W-14 nối recorder vào DB web. |

## Câu hỏi và yêu cầu chuyển Pha A

Đã giải quyết câu hỏi không vàng: kiểm đầy đủ fixture cần canonical của bốn cuốn khác trong kho mới; chủ dự án đã cho gọi trực tiếp coverage=none ở application.
Agent chính không tự nhắn sang chat khác; chủ dự án là đầu mối Pha A.
