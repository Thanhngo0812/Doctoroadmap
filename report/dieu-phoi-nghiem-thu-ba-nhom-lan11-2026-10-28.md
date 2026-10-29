# Nghiệm thu ba nhóm lần 11 và kế hoạch tiếp theo — 2026-10-28

**Chỉ W-12 đủ điều kiện ghép.** Đã ghép local **1511f05c274ba747989c9bf4285baaf413eb1d8d**; chưa push theo quyết định chủ dự án 24/10. W-17.1 và lát 1 W-23 giữ ở nhánh. Chi nhà cung cấp mới **0 USD**. [Lời giao ba nhóm](lenh-giao-viec-ba-nhom-lan11-2026-10-28.md).

## 1. Nguồn và phạm vi

| Nhóm | Bản bàn giao ghim | Phán xét |
|---|---|---|
| Web | a8e2075dac329154cc98f0a03b6c600ea7c958d4, nguồn tác giả a594a469 | W-12 đạt toàn vé, đóng WEB-R10-01 |
| Lõi | 862dd805180201647cd6a3dda54c2083073d1e84, nguồn 847cfe94 | POL-R10-01 sửa đúng; chưa nhận backend vì CORE-R11-01 |
| Thiết kế | 60412c87df1b684c97e6148d1f88f578d5202322 | Nhận xét/crop đúng được ghi nhận; cả lát 1 chưa nhận vì D-R11-01/02 |

Nền đầu 26d43b83. Main tiến thành **b64b88478e72cc36991815006923d9b3ae0beb93** khi làn Claude ghép DG-20; cổng trước khởi chạy bắt đúng thay đổi này. Đã nhận main vào candidate cuối **33f5b2d2d5f30f9e1778a2f1ddeecc3ce2180e81** trước full PG/build/browser và chạy lại React trên đúng mốc mới. React lượt trước 163,33 giây ở 3b90bf68 chỉ là lịch sử. Frontend Git tree giữa bản web bàn giao và candidate cuối giống hệt; AuthProvider/Account W-04 được giữ. Không lấy kiểm ở thư mục chung/nhánh cũ làm kết quả source mới. DG-20 là phần làn đánh giá đã ghép; cổng hồi quy này không thay nghiệm thu khoa học của làn đó.

## 2. Cổng độc lập trên bản sẽ ghép

| Cổng | Kết quả | Bằng chứng |
|---|---|---|
| Python toàn repo, PostgreSQL bắt buộc | **3545 pass/0 fail/3 skip/1 xfail** | [JUnit](coord-ba-nhom-lan11-evidence-2026-10-28/runs/full-final.xml), [native/source/command](coord-ba-nhom-lan11-evidence-2026-10-28/runs/full-final-exit.json) |
| React | **259 pass**, native 0 | [JUnit](coord-ba-nhom-lan11-evidence-2026-10-28/runs/react-received-main.xml) |
| Build | native 0 | [receipt](coord-ba-nhom-lan11-evidence-2026-10-28/runs/build-final-exit.json) |
| Browser HTTP/auth/PG thật |12 cấu hình/49 PNG/49 Axe, **0 violation/0 pageerror** | [audit](coord-ba-nhom-lan11-evidence-2026-10-28/browser-w12/audit.json), [runtime](coord-ba-nhom-lan11-evidence-2026-10-28/browser-w12/runtime.json) |

Ba skip: hai ca đánh giá cần DANHGIA_KHO_CHUNG và Cloudinary live chưa bật. Xfail SA-66 là recording answer-2 cũ cần ghi lại trả phí. Tên/lý do chính xác ở [tổng hợp](coord-ba-nhom-lan11-evidence-2026-10-28/gate-summary.json); không thêm skip để làm xanh. Cổng chạy qua scripts/w05_run_tests.py, basetemp mới; một full PG/lúc. Dữ liệu chép thường theo allowlist/SHA:3145 tệp phát triển sáu cuốn, PDF train 1054520 bytes/SHA 1f019766…; không learner store/live cache/tập giữ lại/liên kết.

Browser có256 HTTP JSON,15 ảnh SQL connection độc lập,5 video giữ trong worktree với [SHA/dung lượng](coord-ba-nhom-lan11-evidence-2026-10-28/retained-videos.json). Font CDP thực Be Vietnam Pro Bold custom16 glyph. Đã xem trực tiếp ảnh 390 tối, 1280 đang tải và 1280 gửi thành công, không tràn/ngắt thao tác; taste0 FAIL,1 WARN về khoảng trống ở khoá thử chỉ có1 khoá.106 console entries là HTTP lỗi chủ ý/CSP auditor; không gọi console hoàn toàn sạch. DB UUID của chính harness đã đóng/gỡ và kiểm độc lập không còn; thread dừng/port8027đóng. Không đụng DB phiên khác/DB lượt bị ngắt.

## 3. Web — WEB-R10-01 đã đóng

Sửa hai điều kiện: disabled nút gửi khi GET pending và guard submit khi loading. Cho nhập/giữ draft; GET thành công/lỗi đều thoát loading, gửi/thử lại bình thường. Không thêm framework/cache/endpoint. Backend50 email/200 thư/TTL 7 ngày/đúng email đã xác minh và membership chủ động giữ nguyên.

Độc lập đặt nguyên component af2993a5 lên nền tích hợp:3 assertion fail/16 control pass/0 setup error. Bỏ disabled guard:3fail; bỏ submit guard:2fail. Tất cả khôi phục byte/SHA trước cổng xanh. [Mutation](coord-ba-nhom-lan11-evidence-2026-10-28/web-mutations.json), [review](coord-ba-nhom-lan11-evidence-2026-10-28/web-review/review.md). Browser giữ response GET HTTP thật: không POST khi tải, sau tải đúng 1 POST và pending/nút huỷ còn sau reload; SQL độc lập xác nhận. Bốn lượt giữ GET có số hàng ban đầu **1,2,0,1**; không gọi đây là ma trận rỗng/có × motion cân bằng 2×2. Unit kiểm cả snapshot rỗng/có và error/retry/cleanup.

Proof còn gồm dedupe,TTL 7 ngày,member cap 200,verified email trước membership,accept chủ động,wrong email/cancel/expiry/rate 200 và token không vào request/storage. FakeMailer, không SMTP thật.798 SHA nguồn raw receipts giải thích được qua Git LF/CRLF/raw snapshot,184 evidence SHA đúng; source kiểm → delivery không thay src/scripts. Helper audit đầu chuẩn hoá cả binary nên có falsepositive; [audit cuối](coord-ba-nhom-lan11-evidence-2026-10-28/source-evidence-audit.json) phân biệt đúng, không che thay mã.

## 4. Lõi — CORE-R11-01 Required/P2

**Admin đầu tiên A đang active; B là admin thêm sau. A khoá B thành công, rồi PATCH B role=user/quota 7 trả409 last-admin.** SQL vẫn có A active/admin và B disabled/admin. Hạ B không làm mất admin active; guard đang dùng admin_count active cho cả target disabled. Lỗi ở AdminService.update_user:57.

Probe HTTP/PG độc lập trên98f9c38d: **1 assertion fail/1 control pass/0 setup error**, native 1. Control bảo vệ admin đầu tiên xanh. [HTTP/SQL](coord-ba-nhom-lan11-evidence-2026-10-28/core-review/core-probe-proof.json), [test chạy lại](coord-ba-nhom-lan11-evidence-2026-10-28/core-review/test_core_probe.py), [JUnit](coord-ba-nhom-lan11-evidence-2026-10-28/runs/core-independent.xml), [review](coord-ba-nhom-lan11-evidence-2026-10-28/core-review/review.md). Chỉ áp guard khi chuyển đổi thực sự giảm admin active; giữ lock/registry/đầu tiên và rollback, thêm disabled→user/enable+demote/multifield controls. Không tự vá productcode ở main.

Định danh singleton bền vững, trigger giữ registry và tài khoản được bảo vệ, bootstrap/assignment/audit transaction, CLI đối chiếu DB cũ và DTO có trạng thái chưa xác lập đã đúng hướng; không đếm admin cuối thay bảo vệ đầu tiên. Migration w17_0009 nối w12_0008 chưa áp DB dùng chung. DELETE API W-20 chưa có; trigger/FK là bảo vệ thấp hơn.3.600 pass/14 mutant là báo cáo của tác giả, không lấy thay cổng nghiệm thu độc lập của backend còn lỗi. Manifest380 tệp có378 khớp;2 hàng redactions.json/packaging-note.json stale cần cập nhật khi chốt.

## 5. Thiết kế — giữ phần đúng, hoàn thiện hai Required

Chín PNG/SHA/bytes và3 crop React đúng từng pixel;3hash source raw CRLF/Git LF đúng. Đã sửa đúng AA 6,7657/target HTML 27,1875px, rút chứng nhận no-lag và sửa copy W-04/W-12. Không có bằng chứng targetReact lỗi; không yêu cầu Cloud. [Kiểm ảnh](coord-ba-nhom-lan11-evidence-2026-10-28/design-review/evidence-inspection.json), [review](coord-ba-nhom-lan11-evidence-2026-10-28/design-review/review.md).

**D-R11-01:** ảnh/số đo phải gắn source thực đang so. W-10 reuse 1fc0f553 → aaf68eb đúng nhưng ContentLibrary hiện tại có thêm UsageLimits; W-08 có library/assistant. Chụp component hiện tại hoặc chứng minh reuse hẹp leaf/style/state, không chứng nhận toàn module hiện hành từ khoảng diff cũ. Ảnh lịch sử giữ nhãn.

**D-R11-02:** báo cáoW-08 nói offline Segoe UI/no Faces, JSON lại ghi custom Be Vietnam Pro, 78 glyph/loaded. Tái tạo blocked HTTP độc lập thực sự là Segoe UI/empty Faces; đó là run khác, không tự chứng nhận font của PNG online. PNG thật folded 808×62/open 808×154/W-10 HTML 366×808, khác số trong bảng/JSON đã làm tròn rect. Ghi CSS rect khác decoded PNG dimensions, full SHA/assets/font cùng run. Script chạy lại được cục bộ native 0; ba HTML PNG vẫn byte giống mốc 24538ae0, cần ghi reuse hoặc giữ receipts cùng run. Các đề xuất 2/3 tab/self-check UX còn mở; giữ React đã nhận trong lúc chốt bằng chứng.

## 6. Kế hoạch và bảo toàn

Lõi sửa CORE-R11-01→điều phối nhận backend→webReact W-17.1 Người dùng/Nhật ký và lõi W-17.2 metadata bản dựng/khoá mẫu. Thiết kế sửa hai receipt rồi mở rộng W-23. Chưa mở retry/cancel thay chủ khi port/route/grant/budget chưa chốt với Claude; không giả Actor/upload owner. Chi/validation và W-18/W-19/W-20/W-21 còn mở. Bảo vệ xoá bootstrap theo ADR 0030 phải giữ ở W-20. [Lời giao đầy đủ](lenh-giao-viec-ba-nhom-lan11-2026-10-28.md).

Không push/Gemini/SMTP/Cloudinary/paid grant/rerun W-15, không đổi Vertex hoặc bật trần. Không xoá/dọn artifact/PDF/ZIP/snapshot/worktree/DBW-15, không junction/symlink/hardlink, tuyệt đối không đụng tmp/t01a-clean-ff797eb. Tám tracked dirty và216 untracked trước lượt giữ nguyên SHA (gồm8 W-23). Lượt ghép thử core gặp Filename too long;608 tệp checkout dở trong **worktree riêng của lượt này** đã được lưu nguyên byte/SHA vào tmp/coord-r11-tools-20261028/failed-merge-files trước ghép lại với core.longpaths=true, không xoá hoặc đụng dữ liệu gốc.

Các phiên review phụ dừng trước kết luận do hạn mức; điều phối trực tiếp hoàn tất soát và các probe nêu trên. Không gán kết quả toàn diện cho phiên chưa hoàn thành. [Manifest bằng chứng](coord-ba-nhom-lan11-evidence-2026-10-28/manifest.json) ghi SHA raw vàSHA archive sau chuẩn UTF8/LF; bản raw/video giữ trong tmp. Lệnh/cwd/native/giây/source pin ở receipts và helpers. Hồ sơ này cùng lời giao đã commit local; chưa gửi nhân viên bên ngoài.
