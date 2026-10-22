# doc2roadmap

Pipeline B0 tất định parse PDF/DOCX thành cây/chunk có version. A3 trích thực thể có bằng chứng và media;
A3′ lập chỉ mục vector + BM25 để truy hồi lai.

## Mở web WayFinder

Xem [hướng dẫn mở PostgreSQL, backend và frontend](src/web/README.md). Có lệnh PowerShell cho worktree W-07 trên máy hiện tại, địa chỉ truy cập, cách chạy bản build và dừng service.

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
# Đường Docling tường minh (PDF/DOCX; bắt buộc khi tái lập các lượt cũ):
.\.tools\uv.exe run doc2roadmap ingest path\to\book.pdf --doc-id book-v1 --a1 docling
.\.tools\uv.exe run doc2roadmap inspect --doc-id book-v1
.\.tools\uv.exe run doc2roadmap a3 --doc-id book-v1
.\.tools\uv.exe run doc2roadmap extract --doc-id book-v1 --few-shot path\to\few-shot.txt
.\.tools\uv.exe run doc2roadmap search "quá khớp" --doc-id book-v1
.\.tools\uv.exe run doc2roadmap a3-report --doc-id book-v1
```

Artifact mặc định nằm trong `artifacts/`; ảnh nằm tại `parse_tree/<doc_id>/vN/images/`. Đổi root bằng
`DOC2ROADMAP_ARTIFACT_DIR`.

### Dựng một cuốn (W-13)

```powershell
.\.venv\Scripts\python.exe -m doc2roadmap.presentation.cli.main build --file doc-6.pdf --doc-id new-book --dry-run
```

`--dry-run` đọc và kiểm tệp thật, báo các phụ thuộc hiện có, không gọi mô hình hoặc tạo graph. Bỏ cờ này để chạy qua cache; cache thiếu thì dừng trước khi chi.
Chỉ thêm `--allow-spend` khi đã duyệt chi. Chuỗi đầy đủ gồm đọc/kiểm sớm → gán vai trò → A3/A3′ → A4/A5 không vàng → roadmap → chuẩn bị Pha B.
Kết quả/usage cuối lượt được ghi vào `artifact_dir/builds.sqlite3`, kể cả khi lỗi hoặc huỷ; không tính dự toán.
Worker có thể gọi `build_document_runner(settings, recorder=...)` để dùng DB web thay SQLite. Xem [báo cáo W-13](report/w13-dung-mot-cuon-2026-10-19.md).

`ingest` mặc định `--a1 nhe`: R2 với hai mô hình `full` có SHA-256 tại `vendor/a1-nhe/`, chỉ nhận PDF gốc.
Bản quét/OCR nằm ngoài phạm vi của cả hai đường. Trang bìa toàn ảnh không tự làm PDF gốc thành bản quét.
DOCX, `--pdf-backend`, `--pdf-text-policy` và cờ pipeline dùng `--a1 docling`. Cảnh báo chữ chặn ingest;
chỉ cho qua khi có `--allow-text-quality-reason` hợp lệ, không tự đổi đường. Bộ nhẹ ưu tiên tốc độ/RAM;
không được diễn giải thành đã đạt luật chất lượng pha 4 của vé 15.

Ba trần chunk có thể đổi qua `DOC2ROADMAP_MAX_TOKENS` (512), `DOC2ROADMAP_MAX_TABLE_TOKENS` (2048) và
`DOC2ROADMAP_HARD_CAP_TOKENS` (6000). Mọi giá trị được ghi vào manifest và tham gia version hash.

Prompt A3 nằm trong `src/doc2roadmap/application/prompts/a3/`; few-shot mặc định là
`a3/few-shot/default.txt`, còn các bộ theo loại tài liệu nằm cùng thư mục. Có thể truyền đường dẫn bất kỳ bằng
`--few-shot` trên lệnh `extract`/`a3` hoặc `DOC2ROADMAP_EXTRACTION_FEW_SHOT`; nội dung được tính vào `prompt_hash`.
Xem [quy ước bố cục và thay đổi prompt](src/doc2roadmap/application/prompts/README.md).

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
Đặt `DOC2ROADMAP_CANONICAL_CONCURRENCY=16` trong `.env` (mặc định 16, số nguyên dương)
để giới hạn số lời gọi LLM A4/A5 đồng thời **trong mỗi lượt chạy một tài liệu**; đặt 1 để chạy tuần tự.
Các job độc lập chạy song song; phán cụm xong mới vá bằng cụm nhỏ đủ thành viên hai node, gộp xong mới mô tả,
kiểm draft xong mới viết lại.
Concurrency không vào khóa cache. Chạy bốn tiến trình với concurrency 16 có thể đạt 64 lời gọi đồng thời;
đây không phải giới hạn toàn hệ thống hay giới hạn requests/phút. A3 dùng `DOC2ROADMAP_EXTRACTION_CONCURRENCY` riêng.
Xem [trạng thái task, cách chạy và giới hạn kiểm chứng](feedback/F18-a4-a5-hop-nhat.md).

### Chuỗi gộp trước A8 (vé 17)

A4/A5 đầy đủ chỉ còn chuỗi `gop`. `--names-only` và `--prepare` giữ đường lớp tên cũ
cho D-01 đã đóng băng. Artifact v3 cũ vẫn đọc được ở A8, A10, bộ chấm và Pha B;
để dựng lại toàn bộ pipeline v3, dùng mã trước vé 19n.

```powershell
.\.tools\uv.exe run doc2roadmap a4 --doc-id book --gold tests/fixtures/a4/gold-blind.json --no-gold-for-doc --dry-run
# Sau khi duyệt dự toán, thay --dry-run bằng --allow-spend.
.\.tools\uv.exe run doc2roadmap roadmap --doc-id book --dry-run
```

`roadmap` mới cần canonical của chuỗi gộp. **Chạy `a4` đầy đủ trên tài liệu cũ sẽ
chuyển canonical sang chuỗi `gop`, đổi đầu vào của lần `roadmap` sau.** Neo và danh
tính đã nằm trong canonical; ba stage `provenance`, `teaching`, `identity`, các điểm
dừng tương ứng và cờ `--identity-review` đã gỡ. Quyết định gộp của người duyệt nạp ở
`a4 --merge-review`.

Pass chính mặc định chạy các phiên song song, không đưa cạnh của phiên trước vào
đầu vào phiên. Đặt `DOC2ROADMAP_ROADMAP_MAIN_PARALLEL=false` để chạy nối tiếp trong
từng chương như trước; tuỳ chọn này có trong khoá cache. Số worker và bộ giới hạn
tốc độ hiện có vẫn điều khiển mức đồng thời.

Neo dùng một lời gọi cho mỗi khái niệm; lời phán sửa dùng riêng từng mục.
Đã gỡ neo gom A5, đề cử theo mô tả nháp và gom lô lời phán sửa, cùng các cờ chọn
chuỗi/chế độ neo. Các biến môi trường cũ `UPSTREAM_CHAIN`, `ANCHOR_BATCH_MODE`,
`MERGE_DESCRIPTION_ENABLED`, `MERGE_DESCRIPTION_TOP_K`, `MERGE_DESCRIPTION_MIN_SIMILARITY`
và `CANONICAL_REPAIR_BATCH_SIZE` (đều có tiền tố `DOC2ROADMAP_`) bị bỏ qua có cảnh báo;
xoá chúng khỏi `.env` cũ.

Quyết định người duyệt vào `a4 --merge-review review.json` ở chuỗi `gop`, theo định dạng
`{"doc_id":"book","decisions":[{"left":"node_…","right":"node_…","decision":"Không gộp"}]}`.
Các lựa chọn: `Đồng ý gộp`, `Không gộp`, `Là hai nghĩa khác nhau`,
`Không chắc`. Danh sách gộp khác tên kèm bằng chứng nằm ở `merge_review` trong canonical.

Để chấm vàng cũ, thêm `--remap-gold-ids` cho `a8-score` hoặc `a8-roadmap-score`.
Nếu vàng gán theo provenance đã vá, `a8-score` cần thêm `--gold-graph <graph-gán-gốc>`
để xác thực tập gán trước khi chuyển ID. Bộ chấm liệt kê và từ chối bộ vàng có ID không
quy được; tệp vàng gốc giữ nguyên. Cổng đổi mặc định đã qua ở vé 19l;
quyết định luồng mặc định ghi ở [ADR 0016](doc/adr/0016-danh-tinh-trong-a4-neo-trong-a5.md).
