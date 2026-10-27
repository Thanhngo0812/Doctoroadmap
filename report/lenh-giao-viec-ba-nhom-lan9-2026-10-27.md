# Lời giao ba nhóm sau nghiệm thu lần 9 — 2026-10-27

[Biên bản nghiệm thu](dieu-phoi-nghiem-thu-ba-nhom-lan9-2026-10-27.md). Chủ dự án chuyển từng phần; điều phối chưa gửi sang phiên nhân viên bên ngoài. Nhận main local cuối có W-16, backend W-12 và guard thiết kế đã soát. **Chỉ commit local, chưa push GitHub** theo quyết định chủ dự án 24/10. Không cần Cloud Figma.

## 1. Nhóm web — React W-04 trước, tiếp đó React W-12

W-16 đã được nhận trọn vé. Giữ hồi quy usage-1, giờ Việt Nam, max=null, thông báo hết trần và đọc nội dung có sẵn; logic sinh/cache/retry/ngân sách tiếp tục ở core. Không làm lại backend W-04 hoặc W-12.

Nhận main local cuối; mở nhánh work/w04-account-react tại tmp/w04-account-react. Nếu đường dẫn đã có, kiểm HEAD và chủ sở hữu trước, không xoá hoặc tái sử dụng phần việc chưa rõ. Đọc:

- [W-04](../task/web/W-04-ho-so-doi-mat-khau-dang-xuat-moi-noi.md), [spec chức năng](../doc/web-chuc-nang-spec.md) mục 2/10/11 và [spec thiết kế](../doc/web-thiet-ke-giao-dien-spec.md).
- [Báo cáo backend W-04](w04-account-backend-2026-10-26.md), OpenAPI sinh từ ứng dụng và các test W-04 hiện có. Backend c1f2fe9 đã được nhận; tái dùng PATCH /me, POST /me/password, POST /auth/logout-all.

Giao diện hồ sơ có ba khối: tên/email/trạng thái xác minh; mật khẩu hiện tại/mật khẩu mới/xác nhận; đăng xuất mọi nơi có hộp xác nhận. Tên 1–60 sau trim, luật mật khẩu lấy từ W-02 hiện hành. Hiện lỗi theo fields, trạng thái đang gửi/thành công/thất bại, không ghi mật khẩu/token vào URL, log hoặc storage. Không thêm danh sách thiết bị hay chức năng xoá tài khoản W-20.

Nghiệm thu bằng hai ngữ cảnh trình duyệt A/B với HTTP/PG thật: đổi mật khẩu từ A giữ A, B nhận unauthenticated; mật khẩu cũ không đăng nhập được, mật khẩu mới dùng được. Logout-all huỷ cả A/B, xoá trạng thái riêng ở React và đưa về đăng nhập an toàn; callback cũ không được đưa dữ liệu người trước lên màn hình mới. Sai mật khẩu hiện tại/CSRF/61 ký tự không làm đổi tài khoản. Ảnh 390/768/1280 × sáng/tối, bàn phím/focus, hộp xác nhận và giảm chuyển động; quay ngắn thao tác chính, 0 USD.

Sau khi bàn giao W-04, W-12 là việc kế tiếp, tách nhánh work/w12-invitations-react tại tmp/w12-invitations-react từ main đã nhận backend. Không đưa cả hai vé vào một nhánh khó soát. Nếu W-04 đang chờ nghiệm thu, có thể chuẩn bị W-12 trên nhánh riêng từ main hiện hành, ghi rõ phụ thuộc và không tự nhận W-04 đã ghép.

Đọc [W-12](../task/web/W-12-moi-qua-email.md), [báo cáo backend W-12](w12-email-invitations-backend-2026-10-27.md), spec chức năng mục 6/11 và OpenAPI. Backend f5cd206 đã được nhận, migration w12_0008 nối w11_0007; không tạo migration frontend. Giữ nguyên giới hạn 50 email/lần, gộp trùng, 200 thư/chủ/ngày theo giờ Việt Nam và TTL 7 ngày.

Giao diện W-12 gồm hộp mời theo email trong chia sẻ, danh sách lời mời đang chờ/huỷ và khối lời mời ở “Khoá học của tôi” với chấp nhận/từ chối. Hiện lỗi định dạng, email_unverified, rate_limited và course_full từ API; không suy diễn gửi thư thành công là đã phát tới hộp thư. Thông báo dữ liệu cho người tham gia phải đúng W-11: chủ khoá thấy hoạt động gần nhất/tiến độ module; không thấy chat, tài liệu riêng hoặc đáp án quiz.

Chủ dự án đã chọn link đăng ký dùng fragment /dang-ky#invitation=<token>, chỉ nhận lời mời sau xác minh đúng email. Token không cấp membership. Kiểm chuyển đăng ký/đăng nhập/xác minh mà không rò token vào query, log, analytics hoặc request thừa; dùng đúng hợp đồng backend và cơ chế liệt kê lời mời của tài khoản đã xác minh. Người khác email, chưa xác minh, hết hạn/đã huỷ/đầy khoá không được nhận. Không sáng tạo endpoint nhận membership bằng raw token. FakeMailer xuất HTML cho kiểm, không gửi SMTP thật.

Mỗi vé bàn giao riêng báo cáo, commit cuối, ví dụ HTTP/JSON đã che thông tin nhạy cảm, JUnit/React/build, ảnh/video, SQL kiểm độc lập và danh sách SHA-256 nguồn/bằng chứng. Giữ RED→GREEN cùng phép phá guard có assertion fail/0 setup error. Python qua scripts/w05_run_tests.py, PostgreSQL bắt buộc; đăng ký cửa cổng PG toàn repo để không đụng phiên khác. Không chỉ chạy test của vé rồi gọi là cổng toàn repo.

## 2. Nhóm lõi — mốc backend W-17.1: người dùng và nhật ký quản trị

Backend W-12 đã được nhận; toàn W-12 còn React do web làm. Không làm lại lời mời, không gửi thư thật, không sửa transport/cache/giá/trần lõi. Lưu ghi chú tùy chọn về lỗi hook sau commit xác minh: token/email đã commit nhưng callback lỗi có thể làm HTTP báo thất bại; list_my_invitations hiện tự sửa liên kết bền vững. Đây là cải thiện vận hành chưa giao bắt buộc, không phải lỗi cấp quyền đang chặn W-12.

Nhận main local cuối, mở work/w17-admin-users-backend tại tmp/w17-admin-users-backend. Đọc [W-17](../task/web/W-17-quan-tri.md), [spec chức năng](../doc/web-chuc-nang-spec.md) mục 3/8/9/10/11, [spec DB](../doc/web-co-so-du-lieu-spec.md), các AccountService/AuthStore/session/audit/policy hiện có. **Đợt này chỉ nhận mốc backend người dùng và nhật ký; toàn W-17 vẫn mở.** React do web ở lượt sau.

Phạm vi:

- AdminService.list_users/update_user và HTTP GET /admin/users, PATCH /admin/users/{uid}; tìm email, thông tin tạo/lần đăng nhập/số khoá sở hữu/lượt dựng tháng, đổi active/disabled, role và build_monthly_max theo spec. Phân trang/lọc có giới hạn, schema lỗi ổn định; ghi rõ null theo luật trần demo, không tự bật trần toàn hệ thống.
- GET /admin/audit chỉ trả siêu dữ liệu cho phép, lọc người/loại/thời gian theo spec. Tái dùng audit_event; mọi thay đổi admin phải ghi audit cùng giao dịch. Không dựng hệ IAM hay schema nhật ký mới khi dữ liệu hiện có đáp ứng.
- Người thường/khách bị chặn mọi route admin hiện có và mới; kiểm tự liệt kê route để không bỏ sót. Admin không có quyền đọc nội dung học trong khoá không tham gia. Đặt chuỗi đánh dấu vào chat/tài liệu/đáp án thử và quét toàn phản hồi admin: không được có nội dung riêng, mật khẩu/hash/token hoặc extra tuỳ ý.
- Disable phải huỷ mọi phiên ngay; enable không hồi sinh phiên cũ. Kiểm hai phiên/HTTP thực. Admin cuối không tự hạ quyền; hai giao dịch hạ quyền cạnh tranh không được cùng vượt qua phép kiểm admin cuối, không chỉ đếm trước giao dịch. Với việc disable admin cuối, ghi rõ hành vi hiện có và đề xuất nếu spec còn thiếu; không tự thêm chính sách vào spec. Thay đổi trái quyền/sai fields hoặc lỗi audit phải rollback cả dữ liệu và session.

Giữ domain/policy và application ports tách FastAPI/SQLAlchemy, dùng lại hạ tầng đã có. Không tạo migration rỗng. Nếu phát hiện cần đổi schema, nêu lý do và nối đúng head w12_0008 trên main mới, không sửa migration đã ghép. Không tự thêm chức năng theo dõi chat hoặc xuất dữ liệu người học.

Kết quả cần có: báo cáo report/w17-admin-users-backend-2026-10-27.md (hoặc ngày thực tế), schema/JSON cho React, nguồn commit/SHA, test PostgreSQL bắt buộc về cạnh tranh/rollback/quyền/phiên, RED→GREEN và mutation. Cổng toàn repo qua runner trong cửa được thống nhất; không gửi thư, không gọi Gemini/Cloudinary thật, chi mới 0 USD.

Sau mốc này mới đề xuất W-17.2 bản dựng/khoá mẫu, rồi W-17.3 chi/log lecture_validation/Cloudinary cache 1 giờ. Các phần đó **chưa hoàn tất và chưa phải phạm vi bắt buộc của lần giao này**. Khi làm phần chi phải cộng receipt build đúng một lần, bỏ trace counted_in="build", giữ cờ thiếu usage/billing_verified và nhãn “ước theo token, không thay hoá đơn”; không coi số tổng là hoá đơn. Cloudinary dùng adapter giả khi kiểm, chưa cấp quyền gọi thật. Không dùng mốc W-17.1 để đánh dấu hoàn thành cả vé.

## 3. Nhóm thiết kế — hoàn tất bằng chứng W-23, hỗ trợ W-04/W-12

Nhận main local cuối, mở nhánh work/w23-paired-web-evidence tại tmp/w23-paired-web-evidence. Guard D-R8-02 đã đạt: thực thi onclick thật và mutation lọc sai bị bắt. Giữ test này; không làm lại token, branding, công thức đã nhận, plugin hoặc Cloud Figma.

Đọc [W-23](../task/web/W-23-doi-chieu-figma-va-giao-dien.md), spec thiết kế mục 3a, báo cáo W-24 đã đính chính D-R9-01/02 và [review thiết kế R9](coord-ba-nhom-lan9-evidence-2026-10-27/design-review/review.md). **W-23 còn mở vì thiếu bằng chứng đối chiếu thực, không phải thiếu Cloud.** Không tiếp tục thay cột ảnh HTML bằng đường dẫn source rồi kết luận khớp.

Chia làm hai lát, bàn giao lát đầu sớm để tránh lặp sai cách chụp:

1. Hai cặp thực: W-08 self-check gập cùng gập/mở cùng mở; W-10 thư viện “Tạo ở đây” với đúng hai tab hiện hành. Mỗi cặp chụp HTML và React cùng 390 hoặc 1280, cùng theme/motion/trạng thái/dữ liệu tương đương. Ghi full commit, SHA file nguồn, URL, viewport, state, vùng crop và tên file hai ảnh. Nếu mẫu chưa có state thì bổ sung state trong HTML ở nhánh thiết kế; không sửa React đang có người làm. Xác nhận font Be Vietnam Pro đã tải, ghi số đo thực cho điều tuyên bố (padding/target/contrast), không suy số đo từ source anchor.
2. Khi cách chụp đã đúng, hoàn thiện bảng W-08 bài giảng/self-check/source/wait, W-09 answer/menu, W-10 quiz ready/result, hộp tạo tài liệu và thư viện. Bổ sung 768, sáng/tối, bàn phím/focus và reduced-motion theo vé; quay video tương tác thật, ghi đoạn đã xem. Ảnh superscript không chứng minh subscript; ảnh tĩnh không chứng minh hiệu ứng. Được tái dùng ảnh/video cũ nếu ghi nguồn chụp thật và chứng minh source liên quan không đổi; không đổi nhãn thành một lần chụp mới.

Mỗi dòng kết luận một trong: khớp đã đo; React sai; mẫu HTML khác spec; hoặc hai cách đều hợp lý cần chủ dự án chọn. Trường hợp cuối chỉ đề xuất, không tự ghi “đã duyệt”. W-10 ảnh browser-r7-main thực chụp từ 1fc0f553bec808241388b722fa2c10a1c6ead33d; aaf68eb là mốc nhận sau đó, có thể chứng minh tái dùng bằng diff frontend/harness rỗng. Giữ bảng nguồn rõ ràng.

Hỗ trợ web bằng HTML/CSS/token cho hồ sơ W-04 và lời mời W-12, copy đúng spec. Ưu tiên chất lượng giao diện đẹp, rõ, hiệu ứng gọn; được dùng taste-skill chủ dự án nạp và ghi skill đã áp dụng. Không tự đặt luật quota: ngưỡng gần hết 80% hiện ở React là lựa chọn trình bày, không đổi trần core. W-17 chỉ chuẩn bị mẫu Người dùng/Nhật ký theo hợp đồng backend được bàn giao, không bịa dữ liệu sản phẩm.

Bàn giao báo cáo report/w23-doi-chieu-web-thuc-te-2026-10-27.md (hoặc ngày thực tế), manifest SHA-256, bảng cặp ảnh/đo đạc/cách xử lý và video ngắn; không tuyên bố cả W-23 đạt khi còn cặp hoặc quyết định chưa kiểm. Chỉ 0 USD, không cần Cloud Figma.

## 4. Luật chung và thứ tự ghép

- Mọi phiên làm ở worktree riêng dưới tmp, chỉ điều phối mở thư mục chung trên main. Không tự ghép main/push. Bàn giao commit cuối đã soát, không gom file của nhóm khác.
- Không dọn worktree, artifact, PDF/ZIP/snapshot hoặc DB W-15; không tạo junction/symlink/hardlink. Tuyệt đối không đụng tmp/t01a-clean-ff797eb. Fixture test chỉ chép tệp thường theo allowlist/SHA, không đọc cache học thật hay tập giữ lại.
- Một cổng Python/PG toàn repo mỗi lúc; báo điều phối cửa kiểm trước chạy. Browser dùng DB UUID riêng theo harness; chỉ harness sở hữu DB được xử lý vòng đời của nó, không dọn DB phiên bị ngắt.
- Sau khi nhận main mới: web W-04 và lõi W-17.1 độc lập, thiết kế chỉ sửa vùng thiết kế/bằng chứng. Web W-12 phụ thuộc backend W-12 đã ghép; frontend W-17 chờ hợp đồng W-17.1. Điều phối chốt exact commit, nhận main mới, kiểm cổng và ghép --no-ff local từng mốc.
- SA-61 đã ghép local ab5c2fa, **web vẫn Vertex** đến khi chủ dự án yêu cầu đổi. Không paid/grant mới; không chạy lại W-15 hoặc phục hồi dữ liệu. W-18/W-19/W-20/W-21 chưa được nhận hoàn tất và chưa giao chen vào lượt này.
