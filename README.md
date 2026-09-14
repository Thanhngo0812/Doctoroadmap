# doc2roadmap

Pipeline B0 tất định parse PDF/DOCX thành cây/chunk có version. A3 trích thực thể có bằng chứng và media;
A3′ lập chỉ mục vector + BM25 để truy hồi lai.

## Cài và kiểm tra

```powershell
.\.tools\uv.exe sync --all-extras
.\.tools\uv.exe run pytest -m "not integration"
.\.tools\uv.exe run python scripts/smoke_docling.py
```

Python được ghim ở 3.12.11 qua `.python-version`. Smoke test Docling cần tải model ở lần chạy đầu tiên.

LibreOffice là phụ thuộc tuỳ chọn cho DOCX chứa hình vẽ DrawingML. Không có LibreOffice, ảnh raster nhúng vẫn
được trích; hình vector không render được sẽ tạo cảnh báo `missing_image` hướng dẫn cài LibreOffice.

## CLI

```powershell
.\.tools\uv.exe run doc2roadmap ingest path\to\book.pdf --doc-id book-v1
.\.tools\uv.exe run doc2roadmap inspect --doc-id book-v1
.\.tools\uv.exe run doc2roadmap a3 --doc-id book-v1
.\.tools\uv.exe run doc2roadmap extract --doc-id book-v1 --few-shot path\to\few-shot.txt
.\.tools\uv.exe run doc2roadmap search "quá khớp" --doc-id book-v1
.\.tools\uv.exe run doc2roadmap a3-report --doc-id book-v1
```

Artifact mặc định nằm trong `artifacts/`; ảnh nằm tại `parse_tree/<doc_id>/vN/images/`. Đổi root bằng
`DOC2ROADMAP_ARTIFACT_DIR`.

Ba trần chunk có thể đổi qua `DOC2ROADMAP_MAX_TOKENS` (512), `DOC2ROADMAP_MAX_TABLE_TOKENS` (2048) và
`DOC2ROADMAP_HARD_CAP_TOKENS` (6000). Mọi giá trị được ghi vào manifest và tham gia version hash.

Prompt A3 mặc định nằm trong `src/doc2roadmap/application/prompts/`: phần hướng dẫn dùng tiếng Anh, còn
đoạn corpus few-shot giữ tiếng Việt. Có thể chọn bộ few-shot khác bằng `--few-shot` trên lệnh `extract`/`a3`
hoặc `DOC2ROADMAP_EXTRACTION_FEW_SHOT`; nội dung được tính vào `prompt_hash`.

Luồng A3, vai trò từng file, số đo thật và lệnh đánh giá được ghi tại
[`report/luong-xu-ly-a3-trich-thuc-the.md`](report/luong-xu-ly-a3-trich-thuc-the.md).
## Review kiểu thực thể (F53)

Xem danh sách cần duyệt mà không chạy lại AI:
`doc2roadmap a3-review-types --doc-id nhap-mon-ml --doc-id baocao-canhan`.
Lặp `--doc-id` để chọn corpus; [cột số liệu và kết quả thật F54](report/xu-ly-feedback-f54.md).

Quyết định `learnable` đã duyệt được đọc từ `artifacts/type_registry.json` (theo
`DOC2ROADMAP_ARTIFACT_DIR`), giữ nguyên qua các lần trích và tham gia khóa cache.
Xem [định dạng registry và kiểm chứng F53](report/xu-ly-feedback-f53.md).
### A4/A5 — hợp nhất ứng viên

`doc2roadmap a4 --doc-id baocao-canhan --names-only` chạy lớp tên không mạng.
`--prepare` chỉ dựng đề cử bằng embedding. Chạy A4/A5 đầy đủ cần `--gold` đã gán mù.
Bộ 416 nhãn AI đã được chủ dự án chấp nhận: `tests/fixtures/a4/gold-blind.json`.
Đặt `DOC2ROADMAP_CANONICAL_CONCURRENCY=4` trong `.env` (mặc định 4, số nguyên dương)
để giới hạn số lời gọi LLM A4/A5 đồng thời **trong mỗi lượt chạy một tài liệu**; đặt 1 để chạy tuần tự.
Các job độc lập chạy song song; phán cụm xong mới vá bằng cụm nhỏ đủ thành viên hai node, gộp xong mới mô tả,
kiểm draft xong mới viết lại.
Concurrency không vào khóa cache. Chạy bốn tiến trình với concurrency 4 có thể đạt 16 lời gọi đồng thời;
đây không phải giới hạn toàn hệ thống hay giới hạn requests/phút. A3 dùng `DOC2ROADMAP_EXTRACTION_CONCURRENCY` riêng.
Xem [trạng thái task, cách chạy và giới hạn kiểm chứng](feedback/F18-a4-a5-hop-nhat.md).
