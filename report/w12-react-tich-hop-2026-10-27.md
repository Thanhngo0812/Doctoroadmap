# W-12 — React mời qua email và lời mời trong ứng dụng

Bàn giao cuối sau nhận main đã chốt 530a8c9f: nguồn 07902011, 3.433 Python và 243 React đạt; build/browser native 0. Bằng chứng cuối ở browser-merged-final; phần cuối báo cáo ghi đầy đủ cổng sau merge, phần kiểm trên nền 4c69322c được giữ làm lịch sử.

## Nhánh và phạm vi

Nhánh `work/w12-invitations-react`, worktree `tmp/w12-invitations-react`, tách main
`4c69322c9ee23f65902a2ab4f42b519c5e4ca828`, có backend W-12 `f5cd2060` đã nhận.
Nguồn web trước nhận main `6cd3612264e35133381bfe3e14903267af35f2e9`; mốc tích hợp cuối sau nhận main đã chốt là `079020110a975e6da211a7a36a1981082bc87fe6`.
Không đổi backend/use case/migration, không sửa vé/kế hoạch/handoff, không ghép/push main.
Head migration vẫn `w12_0008` nối `w11_0007`.

W-04 bàn giao riêng `f52466dc` ở `tmp/w04-account-react`, chưa tự coi là đã được điều phối ghép.
W-12 xuất phát main hiện hành theo quyền chuẩn bị vé sau trong khi chờ xét W-04; không kéo mã W-04
vào đây. Khi điều phối tích hợp, giữ AccountPage/AuthProvider/epoch guard W-04; thay đổi Auth của
W-12 chỉ ở ngữ cảnh fragment và chuyển form trong AuthPage, không viết lại tài khoản/backend.

Hộp chia sẻ có hai tab “Bằng link”/“Mời qua email”; giữ luồng link W-11 hiện có.
Mời qua email hỗ trợ dán dấu phẩy/xuống dòng, 1–50 đầu vào trước gộp trùng, trim/lower/dedupe,
trường lỗi đỏ và thông báo nhỏ, đang gửi/khoá gửi trùng, danh sách chờ/hết hạn/tải lại/huỷ.
Thông báo thành công chỉ xác nhận tạo lời mời và yêu cầu gửi thư, không khẳng định đã phát tới hộp thư.
Lỗi `email_unverified`, `rate_limited`, `validation` dùng envelope API; không tự retry gửi thư.

“Khoá học của tôi” có khối Lời mời, chấp nhận/từ chối, tải lại và lỗi `course_full`/hết hạn/phiên.
Trước nhận, nói rõ chủ khoá thấy tên/ngày tham gia/hoạt động gần nhất/tiến độ module, không thấy
chat/tài liệu riêng/đáp án quiz. Chấp nhận xong tải danh sách khoá từ API thật, không thêm membership giả.
Đọc danh sách lỗi không in trạng thái rỗng; có thể thử tải lại. Cleanup abort callback khi đổi khoá,
đóng/chuyển tab, đổi tài khoản hoặc rời màn; account ID là key của inbox.

## Hợp đồng và token

Đọc AGENTS, quy trình nhánh/fixture, vé W-12, spec chức năng mục 6/11, spec thiết kế,
`report/w12-email-invitations-backend-2026-10-27.md`, OpenAPI và test backend W-12 đã nhận.
API dưới `/api/v1`, cookie/CSRF/Origin giữ nguyên:

| Thao tác React | API |
|---|---|
| Gửi/list/huỷ ở hộp chia sẻ | POST/GET `/courses/{cid}/invitations`, DELETE `/courses/{cid}/invitations/{iid}` |
| Inbox tài khoản đã xác minh | GET `/me/invitations` |
| Chấp nhận/từ chối bằng ID công khai | POST `/invitations/{iid}/accept`, POST `/invitations/{iid}/decline` |

Không thêm endpoint nhận membership bằng raw token, không gửi owner/account/email tuỳ ý trong body accept.
Các item public chỉ có `id,course_id,course_title,email,status,expires_at,created_at,responded_at`;
harness kiểm chính tập field trên JSON thật trước khi che dữ liệu nhạy cảm để ghi bằng chứng.

Link `/dang-ky#invitation=<token>` chỉ là ngữ cảnh đăng ký. AuthPage thay URL hiện hành bằng pathname/search
không fragment, rồi chỉ giữ `{invitation:true}` trong router state; cả link header/footer và navigate của
view transition giữ boolean này cùng next nội bộ đã sanitize theo W-11.
Token không vào body đăng ký/login, query, persistent storage, analytics/log hay lời gọi lấy membership.
Tài khoản đăng ký mới vẫn chưa thấy lời mời trước xác minh; W-03 xác minh đúng email, backend gắn pending;
membership chỉ có sau chấp nhận rõ ràng. Email khác mở cùng link không được nhận quyền.

## Thiết kế và quan sát

Áp dụng design-taste-frontend app screens, frontend-ui-engineering/TDD/Git/security.
Tham khảo `design/preview/w11_course_management_screens.html`, giữ token/font/logo main đã duyệt.
Chọn textarea nhiều email theo vé thay input một email của preview; không dùng câu “liên kết tham gia
trực tiếp” của preview để thay hợp đồng xác minh rồi chấp nhận. Không nhập nguyên nhánh thiết kế.
Giữ Be Vietnam Pro, header Artboard 24/28; motion 120/200 ms và tắt animation thông báo khi reduced-motion.

Câu hỏi chính: “Tôi muốn mời ai?” ở hộp chia sẻ, “Tôi có muốn vào khoá này?” ở inbox.
Danh sách phẳng, tên khoá/email ở trước, hạn dùng theo giờ Việt Nam, hành động chấp nhận/từ chối tách rõ.
390 px xuống hàng các hành động; 768/1280 giữ cột hành động bên phải. Tab có ArrowLeft/Right/Home/End,
focus/keyboard và vùng bấm ít nhất 44 px. Không thêm bảng số liệu/trang trí giả hoặc thư viện phụ thuộc mới.

Taste sheet đối chiếu `editorial-greeting`, seed `641862912`, giữ palette/type và shell main;
sheet dùng để soát inbox hiện có, không tuyên bố redesign toàn trang/shell theo sheet trước khi viết mã.
Inspector app 1280/768/390: 0 FAIL, WARN `hero-void` từ lưới khoá main chỉ có một khoá đã tham gia;
giữ số liệu/khoá thật, không tạo thẻ giả để lấp chỗ và không thay lại lưới W-06 trong vé này.
CDP kiểm font trên heading của trang HTTP thật, không chỉ dựa vào computed font-family/DOM clone.
Snapshot inspect là bản thiết kế lấy từ DOM HTTP, bỏ script; không thay HTTP/SQL acceptance.

Soát thị giác độc lập đã kiểm email-pending/email-invalid/inbox-pending 390/768/1280 sáng/tối,
không có Required về bố cục/focus. Soát ảnh phát hiện asset trống tối của main trỏ OTP1.png không có;
đã sửa đúng tham chiếu sang OTP4.png sẵn có, không đổi layout/thư viện W-10. Browser cuối bắt buộc
decode ảnh thực, lưu kích thước tự nhiên của ảnh trước khi chụp; không che lỗi ảnh bằng screenshot mock.

## RED → GREEN và guard

- `react-red`: 10 fail/1 control pass trên UI main chưa có email/inbox/fragment; không setup error.
  Lượt này trước các chỉnh test nhập bằng paste và hai test lỗi đọc danh sách, không gán RED đó cho
  toàn bộ suite cuối. Nguồn sản phẩm main trong capture, test lúc đó còn untracked.
- `react-green1`: một timeout do mô phỏng gõ 51 email từng ký tự kéo dài; đổi sang thao tác paste đúng
  yêu cầu sản phẩm, không tăng timeout hoặc giảm assertion. Hai lỗi fragment vẫn tái hiện ở green2;
  chuyển điều hướng sang effect sau khi Router đăng ký listener, green3 đạt 11 test.
- `react-integration1`: 8 fail/6 unhandled do mock Courses cũ trả CourseList cho endpoint invitations mới;
  bổ sung đúng `{items:[]}` cho route mới, giữ mọi assertion lịch sử và số request đếm riêng khoá.
- `list-error-red`: 2 assertion fail/0 setup error trên thông báo rỗng sai khi GET lỗi; green đạt cả 13 test.
- `gate-build-final` lỗi typing option `exact` của getByRole trong test mới; bỏ option không hợp lệ
  (tên chuỗi vẫn match chính xác), không thay expected hay bỏ assertion. Build các lượt sau đạt.
- `dark-asset-red`: 1 assertion fail/0 setup error vì file PNG mà UI trỏ tới không tồn tại.
  `dark-asset-green` kiểm tồn tại và PNG signature đạt; browser cuối kiểm decode tự nhiên thật.
- `mutation-fragment-final3` trên nguồn `6cd36122`: vô hiệu hoá bỏ fragment, cả 2 ca chuyển form
  thường/view transition fail assertion URL vẫn có token, 0 setup error; phục hồi nguyên byte/hash
  trong `mutation-restored-final3.json`. Các mutation trước được giữ riêng, không gán lại cho HEAD cuối.
- Smoke1 đi được tạo/huỷ/full/đăng ký/xác minh/nhận, nhưng POST control fill-rate của harness thiếu CSRF
  trả 403; sửa gửi Origin/CSRF thật cho control, không bỏ guard. Không tính smoke1 là browser GREEN.
- Browser final1/final2 trước vá asset đều có native 0 nhưng ảnh tối còn asset lỗi; giữ lịch sử riêng,
  không dùng chúng thay cho bằng chứng cuối. `gate-python-final` chủ động dừng đúng pytest leaf W-12
  để nhận vá ảnh; native `4294967295`, không JUnit hoàn chỉnh, không phải GREEN.

## HTTP/PostgreSQL/browser cuối

Nguồn tích hợp cuối `07902011`, `dirtySourcePaths=[]`; DB UUID riêng, real HTTP/auth/Argon2/PostgreSQL,
PostgresPhaseBStore và graph doc-1 v8 từ fixture đã chép/hash. FakeClock/FakeMailer, không gọi model,
embedding/media/Cloudinary/SMTP; giữ transport Vertex và policy hiện hành. Không seed DB chủ dự án.

12 cấu hình 390/768/1280 × sáng/tối × reduced-motion thường/giảm; ảnh/video, Axe đúng document từng
trạng thái đã chụp, overflow/vùng bấm/focus/tab keyboard và font thực. Bằng chứng cuối sau nhận main ở `browser-merged-final`.
Các request test-only `/__test/w12/*` chỉ có trong harness UUID, guard bằng actor quan sát riêng;
đọc thư FakeMailer để mở link như người dùng, không phải endpoint sản phẩm. Không log body thư raw.
HTML mẫu FakeMailer xuất ở `fake-invitation-redacted.html`, thay token bằng marker rõ ràng; không gửi mail thật.

SQL qua engine/connection độc lập tại các bước xác nhận:

- Gộp email trùng còn một pending, token chỉ hash 32 byte, TTL đúng 7 ngày.
- Huỷ/hết hạn trả 410, người khác email trả 404; không thêm membership.
- Khoá đủ đúng 200 thành viên trả course_full, không hạ giới hạn cấu hình để kiểm; 199 tài khoản
  tổng hợp chỉ được seed trong DB UUID của harness rồi huỷ cùng DB.
- Chấp nhận có membership `via=email`; từ chối không có membership.
- Đăng ký đúng email nhưng chưa xác minh: invitee chưa gắn, API accept 403, UI không có nút nhận.
- Xác minh qua HTTP W-03: pending được gắn nhưng SQL vẫn chưa có membership; bấm nhận sau đó mới có.
- Đủ 200 audit gửi/chủ/ngày, request tiếp trả 429 và không sinh lời mời over-limit.
- URL/body request/history/storage không chứa invitation token; JSON public kiểm field trước redaction.

Lỗi console HTTP 401/403/409/429 có chủ đích và cảnh báo CSP khi Axe thử fetch font/inject style được
giữ trong audit. Không hạ CSP hay tuyên bố console sạch hoàn toàn. Pageerror và token leak phải rỗng.
Không tuyên bố test đọc danh sách lỗi bằng fetch giả là bằng chứng HTTP/PG thật; ca đó thuộc suite React.

## Lượt kiểm trước nhận main 530a8c9f (giữ để đối chiếu)

Chủ dự án xác nhận cửa riêng cho W-12: “Cửa trống; web chạy khi chốt mã”. Một full PG mỗi lúc,
mutation chạy trước server/gate và đã phục hồi; basetemp mới dưới tmp, không đưa fixture vào ảnh UI.
3145 tệp fixture copy từ hai manifest W-06, SHA nguồn/đích trong fixture-copy.json; PDF candidate train
được copy/hash riêng cho cổng. Không junction/symlink/hardlink, không nhập kho learner CLI vào web.

Lượt nền 4c69322c native 0: **3407 Python pass, 0 fail/0 error**; 3 skipped và 1 xfailed theo JUnit (phân loại nguyên văn ở log). **243 React pass**, build/browser native 0 trên cùng nguồn `6cd36122`. Browser: 12 cấu hình, 41 ảnh, 41 Axe/0 violations, 208 JSON HTTP, 5 video; 54 lượt decode ảnh đạt, font live Be Vietnam Pro, pageerror/token leak rỗng. Main nền kiểm trước cổng vẫn `4c69322c`.
Lệnh/native/source SHA/JUnit trong capture của từng lượt; các lượt cũ được giữ, không ghi đè. Xem phần tích hợp sau main 530a8c9f ở cuối báo cáo để lấy lượt cuối, thay vì lượt trên nền cũ.

```text
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe scripts/w05_run_tests.py -o addopts= -q --basetemp=tmp/cong-w12-react-final3 --junitxml=report/w12-react-evidence/gate-python-final3.xml
npm.cmd --prefix src/web/frontend test -- --pool=threads --maxWorkers=1 --reporter=default --reporter=junit --outputFile=../../../report/w12-react-evidence/gate-react-final3.xml
npm.cmd --prefix src/web/frontend run build
```

Chờ điều phối soát/ghép W-12 riêng; không tự đóng vé từ mốc này. Không có câu hỏi hợp đồng còn mở.

Ảnh xem nhanh: [hộp mời 1280 sáng](w12-react-evidence/browser-final3/email-pending-1280-light.png), [inbox 1280 sáng](w12-react-evidence/browser-final3/inbox-pending-1280-light.png), [390 tối sau vá ảnh](w12-react-evidence/browser-final3/inbox-pending-390-dark.png). Video owner/receiver/newcomer/other/unverified trong cùng thư mục. Bản soát thị giác cuối đã xác nhận hình minh hoạ tối hiển thị đúng.

[HTML thư xem offline](w12-react-evidence/fake-invitation-preview-offline.html) là bản dẫn xuất của FakeMailer đã che token, chỉ nhúng logo Artboard 24 sẵn có để không phụ thuộc server test đã dừng. Bản HTML FakeMailer gốc sau che token vẫn giữ riêng trong browser-final3; không coi preview này là thư đã phát hoặc luồng HTTP thật.

Log/XML giữ nguyên byte bằng attributes riêng, không chuẩn hoá native log. Text lịch sử browser nguyên byte ở historical-browser-text-originals.zip; ảnh/video cũ vẫn giữ local, không trộn vào ảnh cuối. source-snapshot.zip giữ byte của 11 tệp mã/harness thay đổi đã thực thi, để đối chiếu SHA kể cả khi Git checkout đổi CRLF/LF. SQL W-15/W-25 do gate tạo được chép/hash vào evidence vé này; không xoá hoặc stage các thư mục gốc ngoài vé. manifest.json ghi SHA nguồn và bằng chứng; http-examples.json chọn phản hồi HTTP thật đã che dữ liệu nhạy cảm. Basetemp/fixture không được Git theo dõi trong gói bằng chứng.

## Nhận main sau lượt trên nền 4c69322c

Trong lúc đóng gói, main nhận DG-10 ở 530a8c9f (mã/test đánh giá, không đổi src/scripts web). Chủ dự án chốt nguyên văn: “Chốt main nền 530a8c9f cho đợt W-12”. Lượt 6cd36122 trên nền 4c69322c được giữ làm lịch sử, chưa dùng làm cổng tích hợp sau nhận main mới. Nhóm web đã nhận đúng mốc đã chốt và chạy lại cổng; kết quả sau merge ở phần tiếp theo.

## Bàn giao tích hợp cuối sau nhận main 530a8c9f

Main đã chốt `530a8c9f5109bac549b224f17ffee727d2767c07`, merge tại `079020110a975e6da211a7a36a1981082bc87fe6`. Không rebase/ghép main chung. Tất cả lượt kiểm dưới đây ghim nguồn merge này, mã src/scripts không đổi so với 6cd36122 (đối chiếu toàn bộ SHA trong web-source-equivalence.json). Đây là kết quả cuối của đợt W-12; các lượt nền 4c69322c phía trên là lịch sử.

**3433 Python pass, 0 fail/0 error; 4 skipped/xfailed theo JUnit; 243 React pass; build và browser native 0.** PostgreSQL thật, 12 cấu hình, 41 ảnh, 41 Axe/0 violations, 208 JSON HTTP, 5 video, 54 lượt decode ảnh đạt. Pageerror/token leak rỗng, font CDP Be Vietnam Pro, DB UUID đã huỷ/server đã dừng, 0 USD.

Guard fragment chạy lại trên 07902011: mutation-fragment-merged-final có 2 assertion fail/0 setup error, phục hồi nguyên byte trong mutation-restored-merged-final.json trước mọi server/cổng. Không gán receipt mutation cũ cho mốc merge.

```text
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe scripts/w05_run_tests.py -o addopts= -q --basetemp=tmp/cong-w12-react-merged-final --junitxml=report/w12-react-evidence/gate-python-merged-final.xml
npm.cmd --prefix src/web/frontend test -- --pool=threads --maxWorkers=1 --reporter=default --reporter=junit --outputFile=../../../report/w12-react-evidence/gate-react-merged-final.xml
npm.cmd --prefix src/web/frontend run build
```

Các capture gate-python/react/build/browser-merged-final ghi lệnh, source SHA và native exit. SQL/HTTP/runtime cuối trong browser-merged-final; HTTP mẫu ở http-examples-merged.json. source-snapshot-merged.zip giữ byte 11 tệp thay đổi đã kiểm; manifest.json cập nhật cho gói cuối, còn bản manifest nền cũ trong commit checkpoint trước merge. Chưa tự nghiệm thu/ghép main.

Xem [hộp mời 1280 sáng](w12-react-evidence/browser-merged-final/email-pending-1280-light.png), [inbox 1280 sáng](w12-react-evidence/browser-merged-final/inbox-pending-1280-light.png), [inbox 390 tối](w12-react-evidence/browser-merged-final/inbox-pending-390-dark.png); video owner/receiver/newcomer/other/unverified cùng thư mục.
