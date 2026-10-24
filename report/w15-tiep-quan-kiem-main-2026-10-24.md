# W-15 — tiếp quản và kiểm main sau SA-69 — 2026-10-24

## Hiện trạng của lượt tiếp quản

Tiếp vai trò nhóm lõi trong phạm vi W-15 và các vé được giao tiếp, làm tại `tmp/w15-real-build`, nhánh `work/w15-real-build`.
Đã đọc handoff `ca409b1`, AGENTS.md, quy trình nhánh, quy tắc fixture, vé/spec và lệnh giao hiện hành.
Các điểm chờ port/adapter trong lịch sử đã được thay bởi milestone sau port; không triển khai lại.

Worktree sạch tại `ca409b1fede5d3135aaedb6cb6559332a1212a66`; nhận main
`a71a90bc19f898e088fdc32ab0b0439d9dd4087c` bằng merge **`e48ee1bc59238c4b3f929176811b8e5d83c5a412`**, không xung đột.
Thư mục chung vẫn `main`. Không ghép/push main, gửi tin sang phiên khác, sửa vé/spec/handoff điều phối hoặc dọn dữ liệu.
Main này đã có SA-69 `973fa99`, chưa có SA-70. Sự tồn tại worktree/cổng SA-70 không được tính là đã ghép.

**Mốc đầu sau SA-69: scope 42 đạt/3 lỗi; full 2.443 đạt/4 lỗi, 1 skip/1 xfail; native exit 1, không setup error.**
Main tiến tới **`9ce5ee75e4ffec79a1c2a0cd2933f3211da78570`**, đã ghép SA-70 `5188908`, ngay sau cổng full này.
Lưu nguyên kết quả `e48ee1b` làm lịch sử; tiếp nhận nền SA-70 và kiểm lại trước chốt trạng thái hiện hành.
Chưa chạy React/build trên `e48ee1b` vì sẽ chạy cả ba cổng trên nền mã mới. Toàn W-15 vẫn mở và chưa có quyền chạy có tiền.

## Bằng chứng mới và lỗi cổng

Lệnh chạy tại gốc worktree, Python `C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe`, luôn qua
`scripts/w05_run_tests.py` để nạp mã worktree, bắt buộc PostgreSQL và không dùng pytest cache.
Wrapper `src/web/backend/tests/w15_capture.py` ghi lệnh đầy đủ, commit, SHA nguồn, native exit, log UTF-8 và thời gian.

| Lượt trên `e48ee1b` | Kết quả | Bằng chứng |
|---|---|---|
| `resume-scope-20261024-01` | 42 đạt, 3 assertion fail; exit 1; 88,92 s gồm runner | [JUnit](w15-evidence/runs/resume-scope-20261024-01.xml), [lệnh/exit/SHA](w15-evidence/runs/resume-scope-20261024-01-exit.json), [log](w15-evidence/runs/resume-scope-20261024-01.log) |
| `resume-full-20261024-01` | 2.443 đạt, 4 assertion fail, 1 skip, 1 xfail; exit 1; 554,08 s gồm runner | [JUnit](w15-evidence/runs/resume-full-20261024-01.xml), [lệnh/exit/SHA](w15-evidence/runs/resume-full-20261024-01-exit.json), [log](w15-evidence/runs/resume-full-20261024-01.log) |

Các assertion giữ nguyên:

1. `tests/unit/application/test_phase_b_assistant_sa66.py::test_system_prompt_is_the_text_block_of_the_spec_word_for_word` (dòng 426).
   SA-69 đã bổ sung hai dòng về gọi nguồn là sách/không lộ chỉ dẫn. Chênh lệch **hiện tại** là luật `[formula: …]` và dòng báo quiz/tài liệu đã tạo,
   thuộc yêu cầu SA-70/`assistant-prompt-5`; mã hiện vẫn `assistant-prompt-4`.
2. `tests/unit/application/test_phase_b_lecture3_sa64.py::test_system_prompt_sent_to_the_model_is_the_spec_text_plus_one_format_line[True]`
   và `[False]` (dòng 150). Lời nhắc còn thiếu soát ví dụ tự nghĩ, giới hạn câu nối khái niệm kế tiếp và giữ chiều/phạm vi phát biểu của sách.
   Ngoại lệ một dòng `SELF_CHECK_LINE` vẫn được giữ trong đối chiếu.
3. Full còn phát hiện `tests/unit/application/test_phase_b_assistant_sa69.py::test_prompt_version_is_4_and_its_last_two_lines_are_the_spec_ones`
   (dòng 199): hai dòng cuối của spec đã đổi do thêm câu về quiz/tài liệu. Đây là ca mới theo SA-69, không nằm trong scope nhanh 45 ca.

[Diff mới](w15-evidence/resume-20261024-01/prompt-diff.json) được trích bằng AST/text, không import provider.
[Provenance](w15-evidence/resume-20261024-01/source-provenance.json) đối chiếu 7 blob core/spec/test: HEAD và main khớp.
Đây là tái hiện trên mốc mới, không sao chép ba lỗi lịch sử thành kết luận mới.
Tại mốc này, bốn lỗi thuộc phần SA-70 vừa được ghép trong lúc full chạy; tiếp nhận main và kiểm lại cả assertion kế nhiệm SA-69.
Không rollback spec, đổi expected, bỏ label-roles hay dùng mã SA-70 chưa ghép để làm xanh W-15.

## Pipeline thật, PostgreSQL và hai dry-run 0 USD

42 ca phạm vi gồm nguyên 5 biến thể DocumentPipeline thật/provider fake, hai dry-run thật, adapter/port dương âm và guard W-25.
SQL qua connection độc lập, cache/tên/A12/runtime con/spend guard, usage thiếu, receipt/huỷ/lease giữ các assertion đã có.
Các USD trong ma trận provider fake chỉ chứng minh ghi sổ; không phải chi thật hoặc dự toán sách.
Không chạy lại 17 mutation vì lượt này không đổi mã W-15; kết quả RED 17/17 và 2 guard lặp của session trước vẫn là bằng chứng lịch sử.

Fixture `builds` chặn HTTP model/embedding, Vertex credentials headers, SMTP và Cloudinary; `guarded_pg` chặn ADC và JSON/SQLite fallback.
Default factory/dry-run dùng `allow_spend=False`, Vertex placeholder `dry-run-no-network/global`, PostgreSQL thật và collector web.
Toàn pipeline dùng fake model/embedding như fixture đã được bàn giao; không biến ngoại lệ test thành quyền chi production.
Chuỗi sản phẩm giữ ingest nhẹ → kiểm chữ → label-roles → A3/A3′ → A4 vi/coverage none → roadmap → learning_prep.

| Quan sát mới từ lượt scope | Doc-6 | Ứng viên rau thuỷ canh |
|---|---|---|
| SHA-256 PDF | `82cb494d407c4755d29deb7c08b9a4f3794f79e241c307fd2b5dfc149cd559c7` | `1f019766e74a747d293c15ad5bc86b2ea90420b49a8437cf27c1f6805656a627` |
| Trang / ID web | 25 / `u-82cb494d407c4755d29d` | 52 / `u-1f019766e74a747d293c` |
| Wall đọc + kiểm sớm | 2,3091313 s | 7,7411326 s |
| Parser | `a1-nhe:r2-full` | `a1-nhe:r2-full` |
| Collector / status | 1 / dry_run | 1 / dry_run |
| Provider sinh/embedding; USD thật | 0/0; 0 | 0/0; 0 |
| Build/attempt/course/usage/cache SQL | tất cả 0 | tất cả 0 |
| Label-roles plan | 78 headings, 2 batch ban đầu | 103 headings, 6 batch ban đầu |

[SQL/collector doc-6](w15-evidence/sql/resume-scope-20261024-01/real-dry-run-doc-6.json),
[ứng viên](w15-evidence/sql/resume-scope-20261024-01/real-dry-run-candidate.json),
[ma trận và usage](w15-evidence/sql/resume-scope-20261024-01/).
Đầu vào được copy độc lập/đối chiếu SHA; 127 tệp doc-6 theo manifest đã ghim. Không link, mở tập giữ lại, nhập live.json hoặc chi lịch sử.

Các thời gian là quan sát từng lượt, không phải benchmark hoặc dự báo phút/cuốn. Lần kiểm tiến trình đầu chưa có Python;
kiểm chi tiết sau đó thấy cổng `tmp/cong-sa70` khởi động 12:35:34, trong khi full W-15 khởi động 12:39:31.
Không dừng hay sửa tiến trình làn khác. Cơ sở dữ liệu test tách riêng theo UUID; tải CPU có thể ảnh hưởng thời gian.

## Chuẩn bị tiếp: phần planner còn thiếu và đề nghị đúng làn

Đây là đề nghị kỹ thuật để chủ dự án chuyển làn, **chưa là port đã cài hoặc quyết định mở chi**.
Không thêm dự toán vào API/UI người tải. Tái dùng planner đã có, không xây bộ ước lượng song song ở web.

| Điểm từ mã hiện hành | Khả năng / giới hạn |
|---|---|
| `BuildDocument.execute(..., dry_run=True)` | Chạy read/kiểm sớm, gọi `pipeline.inspect(doc_id)`, phát 3 planned; chưa gọi planner các bước sau |
| `DocumentPipeline.inspect(doc_id)` | Chỉ version mới nhất, luôn `cache_validated=False`; không phải chứng cứ hit/miss hợp lệ |
| `LabelChunkRoles.plan(doc_id, ...)` | Đã chạy trên bản sao đúng u-hash; ước 3 ký tự/token, output 512 mặc định, chưa retry/repair; `.002936`/`.009970` USD không là trần |
| `ExtractEntities.execute` / `IndexDocument.execute` | Chưa có phương thức plan tương ứng; không gọi execute để giả làm planning |
| `Canonicalize.plan(doc_id, declared_language='vi')` | Cần candidate thật; khi miss mới biết số tên embedding, calls/USD embedding còn None, các phần sau unknown |
| `BuildLearningGraph.plan(doc_id, stop_after='stages')` | Cần canonical gop thật; truyền artifact hợp lệ qua chuỗi; thiếu upstream thì unknown. Tổng đã biết được ghi rõ không là ngân sách tối đa |
| `IndexConcepts.execute(..., dry_run=True, allow_spend=False)` | Có khi graph thật đã tồn tại và dùng đúng PG; chưa có graph u-hash thì không suy cache hit từ graph alias v29 |

Đề nghị phần lõi tối thiểu nếu tiếp tục mở planner: cung cấp một hàm nội bộ `DocumentPipeline.plan(doc_id, *, language='vi')`
**tách khỏi inspect/DTO web hiện có**, dùng cùng cấu hình/factory stage với đường execute; làn Claude chốt chữ ký/tệp trước sửa.
Tệp dự kiến: `src/doc2roadmap/composition_build.py`; bổ sung plan ở `extract_entities.py`, `index_document.py` nếu làn sở hữu chọn thực hiện.
Kết quả đề nghị gồm doc_id, pipeline/config fingerprint, từng stage, upstream/version, trạng thái reused/run/unknown,
generation_calls/embedding_calls/USD có thể null, lý do unknown, known_total và estimate_complete.
Không có downstream thật thì giữ unknown; không tạo graph giả, đổi ID/version hoặc chạy model để lấp số.

Assertion cần cho port: planner chạy khi model session/embedding/ADC/JSON/SQLite constructor bị cấm; không đổi hash cây artifact,
không thêm PG record/cache/usage/queue; candidate/canonical/graph thiếu vẫn trả unknown; đổi nội dung/config làm mất reuse;
label-roles còn run thì downstream không dùng chunk/artifact cũ; tổng known không biến thành cap.
Các ca RED→GREEN này thuộc port mới, chưa được tuyên bố đã chạy trong W-15.

Phần embedding wait cần nguồn đo ở `infrastructure/embedding/gemini.py::_embed_vertex` và
`infrastructure/llm/rate_limit.py::AdaptiveModelLimiter.acquire`, tách chờ permit, xác thực, request và retry.
Limiter hiện chỉ snapshot số đếm, không có duration chờ. Không lấy toàn bộ wall concepts hay tổng duration lời gọi song song làm wait của cuốn.
Đây là đề nghị instrumentation cho làn sở hữu, W-15 chưa sửa các tệp này.

## Đề nghị lượt thật và phần còn mở

Ứng viên giữ `document-data/train/nong-nghiep/rau-thuy-canh.pdf`, hash/52 trang ở trên, bản stage `tmp/w15-candidate/input.pdf`.
Phạm vi đang chuẩn bị: **một lượt dựng qua web dưới u-hash/pipeline version của commit được soát**, chưa chạy.

| Bước | Cache | Sinh / embedding dự kiến | USD / phút lượt thật |
|---|---|---|---|
| doc_reading | Bản sao dry-run có parse/chunks; không suy thành toàn pipeline hit | 0 / 0 | 0 USD; wall dry-run có số riêng ở trên |
| concepts | Nhãn còn run; A3/A3′/A4 chưa xác minh | Nhãn 6 ban đầu, phần còn lại unknown / unknown | unknown |
| graph, tên module | Thiếu canonical/graph đúng profile web | unknown / unknown | unknown |
| learning_prep | Thiếu graph web | unknown / unknown | unknown |
| Tổng / embedding wait / cap | chưa đủ phụ thuộc | unknown | unknown / null / chưa đủ căn cứ |

Lượt doc-6 qua web tới ready/mail vẫn chưa chứng minh 0 USD. Giữ alias v29 khác u-hash; không nhập learner cache hoặc sửa version để ép reuse.
Adapter production hiện vẫn cố định `allow_spend=False`; mọi thay đổi cho lượt có tiền cần phạm vi triển khai/guard được soát trước,
sau đó dry-run và tin nhắn duyệt mới cho đúng cuốn/hash/lượt/trần. “Tiếp tục”, ngân sách W-13/SA/khôi phục cũ không cấp quyền chi W-15.
Chưa đề nghị một trần số học khi dữ liệu toàn chuỗi còn unknown; chưa có số để đề xuất hạn mức ngày/tháng từ đo thật.

## Bảo toàn và review

[Kiểm nguyên trạng 401 entry](w15-evidence/resume-20261024-01/historical-integrity.json) của manifest 20261024 đạt.
Giữ bằng chứng mới ở nhãn mới; báo cáo này thay trạng thái cổng cũ theo mốc kiểm mới, không sửa kết quả lịch sử.
Mã W-15/test/guard/schema không đổi trong lượt tiếp quản. Cổng và bước chuẩn bị không làm toàn W-15 hoàn tất.
Review cuối: đối chiếu native exit/JUnit, kiểm phạm vi đường dẫn, SHA bằng chứng cũ, giữ export hồi quy trước khi phục hồi,
không commit secrets/PDF/artifact/.env hoặc tệp của làn khác. Hồ sơ chỉ được commit trên nhánh W-15.
