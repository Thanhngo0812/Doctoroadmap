# Handoff session nhóm lõi — W-15 — 2026-10-24

Tài liệu để chủ dự án kết thúc session cũ và giao session mới tiếp quản. Đây là báo cáo của làn lõi, không phải handoff điều phối và không thay đổi trạng thái nghiệm thu vé. Lần ghi này chỉ tạo tài liệu; không chạy lại pipeline, không nhận main và không gọi provider.

## 1. Đọc phần này trước

- Tiếp đúng worktree **`C:/Users/ngoco/Desktop/Doctoroadmap/tmp/w15-real-build`**, nhánh **`work/w15-real-build`**. Không tạo lại adapter hoặc tạo lại worktree cho cùng việc.
- Commit bàn giao công việc trước khi viết tài liệu này: **`4f122ef17624dd349199774a3e26e825a1e1f510`**. Worktree sạch khi bắt đầu ghi handoff. Commit chứa chính handoff sẽ nằm sau commit này; dùng `git log -1 -- report/handoff-core-w15-session-2026-10-24.md` để tìm.
- Mốc code kiểm gần nhất: **`b59cae0f38db053a0395be80fcf52471ef41099f`**, đã nhận main `fcff7619813b53d09074988760bd60bffc661c6c`.
- Đã xong milestone **sau port: DocumentPipeline thật + provider fake + PostgreSQL; kiểm usage/huỷ/lease/cache; dry-run thật nội bộ 0 USD**. Chưa hoàn thành toàn W-15.
- **42 test W-15/W-25 đạt; 17/17 phép phá guard bị bắt; 143 React đạt/build thành công.** Cổng toàn repo ở mốc đã chạy vẫn đỏ vì prompt/spec lõi. Không trình mốc đó như cổng tổng xanh.
- **Cập nhật lúc viết handoff:** local main đã tiến tới **`a71a90bc19f898e088fdc32ab0b0439d9dd4087c`**, có merge SA-69 **`973fa99`** và docs **`2a39c32`**. Nhánh W-15 **chưa nhận/chưa kiểm** mốc mới này. Ba lỗi prompt trong báo cáo là kết quả lịch sử tại mốc kiểm, phải đối chiếu lại sau nhận main; không mặc định cả ba vẫn còn hoặc đã hết. SA-70 có worktree riêng, sự tồn tại nhánh không chứng minh đã vào main.
- **Chưa được chạy có tiền.** Không dùng phê duyệt W-13/khôi phục/SA-55 hay câu duyệt cũ để mở chi W-15. Chỉ tin nhắn mới của chủ dự án cho đúng cuốn/hash/lượt/trần sau khi đọc dry-run mới mở lượt tương ứng.
- Chủ dự án yêu cầu **không gửi message trực tiếp cho điều phối hoặc phiên khác**. Viết kết quả/câu hỏi/tái hiện trong báo cáo, rồi báo chủ dự án. Không tự ghép/push main.

## 2. Thứ tự nạp tài liệu

Đọc UTF-8, theo thứ tự; chưa cần đọc hàng trăm tệp bằng chứng ngay khi mở session.

1. `AGENTS.md` áp dụng từ thư mục chung và mọi hướng dẫn theo đường dẫn thực tế. Nếu không có tệp, vẫn giữ các quy tắc chủ dự án đã giao: thay đổi tối thiểu, phát biểu giả định, kiểm có thể chứng minh sai, RED trên hành vi cũ trước GREEN.
2. Handoff này; [báo cáo W-15](w15-noi-bo-dung-that-2026-10-22.md), ưu tiên phần đầu **Mốc sau port và dry-run thật — 2026-10-24**. Các đoạn phía dưới là lịch sử, không phục hồi điểm chờ port đã hết.
3. [Quy trình nhánh/ghép main](../doc/quy-trinh-nhanh-va-ghep-main.md), [dữ liệu phát triển/fixture](../doc/du-lieu-phat-trien-va-fixture.md).
4. [Vé W-15](../task/web/W-15-noi-bo-dung-that-do-usd-cuon.md), [ghi chú đầu vào sau W-25](w15-ghi-chu-dau-vao-sau-w25-2026-10-22.md).
5. [Spec chức năng](../doc/web-chuc-nang-spec.md) mục 4 và 8; tìm spec CSDL hiện hành bằng `rg --files doc` nếu cần kiểm bảng/FK. Đọc vé W-13/W-14/W-25 khi chạm hợp đồng tương ứng.
6. [Summary máy đọc](w15-evidence/summary-20261024.json), [manifest bằng chứng mới](w15-evidence/manifest-20261024.json), [native exit gần nhất](w15-evidence/runs/latest-scope-and-spec-20261024-exit.json).
7. Khi nhận main mới, đọc báo cáo điều phối/lệnh giao mới trên main, chỉ đọc; không sửa chúng. Đọc báo cáo SA-69/SA-70 nếu main có thay đổi liên quan tới ba lỗi cổng.

Skills của repo nằm ở `C:/Users/ngoco/Desktop/Doctoroadmap/.agents/skills/`; worktree có thể không chứa các tệp bỏ qua Git này. Session cũ dùng using-agent-skills, documentation-and-adrs, git-workflow-and-versioning, TDD, incremental-implementation, ponytail và code review theo từng phần việc. Session mới đọc skill phù hợp khi áp dụng, không coi việc liệt kê là đã nạp nội dung.

## 3. Phạm vi và quy tắc vận hành bắt buộc

### Git, worktree và quyền sửa

- Thư mục chung `C:/Users/ngoco/Desktop/Doctoroadmap` luôn ở **main**. Không đổi nhánh ở đó, không sửa mã ở đó.
- Làm trong W-15; nhận main bằng **merge, không rebase**. Trước nhận main xem status và tệp dở; không reset/clean/stash cuốn việc người khác. Chỉ commit tệp của mình bằng đường dẫn cụ thể, không `git add -A`, `git add .`, `git commit -a`.
- Chỉ sửa mã/test web trong **`src/web/`**, báo cáo/bằng chứng của W-15. Không sửa vé, bảng kế hoạch, handoff điều phối hoặc spec để ép cổng xanh.
- Không tự sửa **`src/doc2roadmap/`**, đặc biệt `composition_build.py`, `composition_phase_b.py`, `budget.py`, prompt và test lõi thuộc làn Claude. Lỗi cần sửa ngoài phạm vi: ghi bước tái hiện, đường dẫn, assertion và đề xuất vào báo cáo.
- W-15 hiện **không có migration mới**. Không tạo migration để giải quyết việc chỉ là composition/test.
- Không ghép main, không push main, không tự đóng W-15. Người soát nhận đúng commit và điều phối ghép phần web; Claude ghép vé SA theo làn.
- Không dọn bất kỳ worktree/snapshot/ZIP/dữ liệu giữ lại nào. Giữ W-14/W-25 làm bằng chứng; tuyệt đối không đụng `tmp/t01a-clean-ff797eb`.
- Không junction/symlink/hardlink artifact/PDF. Chép độc lập từng tệp theo allowlist/manifest, xác minh SHA nguồn/đích. Không đọc `document-data/test/` hoặc tập giữ lại.

### Dữ liệu, provider và chi phí

- Dev mặc định **fake**. Real cấu hình **Vertex cho sinh lẫn embedding**. Không tự đổi sang Developer API hoặc dùng ADC thật trong test.
- Test chặn model/embedding HTTP, ADC, SMTP, Cloudinary; FakeMailer/MediaStore/fake provider. Không dùng ngân sách để chạy lại replay hoặc thu dữ liệu mới.
- Mọi kho Pha B/use case/cache/session/tên/runtime con/spend guard/recorder của đường web dùng **cùng PostgreSQL thật**, kiểm qua connection độc lập. Không thay mỗi thuộc tính `.store` ở runtime cha để bỏ sót dependency con.
- Cấm JSON Pha B/SQLite CLI fallback; không nhập `artifacts/phase_b/live.json`. Graph/chunks/parse/manifest/index/ảnh Pha A vẫn là **tệp**; không chuyển chúng vào PostgreSQL.
- Log số thực cuối vào DB. App không cần dự toán hoặc hiển thị chi phí cho người dùng. Dry-run/dự toán nội bộ và xin duyệt tiền riêng vẫn bắt buộc.
- Chọn tài liệu → kiểm quyền/tệp → xác nhận rồi mới queue. Tên riêng course được xử lý ở xác nhận theo hợp đồng W-14 đã chốt; course riêng có thể dùng chung build. Đọc DTO hiện hành trước sửa, không quay về giả định confirm body luôn rỗng từ lịch sử cũ.
- DailySpendGuard Pha B là hạn mức sinh nội dung học chung, **không tính module_title/embedding của build**. Không biến assertion purpose lecture thành guard build hoặc sửa budget.py đổi nghĩa.

## 4. Chuỗi sản phẩm phải giữ

```text
ingest (bộ đọc nhẹ mặc định)
→ kiểm sớm, gồm require_text_quality
→ label-roles
→ a3 (A3 trích ứng viên + A3′ lập chỉ mục song song trong cùng lệnh)
→ a4 --language vi, a4_gold_coverage='none'
→ roadmap
→ phase-b a12, concept-index, formulas --pdf (learning_prep; ảnh trang theo port hiện hành)
```

- **label-roles bắt buộc**, đặt trước A3 và A4; dù plan 0 mục cũng chạy/ghi rõ có sinh chunk version mới không. Không bỏ bước để ép cache hoặc chạy qua.
- Nhãn nghĩa là lớp phủ, không đổi chunk ID/text/offset. A3/A3′/A4 đọc chunk theo mã; neo A4/A9/A10/tên/Pha B lấy nhãn qua load_role_chunks. Neo A4 chỉ role noi_dung; thứ tự sai làm neo lệch nhãn.
- Chất lượng chữ bị từ chối: rejected/mã chu_loi; không tự truyền allow_text_quality_reason. Không dùng cấu hình Docling đối chứng T-01a thay mặc định đọc nhẹ.
- Chủ dự án cho gọi coverage none trực tiếp; không quay lại kiểm vàng bốn cuốn khác hoặc tự tạo vàng giả.

## 5. Những phần đã triển khai — không làm lại

| Mốc | Nội dung |
|---|---|
| `78356fb` / hồ sơ `a8bb295` | Adapter RealBuildRuntime/RealBuildAdapter, composition web, PG và fake tests; đã được nhận/ghép trước đó |
| `dba19e5` / hồ sơ `6627c00` | Trace accounting counted_in=build, giữ ca âm thiếu port tương thích; đã nhận/ghép |
| `6bcbae6` | Hồ sơ audit pre-port identity/cache/fingerprint; không phải dry-run |
| `9ac2a85`, `1d91b0b`, `4a4b957` | SA-62/64/65 đã vào main, không còn chờ chọn người hoặc ghép port |
| `ce5f581` | Ca dương default factory/PG đã có trên main; giữ cả ca âm PipelineWithoutStorePort |
| `a888e92d075c8872ab7774981464db68049d8e7d` | Test toàn pipeline thật/provider fake/PG, hai dry-run thật, capture và hai mutation mới |
| `4cbd2acc0e3139a5a3b125a7f1ae5c2c4a542ab1` | Kiểm chính runtime con/spend guard thật đọc ghi xuyên PG connection |
| `b59cae0f38db053a0395be80fcf52471ef41099f` | Nhận main fcff761; 42 test phạm vi đạt, 3 lỗi prompt/spec tái hiện |
| `4f122ef17624dd349199774a3e26e825a1e1f510` | Báo cáo và toàn bộ bằng chứng sau port/dry-run đã commit, worktree sạch |

### Tệp sản phẩm cần biết

- `src/web/backend/wayfinder/infrastructure/real_build.py`: validate Vertex/PG/port trước provider/claim; tạo pipeline mới mỗi attempt; inject phase_b_store và recorder web; adapter cố định allow_spend=False, không có quyền chi mới.
- `src/web/backend/wayfinder/worker.py`: make_real_worker; cấu hình và dependency web dùng cùng engine.
- `src/web/backend/wayfinder/infrastructure/phase_b_store.py`: counted_in=build giữ raw extra, typed cost/token=0. Các dòng bình thường vẫn tính như hợp đồng cũ.
- `src/web/backend/wayfinder/application/build_worker.py`, `application/builds.py`, `infrastructure/build_store.py`: checkpoint/terminal/lease/receipt/idempotency/lock W-25.
- Pipeline version có `web-real:` + hash cấu hình/core/Git HEAD; **commit chỉ sửa docs cũng có thể đổi version**. Không đổi ID/version để ép reuse; trước lượt thật ghim đúng commit/config và kiểm lại.
- Adapter từ chối dry_run=True trước factory/recorder. Dry-run nội bộ dùng trực tiếp BuildDocument với collector web, tách queue.

### Tệp test/harness cần biết

- `src/web/backend/tests/test_real_build_w15.py`: adapter, port dương/âm, cumulative usage/trace/recorder/provider guard đã có.
- `src/web/backend/tests/test_pipeline_postport_w15.py`: thực thi DocumentPipeline thật và mọi stage trên PDF tổng hợp một trang; fake chỉ model/embedding; 5 ca success đủ usage/success thiếu usage/cancel/error/lease.
- `src/web/backend/tests/test_internal_dry_run_w15.py`: hai cuốn, copy manifest/SHA, default factory và core BuildDocument thật, PG/collector/network guard, không queue/course ready.
- `src/web/backend/tests/test_build_cancellation_w25.py`: hai race PostgreSQL xác nhận/huỷ và huỷ/terminal graph/media; receipt muộn/lease/quota.
- `src/web/backend/tests/w15_capture.py`: lưu commit/command/source SHA/native exit/log/thời gian; chọn label mới mỗi lượt. Hàm dùng subprocess capture nên không có log tăng dần, vẫn báo tiến độ bằng kiểm process/đọc công việc độc lập.
- `src/web/backend/tests/w15_mutations.py`: 17 mutation, khôi phục source nguyên byte trong finally; không chạy song song với test khác vì cố ý sửa tạm source.
- `w15_cache_metadata.py`: audit metadata, **không** thay dry-run thật.

## 6. Bằng chứng sau port và cách hiểu đúng

### Pipeline thật + fake provider + PG

PDF tổng hợp tiếng Việt tạo bằng pypdfium2 có sẵn và `C:/Windows/Fonts/arial.ttf`; không thêm reportlab/dependency. Có một khái niệm Ma trận. Các phương thức read/quality/label_roles/A3/A3′/canonical/roadmap/learning_prep và use case thật được chạy. Formulas/page_images được gọi, sách tổng hợp không có công thức nên số ảnh 0; không suy thành đã kiểm chất lượng ảnh sách thật.

Factory **test** assert adapter gửi allow_spend=False, rồi tạo DocumentPipeline với True chỉ trong fixture model/embedding đã thay fake để thực thi mọi nhánh. Production không bật chi; hai dry-run thật vẫn False và không fake phản hồi model. Không sao chép ngoại lệ test thành công tắc production.

Các assertion đã có:

- Tên/module_assignment/A12/concept-index/cache/session được đọc lại bởi engine PG độc lập; naming plan/IndexConcepts reuse không tăng fake calls.
- Spy subclass chỉ quan sát constructor PhaseBRuntime thật và gọi nguyên super. Dòng lecture qua store con đọc được ở reader PG; chính spend guard con từ chối reservation sau đạt cap, không để reservation lưu. Đây là kiểm store/guard học chung.
- Snapshot usage luỹ kế từ đầu attempt/lease; ledger ghi **delta đúng một lần**. Không nhập lịch sử artifact/cache. Một response thiếu số: vẫn giữ chi biết được khác 0, usage_complete=false có giải thích.
- Meter là chi build duy nhất. counted_in=build trace raw giữ nguyên, typed USD/input/output=0; không cộng extra vào tổng lần hai.
- Error sau usage, huỷ khi naming, reclaim lease giữ usage; receipt cũ trả lại không tăng ledger hoặc publish/mail. Tổng dư chưa phân bổ step=null, không chia đều. Đọc không chi có timing nhưng không đòi ledger row 0.
- Thời gian tường từng bước dùng perf_counter; embedding wait chưa có điểm đo riêng → null/measured=false, không suy từ tổng thời gian bước.

Số USD trong ma trận là **fake để chứng minh DB**, không phải chi thật hoặc dự toán sách:

| Ca | Known USD tổng hợp | Calls | Usage complete |
|---|---:|---:|---|
| success đủ | 0.000585 | 15 | true |
| success thiếu | 0.000530 | 15 | false |
| cancel | 0.000570 | 14 | true |
| error embedding | 0.000585 | 15 | true |
| lease cũ | 0.000570 | 14 | aggregate false |

### Dry-run thật nội bộ đã chạy

| Thuộc tính | Doc-6 | Ứng viên cuốn mới |
|---|---|---|
| PDF | doc-6.pdf trong fixture worktree | document-data/train/nong-nghiep/rau-thuy-canh.pdf; bản stage tmp/w15-candidate/input.pdf |
| SHA-256 | `82cb494d407c4755d29deb7c08b9a4f3794f79e241c307fd2b5dfc149cd559c7` | `1f019766e74a747d293c15ad5bc86b2ea90420b49a8437cf27c1f6805656a627` |
| Trang | 25 | 52; 1,054,520 bytes |
| Web ID | u-82cb494d407c4755d29d | u-1f019766e74a747d293c |
| Parser đo | a1-nhe:r2-full | a1-nhe:r2-full |
| Đọc/kiểm ở dry-run đầu | 8.0288435 giây | 12.652333 giây |
| Đọc/kiểm lượt gần nhất b59cae0 | 2.9100616 giây | 10.828216 giây |
| Calls sinh/embedding/chi thật | 0/0/0 USD | 0/0/0 USD |
| Collector; SQL build/attempt/course/usage/cache | 1 receipt dry_run; mọi count 0 | cùng kết quả |
| Plan label-roles | 78 heading, 2 batch ban đầu | 103 heading, 6 batch ban đầu |

- Manifest doc-6: `report/doc1-rebuild-evidence-2026-10-20/development-fixtures.json`, SHA **`5fc819f723f7263fe3d443ec780009a75aae66f2c35db8fe0bc3e3c50464eb84`**; 127 tệp thuộc doc-6 được kiểm/copy độc lập. Test cần các tệp nguồn này còn tại worktree; không có thì báo thiếu, không đổi sang link.
- Candidate metadata: `report/w15-evidence/candidate.json`; không tự tìm trong tập test để thay.
- Dry-run dùng Vertex/project placeholder dry-run-no-network/global, không ADC. Không chứng minh profile triển khai thật có project/config khác reuse cache. Không dùng pipeline fingerprint này như fingerprint production.
- Core dry-run hiện chỉ ingest/kiểm chữ rồi inspect, 3 event planned; completed_steps chỉ doc_reading; cache_validated=false. `.plan` label-roles là kiểm bổ sung không gọi provider.
- Doc-6 alias v29 khác web u-hash. Artifact gốc có parse/chunks/index theo profile cũ; đọc nhẹ dưới u-hash tạo chunks v1, chưa có candidates/canonical/graph/retrieval. Không rename/đổi version để lách.
- Retrieval fingerprint nguồn đã audit: `d3eb66232372c65f42c6f691d968b09109c38a9791c20a07ea921874cc6faaba`; đổi text chỉ trong RAM bị compatibility guard từ chối. Đây là tương thích nguồn, không chứng minh cache toàn pipeline web hit.
- Cache sinh/embedding toàn chuỗi, số calls/chi/phút các bước sau, embedding wait và tổng trần còn **unknown**. Ước công thức riêng label-roles .002936/.009970 USD trong log không có retry/repair/giá xác minh, không dùng làm trần toàn cuốn.
- Không nhập ảnh SA-65 mới khi chưa có manifest/SHA riêng. Không sửa đè snapshot cũ. Không hứa dựng doc-6 toàn phần miễn phí.

## 7. Cổng và lỗi cần kiểm lại sau nhận main

| Lượt / commit | Kết quả nguyên trạng |
|---|---|
| Mutations a888e92 | 17/17 assertion bắt được; không setup error; restore SHA đúng |
| Mutations sau 4cbd2ac | Lặp 2 guard injection/checkpoint: 2/2 bị bắt |
| Full 424019c | 2414 passed, 1 failed, 1 skipped, 1 xfailed |
| Full 9667235 | 2412 passed, 3 failed, 1 skipped, 1 xfailed |
| Scope 9667235 | 42 passed, native exit 0 |
| Latest b59cae0 | 42 scope passed + 3 prompt assertion failed, native exit 1 |
| React 9667235 | 143 passed; frontend build exit 0 |

Ba lỗi prompt tại mốc cũ:

1. `tests/unit/application/test_phase_b_assistant_sa66.py::test_system_prompt_is_the_text_block_of_the_spec_word_for_word`: assistant_context.py SYSTEM_PROMPT khác doc/tro-ly-3-spec.md.
2. Hai biến thể True/False của `tests/unit/application/test_phase_b_lecture3_sa64.py::test_system_prompt_sent_to_the_model_is_the_spec_text_plus_one_format_line`: lecture3.py SYSTEM_TEMPLATE khác mục 4 doc/bai-giang-3-spec.md, ngoài một dòng SELF_CHECK_LINE được phép.

**Main lúc ghi handoff đã thêm SA-69, nên phải cập nhật hiện trạng bằng kiểm lại; không sao chép nguyên ba lỗi thành kết luận mới.** Không sửa core/prompt/spec/assertion để làm xanh trong làn W-15. Bằng chứng cũ: `main-prompt-provenance-20261024.json`, `prompt-diff-20261024.json` trong w15-evidence; giữ chúng nguyên trạng.

Lỗi full đầu `test_main_checkpoint_review_19k.py::test_transport_failure_preserves_every_finished_call_and_reuses_it[main]` peak=3 thay vì4. Chạy riêng hai biến thể đạt, full thứ hai không lặp; nghi scheduling vì helper sleep 15ms không barrier. Chưa gọi đã sửa; nếu tái diễn ghi bằng chứng mới, không giảm assertion concurrency.

Skip Cloudinary live có sẵn, không bật mạng để hết skip. Xfail SA-55 replay answer-2 so hợp đồng answer-3 đã có trước W-15; không thêm skip/xfail và không chạy paid re-record để ép xanh. Lần chẩn đoán chỉ truyền core path từng lỗi exit4 vì chưa load conftest web đăng ký --require-postgres; đây là lỗi dùng runner, không tính guard bắt hồi quy.

## 8. Bằng chứng và bảo toàn

Thư mục chính `report/w15-evidence/` đã commit, gồm:

- `runs/<label>.log`, `.xml`, `-exit.json`: log/JUnit/native exit/commit/source SHA. Các label quan trọng: `full-main-20261024`, `w15-scoped-final-20261024`, `latest-scope-and-spec-20261024`, `real-dryrun-20261024`, `spec-prompt-red-20261024`.
- `sql/latest-scope-and-spec-20261024/`: 5 JSON postport và 2 JSON real-dry-run, trạng thái/receipt/ledger/cache metadata/collector/SQL count. Không in cache text ra báo cáo.
- `mutations/20261024/mutations.json`, `mutations/20261024-final/mutations.json`: RED và source restore.
- `regression-exports/20261024/`, `w25-regressions/<label>/`: output do test hồi quy viết; giữ bản lịch sử nguyên vẹn.
- `summary-20261024.json`: full_gate_green=false, w15_complete=false, paid_run=false; chỉ phản ánh đúng mốc cũ.
- `manifest-20261024.json`: **401 entry** đã kiểm hash. Manifest cũ `manifest.json` 265 entry, `manifest-20261023.json` 229 entry, `pre-port-20261023/manifest.json` 3 entry đều đã kiểm không đổi.
- `normalization-20261024.json`: hash raw/chuẩn hoá, không đổi giá trị SQL/JUnit.

Các helper bỏ qua Git còn trong tmp/: `w15_finish_20261024.py`, `w15_archive.py`, `w15-raw-evidence-20261024`. Chúng đã chạy, có assertion ghim HEAD/destination cũ. **Không chạy lại mù quáng**, không overwrite manifest cũ hoặc archive cũ. Viết lượt/manifest mới nếu có bằng chứng mới.

Các test W-06/W-14 có thể viết lại export tracked; sau lượt mới xem status, lưu output của lượt mình vào evidence mới rồi phục hồi đúng tệp bằng chứng lịch sử đã xác định. Không dùng restore toàn repo hoặc cuốn sửa dở người khác. Không commit .env, secrets, PDF/artifacts/tmp/document-data/node_modules.

## 9. Quy trình session mới tiếp nhận và làm tiếp

### Bước 1 — Kiểm địa chỉ, trạng thái và nền mới (read-only trước)

Chạy trong PowerShell:

```powershell
Set-Location -LiteralPath 'C:/Users/ngoco/Desktop/Doctoroadmap/tmp/w15-real-build'
git branch --show-current
git status --short
git rev-parse HEAD main
git log -8 --oneline main
git log --oneline HEAD..main
git diff --stat HEAD...main
```

Đối chiếu đúng work/w15-real-build. Nếu có sửa dở, phân biệt của ai/phạm vi trước bất kỳ merge/restore. Handoff này không cấp quyền dọn. Kiểm tiến trình gate đang chạy trên máy trước cổng PG dài; không kill cổng làn khác. Không in command line chứa secret hoặc dump .env.

### Bước 2 — Nhận main trên nhánh W-15, xác định phần phải kiểm lại

Khi worktree sạch và nhánh đúng, `git merge main` tại worktree W-15. Không nhận nhánh SA chưa ghép thay main. Ghi hash main trước merge và hash merge. Đọc diff SA-69/SA-70/new ports nếu có; giữ cả ca dương port và PipelineWithoutStorePort. Không sửa lại adapter đã đạt nếu không có lỗi mới tái hiện.

### Bước 3 — Kiểm nhanh các lỗi cổng và scope, dùng label mới

Luôn dùng Python chung **qua runner** để PYTHONPATH trỏ đúng mã worktree. Không `.venv/python -m pytest` trực tiếp. Runner tự thêm PG bắt buộc; nếu không có DB thì dừng chẩn đoán cấu hình local, không dùng SQLite hoặc bỏ marker.

Ví dụ dưới dùng nhãn minh hoạ mới; nếu đã tồn tại thì đổi nhãn/basetemp/JUnit tương ứng. Không chạy nguyên lại vào tên cũ. Truyền một đường test web khi chỉ lọc core để conftest đăng ký --require-postgres.

```powershell
$w15Python = 'C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe'
& $w15Python -X utf8 src/web/backend/tests/w15_capture.py resume-scope-20261024-01 $w15Python scripts/w05_run_tests.py src/web/backend/tests/test_pipeline_postport_w15.py src/web/backend/tests/test_internal_dry_run_w15.py src/web/backend/tests/test_real_build_w15.py src/web/backend/tests/test_build_cancellation_w25.py tests/unit/application/test_phase_b_assistant_sa66.py::test_system_prompt_is_the_text_block_of_the_spec_word_for_word tests/unit/application/test_phase_b_lecture3_sa64.py::test_system_prompt_sent_to_the_model_is_the_spec_text_plus_one_format_line -o addopts= -q --tb=short --basetemp=tmp/w15-resume-scope-20261024-01 --junitxml=report/w15-evidence/runs/resume-scope-20261024-01.xml
```

Đây chạy lại cả hai dry-run read-only/0 USD đã có guard. Nếu main đã đổi tên test lõi, tìm đúng assertion kế nhiệm; không xóa kiểm đối chiếu spec. Chỉ đọc JUnit/native exit thực, không suy từ count cũ.

Nếu lỗi core vẫn có: ghi tái hiện trên **mốc mới**, phạm vi và hướng chuyển làn sở hữu trong report; không gửi message, không chặn mọi việc chuẩn bị độc lập vì lý do cũ đã hết. Nếu có lỗi W-15 trong src/web, RED → vá tối thiểu → GREEN → review đúng phạm vi.

### Bước 4 — Cổng cả repo đúng đỉnh, sau khi scope ổn

Chạy tuần tự Python/React/build, không mutation đồng thời. Full Python **không truyền đường test** để thu cả tests/ và backend. Cập nhật commentary trong lúc chờ, dùng poll khoảng dưới 60 giây, không bỏ session im lâu.

```powershell
& $w15Python -X utf8 src/web/backend/tests/w15_capture.py resume-full-20261024-01 $w15Python scripts/w05_run_tests.py -o addopts= -q --tb=short --basetemp=tmp/w15-resume-full-20261024-01 --junitxml=report/w15-evidence/runs/resume-full-20261024-01.xml
& $w15Python -X utf8 src/web/backend/tests/w15_capture.py resume-react-20261024-01 npm.cmd --prefix src/web/frontend test -- --pool=threads --maxWorkers=1
& $w15Python -X utf8 src/web/backend/tests/w15_capture.py resume-build-20261024-01 npm.cmd --prefix src/web/frontend run build
```

React ví dụ lưu log/native exit; nếu cần JUnit thêm reporter junit/outputFile với đường tuyệt đối như lượt cũ. WinError5: lưu thất bại rồi chạy lại cả vòng bằng basetemp mới; lặp thì đỏ. Khi main tiến tiếp trong lúc chạy, nhận main/đánh giá đổi và chạy lại theo quy trình; không lấy gate mốc khác trình như đúng commit.

Không phải mỗi lượt docs cần chạy lại toàn gate. Mục đích ở đây là kiểm main có mã core mới chưa được W-15 kiểm, không lặp vô hạn khi không có thay đổi hoặc nghi vấn mới.

### Bước 5 — Hoàn thiện đề nghị lượt thật, chưa chạy

- Giữ đúng candidate/hash52trang, hoặc chủ dự án chỉ định cuốn khác thì lập metadata/manifest mới trước. Không lấy dữ liệu test.
- Lập bảng từng bước: cache hit/miss/unknown; gọi sinh/embedding; USD/phút; embedding wait; trần và điểm dừng. Dùng số đo/planner có nguồn. Không coi missing u-hash là bằng chứng mọi cache miss, hoặc graph v29 là cache hit.
- Core dry-run hiện chưa tính đủ phụ thuộc A3/A4/roadmap/learning_prep; ghi rõ unknown, đề xuất phương án planner/port hoặc một phạm vi thử có điểm dừng để chủ dự án quyết. Không tự mở paid exploratory run.
- Nếu cần thêm port/tệp core, ghi đường dẫn/chữ ký/payload/test vào báo cáo để chủ dự án chuyển đúng làn. Không sửa ké SA-54/56/57 hoặc SA-69/70.
- Chỉ trình xin duyệt sau có đề nghị có căn cứ cho đúng cuốn/hash/lượt/trần. Chờ tin nhắn duyệt, không coi hết thời gian hoặc prompt “tiếp tục” là cấp ngân sách.
- Lượt doc-6 qua web tới ready/mail vẫn chưa làm; nếu chưa chứng minh cache dùng được thì báo giới hạn, không hứa 0 USD hoặc gọi provider để thử.

### Bước 6 — Bàn giao mỗi increment

Ghi report mới hoặc thêm phần hiện hành ở đầu report W-15, không sửa bằng chứng lịch sử. Mỗi lượt có hash main/HEAD, command/native exit, JUnit/log, SQL độc lập, provider/transport guard, manifest SHA mới, giới hạn. Commit đường dẫn cụ thể của mình; báo chủ dự án hash và điều còn chờ. Không tự ghi W-15 đạt/đóng hoặc gửi điều phối.

## 10. Những việc còn mở và tiêu chí dừng

| Việc | Hiện trạng khi kết thúc session cũ |
|---|---|
| Adapter/trace/port dương âm | Đã có, đã giữ |
| Toàn pipeline thật + fake + PG và guard W-25 | Đã chạy/đạt phạm vi 42 tests |
| Dry-run thật có collector và bản sao SHA | Đã chạy 2 cuốn, 0 USD, không queue |
| Cổng tổng sau main SA-69 mới | **Chưa nhận/chưa chạy**; kết quả trước vẫn đỏ |
| Cache toàn chuỗi cho doc-6 web identity/profile thật | Chưa chứng minh; không hứa miễn phí |
| Bảng full calls/USD/phút/embedding wait/cap ứng viên | Còn unknown, chưa có trần đủ căn cứ |
| Duyệt paid W-15 | Chưa có |
| Web doc-6 real ready/mail và cuốn mới real end-to-end | Chưa chạy |
| Đọc chất lượng tên/module/bài giảng, số đo thật và đề xuất hạn mức | Chưa đủ dữ liệu |
| Đóng toàn W-15 | **Không** |

Dừng lượt có thể chi nếu không có duyệt đúng phạm vi, sai transport/identity/fingerprint, mạng được gọi khi allow_spend=False, usage thiếu không giải thích, ledger/receipt trùng, lease cũ publish hoặc vượt trần đã duyệt. Giữ log/SQL, báo chủ dự án và đề xuất sửa đúng làn. Không ép thành công bằng bỏ label-roles/guard hoặc sửa dữ liệu gốc.

Session mới có đủ quyền tiếp tục kiểm/chuẩn bị 0 USD trong phạm vi đã giao, không cần xin lại xác nhận cho đọc/merge main vào nhánh của mình/test fake/báo cáo. Quyền đó không bao gồm chi tiền hoặc sửa main/core ngoài làn.
