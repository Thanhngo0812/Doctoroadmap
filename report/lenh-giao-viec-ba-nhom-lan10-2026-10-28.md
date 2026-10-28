# Lời giao ba nhóm sau nghiệm thu lần 10 — 2026-10-28

[Biên bản lần 10](dieu-phoi-nghiem-thu-ba-nhom-lan10-2026-10-28.md). Chủ dự án chuyển từng phần; điều phối chưa gửi phiên nhân viên bên ngoài. Nhận main local cuối đã có W-04 React. **Chỉ commit local/chưa push**, giữ Vertex, chi nhà cung cấp mới 0 USD. Không cần Cloud Figma.

## 1. Nhóm web — sửa W-12 trước, sau đó giao diện quản trị W-17.1

W-04 f52466dc đã được nhận toàn vé; giữ profile/epoch/password/logout-all và hồi quy hai phiên, không làm lại backend hoặc trang hồ sơ. W-12 af2993a5 **chưa nhận/chưa ghép** vì Required WEB-R10-01.

Tiếp trên work/w12-invitations-react tại tmp/w12-invitations-react, nhận main local mới có W-04 và bảo toàn cả hai thay đổi Auth.tsx: AuthProvider/epoch/profile/logout-all của W-04; fragment/AuthPage của W-12. Không sửa từ thư mục chung. Đọc:

- [W-12](../task/web/W-12-moi-qua-email.md), [báo cáo W-12 React](coord-ba-nhom-lan10-evidence-2026-10-28/web-review/author-w12-report.md), spec chức năng mục 6/11.
- [Review web lần 10](coord-ba-nhom-lan10-evidence-2026-10-28/web-review/review.md) và phản chứng [HTTP/SQL](coord-ba-nhom-lan10-evidence-2026-10-28/w12-race/race-proof.json).

**WEB-R10-01 — GET danh sách cũ ghi đè POST thành công:** GET khi mở hộp mời lấy snapshot cũ nhưng trả chậm. Người dùng vẫn gửi được email; POST thành công và DB có pending mới. Sau đó GET cũ tới, setItems thay toàn bộ danh sách, làm mất email vừa mời/nút huỷ dù thông báo thành công vẫn còn. Trên snapshot ban đầu rỗng còn hiện sai “Chưa có lời mời đang chờ”. Lỗi ở Invitations.tsx phần tải danh sách và submit.

Sửa nhỏ nhất để phản hồi đọc cũ không ghi đè kết quả mutation mới: vô hiệu hoá/huỷ lượt đọc cũ, ghép có thứ tự hoặc tuần tự hoá tải/gửi. Tự chọn cách đơn giản; không thêm framework/cache/endpoint. Nếu ngăn gửi trong lúc tải, test phải chứng minh nút bị chặn và gửi được đúng sau khi tải xong. Nếu cho gửi song song, test phải điều khiển chính thứ tự GET trước → POST thành công → GET cũ sau. Sau cùng lời mời và nút huỷ phải đúng DB, không kẹt loading; POST lỗi/GET lỗi/tải lại/đổi khoá/unmount/đăng xuất vẫn đúng. Không chỉ đổi notice hay lấy cờ isStale làm assertion.

Root đã chứng minh bằng HTTP/PG thật: route.fetch giữ response GET thật, không dựng DTO giả; POST 200; connection SQL độc lập thấy pending trước và sau; UI không còn email mới sau giao GET cũ. Native 1 là assertion nghiệp vụ, không setup error. Probe/unit độc lập cũng đỏ, còn 13 test hiện tại của vé vẫn xanh nên phải bổ sung guard mới.

Bàn giao commit mới, test RED trên af2993a5 → GREEN, phép phá guard và SHA phục hồi, full PG qua scripts/w05_run_tests.py trong cửa riêng, React/build/browser thật, SQL và ảnh/video. Không gửi SMTP/Gemini/Cloudinary thật, không thay quy tắc 50 email/200 thư/TTL/email verified hoặc cấp membership bằng token. Đừng tự đánh dấu toàn W-12 đạt trước điều phối.

**Sau khi W-12 được nghiệm thu:** mở work/w17-admin-users-react tại tmp/w17-admin-users-react từ main đã nhận backend W-17.1 bản sửa. Hiện backend 9cf405ac cũng đang giữ ở nhánh vì quyết định bảo vệ admin đầu tiên; không nối UI vào giả định backend này đã ghép.

Phạm vi React đầu của W-17 chỉ gồm Người dùng và Nhật ký: danh sách/tìm/lọc/phân trang; đổi trạng thái, vai trò, quota override theo hợp đồng backend; bảng audit metadata. Quyền admin từ phiên server, API luôn quyết định cuối; xử lý 401/403 và callback cũ khi đổi tài khoản. Không trả/hiện hash, token, raw meta, chat, tài liệu riêng hay đáp án quiz. Không bịa ba tab chức năng chưa có backend hoặc số chi giả. Kiểm 1280, 768 và 390 không vỡ; đẹp, rõ, focus/bàn phím và reduced-motion theo token/taste-skill.

Admin đầu tiên không được khoá/hạ quyền/xoá theo quyết định 28/10. UI phải phản ánh hợp đồng server đã sửa, không suy “admin đầu tiên” từ hàng đầu bảng hoặc bộ lọc đang mở. Không lấy nút disabled thay kiểm phía server. Thao tác hồ sơ/mật khẩu thông thường vẫn dùng W-04, không đưa thuật toán hash vào nhãn cho người dùng.

## 2. Nhóm lõi — sửa W-17.1 theo quyết định mới trước mốc tiếp

Nhánh work/w17-admin-users-backend tại tmp/w17-admin-users-backend, mốc 9cf405ac **chưa nhận/chưa ghép**. Review hợp đồng cũ có 23 probe độc lập xanh/6 mutant bị bắt; quyết định mới đã thay điều kiện nghiệm thu. Đọc:

- [W-17](../task/web/W-17-quan-tri.md), [spec chức năng](../doc/web-chuc-nang-spec.md) mục 3/9/10/11 và [bổ sung review theo quyết định mới](coord-ba-nhom-lan10-evidence-2026-10-28/core-review/policy-addendum.md).
- [Báo cáo backend đang giữ](coord-ba-nhom-lan10-evidence-2026-10-28/core-review/author-report.md), OpenAPI/DTO/mutation hiện có.

Chủ dự án nói nguyên văn **“admin đầu tiên ko đc khóa hay gì”**. Phạm vi đã ghi nhận: tài khoản admin đầu tiên được bảo vệ khỏi khoá quản trị (status disabled), hạ vai trò và xoá, kể cả tự thao tác hoặc admin khác thao tác. Đây là bảo vệ định danh admin đầu tiên bền vững, không chỉ cấm hạ admin cuối. Giữ các bảo vệ đăng nhập/CSRF/session W-02/W-03 và việc đổi hồ sơ/mật khẩu thông thường.

**POL-R10-01:** mã hiện tại vẫn khoá được admin đầu tiên và đếm cả admin disabled khi kiểm admin cuối. Phép kiểm mới test_new_owner_policy_first_admin_cannot_be_disabled đã assertion RED/0 setup error trên bản bàn giao. Sửa trước khi xin nghiệm thu lại:

- Ghi nhận định danh admin đầu tiên bền vững phía server khi bootstrap; không tạo thêm một hệ vai trò mới. Không suy lại từ role/status hiện hành, thứ tự bảng, created_at của một tài khoản thường hoặc tham số client.
- Tài khoản thường cũ được nâng admin sau này không được thay định danh admin đầu tiên. Admin thêm sau vẫn quản trị được theo spec nhưng không làm mất bảo vệ người đầu tiên.
- Mọi đường service/API liên quan phải từ chối disable/demote/delete tài khoản được bảo vệ, kể cả PATCH nhiều trường; từ chối nguyên tử, không đổi field khác/phiên/audit giả. Tên lỗi/fields/DTO cho React phải rõ và ổn định. Các thao tác hợp lệ trên tài khoản khác vẫn chạy.
- Với DB hiện hữu, báo rõ cách nhận diện/gán admin đầu tiên và kế hoạch chuyển schema nếu cần. Không tự chạm DB dùng chung hoặc phục hồi W-15. Nếu thêm migration, nối đúng head main mới (hiện w12_0008), không sửa migration đã ghép, không tạo migration rỗng.
- Giữ các guard cũ: disabled actor/stale actor bị chặn, disable người thường huỷ mọi phiên/enable không hồi sinh, cạnh tranh/rollback/audit, quota null và biên tháng Việt Nam, projections không dữ liệu riêng.

Test phải phân biệt “đầu tiên” và “cuối cùng”: có hai admin mà người đầu tiên vẫn không bị hạ/khoá; chỉ admin sau được đổi; tài khoản thường cũ được nâng admin không đổi người được bảo vệ; tự thao tác/admin khác thao tác, PATCH nhiều field, cạnh tranh, rollback và đối chiếu SQL độc lập. Thay expected test cũ “cho phép disable admin cuối” bằng chính sách mới có RED→GREEN, giữ lịch sử trong báo cáo; không skip/xoá guard để né việc sửa.

Bàn giao report/w17-bao-ve-admin-dau-tien-2026-10-28.md (hoặc ngày thực tế), commit cuối, schema/DTO/JSON cho React, chứng minh đỏ trên mã cũ/xanh trên mã mới và mutation assertion fail. Nhận main mới có W-04 trước cổng cuối; một full PG/lúc qua runner. 0 USD, không SMTP/Gemini/Cloudinary thật. Backend được nhận sau sửa vẫn không đóng toàn W-17 còn React/chi/bản dựng/khoá mẫu.

**Sau khi W-17.1 bản sửa được nhận:** mốc backend kế tiếp W-17.2 chỉ làm danh sách siêu dữ liệu bản dựng và đánh dấu/bỏ khoá mẫu theo GET /admin/builds, PATCH /admin/courses/{cid}. Tái dùng bảng/BuildService/CourseService/policy đã có, phân trang/lọc giới hạn, audit, chỉ metadata và mẫu dev thuộc allowlist sáu cuốn; không đọc nội dung học hoặc tự khởi chạy nhà cung cấp.

Phần retry/cancel thay chủ khoá phải chốt hợp đồng riêng trước nối: BuildService hiện yêu cầu requested_by và require_upload, bảng HTTP có admin retry nhưng chưa liệt kê admin cancel. Không giả Actor của người tải hoặc bỏ guard requested_by chung để mở quyền admin. Ghi đề xuất port/route vào mục 8 bàn giao, phối hợp điều phối/Claude. Phần spend_summary/system caps/lecture_validation/Cloudinary là mốc sau, không gom vào bản sửa bảo vệ admin; khi làm chi phải loại counted_in="build" khỏi phép cộng trùng và ghi “ước theo token, không thay hoá đơn”.

## 3. Nhóm thiết kế — sửa lát 1 W-23 bằng bằng chứng đúng khung và số đo

Nhánh work/w23-paired-web-evidence tại tmp/w23-paired-web-evidence, mốc 24538ae0 **chưa nhận/chưa ghép**. Giữ mốc token/branding/math và guard D-R8-02 đã nhận; không Cloud Figma. Đọc [W-23](../task/web/W-23-doi-chieu-figma-va-giao-dien.md) và [review thiết kế lần 10](coord-ba-nhom-lan10-evidence-2026-10-28/design-review/review.md).

Sáu PNG có thật và SHA/bytes đúng; W-10 tái dùng nguồn 1fc0f553 đến aaf68eb có diff rỗng là hợp lệ. Lỗi nằm ở phương pháp so và kết luận. Sửa bốn Required, chỉ trong vùng thiết kế/bằng chứng:

1. **D-R10-01:** ba ảnh React là bản gốc lịch sử, không phải capture/crop mới. W-08 React 1280×2380/2572 so với HTML 808×62/154; W-10 React 390×900 so HTML section 366×808. Chụp/crop cùng vùng và state hai bên, giữ cùng trạng thái khối tiên quyết hoặc cắt khỏi vùng so; ghi nguồn lịch sử thật. Cùng bề rộng viewport chưa đủ. React hiển thị câu hỏi ở ngoài, summary “Xem đáp án” không có tam giác; HTML dùng câu hỏi trong summary. Ghi khác biệt thật và phương án, không gọi đồng nhất. Được dùng nội dung tổng hợp tương đương trong HTML; không sửa React chưa được phân công.
2. **D-R10-02:** đo vùng click đúng phần tử. Summary HTML cao 27,1875 px; padding 16 px của details không nhận click. React lịch sử có guard target đạt, không có bằng chứng React bị lỗi target. HTML #29A9FF trên #161B22 đạt 6,7657:1 (đạt AA chữ thường), không phải >7:1/AAA. Sửa narrowly owned HTML target nếu dùng làm chuẩn, hoặc ghi lệch rõ. Rút chứng nhận “không giật lag” nếu chưa có đo/video tương tác thật.
3. **D-R10-03:** hash W-08 41b6336e không khớp source. Ghi đầy đủ raw browser input SHA và SHA Git/LF, không trộn CRLF. Mỗi cặp có capture commit, raw source/assets hash, URL, viewport/DPR/theme/motion, state, crop/scroll coordinates, screenshot SHA, computed metrics/contrast và font thực. Font-family hoặc document.fonts.check không chứng minh font đã tải; chờ font và ghi FontFace/CDP platform fonts. Capture fallback phải gắn nhãn, không dùng chứng nhận intended-font. Lưu metrics/receipt thành JSON, không chỉ in console rồi viết bảng bằng tay. Một lệnh/cwd rõ ràng phải tái tạo được cả hai phía bằng công cụ cục bộ sẵn có, không dựa vào file chưa commit trong root.
4. **D-R10-04:** sửa copy hỗ trợ: mật khẩu 8–128, từ chối mật khẩu phổ biến; Argon2id là chi tiết server, không phải nhãn nhập mật khẩu. Disclosure W-12 phải có hoạt động gần nhất/tiến độ module và không thấy chat/tài liệu riêng/đáp án quiz. Không gọi snippet cũ là đúng chuẩn khi còn thiếu.

Trước hết bàn giao lại đúng hai cặp self-check W-08 và thư viện module W-10 có receipts/metrics thật. Khi cách so đã đúng mới mở rộng các cặp W-08/09/10 còn lại, 768/sáng-tối/reduced-motion/bàn phím và video. Lệch React sai thì giao web sửa; lệch mẫu sai thì sửa HTML; hai cách hợp lý cần đề xuất/chủ dự án chọn, không tự ghi đã duyệt. Đề xuất hai/ba tab hiện vẫn mở, không giả quyết định đã có.

Bàn giao report/w23-lat1-sua-bang-chung-2026-10-28.md (hoặc ngày thực tế), manifest machine-readable SHA-256, nguồn/lệnh/cwd/metrics/ảnh/video. Không sửa các bản untracked trong thư mục chung: root hiện có tám bản sao W-23 được giữ nguyên SHA, chỉ điều phối xử lý khi đến đợt ghép. Giữ lịch sử, không xoá video/artifact/ảnh cũ hoặc mở Cloud để thay yêu cầu đo.

## 4. Cổng ghép và an toàn dữ liệu

- Một vé một nhánh/worktree dưới tmp; thư mục chung luôn main và chỉ điều phối sửa tài liệu/ghép. Không tự push/ghép main, add rộng, reset/stash/restore tệp của người khác.
- Nhận main mới trước cổng cuối; exact commit được soát, source SHA/JUnit/native exit có thật. Python qua scripts/w05_run_tests.py, PostgreSQL bắt buộc và một full PG mỗi lúc. Browser UUID riêng theo harness, không dọn DB phiên khác hoặc DB phiên bị ngắt.
- Không xoá/dọn worktree/artifact/PDF/ZIP/snapshot, không junction/symlink/hardlink, tuyệt đối không đụng tmp/t01a-clean-ff797eb. Fixture chỉ chép tệp thường theo allowlist/SHA, không live learner cache/tập giữ lại.
- Web vẫn Vertex; SA-61 đã ghép ab5c2fa không tự đổi transport. Không cấp/rerun grant hay paid W-15. W-18/W-19/W-20/W-21 chưa hoàn tất; bảo vệ admin đầu tiên phải được giữ khi W-20 làm xoá tài khoản.
