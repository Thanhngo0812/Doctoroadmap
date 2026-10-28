# Nghiệm thu ba nhóm lần 10 và kế hoạch tiếp — 2026-10-28

**Kết luận:** nhận toàn W-04 React và ghép **local 18206f31**. **Chưa nhận/chưa ghép** W-12 React af2993a5, W-17.1 backend 9cf405ac hoặc lát đầu W-23 24538ae0. Giữ các mốc backend W-12, token/branding/math và guard thiết kế đã nhận trước đó. Hồ sơ/test xanh của nhân viên không thay các phản chứng độc lập dưới đây. Chưa push theo quyết định chủ dự án; chi nhà cung cấp mới **0 USD**.

## 1. Quyết định mới của chủ dự án: admin đầu tiên được bảo vệ

Trong lúc nghiệm thu, điều phối nêu việc W-17.1 cho phép disable admin cuối và hỏi chủ dự án. Chủ dự án trả lời nguyên văn ngày 28/10:

> admin đầu tiên ko đc khóa hay gì

Đã ghi nhận: **admin đầu tiên không được khoá quản trị (status disabled), hạ quyền hoặc xoá**, kể cả tự thao tác hoặc admin khác thao tác. Đây là bảo vệ định danh bền vững của admin đầu tiên, không chỉ đếm admin cuối/role/status hiện hành. Hồ sơ/mật khẩu và các bảo vệ đăng nhập/CSRF/giới hạn thử sai hiện hành vẫn giữ.

Quyết định được ghi tại [ADR 0030](../doc/adr/0030-bao-ve-tai-khoan-admin-dau-tien.md), spec chức năng và vé W-17/W-20. Đây là quyết định đã chốt, **không còn chờ chủ dự án chọn giữa hai phương án cũ**, nhưng code W-17.1 chưa thực hiện đúng nên giữ ở nhánh. Không tự viết mã sản phẩm hoặc chuyển DB dùng chung trong lượt điều phối này.

## 2. Mốc bàn giao và kết quả

| Phần bàn giao | Exact commit | Phán xét |
|---|---|---|
| Web — W-04 React | f52466dc092edb1bffa7bb4fe030d5482c4d5836 | Đạt toàn W-04; backend c1f2fe9 đã được nhận |
| Web — W-12 React | af2993a57ae4d9c023e0b77a5d6b699399753427 | Chưa nhận: WEB-R10-01, GET cũ ghi đè lời mời vừa tạo |
| Lõi — W-17.1 backend | 9cf405acbbf8838d05a17b4bb7936d171cb5afa5 | Chưa nhận theo quyết định mới: POL-R10-01; chưa bảo vệ admin đầu tiên |
| Thiết kế — lát 1 W-23 | 24538ae0a658c6e7a7439a8cf3418373e53a7aa4 | Chưa nhận lát 1; D-R10-01…04 về khung so/số đo/provenance/copy; toàn W-23 vẫn mở |

Nhóm web đã tách hai nhánh đúng yêu cầu; W-12 không chứa W-04. Đã ghép thử cả hai cùng W-17.1 tại ứng viên 44de063a trong tmp/coord-r10-acceptance-20261028, Auth.tsx tự ghép và kiểm độc lập giữ cả epoch/profile của W-04 lẫn fragment của W-12. Sau khi thấy lỗi W-12, ứng viên 5fcedba6 ở tmp/coord-r10-final-20261028 chỉ còn W-04/W-17.1. Sau chỉ thị mới của chủ dự án, ứng viên cuối **b766931a47503fa150734dfb5f5a9de8653b2b52** ở **tmp/coord-r10-web-final-20261028** chỉ nhận W-04 trên main **776f1f00b13726fcdc95f12bfd18a2b937bbd153**. Các worktree/bằng chứng trước được giữ, không reset/rebase/xoá dữ liệu.

## 3. Cổng điều phối trên ứng viên được nhận

| Cổng | Nguồn | Kết quả |
|---|---|---|
| Python toàn repo, PG bắt buộc qua runner | b766931a47503fa150734dfb5f5a9de8653b2b52 | 3.527 pass / 0 fail / 3 skip (Cloudinary live + hai replay DG cần kho graph thật), 1 replay xfail cũ; native 0 |
| React | b766931a47503fa150734dfb5f5a9de8653b2b52 | 239 pass, native 0 |
| Build | b766931a47503fa150734dfb5f5a9de8653b2b52 | Native 0 |
| Browser W-04: HTTP/PG/auth/Argon2 thật, Mailer/clock giả | b766931a47503fa150734dfb5f5a9de8653b2b52 | 12 cấu hình, 38 ảnh, 38 Axe, 70 JSON HTTP, 29 snapshot SQL; native 0 |

Lệnh/cwd/HEAD/native/elapsed/JUnit nằm trong [gói bằng chứng](coord-ba-nhom-lan10-evidence-2026-10-28/manifest.json), [tổng hợp cổng](coord-ba-nhom-lan10-evidence-2026-10-28/gate-summary.json) và [JUnit Python](coord-ba-nhom-lan10-evidence-2026-10-28/runs/full-web-final.xml). Cổng xanh này **không chứa W-12 React/W-17.1 mới**, nên không diễn giải rằng các bản bị giữ đã đạt.

Cổng PG của phiên DG-20 đang chạy khi bắt đầu; điều phối đợi, không dừng phiên khác. Cổng riêng ở 5fcedba6 bắt đầu sau DG-20, rồi được điều phối dừng đúng pytest của mình khi chỉ thị admin đầu tiên tới: native 4294967295/71,06 giây, không JUnit hoàn chỉnh, không tính xanh. Giữ log/receipt cùng các lượt React/build/browser đã hoàn tất ở ứng viên trước. Các lượt cuối có nhãn mới, không đè bằng chứng cũ.

Fixtures đưa vào mỗi worktree bằng helper allowlist/SHA: **3.144 tệp thường**, không link và không nhập learner store. PDF candidate phát triển 1.054.520 byte có SHA-256 1f019766e74a747d293c15ad5bc86b2ea90420b49a8437cf27c1f6805656a627 được copy riêng cho test sẵn có, không chạy W-15 paid/operator. Không đọc tập giữ lại/cache người học thật, không dọn artifact/ZIP/PDF/snapshot/DB W-15 hoặc tmp/t01a-clean-ff797eb.

## 4. W-04 đạt: tài khoản, mật khẩu và huỷ phiên được kiểm thật

Trang /tai-khoan có ba khối thông tin, đổi mật khẩu và đăng xuất mọi nơi có xác nhận. Tên trim 1–60, mật khẩu 8–128 theo backend W-02, fields lỗi gắn đúng trường. Không thêm danh sách thiết bị/xoá tài khoản. AuthProvider có epoch để phản hồi phiên cũ không ghi đè tài khoản mới; form abort khi rời màn, bí mật chỉ ở state form.

Review độc lập: **13 test W-04 focused pass**, trong đó ba probe riêng kiểm stale identity; mutant bỏ guard epoch làm assertion fail/0 setup error và source được phục hồi đúng SHA. Các file nguồn/bằng chứng nhân viên và sự đồng nhất src/scripts giữa nguồn chạy cổng bc4349fd và tip f52466dc đã kiểm. [Review web](coord-ba-nhom-lan10-evidence-2026-10-28/web-review/review.md).

Browser của điều phối chứng minh bằng HTTP và SQL qua connection độc lập:

- Đổi mật khẩu từ A giữ A, B bị 401; mật khẩu cũ không login được, mật khẩu mới login được.
- Login lại để có hai phiên, logout-all huỷ cả A/B, tài khoản khác vẫn dùng được. Không suy tổng số phiên cả DB phải bằng 0 vì observer/tài khoản khác có phiên riêng.
- Sai mật khẩu/CSRF/tên 61 không đổi dữ liệu; audit password_changed/logout_all không chứa bí mật.
- GET /me cũ được giữ rồi trả sau logout-all/login người khác, UI vẫn là người mới. URL/history/storage không có mật khẩu tổng hợp.
- 390/768/1280 × sáng/tối × thường/giảm chuyển động, focus/44px/overflow, lỗi đỏ, hộp xác nhận/Escape/trả focus; 0 Axe violation và 0 pageerror. Console có các 401 có chủ đích và CSP cảnh báo từ phép kiểm font/style của Axe; không gọi console hoàn toàn sạch.

Đã xem ảnh thật desktop/mobile và dialog/lỗi. Giao diện rõ ba nhóm thao tác, giữ WayFinder/Be Vietnam Pro/token, form xếp dọc trên mobile; không có Required thị giác mới. Taste inspector có WARN khoảng trống 44px ở khối danh tính, đã được người làm giải thích là chỗ phản hồi xác minh để tránh nhảy form; không thu hồi cả mốc vì một gợi ý polish. Không dùng DOM clone của inspector thay HTTP/SQL thật. [Audit browser](coord-ba-nhom-lan10-evidence-2026-10-28/browser-w04/audit.json).

## 5. W-12 chưa đạt: phản hồi GET cũ che lời mời đã tạo

**Required WEB-R10-01, P2 — Invitations.tsx:19 và submit.** Tải danh sách ban đầu dùng GET và sau đó setItems toàn bộ; form vẫn gửi trong lúc GET chưa xong. POST tạo lời mời thành công cập nhật items/notice. GET cũ về sau thì ghi snapshot cũ đè lên kết quả mới. Người dùng mất email/nút huỷ trên UI; nếu snapshot cũ rỗng còn thấy sai thông báo chưa có lời mời.

Guard hiện tại không bắt được: **13 ca W-12 hiện có independently pass**, nhưng probe mới trên component thật có **1 assertion fail/0 setup error + 3 control pass**. Hai phép phá guard riêng của web (epoch/fragment) đều bị bắt và phục hồi byte/SHA; chúng không thay việc sửa race danh sách.

Điều phối tái hiện bằng **HTTP/PG thật**, nguồn ứng viên 44de063a có đúng component từ af2993a5: Playwright route.fetch lấy GET thật trước POST rồi giữ response; không dựng DTO giả. POST 200 và SQL độc lập thấy pending mới trước/sau. Sau trả GET cũ, UI không còn email mới, assertion “New pending invitation exists in PostgreSQL but older GET erased it from UI” fail/native 1. Snapshot HTTP này còn một lời mời khác, nên UI còn record cũ nhưng thiếu record mới; thông báo danh sách rỗng là case unit riêng. [SQL/proof](coord-ba-nhom-lan10-evidence-2026-10-28/w12-race/race-proof.json), [log](coord-ba-nhom-lan10-evidence-2026-10-28/runs/w12-real-race2.log).

Lượt root đầu w12-real-race không được tính là phản chứng sản phẩm: probe đã đòi email mới hiện ngay khi loading còn che danh sách. Đã sửa chỉ kỳ vọng sau GET, dùng UUID/nhãn mới race2 và giữ cả log đầu. Không sửa product hoặc hạ assertion cuối. Các DB UUID do chính harness tạo đã kết thúc; không dọn DB phiên khác.

Sửa tối thiểu bằng vô hiệu hoá đọc cũ hoặc tuần tự hoá tải/gửi, giữ loading/error/retry/unmount/đổi tài khoản. Phải chứng minh UI cuối khớp DB và có nút huỷ, không chỉ đổi thông báo. Backend W-12 đã nhận ở R9 vẫn giữ; không làm lại Mailer, quota, verified-email hay membership.

## 6. W-17.1: hợp đồng cũ xanh, quyết định mới bắt buộc sửa

Mốc 9cf405ac gồm ba route GET/PATCH admin/users và GET admin/audit, typed DTO chỉ metadata, pagination/bounded filters, atomic audit/session revoke, race last-role-admin, quota tháng Việt Nam/null. Không migration mới, head w12_0008. Đã soát **23 probe độc lập pass**, 6 mutant bị bắt bởi 7 assertion/0 setup error, phục hồi đúng SHA; 261 file source copy/144 SHA nguồn cổng/233 file bằng chứng và 11 mutant tác giả đều khớp. Các probe reviewer là offline/memory/SQL/HTTP DTO, không gọi chúng là lượt PostgreSQL của điều phối. Full PG 3.481 pass là báo cáo nhân viên trên hợp đồng cũ, không phải nghiệm thu theo quyết định mới.

Theo spec trước câu trả lời, việc disable admin cuối là một điểm chưa chốt đã được người làm nêu minh bạch. Sau chỉ thị mới, **Required POL-R10-01** thay cho ghi chú Optional cũ: bản bàn giao vẫn cho disable người đầu tiên, không có bảo vệ định danh đầu tiên trước hạ quyền/xoá. Test test_new_owner_policy_first_admin_cannot_be_disabled đã chạy trên source không đổi: **1 assertion fail/0 setup error/native 1**. [Bổ sung review](coord-ba-nhom-lan10-evidence-2026-10-28/core-review/policy-addendum.md), [JUnit đỏ](coord-ba-nhom-lan10-evidence-2026-10-28/core-review/runs/owner-policy-red.xml).

Không trộn hai chuẩn rồi gọi mốc đạt. Nhóm lõi phải sửa, giữ test cũ về quyền/Actor/rollback/session/quota và bổ sung định danh bền vững: tài khoản thường cũ được nâng admin sau không được thay người đầu tiên; cả admin đầu tiên và người khác đều không được disable/demote/delete tài khoản đó; PATCH nhiều field/cạnh tranh phải từ chối nguyên tử. Cách lưu/migration/lỗi/DTO do bản sửa đề xuất, không tự chạy DB dùng chung. [Review gốc](coord-ba-nhom-lan10-evidence-2026-10-28/core-review/review.md) được giữ đúng bối cảnh cũ; addendum mới là phán xét hiện hành.

## 7. W-23 lát đầu chưa đạt; bằng chứng thật nhưng kết luận còn sai

Sáu PNG tồn tại, bytes/SHA đúng và ba React PNG đúng là bản sao nguyên byte của ảnh lịch sử; không thấy bằng chứng tạo ảnh React giả. Diff W-10 1fc0f553 → aaf68eb rỗng, cho phép tái dùng đúng phạm vi. Tuy vậy bốn Required còn lại:

- **D-R10-01:** khung so khác nhau: React W-08 1280×2380/2572 với HTML crop 808×62/154; React W-10 viewport 390×900 với HTML section 366×808. Câu hỏi/summary/icon và khối tiên quyết còn khác state. React là câu hỏi bên ngoài + “Xem đáp án”, không phải nhãn/icon report mô tả. Không thể gọi đồng nhất chỉ vì cùng viewport.
- **D-R10-02:** vùng click summary HTML **27,1875px**, phần padding ngoài không toggle; không phải đo cả details rồi nhận target 44. HTML #29A9FF trên #161B22 là **6,7657:1**, đạt AA chữ thường nhưng chưa >7:1/AAA. Không có chứng cứ React target bị lỗi; guard lịch sử React đạt vẫn giữ. Ảnh tĩnh không chứng minh không giật/lag.
- **D-R10-03:** hash HTML W-08 41b6336e không khớp raw CRLF 066de462… hoặc Git/LF ef89ee7e…; thiếu full hash, URL/crop tọa độ/metrics/receipt font hai bên. Probe offline chỉ rõ computed family và fonts.check không chứng minh custom font thật; CDP ở cấu hình offline dùng Segoe UI/Arial. Không suy điều đó thành khẳng định font của ảnh tác giả ban đầu, vì ảnh ban đầu không có receipt font.
- **D-R10-04:** hướng dẫn W-04 “Argon2id ≥8” chưa đúng luật 8–128/common-password và không phải nhãn người dùng; copy W-12 còn thiếu last activity/module progress và loại trừ tài liệu riêng/đáp án quiz.

Các counterexample HTML được chạy trên file gốc không đổi, HTTP(S) ngoài bị chặn, dùng Chromium riêng; số đo/ảnh fallback ghi nhãn offline. Target ở padding không mở details, summary click mở được; không dựa vào flag tự gán. [Review chi tiết](coord-ba-nhom-lan10-evidence-2026-10-28/design-review/review.md), [số đo](coord-ba-nhom-lan10-evidence-2026-10-28/design-review/html-probe.json). Không sửa file sản phẩm hoặc file untracked của nhân viên.

Tiếp lát 1 đúng crop/state, receipts và copy trước mở rộng lượt 2. Đề xuất hai/ba tab đang để chủ dự án chọn, chưa có quyết định được giả lập. Mốc token/branding/math/guard đã nhận không bị thu hồi. Không Cloud Figma.

## 8. Kế hoạch tiếp

| Nhóm | Việc giao ngay | Sau khi nhận mốc sửa |
|---|---|---|
| Web | Sửa WEB-R10-01 trên nhánh W-12, nhận main có W-04, chạy lại đúng cổng/SQL/browser | React W-17.1 Người dùng/Nhật ký sau khi backend bảo vệ admin đầu tiên được ghép |
| Lõi | Sửa POL-R10-01 trên W-17.1, định danh admin đầu tiên bền vững, guard/test/migration nếu cần | W-17.2 metadata bản dựng/khoá mẫu; chưa làm cả khu chi hoặc retry/cancel chưa chốt port |
| Thiết kế | Sửa D-R10-01…04 của hai cặp W-23, lưu JSON metrics/provenance/font thật và copy đúng | Các cặp còn lại/768/theme/motion/bàn phím/video sau khi phương pháp được nhận |

[Bản MD giao việc lần 10](lenh-giao-viec-ba-nhom-lan10-2026-10-28.md) đã soạn, chưa gửi phiên bên ngoài. Không giao làm lại phần đạt. Backend W-17 sau sửa vẫn chưa đóng toàn vé; W-18/W-19/W-20/W-21 chưa hoàn tất.

Điểm kỹ thuật cho Claude/điều phối trước mốc admin retry/cancel: BuildService hiện require_upload và requested_by; spec mục 9 yêu cầu admin huỷ/thử lại thay chủ, bảng HTTP mới ghi admin retry mà chưa có admin cancel. Phải chốt port/route/projection, không giả Actor người tải hoặc bỏ guard chung. Đây không cản sửa bảo vệ admin đầu tiên. SA-61 đã ghép ab5c2fa; web vẫn Vertex tới chỉ thị đổi của chủ dự án.

## 9. Chi phí, bảo toàn và giới hạn

Chi mới của điều phối/review/browser **0 USD**, chỉ fake clock/Mailer/model theo cổng; không gửi SMTP/Cloudinary/Gemini/ADC thật, không cấp/rerun grant hay paid W-15. Không cộng số giả trong test thành chi nhà cung cấp.

Tám tệp tracked dở ở root được giữ theo SHA đầu lượt. Tám bản sao W-23 untracked (report, sáu PNG, capture script) đã tồn tại trước nghiệm thu, được ghi SHA/bảo toàn, không đưa vào commit điều phối và không sửa đè. Các báo cáo từ nhánh bị giữ được sao chép vào gói review làm bằng chứng có raw SHA, không đổi phán xét thành đã ghép. Không add rộng/stash/reset/restore/cleanup.

Gói bằng chứng ghi raw SHA và SHA bản text chuẩn hoá UTF-8/LF; log UTF-16 nếu có được decode BOM, raw giữ nguyên. Browser thô/38 ảnh/2 video và các lượt thử ở cả ba worktree được giữ local, có danh sách SHA; ảnh đại diện và phản chứng W-12 đi vào gói. Chỉ ghép/commit local; cổng PG/cửa điều phối mở lại sau commit hồ sơ cuối.
