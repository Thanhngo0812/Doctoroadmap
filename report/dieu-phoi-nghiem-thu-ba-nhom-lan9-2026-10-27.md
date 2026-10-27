# Nghiệm thu ba nhóm lần 9 và kế hoạch tiếp — 2026-10-27

**Kết luận:** nhận trọn W-16; nhận mốc backend W-12; nhận guard thiết kế D-R8-02. W-12 vẫn còn React, W-23 vẫn mở vì thiếu cặp ảnh đối chiếu thực. Đã ghép **local 1513ac7f**, chưa push theo quyết định chủ dự án 24/10. Không có quyền chi mới; chi kiểm đợt này **0 USD**.

## 1. Mốc được soát và cổng tích hợp

| Nhóm | Commit bàn giao đã ghim | Phán xét |
|---|---|---|
| Web | 6ee153864522eb1510e3ec88dc5e9c52e1cfe2ca, work/w16-usage-react | Nhận W-16 React và đóng toàn W-16, backend đã nhận d1bf42b |
| Lõi | f5cd20609913ac2c99b6ccb905a365275d8c13a1, work/w12-email-invitations-backend | Nhận backend W-12, migration/mẫu thư/API; toàn vé còn UI |
| Thiết kế | bda1366b8d033ce0dcf4660651959293c178f7c8, work/w24-figma-evidence | Nhận D-R8-02, giữ mốc thiết kế web W-22/W-24; W-23 chưa đạt |

Nền ban đầu e52bf4f2, commit đăng ký cửa nghiệm thu f96c7f86. Ba nhánh được ghép trong tmp/coord-r9-acceptance-20261027, không làm ở thư mục chung. Không giả định thông báo giữ cửa đã được phiên khác xác nhận. Trong cửa kiểm, Claude tiếp tục nhận mã làn đánh giá Pha A; điều phối nhận **main 95827530da45194c353fd0bebffe6bbcb74b03ce** vào candidate **8a3c262fa09962493256604f72e0882447bc803c**, kiểm lại toàn cổng trước ghép. Các merge riêng của làn đánh giá giữ nguyên; đây không phải biên bản nghiệm thu lại DG.

| Cổng điều phối | Nguồn được kiểm | Kết quả |
|---|---|---|
| Python toàn repo, PostgreSQL bắt buộc | 8a3c262f, qua scripts/w05_run_tests.py | 3.407 đạt / 0 fail / 3 skip (Cloudinary live + hai replay DG cần kho graph thật) / 1 replay xfail cũ; native 0 |
| React | 8a3c262f | 229 đạt, native 0 |
| Build React | 8a3c262f | Đạt, native 0 |
| Browser HTTP/PG thật, provider giả | b0d7677b | Đạt; 12 cấu hình, 66 ảnh, 66 Axe, 0 violation, 226 bản ghi HTTP |
| Browser tái dùng sau nhận main | b0d7677b → 8a3c262f | Diff src/web, design và hai harness W-16 rỗng; không gắn nhãn nguồn chụp thành 8a3c262f |

Cổng trước khi nhận main mới ở b0d7677b có 3.193 Python đạt; không dùng số này thay cổng cuối. Hai ca replay DG mới bỏ qua theo điều kiện DANHGIA_KHO_CHUNG chưa đặt; không bật kho dùng chung để lấy kết quả xanh và không nhận nghiệm thu replay graph thật của DG từ lượt này. Toàn bộ lượt trước, kể cả lượt ngắt/đỏ, được giữ. PostgreSQL dùng db-test ở 5433, một cổng toàn repo mỗi lúc; test đánh giá dùng fixture/fake, không chạy pipeline trả phí hay đọc tập giữ lại.

JUnit/lệnh/HEAD/exit/elapsed ở [cổng cuối](coord-ba-nhom-lan9-evidence-2026-10-27/runs/full-rebased.xml), [tổng hợp cổng](coord-ba-nhom-lan9-evidence-2026-10-27/gate-summary.json). [Đối chiếu Git blob](coord-ba-nhom-lan9-evidence-2026-10-27/product-comparison.json) kiểm 36 file thuộc thay đổi ba nhánh: chỉ hai harness W-16 khác nguồn nhân viên vì các điều chỉnh QA dưới đây; application/frontend/test thiết kế bàn giao giữ nguyên. OpenAPI sinh từ ứng dụng tổng hợp vẫn khớp bản ghép, có 60 operation.

## 2. Web — W-16 đạt, không chuyển chính sách core lên React

Trang Mức dùng, menu tài khoản và dải hết trần dùng usage-1; hiển thị tỷ lệ và giờ đặt lại Việt Nam, không USD/cost cho người học. Max=null là “không giới hạn”, không biến thành hết lượt. Các trạng thái 35%/85%/100%, giới hạn dựng hữu hạn/tắt, lỗi/tải lại, callback cũ và refresh sau thao tác đã được kiểm. Ngưỡng nhãn gần hết 80% là lựa chọn trình bày của React; spec không ấn định 70% hoặc 80%, không phải thay đổi trần tiền.

Kiểm độc lập gồm 48 ca hiện có + 2 ca focus/abort + 1 ca event callback. Năm phép phá đều bị assertion bắt: max=null sai, hết trần chặn cache, giờ máy thay giờ Việt Nam, callback abort ghi dữ liệu cũ, callback cũ phát thêm refresh. Source khôi phục đúng SHA; 299 file bằng chứng nhân viên, 57 file source copy, bốn bộ nguồn cổng × 783 file đều đối chiếu đúng, có ghi khác biệt checkout CRLF/Git LF. Không cộng các lượt chạy chồng lặp vào số test toàn repo. [Review web](coord-ba-nhom-lan9-evidence-2026-10-27/web-review/review.md).

Trong browser thật:

- Khi người học hết trần, ý định vẫn đến core và trả daily_limit; phát lại cùng ý định không tăng model call. React không tự sinh hoặc tự ấn định ngân sách.
- Khi trần nội dung chung chạm, bài đã có vẫn mở, bài lạnh trả tran_he_thong, quiz trong ngân hàng vẫn dùng được. Trước/sau đều 50 ledger row; lectureCalls=1, generatorCalls=1, documentCalls=4, assistantCalls=0. Đây là quan sát độc lập, không chỉ kiểm cờ trạng thái.
- SQL riêng xác nhận 4 tài liệu và 2 quiz attempt đúng người học. Số USD trong ledger thử là dữ liệu giả để kiểm trần, **không phải chi nhà cung cấp thực** và không cộng vào mục chi.

**Giới hạn:** 220 JSON response đã thu đủ body, không còn privacyFailure/pendingRejection/pageError. Có hai SSE: lecture thu đủ và có failure tran_he_thong; trường terminalSeen của helper không nhận diện terminal lecture. Stream quiz chưa thu trọn đến terminal vì harness chuyển trang khi câu hỏi xuất hiện. Vì vậy đợt này không tuyên bố kiểm đầy đủ terminal/privacy của mọi stream; nhận W-16 dựa trên UI/SQL/model-count và giữ nguyên cổng W-10 đã nhận ở R8, không nhận thêm hợp đồng stream mới. [Audit browser](coord-ba-nhom-lan9-evidence-2026-10-27/browser/audit.json), [tổng hợp](coord-ba-nhom-lan9-evidence-2026-10-27/browser-summary.json).

Chất lượng thị giác được xem trên ảnh thật ở desktop/mobile, 390/768/1280, sáng/tối và giảm chuyển động. Không tràn ngang hoặc target dưới ngưỡng trong harness; 92 mẫu contrast bổ sung có mức thấp nhất 5,84:1. Be Vietnam Pro tải ở cả ba cỡ. Taste inspector không FAIL; có một WARN khoảng trắng 48px trong thẻ 100% ở desktop, là gợi ý polish không chặn vé. Không dùng kết quả inspector thay toàn bộ W-23.

Console không trống: 2 lỗi HTTP 401 dự kiến trong kiểm auth, 132 thông báo CSP (font/inline bị chặn), 1 ERR_FAILED do điều hướng; pageErrors=0. Log server có cảnh báo đóng kết nối WinError10054/graceful shutdown trong kiểm browser; runtime cuối xác nhận thread dừng. Không gọi các log này là lỗi sản phẩm đã sửa hoặc chứng nhận không có cảnh báo.

## 3. Lõi — nhận backend W-12, còn React

Đã có sáu route lời mời, SharingService và port/store PostgreSQL, migration w12_0008 nối w11_0007, mẫu thư FakeMailer. Hợp đồng giữ 50 email/lần sau kiểm/gộp trùng, 200 thư/chủ/ngày giờ Việt Nam, TTL 7 ngày; mời lại cập nhật hàng cũ; chỉ đúng email đã xác minh được gắn/nhận lời mời. Membership và hạn chỗ được bảo vệ nguyên tử, bao gồm cạnh tranh link/email và lỗi audit rollback. ConsoleMailer không in fragment token; DB chỉ giữ hash.

Quyết định link được báo cáo nhân viên trích từ chủ dự án: **“Dùng fragment, xác minh đúng email rồi nhận lời mời (đề xuất)”**. Backend phát /dang-ky#invitation=<token>; raw token không cấp membership, không bỏ yêu cầu xác minh/email. Web phải hoàn thiện luồng fragment/đăng ký/đăng nhập/UI; backend đạt không thay nghiệm thu frontend hay chứng minh thư đã phát thật.

Kiểm độc lập 21 ca dùng application thật và SQL binding SQLite; không gọi đó là lượt PostgreSQL. Ba mutant độc lập bị bắt, không setup error, source phục hồi đúng SHA. Audit kiểm 383 file bằng chứng, 17 file source identity và tái tạo 11 mutant nhân viên với XML assertion fail. Cổng PostgreSQL điều phối kiểm test_two_runtimes_race_on_last_mail_or_course_seat (gồm link/email), test_pg_rollback_on_audit_failure, test_schema_pending_unique_hash_and_head, test_registration_not_bound_until_matching_email_verified và test_verified_callback_covers_all_courses_and_list_recovers_after_hook_interruption. Các ca này kiểm cạnh tranh suất cuối, rollback, schema và ràng buộc verified email. [Review lõi](coord-ba-nhom-lan9-evidence-2026-10-27/core-review/review.md), [probe độc lập](coord-ba-nhom-lan9-evidence-2026-10-27/core-review/test_independent_w12.py).

Ghi chú **Optional**: callback gắn lời mời chạy sau commit xác minh email; callback lỗi có thể làm HTTP báo lỗi dù token/email đã commit. List_my_invitations tự sửa liên kết còn thiếu, không cấp quyền sai và có test ngắt/hồi phục. Có thể cải thiện cảnh báo vận hành/trả kết quả xác minh trong vé nhỏ riêng; không coi đây là Required đang chặn backend W-12 và không tự sửa mã sản phẩm khi điều phối.

## 4. Thiết kế — guard đạt; W-23 chưa đủ bằng chứng

D-R8-02 đã được làm đúng: VM lấy onclick từ markup thật, không truyền tham số cứng bỏ qua wiring. Kiểm độc lập 64 xanh → sửa markup here/elsewhere thành button/assistant → 1 assertion fail/0 error/native 1 → phục hồi SHA → 64 xanh. Nhận cải thiện guard, không làm lại token/branding/math hoặc Cloud.

Review phát hiện hai Required tài liệu, đã sửa có ngày trong [báo cáo phối hợp W-24/W-23](w24-w10-w23-phoihop-2026-10-25.md):

- **D-R9-01:** source anchor không phải ảnh HTML cùng trạng thái. Rút kết luận padding/font/44px hoặc chấp thuận bố cục khi chưa đo/có quyết định. Sửa mô tả thư viện React có hai tab tại module, không phải ba; ảnh superscript không chứng minh subscript. Video mới chỉ xem mẫu frame, không xác nhận liên tục mọi khoảng thao tác tác giả nêu.
- **D-R9-02:** ảnh W-10 browser-r7-main có nguồn chạy 1fc0f553bec808241388b722fa2c10a1c6ead33d, không phải aaf68eb. Diff frontend/harness đến aaf68eb rỗng nên được tái dùng đúng phạm vi, không đổi nguồn chụp.

Cả 10 PNG/3 WEBM tham chiếu có thật và bytes khớp nguồn; anchor tồn tại không chứng minh hai giao diện đồng nhất. **W-23 vẫn mở.** Lượt tiếp phải tạo cặp chụp HTML/React cùng viewport/theme/motion/state, nguồn SHA/URL/crop/font/số đo và cách xử lý lệch. Modal/viewer hay menu khác mẫu mà đều hợp lý phải ghi đề xuất cần chủ dự án chọn. Không tự duyệt thay. [Review thiết kế](coord-ba-nhom-lan9-evidence-2026-10-27/design-review/review.md).

## 5. Điều chỉnh QA và các lượt bị ngắt

Điều phối không sửa application. Chỉ sửa harness để ghép/kiểm chính xác:

1. scripts/w16_web_runtime.py đổi assertion head từ w11_0007 sang w12_0008 do nhận migration W-12 (commit 2d36ed7b).
2. scripts/w16_web_check.cjs thu JSON bằng clone trước khi giao response cho app, tránh response.text DevTools mất body sau điều hướng (605d13d2).
3. Sửa guard thu JSON phải giữ lỗi đọc/parse/privacy vào mảng lỗi audit ngay cả khi app catch promise (b0d7677b). Review độc lập QA-R9-JSON-1 thấy RED trên 605d13d2, GREEN trên b0d7677b bằng callback và final assertion thật trích từ harness. Sáu ca safe/abort chủ động được phép; private/malformed/unexpected abort/read error buộc final audit thất bại. [Review QA](coord-ba-nhom-lan9-evidence-2026-10-27/web-review/qa-json-review.md).

Các lượt full/browser ban đầu bị ngắt khi phiên nhận “tiếp tục”, hoặc do điều phối dừng đúng tiến trình của mình trước thay đổi QA, không có JUnit/receipt hoàn tất thì không tính xanh. Lượt browser-resume native 1 do body DevTools không đọc được sau điều hướng là lỗi harness đã giữ log; không gán thành lỗi application. Các lượt full-resume/full-json đã dừng và browser-json chỉ là checkpoint, không thay cổng cuối. [Kiểm kê lượt ngắt](coord-ba-nhom-lan9-evidence-2026-10-27/interrupted-runs.json).

DB UUID của lượt browser đầu bị ngắt **wayfinder_w16_ea97feb131fd4688b60ae0a216f91c6e** được giữ nguyên, không dọn. DB UUID của harness cuối đã tự kết thúc vòng đời; kiểm SQL độc lập không còn DB đó, cổng 8026 đóng, thread dừng. Không đụng DB W-15, dữ liệu gốc hoặc tmp/t01a-clean-ff797eb. Fixture phát triển đưa vào worktree bằng bản chép thường 3.144 tệp theo allowlist/SHA, không dùng liên kết. Candidate PDF 1.054.520 byte có SHA-256 1f019766e74a747d293c15ad5bc86b2ea90420b49a8437cf27c1f6805656a627, nlink=1; không dựng paid từ tệp đó.

## 6. Kế hoạch tiếp và phân vùng

| Nhóm | Việc tiếp theo | Điều kiện bàn giao |
|---|---|---|
| Web | React W-04; sau đó React W-12 trên nhánh riêng | Hai phiên đổi mật khẩu/logout-all; sau đó UI mời/fragment/email verified/giới hạn và membership qua API thật, ảnh/video/SQL |
| Lõi | Backend W-17.1: quản trị người dùng và audit | Quyền admin, khoá/hủy phiên, không mất admin cuối khi cạnh tranh, audit/rollback/không lộ dữ liệu học; toàn W-17 còn mở |
| Thiết kế | W-23 cặp ảnh thực, trước tiên self-check W-08 và thư viện W-10; hỗ trợ mẫu W-04/W-12 | Hai ảnh cùng state có provenance/số đo, bảng lệch/cách xử lý và video; không Cloud |

Phần W-17 còn lại đi sau: bản dựng/khoá mẫu, rồi chi/log validation/Cloudinary; không gom cả khu quản trị vào một thay đổi khó soát. Bảng chi sau này không cộng trace counted_in="build", chỉ receipt/delta dựng một lần, giữ cờ usage thiếu và nhãn ước theo token. Không bật đề xuất trần demo 5 USD/ngày hay 3 lượt/tháng. W-18/W-19/W-20/W-21 chưa được nhận hoàn tất.

Đã soạn [bản giao việc ba nhóm lần 9](lenh-giao-viec-ba-nhom-lan9-2026-10-27.md), **chưa gửi phiên bên ngoài**. Mỗi phiên nhận main mới, worktree/nhánh riêng; một cổng PG toàn repo mỗi lúc. Coordinator chốt exact commit, nhận main mới, chạy cổng rồi merge --no-ff local. SA-61 đã ghép ab5c2fa, web vẫn Vertex đến chỉ thị đổi của chủ dự án.

## 7. Bảo toàn và chi phí

Không thêm lời gọi Gemini/SMTP/Cloudinary/ADC thực, không phát grant, không chạy lại W-15/khôi phục. Chi điều phối mới **0 USD**. Các giá trị giả lớn trong SQL kiểm hạn không phải tiền đã chi. Chi lịch sử W-15 giữ ở biên bản trước; không cộng lại vào đợt này.

Sáu tệp dở lịch sử giữ nguyên SHA. Tệp kế hoạch đánh giá Pha A được phiên khác cập nhật/commit trong cửa R9; ghi mốc quan sát mới, không khẳng định nó còn cùng SHA lúc bắt đầu và không đưa phần dở vào commit điều phối. uv.lock cũng xuất hiện phần sửa của phiên khác và được bảo toàn. [Snapshot tệp bảo vệ](coord-ba-nhom-lan9-evidence-2026-10-27/protected-resume.json) cùng kiểm cuối ghi tám tệp được giữ kể từ lúc tiếp tục. Không add rộng/stash/reset/restore file của người khác.

[Manifest bằng chứng](coord-ba-nhom-lan9-evidence-2026-10-27/manifest.json) ghi SHA raw và SHA bản text chuẩn hoá LF, không thay raw. Bộ browser lớn/66 ảnh/2 video giữ ở worktree, có danh sách SHA và ảnh đại diện trong gói. Bằng chứng guard thất bại cũng được giữ. Cửa nghiệm thu/PG mở lại sau commit hồ sơ local; **không push**.
