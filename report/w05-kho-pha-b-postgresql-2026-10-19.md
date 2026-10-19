# W-05 — Kho Pha B PostgreSQL

Ngày 2026-10-19. Nhóm lõi triển khai trên nhánh `work/w05-postgres`, worktree `tmp/w05-postgres`, từ nền W-01 `c91551f`. W-13 đã hoàn tất theo báo cáo riêng; không mở lại phần doc-6. Chi phí mô hình của W-05: **0 USD**.

## Phần bàn giao

| Mốc | Commit / nội dung |
|---|---|
| Nền web | `c91551f` — W-01 |
| Port và lõi | `b3e9c5f` — lọc usage, ẩn danh, truy vấn trần ngày vẫn cộng reservations |
| Migration | `0602768` — bốn bảng, chỉ mục, kiểm baseline và HEAD |
| Adapter và nối dây | `e163815` — CRUD, khóa process, negative TTL, composition, regression |
| Sửa isolation | `8600e27` — test đọc snapshot độc lập; `atomic()` dùng READ COMMITTED trên connection |

Migration hiện hành: `w01_0001 → w05_0002`. Nhóm W-02 dùng `down_revision = "w05_0002"` cho `w02_0003`. Test kiểm đúng một head và nâng DB rỗng lên HEAD đã đạt trên nhánh W-05. **Việc ghép và kiểm lại cùng migration W-02 còn thuộc checkpoint tích hợp của hai nhóm**, chưa nhận đã nghiệm thu thay nhánh W-02.

Không nhập hoặc sửa `artifacts/phase_b/live.json`. SQLAlchemy/psycopg nằm ở `wayfinder`; CLI lõi tiếp tục dùng JSON. Không thêm phụ thuộc vào lõi, không thay luật/trần SA-47/48.

## Thiết kế được cài

- Bốn bảng: `phase_b_cache`, `phase_b_negative`, `phase_b_record`, `usage_ledger`. Migration cố định DDL riêng, không import metadata ứng dụng có thể thay đổi về sau.
- Record giữ nguyên `value`; cột `owner`/`doc_id` chỉ là phép chiếu để lọc. Ghi đè record không có hai trường này sẽ xóa phép chiếu cũ.
- `usage_ledger.extra` giữ **toàn bộ dict gốc**, kể cả trường đã có cột. Cách này giữ float nhỏ hơn độ chính xác `numeric(12,6)`, cách viết timestamp, khác biệt thiếu khóa/null và trường lạ. Cột tách riêng phục vụ lọc/chỉ mục; đọc qua port trả dict gốc. Các phép cộng đòi độ chính xác theo port nên dùng dữ liệu qua port, không coi tổng cột numeric đã làm tròn là bản sao chính xác mọi float gốc.
- `usage_rows` kết hợp các bộ lọc bằng AND; `since` bắt buộc có múi giờ; `purposes=set()` trả rỗng. Ẩn danh cập nhật cả cột và JSON learner_id thành `deleted`, giữ nguyên tiền và trường khác.
- `single_flight`: `_Flight` trong process → session advisory lock trên pool riêng → đọc lại cache/negative → mới sinh. Có timeout chờ pool/khóa; timeout lấy khóa không tạo negative và không chạy generator. Unlock được kiểm tra; lỗi unlock làm connection bị invalidate.
- Negative lưu chung trong DB, TTL tính theo đồng hồ DB. Chỉ khôi phục exception từ danh sách lớp đã đăng ký; loại lạ thành `RuntimeError` với tên loại/câu báo, không import tùy ý.
- `atomic()` dùng transaction advisory lock chung của kho Pha B. Ngữ cảnh lồng dùng chung connection/transaction; lỗi ngoài cùng rollback. Khóa chung là lựa chọn nhỏ nhất theo port chưa có scope khóa, có thể giới hạn thông lượng nếu nhiều cập nhật DB đồng thời; không giữ nó quanh lời gọi nhà cung cấp.
- `atomic()` đặt `READ COMMITTED` trên connection riêng cho giao dịch, giữ nguyên isolation mặc định của engine. Test hồi quy phát hiện engine `REPEATABLE READ` có thể giữ snapshot cũ sau khi chờ khóa; phép đọc sau phải nhìn thấy cập nhật vừa commit từ connection khác.
- Composition web tạo store PostgreSQL, pool khóa riêng cấu hình bằng `WAYFINDER_PHASE_B_LOCK_POOL_SIZE` (mặc định 8); timeout khóa lấy từ `BSettings.lecture_click_timeout_seconds`. Không dùng pool dữ liệu để giữ session lock trong suốt lúc sinh.

## Kind thực tế và trường owner

Quét các lệnh get/put/list/delete record của lõi và preview Pha B; không đóng enum `kind` trong DB.

| Kind | owner ở mức trên cùng | Ghi chú |
|---|---|---|
| `answer` | Có | Kèm doc_id |
| `assistant_state` | Có | State khởi tạo có owner/doc_id; khi ghi giữ lại qua phép gộp state |
| `documents` | Có | Kèm doc_id |
| `feedback` | Có | Đường preview, kèm doc_id |
| `progress` | Có | Kèm doc_id |
| `quiz_attempt` | Có | Kèm doc_id |
| `session` | Có | Kèm doc_id |
| `turn` | Có | Kèm doc_id |
| `lecture_failure` | Không | Có doc_id |
| `module_assignment` | Không | Đường composition Pha B, có doc_id |
| `quiz_hidden_question` | Không | item_id/hidden |
| `quiz_question_report` | Không | Owner chỉ ở các phần tử reports |
| `spend_reservation` | Không | learner_id thay owner; không có doc_id |

Không tự thêm owner vào dict của những kind không có trường này. Cột phép chiếu nullable theo đúng payload.

## Lệnh tái lập

Khởi động PostgreSQL `db-test` của W-01; cấu hình `WAYFINDER_TEST_DATABASE_URL` hoặc `src/web/.env` cục bộ. Runner không in URL/mật khẩu, tạo DB UUID riêng cho từng phiên rồi drop DB đó. Không chạy vào DB phát triển.

```powershell
python -X utf8 scripts/w05_run_tests.py src/web/backend/tests --junitxml=tmp/w05-backend-final.xml
python -X utf8 scripts/w05_run_tests.py src/web/backend/tests/test_postgres_phase_b_store.py src/web/backend/tests/test_postgres_phase_b_concurrency.py src/web/backend/tests/test_postgres_phase_b_regressions.py tests/unit/application/test_phase_b_store.py tests/unit/application/test_phase_b_progress_sa47.py tests/unit/application/test_phase_b_budget_sa48.py --junitxml=tmp/w05-acceptance-final.xml
```

Runner đặt PYTHONPATH trỏ vào mã của worktree. Chạy riêng lõi bằng `PYTHONPATH=src` và `python -X utf8 -m pytest tests/unit`. Những test phát triển đã có cần artifact doc-1/doc-6 và PDF gốc `doc-1.pdf`; worktree dùng lại đúng dữ liệu phát triển này. Không mở bộ held-out, không sửa kỳ vọng để bỏ yêu cầu dữ liệu.

## Kiểm chứng

| Phép kiểm | Kết quả / assertion |
|---|---|
| Hợp đồng dùng chung | Sáu test nguyên hàm trên mỗi backend: memory 6, JSON 6, PostgreSQL 6; không đổi kỳ vọng có sẵn |
| Bộ tập trung W-05 + SA-47/48 | 73 đạt; xem evidence XML/summary |
| Toàn backend W-01/W-05 | 95 đạt, 1 bỏ qua: Cloudinary live opt-in có sẵn, không phải test W-05 |
| Toàn unit lõi trên nền c91551f | 1.829 đạt, 0 bỏ qua, 0 lỗi; 366,61 giây |
| Hai process sinh cùng khóa | `test_two_processes_generate_once`: generator đúng 1 lần, hai kết quả giống nhau |
| Negative liên process | `test_negative_cache_shared_across_processes_then_expires`: A ghi lỗi, B nhận đúng ValueError/câu báo, không sinh; hết TTL thì sinh lại |
| Tranh ngân sách cuối | `test_two_processes_cannot_reserve_the_last_budget_twice`: đã chi 0,10; hai yêu cầu 0,08 trên trần 0,20 chỉ nhận một; tổng đã chi + giữ chỗ không vượt trần |
| Khóa lồng/rollback | `test_atomic_nested_transaction_and_rollback`; lỗi rollback, lần sau vẫn ghi được |
| Isolation | `test_atomic_uses_fresh_snapshots_even_when_engine_default_is_repeatable_read`; đọc thấy cập nhật mới, engine ngoài vẫn REPEATABLE READ |
| Pool/timeout | `test_generation_uses_separate_pool_and_releases_lock`, `test_lock_timeout_does_not_generate_or_poison_cache` |
| Trợ lý đồng thời | Gọi lại test đồng thời gốc với store PostgreSQL, giữ nguyên assertions |
| SA-47/48 PostgreSQL | Import lại test tiến độ/giữ chỗ/lỗi/qua ngày/replay gốc; test late provider bổ sung riêng cho PostgreSQL |
| Thiếu PostgreSQL | `--require-postgres --collect-only` khi bỏ cấu hình: exit 4, không báo xanh bằng skip |
| Composition | Bỏ nối store làm test đỏ; khôi phục đạt, health và CRUD dùng PostgreSQL thật |

**Thử phá guard:** biến `W05_DISABLE_FLIGHT_LOCK=1` ở test harness thay truy vấn khóa bằng SELECT 1: test đỏ vì generator chạy 2 lần. `W05_DISABLE_ATOMIC_LOCK=1`: test đỏ vì nhận cả hai yêu cầu. Biến này chỉ tồn tại ở test, không có nhánh bỏ khóa trong mã sản phẩm. Bỏ cấu hình isolation của `atomic()` cũng làm test snapshot đỏ; luôn khôi phục mã sau phép thử. Bằng chứng đỏ giữ riêng, không trộn với lượt xanh.

**Điều chỉnh test PostgreSQL:** test late provider gốc dùng timeout 30 ms vẫn giữ nguyên cho memory/JSON. Thử gọi nguyên test đó trên PostgreSQL đã đỏ vì DB chưa khởi động provider trước timeout. Bản bổ sung PostgreSQL dùng 300 ms, vẫn buộc provider bị giữ đến sau timeout, kiểm còn reservation, yêu cầu khác bị chặn, release xong ghi usage 0,12 đúng một lần và hết reservation. Không bỏ test cũ hoặc hạ assertion về tiền.

**EXPLAIN:** dữ liệu giả 20.001 dòng; truy vấn learner/day/purposes thực tế dùng `Bitmap Index Scan` trên `ix_usage_learner_day`, trả một dòng, không Seq Scan ledger. Không tắt seqscan hay ép planner. Kế hoạch đầy đủ: [w05-evidence/explain.json](w05-evidence/explain.json). Thời gian trong kế hoạch là phép đo cục bộ, không phải SLA.

Bảng đếm lấy từ JUnit thật: [w05-evidence/summary.json](w05-evidence/summary.json). XML backend, tập trung và các lượt đỏ được lưu cùng thư mục; không cộng các lượt trùng nhau thành tổng test độc lập. Lượt full unit đầu có bốn lỗi thiếu artifact/PDF trong worktree; bổ sung dữ liệu phát triển rồi cả bốn chạy riêng đạt, sau đó full unit đạt như trên. Không sửa test để chữa lỗi môi trường.

Review tại commit mã `8600e27` đã kiểm phạm vi diff, câu SQL bind tham số, whitelist exception, giải phóng session lock, rollback/ngữ cảnh lồng, isolation và bộ lọc vẫn tính reservations. `git diff --check` đạt. Người soát độc lập vẫn là bước tiếp theo.

## Giới hạn bàn giao

- Cần nhóm web ghép chuỗi migration W-02 rồi chạy lại một-head/DB-rỗng trên nhánh hợp nhất; vé giữ tiêu chí tích hợp này mở.
- Khóa atomic chung ưu tiên tính đúng theo port hiện tại; chưa tối ưu khóa theo learner/document.
- Các usage có số USD trong test là dữ liệu giả. Không gọi mô hình/ADC hay Cloudinary thật trong lượt nghiệm thu W-05; không phát sinh hóa đơn.
- Báo cáo và test này chuẩn bị cho người soát độc lập; không tự mở W-06 hoặc W-15.
