# Lời giao ba nhóm sau nghiệm thu lần 8 — 2026-10-26

[Biên bản nghiệm thu](dieu-phoi-nghiem-thu-ba-nhom-lan8-2026-10-26.md). Chủ dự án chuyển từng phần;
điều phối chưa gửi phiên bên ngoài. Nhận main local cuối có W-10, backend W-04 và guard thiết kế đã soát.
Chỉ commit local, **chưa push GitHub** theo quyết định chủ dự án 24/10. Không cần Cloud Figma.

## 1. Nhóm web — React W-16 trước, sau đó React W-04

> W-10 aaf68eb được nhận sau kiểm độc lập và cổng tích hợp mới. Hai lỗi R-W10-1/2 đã đóng;
> không làm lại quiz/tài liệu/thư viện, admission chung hoặc token callback. Giữ hồi quy và harness tee SSE mới.
>
> Nhận main local cuối và mở nhánh work/w16-usage-react tại tmp/w16-usage-react, không làm tiếp W-16 trên nhánh W-10.
> Đọc task/web/W-16-muc-dung.md, spec chức năng mục 8, mẫu HTML/CSS/token và backend usage-1 đã nhận d1bf42b.
> Tái dùng GET /me/usage, không viết lại query/backend hoặc chuyển logic sinh/cache/retry/ngân sách core sang React.
>
> Lát 1: trang “Mức dùng”, thanh dùng đúng used_ratio, giờ đặt lại theo Asia/Ho_Chi_Minh,
> builds_this_month.used/max/reset; max=null ghi “không giới hạn”, không hiển thị USD/cost cho người thường.
> Kiểm còn nhiều/gần hết/hết, lỗi/tải lại, giờ Việt Nam và null không biến thành 0 lượt còn lại.
> Lát 2: dải cố định ở chat/nút tạo tài liệu khi learner_today.limited; ghi giờ đặt lại, không che nội dung/controls.
> Khi shared_content_today.limited thì ghi nội dung mới tạm dừng, dùng đúng phản hồi tran_he_thong của W-08.
> Hết trần vẫn xem được bài/tài liệu/quiz có sẵn; cache hit không bị chặn bởi phép kiểm UI chung chung.
> Giữ tách trần tiền theo ngày với documents_per_hour và 10 lượt trợ lý/phút; không suy từ tần suất thành tiền/quota.
> React chỉ phản ánh API; không chặn toàn bộ nút quiz nếu core còn ngân hàng dùng lại, không tự reset cache hằng ngày.
>
> Kiểm thật 390/768/1280 × sáng/tối và reduced-motion, keyboard/focus/44px, stale usage khi chuyển route/đăng xuất,
> chốt nguồn giờ đặt lại/ratio và ảnh ba trạng thái. Fake clock/models/Mailer/media; backend/HTTP/PG thật, 0 USD.
> RED→GREEN cho hành vi mới và một phép phá guard có assertion fail, giữ các hồi quy W-08/W-09/W-10.
> Một cổng PG toàn repo/lúc qua scripts/w05_run_tests.py; React/build/browser đúng commit cuối.
>
> Sau khi W-16 React được nghiệm thu, mở work/w04-account-react ở tmp/w04-account-react từ main mới.
> Backend W-04 c1f2fe9 đã có PATCH /me, POST /me/password, POST /auth/logout-all; đọc report/w04-account-backend-2026-10-26.md
> và public JSON/audit. Làm ba khối hồ sơ theo vé: tên/email/trạng thái xác minh; đổi mật khẩu; xác nhận logout-all.
> Mật khẩu hiện tại bắt buộc, mới theo W-02; A đổi thì A còn đăng nhập/B bị hủy, logout-all hủy cả A+B và về trang đăng nhập.
> Map fields/invalid_credentials chính xác, không giữ mật khẩu trong URL/history/localStorage, clear state khi rời màn.
> Không thêm danh sách thiết bị hoặc chức năng xóa tài khoản W-20. Giữ reset W-03 hủy mọi phiên.
> Không bắt đầu hai vé React đồng thời trong cùng nhánh; báo từng mốc để soát, không tự nhận cả hai hoàn tất.
>
> Giao diện cần chỉn chu theo token/thương hiệu và taste-skill đã nạp; Be Vietnam Pro, logo Artboard 9–28,
> motion 120/200ms và giảm chuyển động. Dùng mẫu HTML làm tham chiếu, phối hợp thiết kế kiểm React thật; không chờ Cloud.

## 2. Nhóm lõi — backend W-04 đạt; tiếp mốc backend W-12

> c1f2fe9 được nhận mốc backend W-04, không giao làm lại hoặc tự viết React. Toàn W-04 vẫn chờ web.
> Nhận main local cuối có W-10 và SA-61, giữ cấu hình web Vertex; không chuyển transport để làm vé mới.
> Mở work/w12-email-invitations-backend tại tmp/w12-email-invitations-backend.
> Đọc task/web/W-12-moi-qua-email.md; spec chức năng mục 6, DB bảng invitation, nền SharingService/W-03/W-11.
> Phân công này chỉ là backend và mẫu thư, không đóng toàn W-12 khi chưa có UI hộp mời/khối lời mời.
>
> Chia ba lát:
> 1. Invitation/repository + migration đúng một head nối w11_0007 (kiểm head thực tế main trước viết).
>    Pending unique theo course/email normalized, token chỉ lưu hash, TTL 7 ngày, mời lại làm mới đúng một pending.
>    Tái dùng normalize email/AuthStore/clock/authorization/audit; không tạo hệ tài khoản hay hàng đợi mail mới.
> 2. SharingService và HTTP: POST/GET courses/{cid}/invitations, DELETE .../{iid}, GET me/invitations,
>    POST invitations/{iid}/accept|decline. Tối đa 50 email/lần, gộp trùng, 200 thư/chủ/ngày, kiểm dưới lock khi có cạnh tranh.
>    Chủ khóa chưa xác minh không mời được; người không sở hữu không quản lý, người ngoài không dò được lời mời.
>    Chấp nhận dùng course lock/capacity/membership hiện hành, via=email, nguyên tử, không tăng thành viên hai lần khi retry/race.
> 3. Link đăng ký và gắn pending khi xác minh đúng email, mẫu thư HTML và nhật ký invitation_sent/accepted/declined/cancelled.
>    Người đăng ký nhưng chưa xác minh chưa được gắn lời mời như test W-12; mở link bằng email khác không nhận được.
>    Dùng callback/port nhỏ nếu cần nối AccountService, không để auth nhập ngược hạ tầng invitation hoặc mở bypass xác minh.
>    Nêu câu hỏi nếu hợp đồng token/đường trả về còn mơ hồ; không tự đổi spec hoặc gửi email thật.
>
> HTTP dùng auth/Origin/CSRF/DTO/no-store hiện hành, không lộ hash/raw token qua list/log/audit/OpenAPI fixture.
> RED→GREEN và mutation: người khác nhận mời, chưa xác minh, quá hạn đúng ranh giới7ngày, mời lại/trùng,
> lượt201, hai runtime tranh suất thư/cuối khóa, replay accept và rollback khi ghi/audit lỗi.
> Kiểm bằng client cookie và SQL connection độc lập trên PG; không chỉ dựa flag do hàm vừa gán.
> Mailer/model/media giả, xuất HTML thư để soát; không SMTP/Gmail/Cloudinary/Gemini thật, 0 USD.
> OpenAPI tái sinh từ app đủ W-04/W-10/W-12, một migration mới nối main, không sửa migration đã ghép.
>
> Phạm vi backend sharing/domain/repository/migration/routes/tests, mẫu mail và hook xác minh tối thiểu;
> không sửa React, core học/dựng/giá/transport/ledger, task/kế hoạch/handoff của điều phối. Phối hợp phần mẫu thư với thiết kế.
> Chạy focused/PG toàn repo/React/build theo quy trình, ghi source SHA/native/JUnit/SQL/public JSON; giữ lỗi cũ và dữ liệu W-15.

## 3. Nhóm thiết kế — hoàn tất W-23 bằng ảnh đúng trạng thái; hỗ trợ W-16/W-04/W-12

> feb5f5e được nhận mốc guard JS D-R7-02: hàm HTML thật, bốn fixture chéo, 5→6→5, ba phép phá độc lập bị bắt.
> Không làm lại token/thương hiệu/math hoặc Cloud Figma. Nhận main local cuối ở nhánh/worktree thiết kế hiện hành.
>
> D-R8-01: điều phối đã đính chính bảng ảnh tại report/w24-w10-w23-phoihop-2026-10-25.md.
> Đọc phần có ngày lần8. Không tiếp tục gọi catalog full-page là crop cùngstate, tự kiểm tra đang gập là mở,
> modal giữa tablet là nửa phải, bài Đại số là tim mạch, hoặc trỏ anchor không tồn tại. Bằng chứng lịch sử vẫn được giữ.
> **W-23 chưa đạt**, nhưng W-10 giờ đã nghiệm thu nên không còn chờ hai lỗi chức năng R7.
>
> Chụp/đối chiếu từng cặp theo đúng trạng thái: W-08 self-check mở, viewer nguồn mở, waiting reduced;
> W-09 answer và menu hội thoại; W-10 quiz-ready/result, dialog tài liệu, document viewer và library here/elsewhere.
> Mỗi cặp ghi full commit/source SHA, URL, viewport 390/768/1280, theme/motion, state và crop thực;
> nếu tham chiếu mẫu HTML không có state tương ứng thì bổ sung mẫu hợp spec hoặc ghi khác biệt cần quyết định,
> không kết luận “khớp” từ ảnh không tương ứng. Nội dung fixture có thể khác; đo màu/chữ/khoảng cách/bố cục/tương tác thực.
> Có thể tái dùng bộ browser điều phối report/coord-ba-nhom-lan8-evidence-2026-10-26/browser-local-files.json
> khi nguồn tương thích; raw ảnh/video còn trong tmp/coord-r8-acceptance-20261026, chỉ đọc/chép thường/SHA, không dọn.
> Không gọi dữ liệu tổng hợp là người dùng/mô hình thật. Font phải có bằng chứng nạp/render; fonts.check không đủ.
> Video phải ghi file và đoạn thao tác cụ thể; ảnh tĩnh không chứng minh focus/motion. Không cần Cloud Figma/video Present.
>
> D-R8-02 là cải thiện kiểm thử tùy chọn: VM hiện gọi filterLibrary với tham số cứng;
> đổi onclick here→button/elsewhere→assistant vẫn 64pass. Nên thực thi handler thật hoặc giữ guard tham số markup,
> để mutation wiring đỏ; không chép thuật toán group vào test, không sửa source vốn đang đúng chỉ để vượt kiểm.
>
> Đồng thời đối chiếu mẫu mức dùng/hồ sơ và hộp mời/mẫu thư cho W-16/W-04/W-12 theo spec hiện hành,
> nhất là tỷ lệ/giờ reset/max=null, phiên A/B, lời mời đúng email và thông báo dữ liệu W-11.
> Chỉ vá HTML/CSS/token/tài liệu thiết kế cần thiết, không sửa chéo React/backend của hai nhóm.
> Giữ đẹp/chỉn chu/taste-skill và kiểm keyboard/focus/44px/sángtối/reduced-motion; giao bảng lệch có cách xử lý.

## 4. Luật chung và giao tiếp Claude

> Chỉ commit local/chưa push main/GitHub. Root luôn main, mỗi vé một nhánh/worktree một cấp dưới tmp;
> người làm vé không tự ghép hoặc sửa task/kế hoạch/handoff. Nhận main cuối trước cổng; chỉ ghép commit đã soát.
> Python qua scripts/w05_run_tests.py, PG bắt buộc; kiểm Docker/db-test sẵn trước chạy, một cổng PG toàn repo/lúc,
> basetemp mới khi chạy lại, giữ cả log lỗi môi trường. Không hạ assertion/timeout, thêm skip hoặc nhận setup error làm RED.
> Không stash/reset/restore tệp người khác, không dọn worktree/DB/artifact/snapshot/ZIP/PDF, không link dưới bất cứ dạng nào.
> Không đụng tmp/t01a-clean-ff797eb, cache người học sống hay tập giữ lại. Fixture chỉ chép allowlist/SHA, không commit .env/PDF/artifact.
> Mọi việc mới 0 USD; quyền paid W-15/khôi phục cũ không tái dùng, không chạy lại sách hoặc thử transport thật.
> SA-61 đã ghép **local ab5c2fa** do Claude, không còn ở trạng thái chờ ghép; **web vẫn Vertex** tới chủ dự án yêu cầu đổi.
> Không bật trần build demo: đề xuất5USD/ngày/3lượt có chi/tháng chưa được kích hoạt. Giữ unknown/billing của W-15 đúng hồ sơ.
> Cửa SA/cổng toàn repo mở lại sau commit hồ sơ lần8; Claude nhận main local mới và đọc mục8/10 bàn giao.
