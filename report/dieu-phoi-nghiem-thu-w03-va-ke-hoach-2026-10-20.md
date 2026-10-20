# Điều phối — nghiệm thu W-03 và khởi động lại sau sự cố artifact

**Ngày:** 2026-10-20 · **Người soát:** Codex · **Trạng thái:** **đạt nghiệm thu W-03**, đã ghép **`63f09ad`** và đẩy GitHub; mốc soát/cổng cuối `9de8e75`.

## 1. Phạm vi và mốc kiểm

Chủ dự án xác nhận các nhóm dừng sau sự cố artifact, web mới hoàn tất W-03. Báo cáo này kiểm W-03 trước rồi lập kế hoạch tiếp; không xem W-06 hay toàn bộ W-24 là đã xong.

- Main nền: `37ad48f23f61a11f7610c2556110e9fca7873d29`.
- Nhóm web giao: `e1f62974e42e3ac8036a6fe82ff79fb69ec0bf9c`, nhánh `work/w03-email-recovery`.
- Mốc sau sửa phát hiện khi soát: **`9de8e753eaf521dc2f0938d43236aa156d335c93`**, nhánh `work/coord-w03-acceptance`, worktree mới `tmp/coord-w03-acceptance`.
- Chênh lệch `e1f6297..9de8e75` chỉ sửa năm câu chữ trong hai bản thiết kế local; mã backend/React và harness trình duyệt giống nhau. Soát backend và chạy trình duyệt trên mã W-03 này; cổng cuối Python/React/build ghim riêng `9de8e75`.
- Chép 3.081 tệp / 195.556.758 byte từ snapshot cố định `document-data/development-rebuilt-2026-10-20`, kiểm SHA-256 cả nguồn và đích; không dùng liên kết. Không mở kho Pha B live chung hoặc tập giữ lại; không dọn worktree.

Nguồn đối chiếu: [vé W-03](../task/web/W-03-xac-minh-email-quen-mat-khau.md), [hợp đồng HTTP](w03-hop-dong-trien-khai-2026-10-20.md), [bàn giao schema](w03-schema-handoff-2026-10-20.md), [báo cáo web](web-w03-nghiem-thu-2026-10-20.md), [bổ sung logo](web-w03-logo-email-2026-10-20.md).

## 2. Phán xét mã và phát hiện đã sửa

Soát độc lập backend tại `e1f6297`: không còn lỗi Critical/Required; chạy thêm 70 test chuyên biệt đạt. Đã kiểm vòng đời token, chuẩn hoá email, transaction/khoá khi reset đồng thời với login/request, huỷ phiên, Origin/CSRF, bảo mật thư và escape mẫu HTML. Sau bản sửa thiết kế, người soát chấp thuận `9de8e75` cho W-03 và phần thiết kế local mang theo, không chấp thuận đóng W-24/Figma đầy đủ.

**Lỗi Required đã sửa:** plugin Figma và preview auth ghi link reset có hạn 15 phút, có chỗ ghi cả link xác minh 15 phút; trái hợp đồng đang chạy. Commit `9de8e75` sửa reset thành **60 phút**, xác minh thành **24 giờ** trong `design/figma-plugin/code.js` và `design/preview/w03_auth_screens.html`. Không thay TTL backend để chạy theo bản vẽ sai.

Các commit mang theo `781415b`, `79cb9c9`, `6cd6be7` đã được xét trong phạm vi lần ghép này: bố trí thông báo W-02 được giữ, dữ liệu token local được ghi đúng nguồn local, preview và helper được phép tích hợp sau khi sửa TTL. Các giới hạn sau vẫn thuộc W-24:

- Chưa có bằng chứng Variables xuất trực tiếp từ file Figma và bảng đầy đủ trang/trạng thái/node/video.
- Helper nối reaction có nhánh bắt lỗi/không nối khi API không sẵn sàng, trong khi thông báo cuối vẫn có thể nói đã nối. Không lấy thông báo đó làm chứng cứ prototype Figma hoạt động.
- Audit HTML đã tiến bộ nhưng chưa chứng minh clipboard thật, hành vi citation/scroll đầy đủ hoặc GIF đứng khung theo thời gian. Không dùng con số 4/4 để đóng các mục này.

Ghi chú không chặn W-03: cùng status/body của yêu cầu reset chưa chứng minh không có kênh chênh lệch thời gian; hàng đợi thư ở bộ nhớ không bảo đảm giữ thư qua lần khởi động lại. `git diff --check` còn khoảng trắng trong preview/helper và bằng chứng RED được mang theo; không sửa định dạng ngoài phạm vi để đổi mốc vừa kiểm. Log React độc lập cũng có dòng trống cuối do công cụ in ra; giữ nguyên byte và SHA-256 của bằng chứng. Kiểm khoảng trắng cho các tệp Markdown điều phối riêng đạt.

## 3. Kiểm thử do điều phối chạy

| Phép kiểm | Kết quả | Bằng chứng độc lập |
|---|---|---|
| Cổng nền trước bản sửa câu chữ | 2.085 đạt, 0 fail, 1 bỏ qua, exit 0; 434,09 giây | `coord-w03-evidence-2026-10-20/baseline-python.*` |
| Cổng cuối tại `9de8e75`, PostgreSQL bắt buộc | **2.085 đạt, 0 fail, 1 bỏ qua, exit 0; 358,44 giây** | `coord-w03-evidence-2026-10-20/final-python.*` |
| React tại `9de8e75` | 62 test đạt, exit 0 | `coord-w03-evidence-2026-10-20/final-react.log` |
| TypeScript/Vite build tại `9de8e75` | đạt, exit 0 | `coord-w03-evidence-2026-10-20/final-build.log` |
| Soát backend độc lập | 70 đạt | `coord-w03-evidence-2026-10-20/reviewer-backend.xml` |
| Chromium, HTTP + PostgreSQL + Argon2 thật | 18 cấu hình giao diện, 8 assertion luồng, 4 trạng thái link lỗi; 0 lỗi JavaScript, 0 tràn ngang, 0 vi phạm axe được phát hiện | [browser-audit.json](coord-w03-evidence-2026-10-20/browser-audit.json), [runtime](coord-w03-evidence-2026-10-20/isolated-runtime.json), ảnh và video cùng thư mục |
| Taste inspector ở 1280/768/390 | 0 FAIL, 1 WARN khoảng trống desktop; chấp nhận cho form một nhiệm vụ | `coord-w03-evidence-2026-10-20/taste-inspect.log` |
| Prototype HTML local | bản đúng 4/4; cố ý vô hiệu gập nội dung thành 3/4, exit 1 đúng assertion | `coord-w03-evidence-2026-10-20/prototype-green.log`, `prototype-red.log`, `prototype-mutation.json` |

Một test bỏ qua là Cloudinary live, chỉ chạy khi bật rõ `WAYFINDER_RUN_CLOUDINARY_TESTS=1`; PostgreSQL không bị bỏ qua. Dùng Mailer giả, không gửi Gmail thật, không gọi mô hình hoặc Cloudinary. **Chi mới: 0 USD; lời gọi mô hình: 0.**

Trình duyệt chạy cơ sở dữ liệu tạm riêng, migration lên đúng một head `w03_0004`, rồi tự đóng và xoá đúng DB tạm của harness. Đã quan sát độc lập:

1. Đăng ký có thư giả; mở GET không tiêu thụ token; POST xác minh cập nhật tài khoản thật.
2. Link xác minh/reset hết hạn hoặc đã dùng bị API từ chối và giao diện hiển thị đúng; không sót thông báo thành công của link trước.
3. Yêu cầu reset cho email có/không có tài khoản cùng phản hồi; email không tồn tại không có thư.
4. Mật khẩu xác nhận lệch bị chặn ở form; reset thành công huỷ cả hai phiên cũ; mật khẩu cũ thất bại và mật khẩu mới đăng nhập được.
5. Giảm chuyển động không còn animation phản hồi đang chạy. Ảnh sáng/tối được chụp tại 390, 768, 1280 px; đã xem ảnh thực trên desktop/mobile.

Ba phép phá expiry/single-use/session-revocation của W-03 nằm trong cổng cuối; tên test và kết quả được lưu JUnit. Phép phá prototype của điều phối chỉ tác động bản HTML tạm, không sửa bản sản phẩm.

Đối chiếu tiêu chí vé với assertion chạy được (tên đầy đủ có trong JUnit):

| Tiêu chí | Test tiêu biểu |
|---|---|
| Đăng ký một thư, xác minh một lần, chỉ lưu băm | `test_register_sends_one_hashed_token_and_verification_is_one_use`, `test_postgres_persists_only_token_hash_and_reset_revokes_every_session` |
| Xác minh hết hạn 24 giờ, email đổi thì link cũ vô hiệu | `test_verification_expiration_and_changed_email_are_rejected` |
| Gửi lại chỉ ba lần mỗi giờ | `test_resend_is_limited_by_shared_store_and_sends_three_per_hour` |
| Reset không lộ email tồn tại, giới hạn chung qua nhiều store | `test_password_reset_request_is_generic_and_throttles_known_and_unknown_emails`, `test_postgres_reset_throttle_is_shared_across_store_instances_and_knownness` |
| Reset 60 phút, một lần, huỷ mọi phiên và token reset khác | `test_password_reset_token_expires_after_sixty_minutes`, `test_password_reset_is_single_use_revokes_all_sessions_and_other_reset_tokens` |
| Token đồng thời/rollback không để trạng thái nửa chừng | `test_postgres_one_use_token_is_serialized_across_independent_stores`, `test_postgres_password_reset_transaction_rolls_back_token_and_session_on_store_failure` |
| Không tháo Origin/CSRF | `test_public_recovery_posts_still_reject_missing_and_foreign_origin`, `test_public_reset_request_is_generic_but_resend_requires_session_and_csrf` |
| Guard phải bắt được bản sai | `test_expiry_assertion_rejects_a_removed_expiry_check`, `test_one_use_assertion_rejects_removed_consumption`, `test_revocation_assertion_rejects_removed_session_deletion` |

Không có Chrome DevTools MCP khả dụng trong phiên; dùng Chromium thật qua Playwright đã có, không giả là đã chạy MCP. Skill áp dụng: `code-review-and-quality`, `security-and-hardening`, `git-workflow-and-versioning`, `browser-testing-with-devtools` với fallback nêu trên, `design-taste-frontend`, `planning-and-task-breakdown`.

### Lệnh tái lập

Chạy từ `tmp/coord-w03-acceptance`, bằng interpreter thư mục chung:

```text
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe scripts/w05_run_tests.py -o addopts= -q --basetemp=tmp/coord-w03-final --junitxml=tmp/coord-w03-final.xml
npm.cmd --prefix src/web/frontend test -- --pool=threads --maxWorkers=1
npm.cmd --prefix src/web/frontend run build
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe -X utf8 scripts/w03_browser_runtime.py
node tmp/coord-verify-prototype.cjs
node tmp/coord-mutant-prototype.cjs
```

Lệnh cuối **phải exit 1**. Hai bản script prototype tạm chỉ đổi đường dẫn công cụ Playwright dùng chung và mục tiêu HTML bản phá; bản nguyên trong repo có đường dẫn công cụ không tồn tại ở worktree mới. Các lượt Python/npm được gọi bằng `subprocess.run`, lưu native return code, không suy đoán từ mã thoát pipeline PowerShell. Giữ riêng kết quả trước và sau sửa; không gắn lại nhãn commit cho lần kiểm cũ.

## 4. Dữ liệu đã đủ để tiếp tục phần nào?

Sáu graph phát triển tải được qua kho hiện tại; số đo chỉ gồm metadata:

| doc_id | graph_version | module | khái niệm học được |
|---|---:|---:|---:|
| doc-1 | 8 | 35 | 223 |
| nhap-mon-ml | 50 | 15 | 75 |
| naive-bayes | 49 | 5 | 33 |
| doc-6 | 29 | 2 | 11 |
| xstk-ch3-1 | 68 | 14 | 82 |
| doc-4 | 27 | 91 | 495 |

Vì vậy **W-06 không còn bị chặn bởi việc phải dựng lại doc-1/doc-6**. Đây là kiểm graph tải được, không phải nghiệm thu mọi luồng bài giảng/chat/quiz hay xác nhận mọi media đã đưa lên Cloudinary.

Doc-6 đã khớp 122/122 SHA-256 trong đợt phục hồi. Doc-1 mới dùng v8; không giả v45/v57. Quiz unit đã dùng fixture trong repo. Cache CLI doc-1 tách riêng theo [runbook](../doc/du-lieu-phat-trien-va-fixture.md); web W-06 phải nối đúng `PostgresPhaseBStore`, không nhập cache live chung hoặc cho runtime rơi về JSON. Giới hạn quiz cloze offline 1/5 ở mẫu đã thử vẫn cần xử lý trước nghiệm thu quiz W-10, không che bằng test xanh W-03.

## 5. Kế hoạch tiếp theo và điểm nghiệm thu

Ưu tiên **một vé W-06 đầu-cuối**, lõi và web cùng làm trên hợp đồng rõ; thiết kế tiếp tục W-24. Không yêu cầu làm lại W-01/W-02/W-05/W-13 khi mã không đổi. Các lời giao có thể sao chép ở [tệp riêng](lenh-giao-viec-sau-w03-2026-10-20.md); chưa gửi sang phiên nhân viên.

| Thứ tự | Nhóm và việc | Đầu ra bắt buộc | Điểm kiểm để mở việc sau |
|---|---|---|---|
| 0 | Điều phối chốt W-03, ghép đúng mốc, cập nhật hồ sơ | main và origin/main cùng mốc; báo cáo/cổng/ảnh; schema `w03_0004` | W-03 đạt, không còn tranh sửa AccountService |
| 1 | Lõi + web chốt hợp đồng W-06 | JSON `GET /courses`, roadmap; lỗi/route; giao diện mẫu/ẩn mẫu ở prod; phân vùng tệp và nhánh | Chốt route join-sample được phép tham gia và phạm vi test người ngoài trước khi cài, không miễn guard rộng |
| 2 | Lõi làm backend W-06; web làm React W-06 song song | `course`, `membership`, migration `w06_0005` nối `w03_0004`; gateway + PostgreSQL/spend guard; trang ba nhóm, tham gia, rỗng/tải/lỗi | DB rỗng lên HEAD; test owner theo actor; test thêm route bỏ guard phải đỏ; trình duyệt gọi API thật; cổng đầy đủ |
| Song song | Thiết kế tiếp W-24, ưu tiên trang W-06 | Variables export thật, bảng node/trạng thái, bốn prototype Figma/video, guard tương tác; TTL auth đúng | Chỉ đóng W-24 khi đủ bằng chứng, không để thông báo helper thay kiểm bấm thật |
| Sau W-06 | Web W-07, W-11; phân công lõi W-14 bộ dựng giả | đường học mẫu/lộ trình, chia sẻ; sau đó tải sách/hàng đợi/worker | Soát lại phụ thuộc Pha B2; W-14 chỉ mở khi W-03 và W-06 đạt; W-13 đã có |
| Khi có người hoặc sau tích hợp W-06 | Web W-04 | hồ sơ/đổi mật khẩu/đăng xuất mọi nơi | Không tách người khỏi đường W-06 nếu chỉ có một phiên web; phân vùng AccountService nếu làm song song |
| Về sau | W-08/W-09/W-10; W-15; W-23/W-21 | nội dung học, dựng thật, đối chiếu thiết kế, triển khai | Đúng phụ thuộc vé; W-15 dry-run và duyệt tiền riêng, W-23 chờ W-22 + các màn học |

**W-06 chia điểm bàn giao nhỏ:** hợp đồng trước; một khoá mẫu tham gia được trên DB + UI; rồi đủ danh sách/gateway/guard; cuối cùng cổng tích hợp. Backend riêng hay React mock riêng không đủ đóng vé. Migration nối `w01_0001 → w05_0002 → w02_0003 → w03_0004 → w06_0005`; không sửa migration đã ghép.

**Rủi ro hợp đồng W-06 cần chốt ngay:** vé nói tự liệt kê mọi route `{cid}` và từ chối người chưa là thành viên, đồng thời có `POST /courses/{cid}/join-sample`. Người tham gia lần đầu chưa là thành viên; không được triển khai hai điều mâu thuẫn rồi nới guard để xanh. Nhóm ghi đề xuất ngoại lệ hẹp chỉ cho khoá mẫu công khai và hành vi prod, để điều phối chốt hợp đồng trước vòng test; mọi route nội dung vẫn phải chặn người ngoài. Báo cáo này chưa tự sửa luật đặc tả.

Trước W-07…W-10, soát độc lập các bàn giao Pha B2 còn treo SA-46/47/49/50/51; không xem trạng thái nhân viên báo xong là đủ nghiệm thu. Không dùng ngân sách phục hồi doc-1 làm phê duyệt chi cho vé mới.

**An toàn dữ liệu cho cả ba nhóm:** nhận main mới trong worktree riêng; dữ liệu test chép theo manifest, kiểm hash, không liên kết; không đụng `tmp/t01a-clean-ff797eb`, không xoá snapshot/ZIP, không dọn worktree. Worker không tự ghép main; bàn giao commit + báo cáo + lệnh kiểm. Backend tiếp tục Vertex; mọi kiểm W-06/W-24 là 0 USD.

## 6. Kết quả ghép

- Commit ghép: **`63f09adef5987bb59f6606e453be565eca9267a2`**, hai cha `37ad48f` và đúng mốc được soát `9de8e75`; `--no-ff`, không xung đột.
- Đã `git push origin main` thành công: `37ad48f..63f09ad main -> main`. Đã đối chiếu mã `src/`, `tests/`, `design/`, `scripts/` ở commit ghép giống hệt mốc qua cổng.
- Hồ sơ điều phối cập nhật sau ghép gồm vé W-03/W-04/W-06/W-24, bảng kế hoạch, nhật ký bàn giao, báo cáo này, lời giao ba nhóm và thư mục bằng chứng độc lập có manifest SHA-256. Các commit hồ sơ không đổi mã sản phẩm.
- Giữ nguyên worktree của nhân viên và worktree nghiệm thu; không có lượt dọn dữ liệu hay xoá worktree. Có thể khởi động lại W-06 theo lời giao; W-24 và các vé sau vẫn theo điểm nghiệm thu riêng.
