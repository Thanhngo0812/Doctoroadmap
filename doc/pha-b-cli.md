# Chạy Pha B trên máy cục bộ

Phạm vi đã cài: vé 01–18 và 24. Các vé 19–23 là phần đánh giá riêng.

## Trang xem thử, không gọi mạng

```powershell
.\.venv\Scripts\python.exe -m doc2roadmap.presentation.cli.main phase-b serve --port 8765
```

Mở <http://127.0.0.1:8765/>. Trang đọc tên và mô tả từ artifact A10 hoàn chỉnh mới nhất. Khi khâu tên vừa hoàn tất, bấm **Nạp lộ trình mới**. Chế độ mặc định dùng mô hình minh hoạ và quiz điền khuyết; nội dung đó không phải kết quả chất lượng của Gemini.

Chỉ có sáu tài liệu phát triển trong trang. Máy chủ chỉ nghe ở `127.0.0.1`; không có đăng nhập hay phục vụ tệp tùy ý. Không dùng kho JSON này đồng thời từ nhiều tiến trình. Nhóm web thay port lưu trữ khi làm bản nhiều người dùng.

## Tên module

```powershell
.\.venv\Scripts\python.exe -m doc2roadmap.presentation.cli.main phase-b names --doc-id doc-6 --graph-version 8 --dry-run
.\.venv\Scripts\python.exe -m doc2roadmap.presentation.cli.main phase-b names --doc-id doc-6 --graph-version 8 --deterministic
```

Lệnh thứ hai dùng đường lùi tất định, không gọi LLM. Khâu tên ghi một phiên bản đồ thị mới; không thay dãy học, thành viên module hay cạnh. Trường `title_source`, `description_source`, `naming_flags` cho biết nguồn và lỗi kiểm của từng module.

Nếu không truyền `--graph-version`, chạy lại khâu tên dùng A10 đầu vào ban đầu của bản tên mới nhất, tránh đổi ngữ cảnh chỉ vì tên hàng xóm đã được đặt lại. Cùng kho cache, model và cấu hình thì phản hồi đã lưu được dùng lại; dry-run báo số lời gọi còn thiếu. Khi truyền rõ `--graph-version`, khâu tên dùng đúng bản đó, kể cả các tên hàng xóm đã thay đổi. Trường `source_graph_version` trong kết quả cho biết bản đầu vào thực tế. Các lượt smoke bàn giao dùng kho `artifacts/phase_b/acceptance-group1.json`; kho này tách với `live.json` mặc định.

Lượt gọi Gemini cần dry-run và phê duyệt theo kế hoạch vé. Sau khi được duyệt, dùng `--mode gemini --allow-spend`. Các lời gọi được ghi theo mục đích trong kho Pha B; bản ghi để phát lại nằm trong `artifacts/phase_b/recordings/` hoặc thư mục `--record-dir`.

## Các use case khác

Xem tham số đầy đủ bằng `phase-b <lệnh> --help`:

| Lệnh | Chức năng |
|---|---|
| `a12` | Lớp gán module, giữ nguyên vector và ID chunk |
| `lookup`, `graph-tool` | Tra khái niệm, tiên quyết, đường học, quan hệ và media đã xác nhận |
| `search` | Truy hồi ưu tiên module, vẫn tìm toàn tài liệu |
| `concept-index` | Chỉ mục tên và mô tả khái niệm, cần duyệt embedding |
| `formulas --pdf <đường-dẫn>` | Cắt ảnh công thức từ PDF gốc, lưu theo phiên bản parse và từng lần xuất hiện |
| `lecture --node-id <id>` | Bài giảng có kiểm trích dẫn; có thể lặp `--node-id` |
| `quiz --module-id <id>` | Tạo lần làm quiz; hoặc truyền danh sách `--node-id` |
| `submit --attempt-id <id> --answers <json>` | Nộp ánh xạ item ID sang option ID |
| `history`, `report-question` | Lịch sử và báo lỗi câu hỏi theo người học |
| `ask --module-id <id> "câu hỏi"` | Trợ lý có công cụ và lịch sử phiên |
| `document --scope <id> "yêu cầu"` | Tài liệu theo yêu cầu; `--output` xuất Markdown có chú thích nguồn |
| `usage` | Tổng USD ước tính từ token, p50/p90 và số lời gọi theo mục đích |

Các lệnh sinh có `--dry-run`, `--owner`, `--store`, `--settings`, `--record-dir`, `--replay-dir`. Dry-run không gọi mô hình và không ghi kho. `--replay-dir` dùng phản hồi đã ghi và kiểm prompt/schema; cần dùng cùng phiên bản đầu vào và cấu hình. Sổ chi có dòng cho lời gọi thất bại; giá trị USD không thay thế hoá đơn của nhà cung cấp.

Nhóm web gọi các use case trong `application/phase_b` và dùng các hợp đồng `lecture-1`, `quiz-1`, `answer-1`, `document-1`; lớp HTTP thử nghiệm nằm ở `presentation/preview`.
