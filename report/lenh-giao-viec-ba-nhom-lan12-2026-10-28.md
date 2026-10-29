# Lời giao ba nhóm sau nghiệm thu lần 12 — 2026-10-28

[Biên bản lần 12](dieu-phoi-nghiem-thu-ba-nhom-lan12-2026-10-28.md). Bản này để chủ dự án chuyển cho ba nhóm; điều phối chưa gửi phiên bên ngoài. Nhận main local mới đã có backend W-17.1. **Chỉ commit local, chưa push; giữ Vertex; chi nhà cung cấp mới 0 USD; không Cloud Figma.**

## 1. Nhóm web — bắt đầu React W-17.1 Người dùng/Nhật ký

W-12 a8e2075d giữ kết quả đạt; không làm lại. Đợt này nhánh web chưa có commit mới để nghiệm thu, React W-17.1 chưa được triển khai. Điều kiện chờ backend đã được gỡ sau nghiệm thu lần 12. Tạo work/w17-admin-users-react tại tmp/w17-admin-users-react từ main local mới; không làm trong thư mục chung hay nối vào nhánh W-12 cũ.

Đọc [W-17](../task/web/W-17-quan-tri.md), [spec chức năng](../doc/web-chuc-nang-spec.md) mục quản trị/quyền/API, [ADR 0030](../doc/adr/0030-bao-ve-tai-khoan-admin-dau-tien.md) và OpenAPI trên main đã ghép. Backend mốc này chỉ có GET/PATCH /admin/users và GET /admin/audit.

Phạm vi: màn Người dùng và Nhật ký tại khu /admin; tìm/lọc/phân trang phía server, sửa trạng thái/vai trò/build_monthly_max theo DTO, xác nhận thao tác nguy hiểm và phản hồi lỗi/hoàn tất đúng response. Audit chỉ metadata công khai theo hợp đồng. Không dựng các thẻ Bản dựng/Chi/Khoá mẫu thành chức năng đã hoạt động khi backend mốc sau chưa có.

- Dùng is_first_admin từ server. Người đầu tiên không khoá/hạ quyền/xoá; không suy từ hàng đầu bảng, thứ tự tạo hay kết quả tìm kiếm. null là DB chưa đối chiếu định danh: giải thích trạng thái, xử lý bootstrap_required; không thêm ô nhập UUID hoặc API gán bảo vệ qua trình duyệt. Server quyết định cuối.
- Admin đã disabled khác người đầu tiên vẫn hạ về user được; PATCH enable+demote cũng hợp lệ. Dùng kết quả backend đã sửa, không chép guard sai ở client. Bật lại không hồi sinh phiên cũ.
- Giữ W-04 Auth epoch/profile/password/logout-all và W-12 fragment/inbox. Chuyển tài khoản/route hoặc mất quyền thì huỷ/loại phản hồi cũ; GET cũ không ghi đè PATCH mới. Xử lý 401/403/409/422, lỗi mạng và retry, không thông báo thành công trước response. Quota null giữ nghĩa kế thừa, không tự bật trần demo hay quyền chi.
- Không hiện password/hash/token, raw audit.meta, chat, tài liệu riêng hoặc đáp án quiz. Kiểm tài khoản thường bị chặn, admin live/stale, đổi role/status trong lúc request chờ và tìm/lọc/phân trang.
- Giao diện đẹp, rõ và nhất quán token/taste-skill, logo/font đã duyệt. Kiểm 1280/768/390, focus/bàn phím/reduced-motion; vùng bấm theo guard hiện hành. Không cần Cloud Figma.

Bàn giao báo cáo, commit source, unit test có phản chứng, full PG qua runner trong cửa riêng, React/build và browser HTTP/PostgreSQL thật với tài khoản tổng hợp, SQL độc lập, ảnh/video. Đừng gọi toàn W-17 hoàn tất: bản dựng/khoá mẫu/chi/validation còn ở mốc sau.

## 2. Nhóm lõi — W-17.2 metadata bản dựng và khoá mẫu

CORE-R11-01 đã đóng tại nghiệm thu lần 12; giữ định danh admin đầu tiên, guard chỉ áp khi thực sự giảm admin active, giao dịch/lock/audit/session và migration w17_0009. Không làm lại registry hoặc sửa migration đã ghép. Tạo work/w17-builds-samples-backend tại tmp/w17-builds-samples-backend từ main local mới.

Mốc này chỉ:

1. GET /admin/builds: danh sách siêu dữ liệu bản dựng, tìm/lọc/phân trang giới hạn theo spec; tái dùng bảng/port hiện có. DTO rõ cho frontend, chỉ metadata được phép, không nội dung giáo trình, raw exception/stacktrace hoặc dữ liệu học riêng.
2. PATCH /admin/courses/{cid}: đánh dấu/bỏ khoá mẫu theo policy W-06 và mẫu phát triển thuộc allowlist sáu cuốn. Tái dùng cờ/bảng đã có; không tạo migration rỗng, không biến tài liệu riêng ngoài allowlist thành mẫu. Mọi mutation audit nguyên tử.

Tái dùng AdminService/BuildService/CourseService ở đúng ranh giới, không nhân đôi ownership/quota policy. Admin live được kiểm ở service lẫn route; người thường/disabled/stale Actor không đọc hoặc sửa. DTO không lộ marker chat/tài liệu/quiz riêng. Phân trang/lọc/biên ngày, thay cờ mẫu, rollback audit và cạnh tranh phải có quan sát SQL độc lập và test thấy đỏ khi phá guard. Chốt JSON/OpenAPI/các trạng thái lỗi làm hợp đồng cho mốc React tiếp theo.

**Chưa triển khai admin retry/cancel, bảng chi, Cloudinary hoặc lecture_validation ở mốc này.** BuildService hiện require_upload/requested_by; không giả Actor người tải hoặc nới guard chung. Port/route cho retry/cancel thay chủ, trạng thái được thao tác, idempotency/race, grant/budget/receipt/mail vẫn cần chốt riêng với điều phối/Claude. Không cản danh sách metadata và cờ mẫu.

Không gọi provider hoặc chạy lại W-15. Khi đến mốc chi, giữ unknown/billing_verified, chỉ cộng receipt build một lần và loại counted_in=build khỏi trace; chưa bật đề xuất 5 USD/ngày hoặc 3 lượt/tháng.

**DB hiện hữu:** việc nghiệm thu W-17.1 chưa áp migration/CLI vào DB dùng chung. Trước khi vận hành màn admin trên DB đó cần backup, đối chiếu UUID bootstrap bằng hồ sơ có căn cứ, migration w17_0009 và protect-first-admin trong cửa operator riêng. Fresh UUID test DB vẫn tự lập người đầu tiên qua bootstrap. Không tự chọn UUID từ created_at, role hiện hành hay hàng đầu bảng.

## 3. Nhóm thiết kế — dùng số đo thật được điều phối bàn giao, rồi mở rộng W-23

Tiếp work/w23-paired-web-evidence trong tmp/w23-paired-web-evidence, nhận main mới. Giữ các phần đúng của f9705f42: crop pixel/SHA, decoded PNG dimensions, phân biệt ảnh lịch sử, đính chính AA/target/no-lag/copy W-04/W-12. Điều phối đã xác minh độc lập bốn khối JSX/CSS lá không đổi; không cần làm lại token/branding/math hoặc mở Cloud. W-23 vẫn mở.

**D-R12-01 Required — số được gọi là đo React còn ghi sẵn:** reactActualMetrics và measuredHeight, leafSourceValid/diff=0 được điền hằng trong script; chạy khi không có source/server React vẫn báo đủ. Receipt còn ghi tab44px, row332px/padding16, h2weight700. Đo trên React thật với Be Vietnam Pro tải thực/CDP: tab 45px; row358px, padding16px0; h2 weight 600. Kích thước do viewport/content/font quyết định; min-height44 không đồng nghĩa measuredHeight44. Không sửa React cho khớp số ghi nhầm.

Đọc [bảng phản chứng](coord-ba-nhom-lan12-evidence-2026-10-28/design-review/design-assertion-proof.json), [số đo hiện hành](coord-ba-nhom-lan12-evidence-2026-10-28/browser-react-fonts/current-react-metrics.json), [runtime nguồn](coord-ba-nhom-lan12-evidence-2026-10-28/browser-react-fonts/runtime.json) và ba PNG cùng thư mục. Điều phối cung cấp cả run font thương hiệu và run fallback tách riêng; đừng ghép font/số đo của hai run. Đây là HTTP/auth/PostgreSQL thật với model/Mailer/media giả, 0 USD; không cần dựng lại toàn bộ nền.

- Dùng các ảnh/JSON này làm nguồn, ghi đúng commit/URL/viewport/DPR/theme/motion/state/font/crop. URL lịch sử c1/m1/n1 đang khai không khớp runtime lịch sử (course_id là UUID, module_001); lấy URL từ receipt thật, không đoán.
- Bỏ nhãn measured/actual cho hằng số; số suy từ source phải ghi rõ inferred/CSS minimum. Nếu script chứng nhận source diff thì phải thực sự trích/băm/so source hoặc dẫn proof có SHA. Số đo cần đến từ DOM/render tương ứng, không chép từ HTML.
- Giữ CSS rect riêng decoded PNG. Khi tái dùng ảnh canonical, gắn metrics/font vào đúng run; không lấy metrics fresh offline cho PNG online cũ. Fallback làm thay kích thước, ví dụ HTML W-10 height770 thay807; không tuyên bố không đổi bounding box.
- Từ hai cặp đã có dữ liệu thật, hoàn thiện bảng lệch theo spec/token, sửa mẫu nếu mẫu sai, báo web khi React sai; hai phương án UX hợp lý giữ đề xuất, chưa tự đổi hai/ba tab hoặc cách đặt câu hỏi. Giữ React hiện có.

Sau bản sửa hồ sơ ngắn này, mở rộng W-08/09/10, 768/sáng-tối, bàn phím/reduced-motion/video theo W-23; đồng thời hỗ trợ bố cục/tương tác Người dùng/Nhật ký cho web. Không sửa React chéo hoặc sửa tám bản W-23 untracked ở root. Giữ toàn bộ ảnh/video/JSON cũ.

## 4. Thứ tự và cổng bàn giao

Backend W-17.1 được nhận → web React W-17.1 và lõi W-17.2 chạy song song → nghiệm thu → mốc React bản dựng/khoá mẫu rồi chi/validation. W-18 tiến độ thành viên, W-19 báo lỗi, W-20 xoá và W-21 triển khai/sao lưu/an ninh chưa đóng. W-20 phải giữ cấm xoá admin đầu tiên. Thiết kế hoàn thiện W-23 song song, không chặn web vì Cloud.

Một vé một nhánh/worktree một cấp dưới tmp; root luôn main và chỉ điều phối ghép. Chỉ commit đường dẫn của mình, không add rộng/reset/stash/restore tệp người khác, không tự push hoặc ghép main. Nhận main mới trước cổng cuối, pin đúng source/JUnit/native; Python qua scripts/w05_run_tests.py, một full PG mỗi lúc. Fixture chỉ ordinary-copy theo allowlist/SHA, không live learner cache/tập giữ lại. Không xoá/dọn WT/artifact/PDF/ZIP/snapshot/DB W-15, không junction/symlink/hardlink; tuyệt đối không đụng tmp/t01a-clean-ff797eb.
