# Lời giao ba nhóm sau nghiệm thu lần 7 — 2026-10-26

[Biên bản và bằng chứng](dieu-phoi-nghiem-thu-ba-nhom-lan7-2026-10-26.md). Soạn để chủ dự án chuyển từng phần;
điều phối chưa gửi phiên bên ngoài. Backend W-16 `d1bf42b` và mẫu thiết kế `26e4a9a` ghép **local `c5b4f5f`**;
W-10 `fa346c9` chưa đạt/chưa ghép. Nhận main local cuối sau commit hồ sơ, không push GitHub.

## 1. Nhóm web — sửa hai Required W-10, sau đạt mới React W-16

> Tiếp `tmp/w10-quiz-documents`, nhánh `work/w10-quiz-documents`, nhận main local mới có backend W-16 và mẫu W-10 đã nhận.
> Giữ phần đã kiểm: DTO đề không đáp án, owner/cuốn, option xáo đúng, nộp nguyên tử/idempotent,
> progress rollback, renderer Markdown/GFM/LaTeX/nguồn, library theo group, 6 module và tần suất trực tiếp,
> lưu tài liệu sau đóng dialog, reload/history/focus. Không làm lại ba lát hoặc sửa use case core.
>
> **R-W10-1 — thiếu hạn tần suất cho tool trợ lý.** Sau 10 tài liệu trực tiếp, POST thứ 11 bị 429,
> nhưng cùng người/cùng giờ yêu cầu qua chat thì tool vẫn tạo ready: model calls 10→11, SQL documents 10→11,
> admission bucket vẫn 10. Phản chứng qua HTTP/PG/core thật, model giả, 1 assertion fail/0 setup error.
> Sửa bằng một cơ chế admission web dùng chung cho button và assistant, đúng actor/xuyên khoá/không đếm hai lần;
> không chép thuật toán sinh/cache/retry/ngân sách của core. Đường bị từ chối phải 0 lần gọi model và không có tài liệu ready.
> Kiểm cả button→assistant, assistant→button, hai khoá cùng người, người khác tách và hai runtime tranh lượt cuối.
> Giữ thông báo giới hạn phù hợp trong tool/chat, không biến thành lỗi nội bộ; policy ngày/tiền và usage-1 không đổi.
>
> **R-W10-2 — nộp quiz chậm ghi vào màn khác.** Tại submit() của ContentPages.tsx,
> giữ phản hồi nộp qa_1, Back về qa_2 rồi trả qa_1: URL qa_2 nhưng màn hiện kết quả qa_1.
> React thật/fetch giả có 1 assertion fail/0 setup; control scratch với guard attempt đạt 10 test.
> Gắn callback success/error/finally/focus với đúng cid/aid/request hiện tại; phản hồi cũ không đổi màn hoặc mở khoá lượt mới.
> Kết quả server đã nộp vẫn bền và mở lại được ở đúng quiz; kiểm Back/Forward, đổi attempt/course,
> lỗi cũ và lượt mới đang pending. Giữ các ca mất phản hồi/idempotency/lựa chọn khi stream/keyboard đã có.
>
> Helper/test/XML nằm trong `report/coord-ba-nhom-lan7-evidence-2026-10-26/web-review/` và `http-repro/`.
> Log đầu helper HTTP chỉ thiếu import w07, không tính làm RED; dùng lượt rate-origin-repro2 có đúng assertion fail.
> Cả hai hồi quy phải đỏ trên hành vi hiện tại rồi xanh sau sửa, không giảm assertion/timeout hoặc thêm skip.
>
> Nên sửa thêm harness w10_web_check.cjs: kiểm các kết quả rejected của Promise.allSettled và lưu SSE body bằng tee
> trước điều hướng; hiện 19 body không thu được, không gọi native 0 là chứng minh tất cả payload riêng tư.
> Đây là ghi chú kiểm thử riêng, không có kết luận đã lộ đáp án trong bản hiện tại.
> Hai sửa chức năng xong thì chạy cổng runner PG toàn repo/React/build/browser mới, source SHA/native/SQL/raw logs,
> giữ bằng chứng lỗi cũ và mutation đúng nguồn. Không tự ghép main.
>
> **Sau khi W-10 được nghiệm thu:** làm phần React W-16 trên backend usage-1 đã ghép.
> Tái dùng GET /me/usage: ratio/limited/reset giờ Việt Nam, builds_this_month.used/max/reset,
> max=null ghi “không giới hạn”, shared_content_today chỉ limited. Người thường không thấy USD.
> Trang mức dùng có còn nhiều/gần hết/hết; dải cố định trong chat/nút tạo tài liệu với giờ đặt lại,
> hết trần vẫn dùng nội dung có sẵn, bài mới khi trần hệ thống chạm theo core.
> Backend đã nhận không giao viết lại; kiểm bàn phím/reduced-motion và ảnh 390/768/1280 sáng/tối/0 USD.
> Mở nhánh/worktree W-16 React riêng khi đến lượt, không nhận toàn W-16 hoàn tất từ mốc backend.
>
> Giao diện tiếp tục theo HTML/CSS/token và taste-skill đã nạp, đẹp/chỉn chu, Be Vietnam Pro/logo Artboard 9–28/motion.
> Không chờ Cloud Figma. Thiết kế đang bổ sung đối chiếu W-23; phối hợp đúng source/viewport/trạng thái.

## 2. Nhóm lõi — backend W-16 đạt; bắt đầu mốc backend W-04

> `d1bf42b` đã nhận mốc backend W-16, ghép local `c5b4f5f`. Giữ query theo actor/ngày/purpose,
> ngày/tháng nửa mở theo giờ Việt Nam, trace build không cộng trùng, quota đếm lượt, DTO không USD.
> Không làm lại phần đã kiểm hoặc tự viết React. Toàn W-16 chờ web sau W-10.
>
> Nhận main local cuối; tạo `work/w04-account-backend` trong `tmp/w04-account-backend`.
> Đọc `task/web/W-04-ho-so-doi-mat-khau-dang-xuat-moi-noi.md`, spec chức năng mục 2 và nền W-02/W-03.
> Đây là phân công **mốc backend**, không đóng toàn W-04 khi chưa có trang hồ sơ React.
>
> Làm ba lát, dùng lại AccountService/repository/password/session/CSRF/audit hiện hành:
> 1. update_profile và PATCH /me: tên cắt khoảng trắng, 1–60 ký tự; 61 hoặc rỗng trả validation/fields.
>    Actor lấy từ phiên máy chủ, không cho sửa vai trò/email/người khác qua payload thừa.
> 2. change_password và POST /me/password: cần mật khẩu hiện tại, mật khẩu mới theo W-02.
>    Sai mật khẩu cũ không thay hash/phiên. Thành công từ A thì hủy B và mọi phiên khác, **giữ A**;
>    định danh phiên hiện tại lấy từ xác thực phía server, không tin session_id/owner do body gửi.
>    Kiểm hash/đăng nhập và hai client cookie độc lập qua HTTP/PG, không chỉ đếm flag. Ghi password_changed.
> 3. logout_all và POST /auth/logout-all: hủy cả A+B, xóa cookie phù hợp, request tiếp đều unauthenticated;
>    chỉ tác động đúng tài khoản, ghi logout_all, giữ Origin/CSRF và luật bảo mật của W-02/W-03.
>
> Phạm vi AccountService/repository/route auth/DTO/test W-04; không sửa learning_runtime/content/React của web đang làm.
> Không tạo migration rỗng nếu schema đã đủ. Chạy service/HTTP/PG, RED→GREEN và thử phá guard phiên,
> giữ hồi quy reset mật khẩu W-03 (reset hủy mọi phiên, khác đổi mật khẩu giữ phiên A).
> Báo JSON public, mã lỗi/fields, audit và nguồn/lệnh/native/SHA cho web, không ghi mật khẩu thật/bí mật.
> OpenAPI mới phải phản ánh route hiện hành; nếu gặp nhánh W-10 cũng sửa schema thì nhận main và tái sinh từ app kết hợp,
> không xóa route hoặc sửa tay JSON để né xung đột. Cổng một PG toàn repo/lúc; frontend không đổi vẫn chạy test/build theo quy trình.
>
> 0 USD, Mailer/model/media giả, không SMTP/Cloudinary/ADC/provider thật. Không chạy lại W-15 hoặc nghiên cứu timeout cũ,
> không thay transport/giá/trần. Giữ unknown W-15 và mọi DB/artifact/plan/grant đã consume.
> Đề xuất build 5 USD/ngày và 3 lượt có chi/người/tháng vẫn chưa bật/chưa là quyền chạy mới.

## 3. Nhóm thiết kế — giữ mẫu W-10 đạt; hoàn thiện guard và W-23 thực

> Nhận main local cuối tại worktree `tmp/w24-figma-evidence`, nhánh `work/w24-figma-evidence`.
> Source `26e4a9a` đã nhận mốc mẫu W-10/D-R6-01: group độc lập origin, 4 fixture chéo,
> 5→6→5 module khóa/mở đúng, công thức/cây truy cập/chỉ số dưới/mobile đạt qua 12 cấu hình.
> Không làm lại thương hiệu/token/math hoặc Cloud Figma.
>
> **D-R7-02 — thay guard chỉ kiểm chuỗi bằng hành vi thật.** 64 unit test hiện vẫn 64 pass khi đảo
> `cardGroup === group` thành `!==`; không gọi test Boolean cục bộ là bảo vệ JavaScript của mẫu.
> Thực thi chính hàm/script từ HTML bằng Node VM hoặc browser/công cụ đã có, không chép lại thuật toán trong test.
> Bốn record chéo phải lọc đúng here/elsewhere/all; cả hàm lọc origin cũ và điều kiện đảo phải làm test fail assertion.
> Giữ kiểm 5→6→5 và cảnh báo/nút disabled; nguồn phá phải phục hồi nguyên byte, ghi native và XML/log.
> Probe độc lập có thể dùng làm mẫu: `report/coord-ba-nhom-lan7-evidence-2026-10-26/design-review/browser-probe.cjs`.
>
> **D-R7-01/W-23 — đính chính đã được điều phối ghi ở đầu báo cáo.**
> Ảnh R5 design-browser/w08-ready-390.png là HTML, không phải React. ordinary-lecture-generated là roadmap+chat,
> lesson-768-dark chưa phải viewer nguồn; các cặp ảnh khác không chứng minh “khớp hoàn hảo”.
> Tuyên bố nghiệm thu từng phần W-23 đã được rút; không xóa log/bằng chứng gốc hoặc gán lại nguồn ảnh.
>
> Lập bảng đối chiếu thực W-08/W-09 trước; W-10 soát bản mới sau hai sửa chức năng của web.
> Mỗi cặp ghi commit/source SHA, URL, viewport/theme/reduced-motion và **cùng trạng thái tương ứng**;
> cùng cỡ ảnh/crop browser phù hợp, không nhầm ảnh section HTML với ảnh viewport React.
> Dữ liệu mẫu có thể khác, nhưng chỉ rõ lệch màu/chữ/khoảng cách/bố cục/thao tác và cách xử lý;
> không ghi “hoàn hảo” khi chưa đo hoặc so trạng thái khác nhau. Ghi rõ mã W-10 ở nhánh khi chưa ghép main.
> Kiểm 390/768/1280 sáng/tối, keyboard/focus/44px, dialog/menu/source/math/reduced-motion; kèm video tương tác thật.
> Khi chặn GoogleFonts thì phải ghi font fallback thực tế, không dùng document.fonts.check=true làm chứng cứ font đã nạp.
>
> Phối hợp web, không tự sửa tệp React họ đang làm. Được dùng taste-skill phù hợp theo spec/brand;
> giữ mốc W-22/W-24 đã nhận, không Cloud/plugin/Variables/Present. Toàn W-23 vẫn mở tới đủ W-10 và bộ đối chiếu.
> Có thể chuẩn bị/đối chiếu mẫu mức dùng/hồ sơ đang có cho W-16/W-04, chỉ cập nhật phần lệch spec, không thêm nghiệp vụ.

## 4. Luật chung và giao tiếp Claude

> Quyết định chủ dự án tiếp tục hiệu lực: **chỉ commit local, chưa push main/GitHub**.
> Root luôn main; mỗi vé/worktree một cấp tmp. Người làm vé không tự ghép, không sửa task/kế hoạch/handoff điều phối.
> Chỉ commit tệp của vé; không stash/reset/restore tệp dở của người khác hoặc dọn worktree/DB/artifact/snapshot/ZIP/PDF.
> Không tạo junction/symlink/hardlink; không đụng tmp/t01a-clean-ff797eb, learner livecache hoặc tập giữ lại.
> Fixture chỉ chép allowlist/SHA; không commit .env/PDF/artifact. Giữ log lỗi và đúng nguồn của từng mutation.
> Python qua scripts/w05_run_tests.py, PG bắt buộc, basetemp mới; chỉ một cổng toàn repo tại một thời điểm.
> Main đổi thì nhận main local/chạy lại cổng trước ghép. Mọi việc mới 0 USD, không tái dùng quyền paid W-15/khôi phục.
> Vertex giữ tới chủ dự án yêu cầu đổi; SA-61 còn nhánh do Claude soát/ghép; SA-67/68 đã ở main.
> Mở lại cửa SA/cổng toàn repo sau commit hồ sơ local lần 7; Claude đọc mục 8/10 bàn giao và nhận main mới.
