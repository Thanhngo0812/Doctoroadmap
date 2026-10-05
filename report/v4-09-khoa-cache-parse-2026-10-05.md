# v4-09 — Khóa cache parse

Ngày 2026-10-05. Không gọi Gemini/Vertex/embedding; chi phí mô hình **0 USD**.

## Thay đổi

- `PipelineConfig` là dataclass đóng băng, đầu vào duy nhất để dựng tuỳ chọn PDF.
  Cấu hình trên parser là thuộc tính chỉ đọc, tránh đổi khóa sau khi converter đã được tạo.
- Mặc định: ảnh 2.0, lấy ảnh hình, OCR bật, RapidOCR/torch, TableFormer ACCURATE,
  cell matching bật, bố cục heron, số luồng theo Docling (kể cả biến môi trường của Docling).
- `parser_config.pipeline` chỉ xuất hiện khi có tuỳ chọn đầu ra khác mặc định.
  Không tăng `ADAPTER_VERSION`, không đổi identifier bộ đọc mặc định, không sửa cache cũ.
- Các tùy chọn được khóa: tỷ lệ ảnh/lấy ảnh, bật OCR/engine/backend/ngưỡng bitmap/OCR cả trang,
  bật cấu trúc bảng/chế độ/cell matching, mô hình bố cục, ba cỡ batch, cỡ queue và polling.
  `num_threads` không nằm trong hash; parse mới ghi `parser_runtime.num_threads` trong manifest.
  Cache hit không được ghi đè số luồng của lượt tạo parse. Artifact cũ thiếu telemetry thì
  báo chưa ghi, không suy đoán số luồng đã dùng.
- CLI `ingest` có cờ cho các tùy chọn trên và `--dry-run` chỉ tra cache, không parse,
  không chunk, không gọi mô hình, không ghi artifact.
- Không bổ sung thuật toán chia cuốn thành nhiều đoạn trang trong vé này. Luồng ingest
  hiện vẫn parse cả cuốn; khi vé 10 đưa chia đoạn vào luồng, tham số chia đoạn phải vào
  `PipelineConfig` và có test vô hiệu hóa cache, không được chỉ đặt trong script/converter.

## Nghiệm thu cache

**30/30 artifact parse hiện có tại `artifacts/parse_tree` giữ nguyên khóa.**
Chi tiết: `tmp/thu-a1/v409-cache-audit.json`; script `scripts/thu-a1/kiem_cache_v409.py`.
Đây là kiểm giữ địa chỉ cache theo cấu hình lịch sử của từng artifact, không phải hứa
mọi version cũ đều được chọn bằng adapter/source hiện tại. Những phiên bản đã lỗi thời
do thay PDF, bộ đọc, `strip_lines` hoặc adapter trước vé này vẫn cần đúng cấu hình cũ.
Không kiểm/đọc nội dung đồ thị, roadmap hoặc nhãn giữ lại.

Hash mốc từ `artifacts/parse_tree/doc-1/v1/manifest.json`:
`c4ce696fe6b6a5d1164a592a967b66accb949f3c1cd72b1dd3ea98a452e375dc`.
Test dùng đúng adapter v8 của artifact, không đổi hash lịch sử sang adapter v11.

Dry-run thật trên `doc-2.pdf`, không cờ pipeline:

| cấu hình | kết quả | parse version | parser_config_hash |
|---|---|---:|---|
| Mặc định | tái dùng | 4 | `4b897c487e4570a11d6fbca40c6a34212d02e2f6631d630e446c8c7750344acd` |
| `--no-do-ocr` | cần parse mới | — | `bc711ca0848d26aac219cde072894bb0a4d91e1af7e3f0accb85e1aab1e9152c` |
| `--num-threads 8` | tái dùng | 4 | như mặc định |

Dry-run doc-1 mặc định cần parse mới vì kho hiện không có parse cùng nguồn và
adapter v11; đây là trạng thái có trước vé 09, không phải mất cache vì thêm pipeline.

## Kiểm engine OCR

Docling đã cài chọn RapidOCR/torch ở nhánh cuối của `OcrAutoModel` trên máy này.
Đã so converter cũ (`PdfPipelineOptions(images_scale=2.0, generate_picture_images=True)`)
với converter mới ghim engine, chạy ngoại tuyến với mô hình đã có:

| tài liệu | trang PDF | JSON Docling chặt | từng mục | adapter |
|---|---|---|---|---|
| naive-bayes | 1–2 | giống | giống | giống |
| doc-1 | 40–41 | giống | giống | giống |
| xstk | 1–2 | giống | giống | giống |
| doc-4 (pypdfium2) | 100–101 | giống | giống | giống |

Bằng chứng: `tmp/thu-a1/v409-cache.json`. Đây là kiểm 8 trang mẫu trên bốn tài liệu,
**không phải chạy lại toàn bộ bốn cuốn**. Nhánh auto trong mã đã cài dựng đúng
`RapidOcrOptions(backend="torch")` với cùng ngưỡng bitmap/OCR cả trang. Vì không
thấy đổi đầu ra ở mẫu, mặc định ghim RapidOCR/torch; không còn tự đổi sang ONNX
khi môi trường cài thêm gói. CLI không cung cấp chế độ auto không xác định engine.

## Test chạy được

**Kết quả cuối: 72 passed**, 2 cảnh báo deprecation của SWIG; `git diff --check` đạt.

- `test_pipeline_change_does_not_reuse_parse`: 3 trường hợp OCR/bảng/engine đã
  **đỏ trước sửa**, `parser.calls == 1` thay vì 2; sau sửa phải tạo version parse mới.
- `test_default_hash_matches_old_artifact_without_pipeline_field`: hash mốc cũ.
- `test_threads_do_not_invalidate_cache_and_new_parse_records_threads`: số luồng
  không gây parse lại; manifest nguồn vẫn 4, parse của nguồn mới ghi 8.
- `test_every_exposed_output_option_changes_the_cache_key`: mọi trường đầu ra được
  phơi ra (trừ luồng) phải đổi hash khi đổi giá trị.
- `test_pipeline_is_frozen_and_converter_options_follow_it`: bất biến, converter
  nhận đúng cấu hình thực tế, số luồng runtime đúng.
- `test_cli_pipeline_flags_reach_ingest`, `test_dry_run_reuses_without_parse_or_writes`:
  cờ đi đến cấu hình; dry-run không gọi parser/save và hash toàn bộ tệp không đổi.

Lệnh kiểm nhóm ingest/parser/CLI:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit/application/test_parse_pipeline_cache.py tests/unit/presentation/test_ingest_pipeline_cli.py tests/unit/infrastructure/test_docling_parser_cache.py tests/unit/infrastructure/test_docling_adapter.py tests/unit/application/test_ingest.py tests/unit/presentation/test_cli.py -o addopts='' -q --basetemp tmp/v409-final-20261005a -p no:cacheprovider
.\.venv\Scripts\python.exe -m doc2roadmap.presentation.cli.main ingest doc-2.pdf --doc-id doc-2 --dry-run
.\.venv\Scripts\python.exe scripts/thu-a1/kiem_cache_v409.py
```

Dùng thư mục pytest tạm riêng trong workspace vì thư mục pytest hệ thống hiện bị
chặn quyền; không thay ACL hay xoá thư mục tạm cũ của người dùng.
Skill Ponytail được áp dụng bằng cách dùng dataclass/argparse sẵn có, tái dùng phép
băm và script đo A1; không thêm dependency hoặc tầng cache mới.
