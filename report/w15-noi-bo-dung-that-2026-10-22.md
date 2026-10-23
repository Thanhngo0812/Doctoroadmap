# W-15 — adapter/composition và kiểm 0 USD — 2026-10-22

## Tiếp nhận sau mốc `6627c00` — main `f96fc00`, 2026-10-23

Đã giữ worktree/nhánh W-15 và nhận main **`f96fc0056e3c5e7316a5ce368fd5680b5aaba6e9`** bằng fast-forward. Mốc web `6627c00` đã được người điều phối nghiệm thu/ghép qua **`e85427a`**; không làm lại adapter/trace accounting. Handoff mục 8 trên main đã ghi đề nghị Claude nhận nền web vào SA-62 và kiểm cổng đúng đỉnh.

**SA-62 `266dbdc` chưa là tổ tiên của main tại lần kiểm này.** Không nhận nhánh SA-62 chưa ghép, không sửa hai tệp composition, không còn coi việc chọn người port là điểm chờ. Điểm chờ hiện tại là Claude nghiệm thu/ghép đúng port. Trong lúc đọc hiện trạng có cổng SA-64 đang chạy; không khởi động chồng cổng PostgreSQL. Đợt này chỉ thêm báo cáo/bằng chứng, không đổi mã sản phẩm, schema hay test đã nghiệm thu.

### Kiểm có thể hoàn tất trước port

Lệnh đã chạy, native exit **0**: `python -X utf8 report/w15-evidence/pre-port-20261023/audit.py`, tại worktree W-15 bằng Python của `.venv` chung. Script tự đặt đường nạp về chính `src/` và backend của worktree; đây là audit metadata/preflight, **không phải pytest hoặc dry-run BuildDocument**. [Kết quả](w15-evidence/pre-port-20261023/result.json).

| Quan sát có nguồn | Kết quả và phạm vi |
|---|---|
| Manifest doc-1/doc-6 được ghim | SHA `5fc819f723f7263fe3d443ec780009a75aae66f2c35db8fe0bc3e3c50464eb84`; 127 tệp doc-6 đối chiếu SHA trước/sau, không links, không thay dữ liệu |
| Graph nguồn | `doc-6` v29, 2 module/27 chunk; chunks v4, parse v2, retrieval v1 |
| Fingerprint retrieval với chunk nguồn | Khớp: `d3eb66232372c65f42c6f691d968b09109c38a9791c20a07ea921874cc6faaba`. Đổi text của một document chỉ trong bộ nhớ bị `assert_retrieval_compatible` từ chối |
| Parser của parse nguồn | `docling:2.114.0+pypdfium2`, adapter version 8; không suy thành parse của bộ đọc nhẹ mặc định hiện hành |
| Hash nguồn so với parse manifest | Khớp `82cb494d407c4755d29deb7c08b9a4f3794f79e241c307fd2b5dfc149cd559c7` |
| Identity web | `u-82cb494d407c4755d29d`; **0/6** thư mục parse/chunks/candidates/canonical/graph/retrieval trong bản sao có ID đó. Đây là miss đường dẫn/identity trong phạm vi bản sao, không phải kết luận mọi cache miss |
| Cache sinh/embedding, chi/gọi/phút để dựng qua web | **Chưa biết**; không đọc learner cache/live.json. Không đổi ID/version, không cam kết doc-6 miễn phí |
| Preflight factory mặc định | Main chưa có tham số `phase_b_store`; `RealBuildRuntime` từ chối trước truy cập engine/provider. Chặn constructor JSON/SQLite, ADC/provider/SMTP/Cloudinary trong preflight |
| Attempt/collector/queue | Không chạy execute; 0 collector receipt, 0 queue claim, 0 provider call/0 USD. Không đưa dry_run vào queue hoặc đổi course ready |

### Phần tiếp theo sau SA-62 được ghép, để người điều phối nhận qua handoff

Mốc chuẩn bị đã xong: adapter và trace/test âm `6627c00` đã ghép, nhận nền web mới, kiểm lại dữ liệu/fingerprint nguồn/preflight an toàn. Handoff main đã có yêu cầu nhận nền web; chỉ ghi báo cáo cho chủ dự án, không gửi tin sang phiên khác hoặc tự sửa handoff của điều phối.

Ngay khi SA-62 ở main: ca dương phải tạo default `RealBuildRuntime`/`make_worker` không có factory giả thay thế, trước provider; giữ `PipelineWithoutStorePort` cho ca âm. Sau đó chạy DocumentPipeline thật với model/embedding fake và PG độc lập, kiểm tên/cache/A12/session/spend guard/usage/receipt/huỷ/lease/identity. Không dùng ca `lecture` làm bằng chứng guard build; không sửa `budget.py`. Artifact Pha A vẫn là tệp. SA-65 nếu cung cấp dữ liệu mới phải nhận manifest/SHA mới và chép riêng, không ghi đè gói này.

**Chưa chạy dry-run thật** vì điều kiện nhận port chưa thoả. Sau kiểm fake/PG mới chạy dry-run nội bộ ở kho bản sao riêng, collector, `allow_spend=False`, guard mạng; giữ chuỗi đọc nhẹ → kiểm chữ → label-roles → A3/A3′ → A4 vi/coverage none → roadmap → learning_prep. Bảng cuốn mới/SHA/52 trang phía dưới vẫn là ứng viên; các số gọi/USD/phút/embedding wait/trần chưa biết giữ nguyên. Không mở chi hoặc xin đóng toàn W-15 trong lượt này.

## Cập nhật 2026-10-23 — tiếp nhận nghiệm thu và hợp đồng SA-62

Mốc adapter/test cũ **đã được điều phối nghiệm thu và ghép**: `eea5472` → `d12b67c`, 2.266 Python/104 React/build xanh. Không giao lại phần đã đạt. Worktree/nhánh W-15 giữ nguyên, đã nhận main **`50a8035ed040f3114239cd214aa9bca9669e5918`**. Các mục sau phần cập nhật này lưu nguyên hồ sơ lượt 2026-10-22.

### Port đã có người nhận, chưa ghép main

Claude chốt SA-62 tại mục 8 handoff: hai tệp composition do làn Claude sở hữu, nhân viên W-15 không sửa. Chữ ký vẫn `DocumentPipeline(settings, *, allow_spend, phase_b_store=None)` và `PhaseBRuntime(..., store=None)`. Delta meter là nguồn chi build duy nhất; usage con mang `counted_in="build"` chỉ là trace. Callback snapshot của adapter không cần đổi `BuildDocument`.

Đã đọc báo cáo SA-62 ở nhánh `work/sa62-port-kho-pha-b`, mốc `071fce7`, **chỉ đọc, không nhận mã chưa nghiệm thu**. Cổng của nhánh đó có hai test W-15 đỏ vì khẳng định port thật chưa tồn tại. Đã sửa hai ca âm bằng factory `PipelineWithoutStorePort`: vẫn phải từ chối trước constructor/claim/provider, không phụ thuộc việc core đã thêm port hợp lệ. Ca dương bằng pipeline tiêm vẫn chạy; chưa coi đó là kiểm toàn pipeline thật. Khi SA-62 lên main phải kiểm tiếp bằng factory mặc định và engine PG độc lập.

### Phần web bổ sung: trace không cộng chi lần hai

`PostgresPhaseBStore.append_usage` giữ **nguyên dict gốc** trong `extra`; `usage_rows()` vẫn trả raw cho đối soát/spend guard. Với đúng `counted_in="build"`, các cột cộng sổ `cost_usd`, `input_tokens`, `output_tokens` bằng 0. Receipt `purpose=build` ghi tổng meter một lần như cũ. Dòng không cờ/cờ khác giữ cách ghi cũ. Không migration, không sửa số lịch sử.

SQL tính chi/token đọc các cột typed; nếu đọc raw `extra` hoặc `usage_rows()` để báo cáo chi/calls thì phải lọc `counted_in != "build"`. Không lấy tổng raw gồm trace làm chi provider. Test dùng chi giả khác 0 và connection PG độc lập: trace vẫn đọc đúng từng giá trị; tổng ledger chỉ còn tổng meter, receipt không nhân đôi. Với purpose mà DailySpendGuard hỗ trợ, trace raw vẫn gây từ chối thật khi vượt trần, không chỉ kiểm flag.

**Giới hạn đã xác minh từ mã và báo cáo SA-62:** `DailySpendGuard.check` chỉ tính `assistant/document/lecture/quiz_gen/quiz_verify`; không tính `module_title/embedding` dù có hay không có cờ. Không tuyên bố những purpose này đã được guard đó chặn. Khâu build có guard `purpose=build` riêng trong web. Không tự sửa `budget.py`; cần người soát đối chiếu giới hạn này với câu giao về trần ngày trước lượt thật.

| Lượt bổ sung | Kết quả | Bằng chứng |
|---|---|---|
| RED trên kho PG cũ | **2 assertion fail, 2 control pass**, exit 1, không lỗi setup; tổng sai `.005` thay `.003` | [JUnit](w15-evidence/runs/trace-red-20261023.xml), [log](w15-evidence/runs/trace-red-20261023.log) |
| GREEN trace/adapter/W-25/kho PG | **67 pass** | [JUnit](w15-evidence/runs/trace-green2-20261023.xml) |
| GREEN sau sửa ca âm tương thích port | **67 pass**, native exit 0 | [JUnit](w15-evidence/runs/compatibility-green-20261023.xml) |
| Mutation trên `dba19e5` | **15/15 bị bắt bằng assertion**, 0 setup error; phục hồi nguồn cùng byte | [Kết quả](w15-evidence/mutations/20261023/mutations.json), [native exit](w15-evidence/runs/mutations-20261023-exit.json) |
| React/build trên `dba19e5` | **104 pass**, build native exit 0 | [JUnit](w15-evidence/runs/react-20261023.xml), [build](w15-evidence/runs/frontend-build-20261023.log) |
| Python/PostgreSQL toàn repo trên `dba19e5` | **2.275 pass, 1 Cloudinary live không bật**, 0 fail/error, native exit 0 | [JUnit](w15-evidence/runs/full-20261023.xml), [log](w15-evidence/runs/full-20261023.log), [commit/argv/SHA/native exit](w15-evidence/runs/full-20261023-exit.json) |

Mã bổ sung được commit tại **`dba19e508631cb2d81f6c69b0a8709d13835ef9b`**, chỉ có năm tệp trong `src/web/`. [SQL cộng chi](w15-evidence/sql/compatibility-green-20261023/single-build-charge.json) cho tổng `.003 USD`, 300 input/60 output, 3 calls ở receipt; hai trace raw `.001 USD` mỗi dòng có chi typed 0. [SQL guard](w15-evidence/sql/compatibility-green-20261023/trace-build.json) giữ raw `.003 USD` và từ chối reservation ở trần `.002 USD`. Đây đều là số fake, provider 0 USD; không phải số đo cuốn mới.

Pytest 495,08 giây, wrapper 508,27 giây là thời gian cổng, không phải phút/cuốn. [SQL cổng cuối](w15-evidence/sql/full-20261023/) và [W-25 SQL](w15-evidence/w25-regressions/full-20261023/) đọc từ PostgreSQL độc lập. Giữ nguyên 265 tệp bằng chứng cũ đã được soát; phần mới có [tổng hợp riêng](w15-evidence/summary-20261023.json), [manifest SHA-256](w15-evidence/manifest-20261023.json) và [chuẩn hoá UTF-8/LF](w15-evidence/normalization-20261023.json). Các export lịch sử W-06/W-14 do test ghi đè đã chép vào `regression-exports/20261023` rồi khôi phục. Mã không đổi sau mốc cổng; commit hồ sơ tiếp theo chỉ chứa báo cáo/bằng chứng. Bản bổ sung này chờ người điều phối soát, nhân viên không tự ghép main.

Lượt `trace-green-20261023` native exit 4 do gọi sai tên hai tệp test, không có test chạy. Giữ log/XML, không tính là GREEN; lệnh đúng ở `trace-green2-20261023`.

### Identity/cache và ứng viên: chỉ đọc metadata được phép

Đã rà **92 manifest** trong bản sao sáu cuốn, kiểm lại SHA-256 từng manifest trước đọc. Hash PDF doc-6 xuất hiện dưới đúng alias `doc-6`; hash ứng viên `rau-thuy-canh.pdf` không xuất hiện trong metadata bản sao này. Cả hai ID `u-82cb494d407c4755d29d`/`u-1f019766e74a747d293c` chưa có thư mục artifact trực tiếp ở sáu loại parse/chunk/candidate/canonical/graph/retrieval trong bản sao. Đây là **miss về định danh/đường dẫn trong phạm vi được phép**, không chứng minh toàn bộ cache mô hình miss hoặc cuốn mới cold toàn cục.

Alias ngoài bộ sáu cuốn, cache sinh/embedding, số gọi/USD/phút/trần vẫn **chưa biết**. Không mở learner cache/live.json/tập giữ lại hoặc in nội dung cache. [Kết quả metadata](w15-evidence/cache-metadata-20261023.json); lệnh đã chạy: `PYTHONPATH=<worktree>/src/web/backend python -X utf8 src/web/backend/tests/w15_cache_metadata.py`. Script chỉ đọc metadata manifest đã xác minh, không phải dry-run pipeline.

**Chưa chạy dry-run thật, chưa chạy doc-6 thật qua web, chưa có tiền hoặc lượt mới được duyệt.** Bảng đề nghị cuốn 52 trang/SHA-256 và các số chưa biết bên dưới vẫn giữ hiệu lực. Toàn W-15 chưa hoàn tất. Việc tiếp sau SA-62 lên main: kiểm xuyên pipeline thật/PG và nguồn chi duy nhất, rồi dry-run trong bản sao riêng/collector web/network guard; không đưa dry-run vào queue/course ready.

## Phạm vi, kế hoạch và nền

Nhánh `work/w15-real-build`, worktree một cấp `tmp/w15-real-build`, từ main `157cbb3`. W-14 đã được nghiệm thu tại `61b5d80`, ghép `7fe63df`. Giữ mọi worktree W-14/W-25; không tự ghép main, không sửa task/kế hoạch/handoff, không sửa ké SA-54/56/57.

Main cập nhật trong lúc chạy cổng đầu tiên: đã nhận `fd185ba99e404864ca59390a151ef4a7916d1d63` bằng merge trên nhánh W-15, tạo **`446caba3e3ab608ad1ad56108fabac6e6c539398`**. Đây là mã nền kiểm lần cuối. Các thay đổi SA-56/57 chỉ được nhận từ main đã duyệt; W-15 không sửa các tệp đó.

Giai đoạn này: adapter/composition web, test fake và PostgreSQL thật, kiểm cache/identity trên bản sao manifest; chi dịch vụ ngoài 0 USD. Chưa mở lượt có tiền hoặc nhận W-15 hoàn tất.

1. Chốt đề nghị port trước sửa lõi → xác minh chữ ký/đường dẫn và test cần có.
2. Cài adapter web và kiểm RED/GREEN → dùng BuildDocument với pipeline được tiêm, không tạo JSON/SQLite ngầm.
3. Kiểm usage/lease/transport/cache và guard W-25 → SQL độc lập; full gate qua runner; báo rõ phần chưa đo.

## Đề nghị port để điều phối phối hợp Claude qua mục 8 bàn giao

**Đã ghi trước khi triển khai adapter; chưa sửa bất kỳ tệp lõi nào.** Chủ dự án yêu cầu chỉ ghi báo cáo, không gửi tin nhắn trực tiếp sang phiên điều phối. Những chữ ký sau là đề nghị, chưa được nhận là đã cài/được phiên Pha A chấp thuận.

| Đường dẫn/chữ ký | Thay đổi đề nghị | Test nghiệm thu port |
|---|---|---|
| `src/doc2roadmap/composition_build.py::DocumentPipeline.__init__(settings, *, allow_spend, phase_b_store=None)` | Nhận kho Pha B từ composition web. Khi được tiêm, roadmap/name/concept-index và runtime con dùng đúng kho đó. CLI giữ mặc định riêng; web không gọi nhánh mặc định | Chặn constructor JsonPhaseBStore/SqliteBuildLog, dùng hai engine PG thật đọc name/cache/module_assignment; không chỉ kiểm thuộc tính store |
| `src/doc2roadmap/composition_phase_b.py::PhaseBRuntime.__init__(..., store=None)` | Chọn store được tiêm trước khi tạo DailySpendGuard/use case/session/model con; không tạo JSON rồi gán lại store | Session/spend guard/cache use case đều ghi/đọc PostgreSQL xuyên connection độc lập, không có live.json |
| `src/doc2roadmap/composition_build.py::build_document_runner(settings=None, *, allow_spend=False, recorder=None)` | Port recorder đã có. Adapter dùng trực tiếp BuildDocument nên không cần sửa factory ở giai đoạn này; nếu sau này dùng factory phải nối cả PG và không gọi mặc định SQLite | Spy recorder terminal đúng một receipt; cấm constructor SQLite; lỗi/huỷ giữ usage |
| `src/doc2roadmap/application/use_cases/build_document.py::BuildDocument.execute(...progress...)` | Không cần sửa ở giai đoạn adapter: web bọc progress completed để chụp usage baseline→hiện tại sau khi bước join; nếu sau này đưa checkpoint vào core thì giữ cùng payload/baseline, không phát trùng | Snapshot luỹ kế attempt, lịch sử meter bị trừ; final thiếu số giữ false; lỗi giữa bước dư step=null |

Payload checkpoint: `progress(step, {"status":"completed", "usage":{"spent_usd":0.003,"model_calls":3,"input_tokens":300,"output_tokens":60,"usage_complete":true}})`. Các số là ví dụ giả. Snapshot tính từ đầu attempt/lease, không delta một bước/historical artifact. Worker hiện ghi phần tăng vào PostgreSQL ledger; final còn dư chưa phân bổ dùng step=null.

Adapter mặc định phải từ chối pipeline thật chưa có port `phase_b_store` **trước khi claim job hoặc gọi provider/ADC**. Test tiêm pipeline fake nhận đúng cùng PostgreSQL; không suy test fake thành port thật đã xong. Không tự sửa tệp Pha A trong lúc chờ.

Điểm cần chốt cùng port: NameModulesB/IndexConcepts có thể tự append usage theo purpose con (concept-index hiện có dòng ước token riêng), trong khi meter W-13 và recorder web ghi tổng `purpose=build`. Phải xác định một nguồn tính chi build, giữ trace con nếu cần nhưng không cộng hai nguồn thành chi nhà cung cấp. Test use case con độc lập trong lượt này không phải bằng chứng đã giải quyết ghi sổ lặp trong DocumentPipeline thật; pipeline mặc định vẫn bị chặn. Không lấy dòng ước lượng concept-index thay usage thực trả của build.

## Adapter/composition đã cài

Commit mã/test: **`78356fb`**. Chỉ thay `src/web/`; không sửa tệp lõi hay migration. Báo cáo/đề nghị port được commit trước mã tại `7f0cf58`.

- `WebSettings.build_runner` mặc định `fake`; `WAYFINDER_BUILD_RUNNER=real` chọn nhánh composition mới. Các tham số manifest của fake vẫn bắt buộc khi chạy CLI ở chế độ fake; giữ thông báo lỗi UTF-8 cũ.
- `infrastructure/real_build.py::RealBuildRuntime` ép Vertex/project/location, xác minh port `phase_b_store`, PostgreSQL và cùng URL DB web. Không gọi provider/ADC khi kiểm cấu hình. Pipeline version có tiền tố `web-real:` + version/config hash của W-13; API/worker dùng cùng cách tính, không reuse nhầm `web-fake-v1`.
- `RealBuildAdapter` tạo pipeline riêng mỗi attempt với `allow_spend=False` và `PostgresPhaseBStore` được tiêm. Dùng trực tiếp `BuildDocument`, recorder luôn do worker truyền vào; không gọi factory CLI mặc định SQLite. Các use case thật session/spend reservation/name/concept-index đã được kiểm với cùng PG và đọc cache/record lại qua engine độc lập bằng model/embedding fake.
- Checkpoint dùng baseline→snapshot theo helper `_set_usage_delta` hiện có của W-13; không sửa helper. Chụp sau callback completed của mỗi bước, dùng cùng quy tắc missing usage như final. USD chuẩn hoá tới 6 chữ số để khớp `numeric(12,6)` trước so sánh luỹ kế trong DB; test meter có lịch sử 9 USD/90 calls chứng minh không bị nhập vào attempt mới.
- Thời gian tường từng bước nằm ở `BuildResult.step_details[step].web_timing.wall_seconds`, đo bằng `perf_counter`/đồng hồ đơn điệu được tiêm trong test, kể cả bước lỗi/huỷ. Không gồm thời gian chờ queue. `embedding_wait_seconds=null`, `embedding_wait_measured=false` vì chưa có điểm đo riêng; không suy từ cả thời gian bước.
- `worker.make_real_worker` dùng cùng PG cho BuildService/recorder/phase store và giữ MediaStore/Mailer giả ở giai đoạn này. Khi factory lõi còn thiếu port, trả `CoreBuildPortUnavailable` trước khi claim, không gán lại `.store` của runtime CLI để lách port.
- Adapter từ chối `dry_run=True` trước tạo pipeline hoặc recorder. Chưa thêm đường chạy dry-run thật; status dry_run không vào queue hoặc đổi course ready.

**Giới hạn có chủ đích:** pipeline thật mặc định **chưa nối chạy được** vì core chưa có port PG. Adapter đã kiểm bằng pipeline fake, core BuildDocument thật và PostgreSQL thật; không coi đó là các dependency con của DocumentPipeline thật đã được port. Những test use case thật độc lập chứng minh port store hiện có tương thích PG, không thay việc kiểm lại toàn pipeline sau khi nhận port Pha A. `allow_spend=False` cố định trong giai đoạn này, chưa có cờ CLI mở chi.

Version hiện dùng helper riêng `_pipeline_version` của core và gồm Git HEAD; commit chỉ thêm báo cáo cũng có thể đổi định danh pipeline. Vì vậy version trong bằng chứng thuộc đúng commit đã chạy, không hứa reuse nguyên khoá cache sau commit khác. Adapter còn dùng helper `_set_usage_delta` của W-13; khi nhận port phải kiểm lại hai điểm phụ thuộc này, chưa tạo bản sao thuật toán trong web.

## RED/GREEN, guard và SQL

Mọi pytest qua `scripts/w05_run_tests.py`, PostgreSQL bắt buộc. Fixture W-14 chặn model/embedding HTTP, Vertex headers, SMTP/Cloudinary; fixture W-15 chặn thêm ADC, JsonPhaseBStore, PhaseBRuntime CLI và SqliteBuildLog. Không chạy mô hình/mail/media thật.

Một ca bỏ qua trong cổng toàn repo là `test_cloudinary_satisfies_shared_media_contract_when_explicitly_enabled`: test Cloudinary live có sẵn chỉ chạy khi bật biến môi trường riêng. Không bật test live trong lượt 0 USD; không thêm skip hoặc giảm guard để đạt cổng.

| Lượt | Kết quả hiện có | Bằng chứng |
|---|---|---|
| RED trước adapter | **11 assertion fail, 0 setup error**, exit 1 | [JUnit](w15-evidence/runs/adapter-red.xml), [log](w15-evidence/runs/adapter-red.log) |
| RED sai engine PostgreSQL | **1 assertion fail**, không nhận DB khác, exit 1 | [JUnit](w15-evidence/runs/engine-red.xml) |
| GREEN adapter/CLI/W-25 | **34 pass** | [JUnit](w15-evidence/runs/adapter-green2.xml) |
| GREEN tích hợp trước bổ sung ca lease cuối | **84 pass**, W-14/W-25/composition/CLI/adapter | [JUnit](w15-evidence/runs/integration-green.xml) |
| Callback lease cũ qua adapter | **1 pass** | [JUnit](w15-evidence/runs/old-lease-green.xml), [SQL](w15-evidence/sql/old-lease-green/old-lease.json) |
| Mutation trên `78356fb` | **14/14 bị bắt bằng assertion**, exit 1 từng phép phá, 0 setup error; byte nguồn phục hồi | [Kết quả](w15-evidence/mutations/mutations.json), [native exit](w15-evidence/runs/mutations-exit.json) |
| React/build trên `78356fb` | **104/104 pass**, build exit 0 | [JUnit](w15-evidence/runs/react.xml), [build log](w15-evidence/runs/frontend-build.log) |
| Cổng Python toàn repo trên `78356fb` | **2.202 pass, 1 skip**, native exit 0 | [JUnit](w15-evidence/runs/full-gate.xml), [log/native exit](w15-evidence/runs/full-gate-exit.json); 606,49 giây gồm runner |
| React/build sau nhận main trên `446caba` | **104/104 pass**, build exit 0 | [JUnit](w15-evidence/runs/react-main.xml), [build/native exit](w15-evidence/runs/frontend-build-main-exit.json) |
| Python/PostgreSQL sau nhận main trên `446caba` | **2.235 pass, 1 skip**, native exit 0; 648,28 giây gồm runner | [JUnit](w15-evidence/runs/full-main-gate.xml), [log](w15-evidence/runs/full-main-gate.log), [native exit/commit/SHA](w15-evidence/runs/full-main-gate-exit.json) |

Các phép phá gồm confirm/cancel, terminal/cancel, media/cancel, receipt đúng một lần, không thư thành công sau huỷ, khoá terminal; thêm ép Vertex, port bắt buộc, cùng PostgreSQL, baseline usage, độ chính xác USD, đồng hồ bước, cấm dry-run trong queue và identity API/worker. Không nới assertion hoặc miễn route khỏi guard.

Các lượt đầu cũng được giữ, không xoá log: `adapter-green` có 8 fail (sai số float/completeness, fixture PG cache chưa truncate và hồi quy thông báo/required args CLI), `children-check` có 1 fail do test dispatch thiếu cấu hình Vertex. Đã sửa nguyên nhân, giữ assertion và chạy lại GREEN; không tính các lượt đó là bằng chứng cổng xanh. Log `*-exit.json` có commit/cwd/argv/SHA-256 vì các lượt thăm dò chạy trước commit mã.

17 ca W-15 nằm trong `src/web/backend/tests/test_real_build_w15.py`: bắt buộc port trước claim; ép transport; snapshot luỹ kế thành công/lỗi/huỷ (đầy đủ/thiếu usage); dry-run không vào queue; session/spend/name/concept-index xuyên PG độc lập; composition worker; huỷ trong graph publication; engine khác DB; identity/cache doc-6; callback lease cũ. Các guard race media/confirm/terminal dùng lại bộ W-25 trong cổng chung và mutation riêng. Không thêm migration hoặc đổi DTO/OpenAPI trong giai đoạn này.

### Ma trận usage/receipt

| Ca pipeline fake qua core thật | Chi tổng hợp ghi DB | Phân bổ/cờ và side effect |
|---|---|---|
| Success | `.003`, 3 calls/300 input/60 output | Ba delta `.001` cho concepts/graph/prep, final receipt 0; success/ready đúng graph |
| Lỗi ở graph | `.002`, 2 calls | `.001` concepts, `.001` terminal chưa phân bổ (`step=null`, attribution=false); không chia đều |
| Huỷ sau learning_prep | `.003` | Giữ usage; cancelled/course failed, không thư thành công |
| Ba ca trên, provider thiếu usage | Giữ số biết được khác 0 | `usage_complete=false`, không xoá hoặc thay chi bằng 0 |
| Huỷ trong graph publication sau kiểm đầu callback | `.003` | Kết nối PG độc lập commit huỷ; terminal cancelled, version NULL, không thư |
| Lease cũ sau reclaim, rồi huỷ lease mới | `.003` lease cũ + `.001` giả của lease mới = `.004` | Receipt cũ lặp không thêm ledger; không publish lên lease mới; completeness false sau reclaim |

Các số trên là **synthetic**, không phải tiền provider. Lưu build/receipt/ledger/transport ở [SQL tích hợp](w15-evidence/sql/integration-green/) và [SQL cổng cuối](w15-evidence/sql/full-main-gate/); guard W-25 có [SQL cổng cuối riêng](w15-evidence/w25-regressions/full-main-gate/). Tổng build phải bằng SUM ledger `purpose=build` của các attempt; usage riêng của các use case Pha B trong test con được phân biệt theo purpose, không cộng nhầm thành chi build.

## Identity/cache doc-6 và dữ liệu

Đã chép **3.144 tệp** theo hai manifest W-06, không links hoặc learner store CLI. Riêng doc-6 có **127 tệp** trong allowlist đã kiểm SHA-256; graph nguồn **v29** tải được. Không dựng lại sáu cuốn hoặc ép số phiên bản.

[Kiểm identity](w15-evidence/sql/integration-green/doc6-identity.json) xác nhận:

| Quan sát | Kết quả |
|---|---|
| Graph nguồn `doc-6` | Có v29, fingerprint được loader kiểm |
| Doc ID web từ chính PDF đó | `u-82cb494d407c4755d29d`, khác `doc-6` |
| Hai upload cùng PDF + cùng real pipeline version | Cùng một build awaiting_confirmation, không attempt/ledger |
| Tra build đó bằng fake pipeline version | Không reuse |
| Cache thật cho định danh/pipeline web mới | **Chưa xác minh**; không suy từ có graph doc-6 |
| Số gọi cần bổ sung/chi/thời gian để hoàn tất doc-6 thật | **Chưa biết** |

Chỉ báo dữ liệu/cache nguồn có, không tuyên bố lượt doc-6 thật qua web 0 USD đã chạy hoặc đã đạt. Không nhập chi cũ từ artifact, không mở live.json hoặc tập giữ lại.

## Ứng viên một cuốn mới và bảng đề nghị trước duyệt tiền

Chọn **ứng viên**, chưa nhận là cuốn cold-cache đã đủ điều kiện chạy: `document-data/train/nong-nghiep/rau-thuy-canh.pdf`, **52 trang**, 1.054.520 byte. SHA-256: `1f019766e74a747d293c15ad5bc86b2ea90420b49a8437cf27c1f6805656a627`.

Đã đọc metadata và chép riêng vào `tmp/w15-candidate/input.pdf`, kiểm hash trước/sau, không link và không đưa PDF vào Git. Không thấy thư mục artifact dưới slug `rau-thuy-canh` hoặc ID web `u-1f019766e74a747d293c`; **chưa rà mọi alias**, nên chưa kết luận hoàn toàn chưa có artifact gộp. [Hồ sơ ứng viên](w15-evidence/candidate.json).

| Bước | Cache hit/miss/unknown | Gọi sinh | Gọi embedding | USD | Phút |
|---|---|---|---|---|---|
| doc_reading | unknown trước dry-run | 0 theo hợp đồng | 0 theo hợp đồng | 0 theo hợp đồng kiểm sớm | Chưa đo |
| concepts: label-roles → A3/A3′ → A4 | unknown | Chưa biết | Chưa biết | Chưa biết | Chưa biết |
| graph: roadmap và tên | unknown | Chưa biết | Chưa biết | Chưa biết | Chưa biết |
| learning_prep: a12/concept-index/formulas | unknown | Chưa biết | Chưa biết | Chưa biết | Chưa biết |
| Tổng/embedding wait | Chưa xác minh | Chưa biết | Chưa biết | Chưa biết | Chưa đo |

**Trần đề nghị:** chưa chốt con số trước dry-run. Không dùng mức “dưới 3 USD” trong vé thành quyền chi hoặc dự toán đo được. Điểm dừng: thiếu port PG, sai transport/identity/cache, thiếu usage không giải thích được, hoặc chưa có tin nhắn duyệt mới cho đúng cuốn/lượt/trần. Bảng này là chuẩn bị đề xuất riêng, không phải dự toán trên app hoặc yêu cầu duyệt tiền ngay.

## Dry-run đã chạy hay chưa và việc còn lại

**Chưa chạy dry-run thật**, chưa chạy lượt doc-6 thật, chưa chạy cuốn mới có tiền. Đã chạy test adapter từ chối đưa dry_run vào queue. Lệnh nội bộ cần chốt sau khi nhận port PG: recorder web/collector được tiêm, kho artifact bản sao riêng, `allow_spend=False`, network guard; không dùng CLI factory mặc định SQLite hoặc JSON live. `inspect` hiện trả `cache_validated=false`, nên vẫn phải kiểm dependency/fingerprint cụ thể trước đề nghị số gọi.

Giữ label-roles bắt buộc; ingest mặc định nhẹ + `require_text_quality`; A3/A3′ song song, A4 tiếng Việt/coverage none, roadmap, a12/concept-index/formulas. Không tự truyền allow_text_quality_reason hoặc dùng cấu hình Docling so sánh T-01a.

Sau khi điều phối/Claude chốt port: nhận mã đúng nhánh/main theo quy trình, kiểm lại dependency con bằng PG độc lập, identity/cache và callback usage, rồi mới dry-run và trình trần riêng. W-15 chưa hoàn tất ở giai đoạn adapter/fake này. **Chi dịch vụ ngoài mới 0 USD**; phê duyệt phục hồi và ngân sách SA-55 không áp dụng.

## Hồ sơ bàn giao và kiểm phạm vi

- Mốc mã đã kiểm: **`446caba3e3ab608ad1ad56108fabac6e6c539398`**, đã chứa main `fd185ba`. Mã web giữ nguyên so với `78356fb`; các commit hồ sơ sau mốc này chỉ thêm báo cáo/bằng chứng. Người điều phối soát rồi ghép, nhân viên không tự ghép hoặc đẩy main.
- [Tổng hợp máy đọc](w15-evidence/summary.json): native exit, số test, 14 mutation, SHA nguồn khớp, port/dry-run/cache thật còn chưa đạt. [Manifest bằng chứng](w15-evidence/manifest.json) ghim SHA-256 từng tệp; [chuẩn hoá](w15-evidence/normalization.json) ghi hash raw và UTF-8/LF. Giữ bản raw trong `tmp/w15-raw-evidence`, không commit.
- JSON giữ nguyên giá trị, JUnit giữ số test/failure/error/skip khi chuẩn hoá line ending và bỏ khoảng trắng cuối dòng. Không sửa nội dung assertion hoặc số kết quả. Đã quét bằng chứng không có giá trị credential đang cấu hình, không chép `.env`.
- Test có sẵn ghi đè export W-06/W-14 trong worktree: đã lưu bản của lượt W-15 vào [hồ sơ regression](w15-evidence/regression-exports/), rồi khôi phục đúng tệp lịch sử. SQL mới do helper W-25 phát ra được chuyển vào hồ sơ W-15; không thay bằng chứng W-25 cũ. SQL không gắn nhãn ở gốc `sql/` là thăm dò, không phải cổng cuối.
- Không thêm migration: tuyến hiện tại giữ `w14_0006` nối `w06_0005`, cổng toàn repo kiểm một Alembic head. Không sửa DTO/route/OpenAPI, task/kế hoạch/handoff hay tệp Pha A. Không dọn worktree, snapshot, ZIP hoặc dữ liệu giữ lại.

**Bàn giao giai đoạn 0 USD, chưa xin đóng W-15.** Cần người sở hữu lõi chốt/nhận port PG và nguồn ghi chi duy nhất; sau đó mới kiểm toàn DocumentPipeline thật, dry-run trong kho bản sao riêng và lập đề nghị có số đo cho đúng lượt/trần.
