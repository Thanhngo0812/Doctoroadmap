# W-13 — dựng một cuốn ở lõi, 2026-10-19

## Kết quả và phạm vi nghiệm thu

Đã cài use case `BuildDocument`, port `BuildRunner`, composition nhận `Settings`, CLI `build`, bộ dựng giả và callback ghi kết quả vào DB. Ba subagent `gpt-6-luna` phụ trách điều phối, nối pipeline, CLI/bộ giả; agent chính đọc mã, sửa lỗi tích hợp, kiểm thử và ghi báo cáo này.

**Cập nhật sau duyệt chi:** đã dựng xong doc-6 cả từ cache lịch sử và từ kho hoàn toàn rỗng, sau đó chạy lại thành công ở 0 USD. Đã đo đủ sáu PDF gốc, gồm `nhap-mon-ml` 20 trang. Chi/usage từng lượt đã ghi SQLite. Xem [báo cáo hoàn tất](w13-hoan-tat-doc6-2026-10-19.md) để nhận kết quả, số chi và hash bổ sung; các bảng kiểm 0 USD bên dưới là lịch sử trước phê duyệt.

**Lịch sử đề nghị:** đã kiểm cả kho cache và ghi [đề nghị chi riêng](w13-doc6-kiem-cache-va-de-nghi-chi-2026-10-19.md). Chủ dự án sau đó duyệt hoàn thành, không còn chờ phê duyệt; không bỏ nhãn để ép qua.

Kế hoạch: [plan](../tasks/plan.md), [todo](../tasks/todo.md). Snapshot bàn giao chỉ gồm mã/test/script/báo cáo W-13 và các đoạn tài liệu do phiên W-13 cập nhật; các thay đổi của phiên khác được giữ nguyên ngoài commit. Hash bàn giao lấy bằng `git log -1 --format=%H` sau khi commit; chưa push.

## Các quyết định đã chốt

- Người dùng thả tệp rồi bấm xác nhận mới dựng. Bỏ tính/hiển thị dự toán trên app; ghi số thực tế của lượt chạy vào DB. UI/hàng đợi/worker thuộc W-14 và nhóm web.
- `doc_reading`: bộ đọc nhẹ cho PDF, Docling cho DOCX; kiểm chất lượng chữ, bản quét, tiếng Việt, 0 USD. Không truyền lý do bỏ qua chất lượng chữ. Lỗi chữ trả `chu_loi`.
- `concepts`: **label-roles bắt buộc → A3/A3′ song song → A4/A5 tiếng Việt**. Nhãn là lớp phủ; đọc nhãn qua cơ chế hiện có của Pha A.
- `graph`: roadmap gồm cụm, mentions, cạnh chính/phụ, kiểm đồ thị, nhãn khái niệm, A10 và tên module.
- `learning_prep`: A12, chỉ mục khái niệm, cắt công thức PDF. Ghim bản graph và parse tương ứng; chỉ trả metadata gọn, không nhét vector vào log DB.
- Chủ dự án đã cho phép gọi trực tiếp `Canonicalize.execute(..., a4_gold_coverage="none", gold_sheet_id=None, declared_language="vi")`. Không đọc/kiểm fixture vàng và không sửa CLI `a4` của Pha A. Cách tạm kiểm đầy đủ fixture bị loại vì kéo theo canonical của bốn cuốn khác trong kho mới.
- Web/worker phải truyền Settings dùng Vertex cho cả sinh và embedding. Composition giữ transport được truyền, không tự chuyển đường. Checkout chưa có mã web/DB web nên kiểm hiện tại ở ranh giới composition lõi; W-14 còn phải nối từ worker thật.

## Cách dùng và chỗ nối DB

```powershell
.\.venv\Scripts\python.exe -m doc2roadmap.presentation.cli.main build --file doc-6.pdf --doc-id new-book --dry-run
```

Dry-run đọc/kiểm đầu vào thật, chỉ liệt kê artifact hiện có với `cache_validated=false`; không khẳng định cache cũ phù hợp với chunk mới. Không gọi mô hình hay tạo graph, không trả dự toán. Bỏ `--dry-run` để chạy qua cache; thiếu cache thì chốt chi dừng trước lời gọi. Chỉ thêm `--allow-spend` sau khi được phép chi.

Worker gọi `build_document_runner(settings, recorder=callback)` rồi `execute(path, doc_id, progress=..., cancelled=...)`. Callback nhận `BuildResult` ở mọi kết thúc, kể cả lỗi/huỷ/từ chối. Đây là chỗ W-14 ghi PostgreSQL cùng actor/build_id của web. CLI mặc định dùng SQLite stdlib tại `artifact_dir/builds.sqlite3`, bảng `build_runs`, mỗi lượt thử một hàng.

Usage được đo từ sự kiện HTTP/token thực trả của adapter trong lượt hiện tại, gồm generation, embedding, repair/retry và phản hồi trước lỗi. Không cộng chi lịch sử trong manifest. Giá quy đổi dùng bảng giá hiện có; không thay thế hoá đơn nhà cung cấp. Thiếu token thì `usage_complete=false`; cờ thiếu của lượt trước không làm sai lượt cache mới. Thời gian ghi là thời gian thực chạy, không phải dự toán.

## Kiểm thử và bằng chứng

| Kiểm | Kết quả |
|---|---|
| Nhóm W-13 (core, pipeline, CLI, fake, SQLite) + bộ đọc thật | **65 đạt** (59 unit + 6 integration), 23,58 giây; `tmp/w13-final-acceptance.log`, XML cùng tên |
| Kiểm trước commit, thêm ca doc-6 cache miss + kiến trúc | **68 đạt** (66 W-13 + 2 kiến trúc), 19,98 giây, không failure/error/skip; `tmp/w13-precommit.xml` |
| Bộ đọc thật và hợp đồng real/fake, cấm mạng | 6 đạt; bao gồm doc-6, hai PDF tiếng Anh, ảnh quét, cache canonical và hợp đồng bộ giả |
| Toàn bộ `tests/unit` | **1868 đạt**, 2 cảnh báo SWIG, 254,16 giây; `tmp/w13-full-final.log`, XML cùng tên |
| Đột biến bỏ label-roles | Bắt được: assertion thứ tự fail |
| Đột biến chuyển label-roles sau canonical | Bắt được: assertion thứ tự fail |
| Đột biến bỏ kiểm sớm | Bắt được: PDF tiếng Anh/bản quét giả không còn bị từ chối, assertion fail |
| Đột biến nối Developer API thay Vertex | Bắt được: assertion tham số cả hai adapter fail |
| Compile/import và `git diff --check` các tệp liên quan | Đạt; chỉ có cảnh báo LF/CRLF của Git trên Windows |

Các đột biến chỉ chạy trong tiến trình thử, không sửa tệp nguồn; `scripts/w13_mutations.py` đòi đúng mã thoát `TESTS_FAILED`, không nhận lỗi collection làm bằng chứng. Kết quả ở `tmp/w13-mutations/results.json`.

Lệnh nghiệm thu chính:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m pytest tests/unit -p no:cacheprovider --basetemp=tmp/w13-full-final --junitxml=tmp/w13-full-final.xml
.\.venv\Scripts\python.exe -X utf8 -m pytest tests/integration/test_w13_build.py -p no:cacheprovider --basetemp=tmp/w13-reader-tests
.\.venv\Scripts\python.exe -X utf8 scripts/w13_mutations.py
.\.venv\Scripts\python.exe -X utf8 -m pytest tests/unit/application/test_build_document.py tests/unit/application/test_build_pipeline.py tests/unit/infrastructure/test_build_log.py tests/unit/infrastructure/test_fake_build_runner.py tests/unit/presentation/test_build_cli.py tests/integration/test_w13_build.py tests/unit/test_architecture.py -p no:cacheprovider --basetemp=tmp/w13-precommit --junitxml=tmp/w13-precommit.xml -q
```

Các assertion chính:

- `test_runs_steps_in_order_preserves_metadata_and_records_usage_delta`: đủ label-roles/A3/A3′/canonical/graph/prep và không lưu toàn văn vào log.
- `test_cancel_after_concepts_prevents_graph_and_retry_reuses_completed_work`: huỷ chặn graph; lỗi graph rồi thử lại không tăng lời gọi những phần đã cache.
- `test_input_gates_reject_before_pipeline_steps`, các test biên 150/200 chữ, 50% trang trống, tỉ lệ dấu 0,01: kiểm cả nhánh chặn và nhánh được phép.
- `test_read_preserves_empty_pages_and_rejects_cached_quality_override`: giữ trang trắng khi đo, không kế thừa lý do bỏ qua chữ lỗi.
- `test_canonical_coverage_none_does_not_read_gold_fixture`: đường không vàng không thể gọi `load_gold`.
- `test_direct_canonical_reuses_doc6_without_gold_or_other_books`: kho tạm chỉ chứa doc-6, canonical v3 `reused=true`, băm cấu hình bằng bản CLI trước, 0 lời gọi; manifest gốc không bị sửa. Bản cache cũ giữ metadata vàng lịch sử, không viết lại nó thành null.
- `test_real_and_fake_share_the_dry_run_contract`: cùng trạng thái/bốn sự kiện tiến trình, chỉ hoàn tất đọc, 0 USD và không ghi graph.
- `test_fake_graph_version_is_latest_loadable_complete_graph`: không chọn graph mới nhất chưa hoàn tất; artifact đích nạp được, nguồn nguyên vẹn, ảnh công thức đúng doc_id.
- `test_failed_build_records_priced_generation_and_embedding_usage`: truy vấn SQLite độc lập thấy 3 lời gọi giả, 350 token vào/70 ra và 0,0001875 USD quy đổi, kể cả khi bước graph lỗi.

## Lệnh đã chạy trên doc-6

Chạy CLI với `DOC2ROADMAP_ARTIFACT_DIR=tmp/w13-cli-acceptance/artifacts`, Vertex project giả `offline-acceptance`; không có quyền chi:

| Lượt | Exit | Trạng thái | Model calls | USD | Graph mới |
|---|---:|---|---:|---:|---|
| `build --file doc-6.pdf --doc-id doc-6 --dry-run` | 0 | dry_run | 0 | 0 | không |
| bỏ `--dry-run`, vẫn không có `--allow-spend` | 1 | failed / SpendNotAllowed ở concepts | 0 | 0 | không |

SQLite có đúng các hàng `dry_run`/`failed`, đều 0 lời gọi và 0 USD. JSON/stderr ở `tmp/w13-cli-acceptance/`. Đây là phép kiểm cache miss dừng trước khi chi, **không** chứng minh hoàn tất toàn bộ chuỗi mới từ cache cũ.

### Tái lập doc-6 ở mức 0 USD cho người soát

Từ gốc repo, với `.venv`, `doc-6.pdf` gốc và hai mô hình bộ đọc nhẹ trong `vendor/a1-nhe/` đã có cục bộ:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m pytest tests/integration/test_w13_build.py -k 'doc6_dry_run or doc6_missing_role_cache' -p no:cacheprovider --basetemp=tmp/w13-doc6-reproduce --junitxml=tmp/w13-doc6-reproduce.xml -q
```

**Kết quả đã chạy: 2 đạt, 0 lời gọi nhà cung cấp, 0 USD.** Mỗi test dùng kho artifact và SQLite tạm riêng, không nạp `.env`, dùng Vertex project giả và chặn cả API sinh, embedding lẫn lấy header ADC. Test thứ nhất đọc thật/dry-run, không tạo graph. Test thứ hai chạy chuỗi thật không có quyền chi: chứng minh đã vào `label_roles`, dừng với `SpendNotAllowed` ở `concepts`, chưa chạy A3/graph, rồi truy vấn SQLite độc lập thấy `failed`, 0 lời gọi, 0 USD. Exit 0 của pytest là phép kiểm hành vi dừng đúng đã đạt; kết quả bản dựng vẫn là `failed`.

**Cache đang thiếu:** cache nhãn tương thích với chunk do bộ đọc nhẹ vừa tạo. Ở kho nghiệm thu `tmp/w13-cli-acceptance/artifacts`, chunks v1 có `config_hash=bf363bcf0c60f814fc706670a01736b7f474173f55d78f0f45de9d0144171b0e`, chưa có bản nhãn nghĩa. Kho lịch sử có bản nhãn v4 dựa trên chunks v2 (`roles_from_chunks_version=2`); đó không phải cache nhãn cho chunk Nhe mới. Cùng `source_hash` của PDF không đủ để coi hai cấu hình chunk/nhãn là tương thích. Không đổi tên cache, chép nhãn giả, bỏ `label-roles`, thay bộ đọc hay nới cổng chữ để ép qua.

Muốn hoàn tất toàn chuỗi ở 0 USD phải cung cấp cache/checkpoint **đúng cấu hình hiện hành** cho nhãn và các bước tiếp theo, rồi chạy lại `build` không có `--allow-spend`. Lượt hiện tại chỉ xác định được điểm thiếu đầu tiên; không khẳng định các bước sau đều cache hit. Chưa có con số xin duyệt cho lượt có tiền, chưa được phép chi. Nếu không tìm được cache phù hợp, cần lập bảng phần việc chưa có cache và con số đề nghị riêng cho chủ dự án trước khi bật `--allow-spend`; không dùng số 0 của phép kiểm dừng làm chi phí dựng xong cuốn.

## Hiệu chỉnh kiểm sớm

Phép đo `scripts/w13_calibrate.py`, kết quả `tmp/w13-calibration/measurements.json`. Chỉ dùng sáu ID phát triển đã cho; không mở tập giữ lại.

| Cuốn | Nguồn đo | Trang | Chữ cái/trang | Trang trắng | Tỉ lệ dấu | Cảnh báo chữ |
|---|---|---:|---:|---:|---:|---:|
| doc-1 | PDF gốc, Nhe | 102 | 806,549 | 0% | 21,819% | 0 |
| xstk-ch3-1 | PDF gốc, Nhe | 59 | 949,136 | 0% | 27,802% | 2 |
| doc-4 | PDF gốc, Nhe | 214 | 2010,808 | 0% | 29,388% | 0 |
| nhap-mon-ml | PDF gốc đã khôi phục, Nhe | 20 | 1263,9 | 0% | 26,929% | 0 |
| naive-bayes | PDF gốc, Nhe | 36 | 183,278 | 0% | 18,885% | 2 |
| doc-6 | PDF gốc, Nhe | 25 | 179,8 | 0% | 24,071% | 0 |
| English 1 (test tạo) | PDF chữ | 1 | 540 | 0% | 0% | 0 |
| English 2 (test tạo) | PDF chữ | 1 | 600 | 0% | 0% | 0 |
| PDF chỉ ảnh (test tạo) | PDF ảnh | 1 | 0 | 100% | 0% | chặn native PDF |

Chọn `scan_min_chars_per_page=150` để không loại slide doc-6; giữ `scan_max_empty_page_ratio=0.5`, `vi_min_diacritic_ratio=0.01`. Không hạ cổng chất lượng chữ để ép xstk/naive-bayes qua. Các số trên là hiệu chỉnh tập phát triển, không phải chứng minh độ chính xác bộ phân loại ngôn ngữ trên mọi tài liệu.

**Hai giới hạn W-13 đã xử lý:** tìm được PDF gốc nhap-mon-ml ở đường dẫn đã ghi trong tài liệu repo, SHA-256 khớp `d5a78c95b7603bffff77d6675c0286beaeb997f5633ac9e598bccb25305d3f71`, đo lại đủ 20 trang; doc-6 đã hoàn tất sau duyệt chi và tái lập thành công ở 0 USD. Việc nối PostgreSQL, UI thả tệp/xác nhận và worker web thuộc W-14/nhóm web.
