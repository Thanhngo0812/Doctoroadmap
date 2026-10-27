# W-12 — Mốc backend lời mời qua email

## Phạm vi và nguồn

Lời giao chủ dự án 2026-10-27, vé `task/web/W-12-moi-qua-email.md`, spec chức năng mục 6,
DB bảng invitation, W-03/W-11 và phân công lần 8. Backend W-04 `c1f2fe9` đã nhận;
không làm lại và không làm React. Nhánh `work/w12-email-invitations-backend`, worktree
`tmp/w12-email-invitations-backend`, tách main `788b600eedc44a161b6ed4c59e88bd59226aa86f`.
Main này có W-04/W-10/SA-61, giữ web Vertex. Nhận main mới bằng merge trước cổng cuối.
Toàn W-12 còn UI hộp mời/khối lời mời và tích hợp do web làm; mốc backend không đóng toàn vé.

Áp dụng Git/TDD/API/security/ponytail theo skill hiện có; chỉ sửa backend sharing/domain/repository,
migration mới, route/DTO, mail template, normalize/hook xác minh và composition tối thiểu.
Không sửa React, lõi học/dựng/giá/transport/ledger, task/kế hoạch/handoff điều phối.
Không gửi message cho phiên khác; mẫu thư và hợp đồng được giao qua báo cáo cho chủ dự án/điều phối.

## Hợp đồng token đã hỏi và chốt

Câu hỏi gửi chủ dự án: “Spec chưa chốt cách dùng token trong link đăng ký. Tôi đề xuất link
`/dang-ky#invitation=<token>`; token chỉ nằm trong thư/fragment, không cấp quyền vào khóa.
Sau khi xác minh đúng email, tài khoản thấy lời mời và chấp nhận qua ID. Anh chọn cách nào?”

Trả lời nguyên văn: **“Dùng fragment, xác minh đúng email rồi nhận lời mời (đề xuất)”**.

Không thêm endpoint đổi token lấy quyền, không thêm payload invitation vào đăng ký W-02/W-03.
Token 32 byte ngẫu nhiên chỉ trong email/fragment, DB chỉ có SHA-256. Mở link bằng tài khoản khác
không gắn lời mời, không tham gia khóa. Xác minh đúng email mới gắn pending, vẫn cần bấm chấp nhận.
Web tiếp nhận fragment khi làm UI sau mốc backend; chưa tuyên bố trang đăng ký hiện xử lý fragment.

## Dữ liệu và giao dịch

Kiểm source Alembic trên main: head `w11_0007`. Migration duy nhất mới `w12_0008`
nối `w11_0007`, không sửa migration đã ghép. Bảng theo spec, token_hash unique 32 byte;
unique partial `(course_id,email_normalized) WHERE status='pending'`, index pending email/người nhận.
Mời lại một pending, kể cả pending có thời hạn đã qua, dùng lại ID/hàng, thay token và hạn 7 ngày;
status đã accepted/declined/cancelled thì lần mời mới có hàng pending mới. List của chủ hiển thị expired
theo clock dù trạng thái lưu còn pending; không chạy job dọn/hủy dữ liệu trong mốc này.

Tái dùng normalize email của AccountService: trim/lower, regex/254 ký tự như W-02;
50 phần tử đầu vào mỗi lần, sau validation gộp trùng. Một email sai làm cả batch lỗi, không gửi một phần.
Hạn mức 200/chủ/ngày là số lượt gửi đã được dành chỗ bằng audit `invitation_sent`, gộp qua mọi khóa
của cùng chủ, độc lập chủ khác. Ngày Việt Nam `[00:00,+1 ngày)` tương ứng đổi ngày 17:00 UTC.
Kiểm count + batch dưới advisory transaction lock theo owner, dùng helper khóa PostgreSQL hiện hành;
không thêm bảng hàng đợi hoặc hệ tài khoản mới.

Thứ tự mutation lời mời: khóa course rồi hàng invitation. Cùng khóa course W-11 dùng khi tham gia
qua link; count capacity + thêm membership `via=email` + status/audit cùng giao dịch.
Retry accept đã accepted và vẫn có membership trả already_member=true, không thêm/audit lần hai.
Nếu đã bị xóa khỏi khóa, lời mời accepted cũ không cấp lại quyền; cần mời mới.
Actor/CSRF/cookie lấy phía server; service đọc lại email/status/xác minh từ account trong DB,
không tin email/owner/account/session/role do body khai. Email khác nhận `not_found`.

AccountService có callback nhỏ `on_email_verified`, composition nối với SharingService sau khi
giao dịch xác minh commit; tầng auth application không nhập hạ tầng invitation. Binding UPDATE đối chiếu
account đã xác minh/active và email normalized ngay ở DB, chỉ pending chưa hết hạn. List lời mời có
binding idempotent để khôi phục nếu process dừng sau commit xác minh nhưng trước callback.
Hai transaction này không được mô tả là một transaction phân tán; việc nhận quyền vẫn kiểm lại email
đã xác minh và membership nguyên tử, nên hook chậm/lỗi không mở bypass.

Tái dùng đúng Mailer W-03, dùng chung instance ở composition. Chỉ gọi mail sau commit invitation/audit;
rollback DB không gửi thư. Nếu Mailer nhận việc rồi SMTP lỗi hoặc hàng đợi W-03 đầy/process restart,
không cam kết thư đã giao: pending vẫn còn và lượt gửi vẫn tính; warning không chứa email/token/provider error.
Chủ khóa có thể mời lại và lượt mới tính vào hạn mức. Không tự retry mail hoặc tạo outbox/hàng đợi mới.

## Hợp đồng HTTP cho web

Mọi đường dẫn dưới `/api/v1`; auth cookie, Origin/CSRF, DTO và no-store theo W-02/W-03/W-11.

| Method/route | Body | Kết quả |
|---|---|---|
| POST `/courses/{cid}/invitations` | `{"emails":["A@example.vn", " a@example.vn "]}` | items đã gộp trùng |
| GET `/courses/{cid}/invitations` | — | pending của khóa, gồm trạng thái expired tính theo clock; chỉ owner |
| DELETE `/courses/{cid}/invitations/{iid}` | — | thông báo hủy; chỉ owner, đúng khóa |
| GET `/me/invitations` | — | pending chưa hết hạn đúng email đã xác minh; chưa xác minh trả items rỗng |
| POST `/invitations/{iid}/accept` | không body/null/`{}` | JoinResult như W-11, already_member/role/joined_at/course_id |
| POST `/invitations/{iid}/decline` | không body/null/`{}` | thông báo từ chối |

Item public: `id, course_id, course_title, email, status, expires_at, created_at, responded_at`.
List dùng join course để lấy tên một query, không N+1 lấy tên khóa; không trả token/hash/invitee ID nội bộ.
POST/accept/decline cấm payload thừa, không lộ request bí mật qua lỗi validation.
Chủ chưa xác minh: 403 email_unverified; khách/disabled giữ chuẩn W-02; ngoài khóa: 404 not_found;
thành viên thường quản lý khóa: 403 forbidden; email khác nhận mời: 404 not_found;
chưa xác minh nhận mời: 403 email_unverified; hết hạn đúng `now >= expires_at`/status không dùng được:
410 link_invalid; đầy khóa: 409 course_full; thư 201: 429 rate_limited/retry_after;
batch/email/payload sai: 422 validation/fields; Origin/CSRF sai: 403 csrf_failed trước body.

Audit `invitation_sent/accepted/declined/cancelled`, actor_id từ phiên, target_kind invitation,
target_id ID lời mời, clock/IP theo hạ tầng hiện hành, meta rỗng; không email/token/hash/mật khẩu.
Mẫu HTML dùng layout W-03, logo cấu hình hiện hành, escape tên khóa/link, hạn 7 ngày và giải thích
chủ khóa thấy tên/ngày tham gia/lần học/tiến độ, không chat/tài liệu/câu trả lời quiz.
Mẫu xuất để thiết kế soát dùng dữ liệu tổng hợp và che token bằng marker rõ ràng.

## Kiểm chứng và lỗi được giữ

`tests/test_w12_invitations.py` chạy PG thật/clock giả, Argon2/cookie auth thật qua composition,
Mailer/model/media giả, chặn SMTP/Cloudinary/ADC/provider. SQL kiểm từ connection độc lập ngoài repository.
Hai runtime dùng engine riêng tranh lượt gửi/suất khóa/accept trùng/mời trùng, không chỉ kiểm cờ gán.

`red-01`: 17 setup errors do fixture truyền SQLAlchemy URL vào WebSettings nhận str, không tính RED nghiệp vụ.
Source schema/repository bắt đầu được thêm trong lúc log lượt setup này chưa trả, nên không dùng lượt đó
để tuyên bố chạy trên một snapshot source ổn định. `red-02` pin SHA riêng: **17 fail/0 setup error**,
route/service invitation chưa có. `green-01`: 16 pass, 1 assertion sai UUID PG so chuỗi HTTP;
sửa test sang str(UUID), giữ log gốc. Các lượt tiếp theo/nguồn mutation/native/JUnit ghi tiếp sau hoàn tất.

Hai assertion head cũ trong test W-11/W-14 được nối sang head mới và thêm kiểm down_revision W-12;
không xóa assertion FK, uniqueness hoặc kiểm race đã nhận. Không sửa test để bỏ gate bảo mật/capacity.

`green-02`: **105 pass** cùng W-03/W-04/W-11. `focused-green-03`: 23 pass; thêm kiểm cổng binding trực tiếp
không gắn tài khoản chưa xác minh/sai email và SQL proof từ connection độc lập:
`focused-green-04`: **24 pass**. Lượt mutation đầu dừng vì teardown SQL proof thiếu fixture `request`;
đồng thời đổi assertion kiểm error JSON thành kiểm status trước rồi code, để mutant thành assertion RED
thay vì KeyError. Đã giữ log/setup error đó, không tính là guard được chứng minh.

| Bất biến | Assertion runnable trong test_w12_invitations.py |
|---|---|
| Gộp email/mời lại một pending, hash/TTL, public DTO | `test_pending_dedup_reinvite_token_hash_ttl_and_public_dto` |
| Đăng ký chưa xác minh chưa gắn, email khác không nhận | `test_registration_not_bound_until_matching_email_verified` |
| Port binding cũng chặn chưa xác minh/sai email | `test_direct_binding_does_not_attach_unverified_or_mismatched_account` |
| Người khác/chưa xác minh không accept/decline | `test_other_user_and_unverified_cannot_respond` |
| Biên 7 ngày, không thêm member, mời lại | `test_expiry_exact_boundary_and_expired_reinvite` |
| Replay accept, từ chối, hủy đúng khóa | `test_accept_replay_decline_cancel_and_course_scope` |
| Owner/validation/Origin/CSRF/payload thừa | `test_owner_authorization_validation_and_csrf` |
| Thư 201/ngày Việt Nam | `test_201st_daily_mail_and_vietnam_day_reset` |
| Hai runtime/engine tranh lượt owner qua hai khóa/suất cuối/accept trùng/mời trùng | `test_two_runtimes_race_on_last_mail_or_course_seat` |
| Rollback DB/status/member khi audit hoặc ghi member lỗi | `test_pg_rollback_on_audit_failure`, `test_pg_rollback_on_membership_write_failure` |
| Head/schema/unique pending thực | `test_schema_pending_unique_hash_and_head` |
| Batch sai không gửi một phần, service cũng kiểm giới hạn | `test_partial_invalid_batch_writes_nothing_and_service_limits_are_enforced` |
| Binding hồi phục khi post-commit hook gián đoạn | `test_verified_callback_covers_all_courses_and_list_recovers_after_hook_interruption` |
| Member đã có không chiếm thêm suất, bị remove không vào lại bằng lời mời accepted cũ | `test_already_member_accept_does_not_consume_capacity_or_restore_removed_access` |
| Mailer lỗi không lộ secret, không tự retry, DB đã commit/hạn mức vẫn tính | `test_mail_failure_is_after_commit_counted_without_retry_or_secret_log` |
| DTO HTTP lọc field private thật và body không chọn người nhận | `test_invitation_dto_filters_private_fields_and_body_cannot_select_recipient` |

Các cửa sổ race được kéo rộng tại read thật bằng delay ngắn trong test, không chép logic sản phẩm.
Test hạn mức dùng hai khóa khác nhau cùng owner để khóa course không che lỗi thiếu khóa owner.

Lượt toàn repo đầu `full-01` trên `6e52bb4`: **3036 pass, 5 fail, 1 skip, 1 xfail**.
Giữ nguyên log/JUnit. Sửa đúng ba điểm tích hợp: fixture AccountService của test composition
cần mailer/callback thay object trống; inventory route khóa cần body emails hợp lệ cho route mới
để thực sự tới assertion quyền 404 (giữ nguyên mọi assertion 404/not_found/probe); renderer account
tiếp tục từ chối kind invitation như W-03, renderer invitation dùng chung hàm layout riêng.
Không đổi test unknown-kind để cho qua và không nới DTO/auth. Đồng thời tăng bằng chứng: đăng ký/xác minh
email khác sau khi có lời mời vẫn không gắn; 7 ngày trừ 1 giây còn hiện, đúng 7 ngày bị chặn;
DB từ chối token_hash ngắn; và W-11 link/W-12 email tranh cùng suất khóa cuối bằng hai engine riêng.

`integration-green-01`: **81 pass**, gồm **25 ca W-12** sau tăng kiểm, cùng composition,
inventory quyền W-06, mailer W-03 và OpenAPI/architecture. Commit sửa `ad7b9fe`, nhận main
`c4e52bb5b62422d702bf3c218778e7ead7020ec9` bằng merge `c6cddc8` (không rebase, giữ output dở).
OpenAPI tái sinh sau cả hai lần merge: **54 operation cũ được giữ, 6 mới, tổng 60**.

Soát sau đó phát hiện hai đường privacy cần phủ: lỗi validation/quyền/CSRF của invitation chưa đi qua
middleware no-store/no-referrer dành cho sharing; ConsoleMailer dev W-03 ghi toàn thân thư nên có thể ghi
token invitation. `privacy-red-01` và `mail-privacy-red-01` đều fail assertion trên hành vi cũ.
Chỉ thêm một dòng nhận diện `/invitations` vào guard privacy sẵn có ở `api/app.py` và che riêng fragment
invitation trong log text/HTML của ConsoleMailer (không sửa SMTP/queue/W-03 token xác minh/reset).
`privacy-regression-green-01`: **71 pass**; `mail-privacy-green-01`: **54 pass**, gồm **27 ca W-12**.

`full-02` đã được chủ động dừng để sửa hai đường privacy trên, khi chưa chạy xong; native
`4294967295`, không có JUnit hoàn chỉnh, không tính là GREEN hoặc lỗi nghiệp vụ mới.
Chỉ dừng đúng pytest leaf của tiến trình sở hữu `--basetemp=tmp/w12-full-02`, không dừng phiên khác
hoặc tự dọn DB/dữ liệu. Log/metadata còn nguyên. Commit privacy `bea0f9b`, nhận main
`c958b89af8980e3bd7f29dc3f227cb1d1e45d0f1` bằng merge `c6a6ae5`;
sinh lại OpenAPI từ app kết hợp vẫn 60 operation. Lượt cổng cuối ghi bên dưới.

## Câu hỏi phối hợp nền đang tiến

Trong lúc `full-03` chạy trên `c6a6ae5`, main lại nhận DG-07 tại `ba784a5` (chỉ làn đánh giá,
không thay backend/OpenAPI W-12). Đã nhận main nhiều lần; một cổng toàn repo hiện khoảng 23 phút.
Theo mục 3.5 quy trình nhánh, trước ghép phải nhận main mới và chạy lại cổng. Hỏi trực tiếp chủ dự án:
tạm giữ main trong một lượt cổng sau khi nhận DG-07, hay cho bàn giao mốc W-12 tại HEAD đã pin để
soát trước, rồi điều phối đồng bộ main/cổng khi chuẩn bị ghép? Chưa có quyết định thì vẫn giữ kết quả
theo đúng HEAD thực chạy, không gán kết quả cũ cho main mới và không tự ghép main.

**Chủ dự án đã chốt, trích nguyên trả lời:** “Cho bàn giao W-12 trên HEAD đã pin; điều phối đồng bộ
main và chạy cổng trước ghép (đề xuất)”. Theo quyết định này, mốc bàn giao pin `c6a6ae5de7206633770582b318ffa14d0c5f85c2`,
đã nhận main `c958b89af8980e3bd7f29dc3f227cb1d1e45d0f1`. Main tiến thêm trong làn đánh giá được ghi quan sát,
không tự nhập vào giữa cổng; điều phối nhận main/cổng cuối khi chuẩn bị ghép. Đây là ngoại lệ cho mốc bàn giao này,
không tuyên bố cổng của HEAD pin đã kiểm cả main mới và không đổi luật ai được ghép/push main.

## Giới hạn chi và trạng thái

Toàn mốc 0 USD; fixture DB/audit là dữ liệu kiểm thử, không mail/thư/usage thật. Web vẫn Vertex,
không SMTP/Gmail/Cloudinary/Gemini thật. Không chạy paid W-15, không nghiên cứu timeout/đổi retry/transport.
Giữ nguyên W-15 DB/artifact/PDF/receipt/plan/grant đã consume. Giá demo billing_verified=false và unknown cũ
0.4139008 USD giữ riêng, không ghi 0 hay hóa đơn. Đề xuất build 5 USD/ngày và 3 lượt có chi/người/tháng
chưa bật và không là quyền chi mới.

Fixture cổng toàn repo chỉ ordinary copy qua helper allowlist/SHA; không link/chuyển run riêng vào kho chung.
Giữ output test cũ ngoài W-12; chỉ commit đường dẫn của mốc, không restore/reset/stash/dọn dữ liệu.
Không tự ghép/push main hoặc sửa hồ sơ điều phối. Backend sẵn sàng soát khi cổng đạt; toàn W-12 vẫn chờ web.


## Kết quả cuối và bàn giao

Commit mã ban đầu `f2c662d9374f327a73134733df935cdc31920764`, sửa tích hợp `ad7b9fe9d5207321bce8410a698a16456f288d92`, sửa privacy `bea0f9b59a6925cd779da2f5be60204bf78def08`, đỉnh đã nhận main và chạy cổng **`c6a6ae5de7206633770582b318ffa14d0c5f85c2`**, main nhận `c958b89af8980e3bd7f29dc3f227cb1d1e45d0f1`; main quan sát lúc bàn giao `a3a20b73ae2d1bdb1108b1b77fe9a00fb2f5c165` (ngoài nền pin, điều phối nhận/cổng trước ghép theo quyết định chủ dự án). PG toàn repo: **3139 pass**, 2 skip/xfail có sẵn; React **219 pass**; build native **0**. Các cổng chạy tuần tự, không có thay source/HEAD giữa cổng; native/lệnh/cwd/source SHA/JUnit trong `w12-evidence/runs/`.

**11/11 mutant bị bắt bằng assertion**, 0 setup error trong lượt được tính, nguồn phục hồi nguyên byte. Tự review correctness/readability/architecture/security/performance: không còn phát hiện chặn; mốc vẫn chờ điều phối soát độc lập.

[JSON/HTML metadata cho web và thiết kế](w12-evidence/public/metadata.json), [mẫu thư HTML đã che token](w12-evidence/public/invitation-email.html), [summary](w12-evidence/summary.json), [manifest SHA](w12-evidence/manifest.json). SQL độc lập có trong từng lượt, đặc biệt `full-03/sql-proof/`; không xuất password/token/hash.

Tổng chi **0 USD**. Mailer/model/media đều giả; không tuyên bố đã giao email thật. Bản evidence commit dùng UTF8/LF, bỏ khoảng trắng/tab cuối dòng vật lý; raw gốc giữ ở `tmp/w12-raw-evidence/`, manifest có cả raw_sha256 và sha256 bản commit. Nếu dữ liệu cấu hình bí mật/token fixture bị in trong traceback thì chỉ bản commit được che với marker rõ ràng; không thay số test/native/source SHA hoặc thuộc tính tên/đếm/trạng thái JUnit; nội dung message có thể che bí mật.

**Backend W-12 sẵn sàng soát; toàn W-12 còn UI/tích hợp của web và thiết kế soát mẫu thư.** Chưa ghép/push main. Giữ nguyên output test ngoài W-12, không đưa chúng vào commit.
