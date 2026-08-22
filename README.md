# doc2roadmap

Pipeline B0 tất định: Docling parse PDF/DOCX thành cây tài liệu, trích ảnh PNG của PDF, sau đó dựng section,
cắt chunk có tham chiếu ảnh và đóng băng artifact có version.

## Cài và kiểm tra

```powershell
.\.tools\uv.exe sync --all-extras
.\.tools\uv.exe run pytest -m "not integration"
.\.tools\uv.exe run python scripts/smoke_docling.py
```

Python được ghim ở 3.12.11 qua `.python-version`. Smoke test Docling cần tải model ở lần chạy đầu tiên.

## CLI

```powershell
.\.tools\uv.exe run doc2roadmap ingest path\to\book.pdf --doc-id book-v1
.\.tools\uv.exe run doc2roadmap inspect --doc-id book-v1
```

Artifact mặc định nằm trong `artifacts/`; ảnh nằm tại `parse_tree/<doc_id>/vN/images/`. Đổi root bằng
`DOC2ROADMAP_ARTIFACT_DIR`.

Ba trần chunk có thể đổi qua `DOC2ROADMAP_MAX_TOKENS` (512), `DOC2ROADMAP_MAX_TABLE_TOKENS` (2048) và
`DOC2ROADMAP_HARD_CAP_TOKENS` (6000). Mọi giá trị được ghi vào manifest và tham gia version hash.
