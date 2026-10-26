# Soát độc lập backend W-04 — vòng 8, 2026-10-26

**Kết luận:** nhận mốc backend tại `c1f2fe9` (mã `b8cb7de`), với điều kiện cổng PostgreSQL tích hợp do điều phối chạy xanh. Không có Critical/Required/Optional mới. Toàn W-04 vẫn mở vì chưa có React trang hồ sơ.

## Phạm vi và tính đúng

Đã đọc test trước source, đối chiếu lời giao lần 7, task W-04 và nền W-02/W-03. Mã sản phẩm chỉ thêm AccountService/port/repository/fake/route/DTO và OpenAPI, không sửa core Pha B/learning runtime/frontend/schema/transport/giá.

- `application/accounts.py:341` và `api/auth.py:57`: trim trước kiểm 1–60; payload thừa bị cấm; cập nhật theo actor từ cookie, giữ email/role/password.
- `application/accounts.py:349`: luật mật khẩu W-02 và kiểm current hash trước ghi; `:359` huỷ các phiên khác với session ID lấy từ xác thực máy chủ. Không nhận owner/session ID từ body.
- `application/accounts.py:369`: kiểm lại session/account sau khóa account ID/email/session; không dùng identity hết hiệu lực cho mutation. Các khóa dùng hạ tầng advisory lock hiện hành; transaction PostgreSQL bao cả hash/revocation/audit.
- `infrastructure/auth_store.py:124`: DELETE luôn giới hạn account_id; chỉ thêm điều kiện loại trừ đúng session khi change password. Mặc định không loại trừ, nên reset W-03/logout-all vẫn huỷ mọi phiên.
- `api/auth.py:218`, `:224`, `:231`: giữ middleware Origin/CSRF, DTO public và no-store; logout-all xoá cookie Path=/, HttpOnly/SameSite và Secure theo request/prod. Audit không lưu mật khẩu.

Correctness, readability, architecture, security và performance: thay đổi nhỏ, tái dùng cơ chế hiện có, SQL tham số, không dependency/migration mới hoặc vòng truy vấn không giới hạn. Không có lỗi cụ thể đáng chặn. Hai dạng fields.loc của nền cũ đã được báo rõ để React hỗ trợ, không đổi error handler ngoài phạm vi.

## Kiểm độc lập đã thực thi

Scratch `tmp/coord-r8-core-review-20261026`: chép thường 332 tệp source (2.542.331 byte), SHA từng tệp trong copied-source.json; không link, không chép artifact/cache hay dùng API thật. Luôn chạy qua bản runner w05_run_tests.py có PYTHONPATH scratch. Chọn fake nên không truy cập DB, không tranh cổng PG của điều phối.

1. **24 ca fake/HTTP đạt**, native 0: toàn tập fake của test_w04_accounts.py, gồm 2 cookie độc lập, hash Argon2id, revoke/replay/cross-account, audit, CSRF, mass assignment, validation và reset cũ.
2. **5 probe độc lập đạt**, native 0: hai phiên cùng đã xác thực tranh đổi bằng mật khẩu cũ chỉ đúng một thắng; phiên thua bị unauthenticated, hash đúng mật khẩu người thắng và chỉ một audit. Ba payload thiếu/null current_password trả 422 và không ghi. OpenAPI app thật bằng snapshot, giữ đủ 44 operation main và thêm đúng 3, không xoá route.
3. **2 mutant thật bị bắt**, mỗi mutant native 1 / 1 assertion fail / 0 setup error: bỏ except_session_id khiến A bị huỷ; đảo điều kiện kiểm current_password khiến mật khẩu sai được chấp nhận. Chỉ mutate source accounts.py trong scratch. mutation-summary.json giữ patch/hash; toàn 332 source đã khôi phục đúng SHA. Chạy lại 2 control xanh native 0.

Lệnh đầy đủ, cwd, thời gian/native và XML/log ở runs/. Probe test độc lập: src/web/backend/tests/test_coord_w04_concurrency.py; helper capture.py/mutate.py tái chạy được. Lượt probe 4 ca đầu được giữ riêng; con số cuối là 5 ca, không cộng lặp.

## Kiểm chứng bằng chứng tác giả

- **143/143** tệp bản commit khớp SHA/bytes và **143/143** raw gốc khớp raw_sha256; không có mismatch.
- **8/8** SHA source trong metadata cổng full cuối khớp worker. Mốc b8cb7de→c1f2fe9 không đổi src/scripts/tests/design.
- XML tác giả: 2.810 testcase, 0 failure/error, 2 skip/xfail => **2.808 pass**; React **203 pass**; metadata native 0, build native 0. Đây là cổng tác giả, không nhận thành cổng độc lập của reviewer.
- Cả **10 mutant** tác giả được tính có native 1, đúng failure count, assertion và 0 error trong XML. Log Docker chưa chạy và lỗi harness ban đầu được giữ; không tính làm RED sản phẩm.
- Worker còn 8 report export ngoài vé bị test cũ sửa; báo cáo tác giả đã kê khai. Reviewer không sửa worker hay chạm các output này.

## Giới hạn và bàn giao điều phối

Reviewer không chạy PG. Cổng kết hợp của điều phối cần giữ 49 ca W-04, đặc biệt atomic rollback test_pg_password_hash_revocation_and_audit_commit_atomically, giữ A/huỷ B, logout-all và stale-session các biến thể postgres. Fake concurrency probe không được gọi là chứng minh PostgreSQL concurrency.

Khi nhận W-10 có route/schema mới, tái sinh OpenAPI bằng app kết hợp; không chọn một JSON làm mất route bên kia. Sau backend đạt, web làm trang hồ sơ/đổi mật khẩu/hộp xác nhận logout-all theo thứ tự kế hoạch, rồi mới đóng toàn W-04.

**Chi mới 0 USD; không provider/SMTP/Cloudinary/ADC thật; không merge/push hoặc thay cấu hình.**
