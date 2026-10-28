# Nghiệm thu ba nhóm lần 12 và kế hoạch tiếp theo — 2026-10-28

**Nhận backend W-17.1, ghép local 4e6f33cbce3c87d545062fbb061f4f3b88dec0d8. Chưa push GitHub.** CORE-R11-01 đã đóng; mở React Người dùng/Nhật ký và backend metadata bản dựng/khoá mẫu. W-23 chưa nhận cả lát vì số đo React còn ghi sẵn. Chi nhà cung cấp mới **0 USD**. [Lời giao ba nhóm](lenh-giao-viec-ba-nhom-lan12-2026-10-28.md).

## 1. Bàn giao được ghim và phạm vi phán xét

| Nhóm | Mốc được soát | Kết quả |
|---|---|---|
| Lõi | a07bff3f604c253cad030b45f744409ab7897bee; nguồn tác giả e7d54a1a | Đạt backend W-17.1; toàn W-17 còn mở |
| Thiết kế | f9705f4299ffd360de8c11861848689b3233503c | Ảnh/decoded PNG/source hẹp đúng; còn D-R12-01 về số đo thực |
| Web | a8e2075dac329154cc98f0a03b6c600ea7c958d4, giữ mốc W-12 lần 11 | Chưa có commit/nhánh/worktree bàn giao React W-17.1 mới; nay được gỡ chặn |

Main nền **35f15fa3fbe6a9e2939149e760545e8e80464419** đã có DG-15/DG-16 và tài liệu DG-18 do làn Claude ghép. Candidate độc lập **34c1712f58122457aeff1dee3cb69f50d3321a0a** nhận main này và đúng mốc lõi, không có bản thiết kế chưa đạt. Frontend tree giống hệt main nền; kiểm React là hồi quy tương thích, không phải một bàn giao UI quản trị mới. Cổng này không thay nghiệm thu khoa học các vé DG.

## 2. Cổng và phép thử độc lập

| Phép kiểm | Kết quả | Bằng chứng |
|---|---|---|
| Python toàn repo/PostgreSQL bắt buộc | **3.696 pass, 0 fail, 3 skip, 1 xfail** | [JUnit](coord-ba-nhom-lan12-evidence-2026-10-28/runs/full-final.xml), [command/cwd/source/native](coord-ba-nhom-lan12-evidence-2026-10-28/runs/full-final-exit.json) |
| React | **259 pass**, native 0 | [JUnit](coord-ba-nhom-lan12-evidence-2026-10-28/runs/react-final.xml) |
| Build | native 0 | [receipt](coord-ba-nhom-lan12-evidence-2026-10-28/runs/build-final-exit.json) |
| W-17 và probe bổ sung | **79 ca W-17 + 2 probe = 81 pass** | [JUnit](coord-ba-nhom-lan12-evidence-2026-10-28/runs/core-green-retry.xml) |
| Mã cũ 862dd805 | 2 assertion fail,0 setup error | [RED](coord-ba-nhom-lan12-evidence-2026-10-28/runs/core-old-retry.xml) |
| Bỏ kiểm target.status active | 6 assertion fail/2 pass,0 setup error | [mutation](coord-ba-nhom-lan12-evidence-2026-10-28/runs/core-missing-status-retry.xml) |
| Bỏ guard đếm admin active | 1 assertion fail/7 pass,0 setup error | [mutation](coord-ba-nhom-lan12-evidence-2026-10-28/runs/core-no-count-retry.xml) |

Tất cả mã bị phá được khôi phục đúng byte/SHA trước cổng toàn repo. Python chạy qua scripts/w05_run_tests.py tại worktree một cấp dưới tmp; PostgreSQL bắt buộc, basetemp mới, một full PG mỗi lúc. Cổng mất1308,36 giây qua wrapper. Hai skip đánh giá cần DANHGIA_KHO_CHUNG; một skip Cloudinary live chưa bật. Xfail SA-66 do recording answer-2 cũ cần ghi lại trả phí. Tên/lý do nguyên bản ở [tổng hợp](coord-ba-nhom-lan12-evidence-2026-10-28/gate-summary.json), không thêm skip hay hạ assertion.

Lượt đầu Docker Desktop tắt nên core-old có2 setup errors, **không tính là RED hành vi**. Đã bật Docker Desktop hidden và chỉ khởi động db-test hiện có, giữ log cũ và dùng label retry. Helper đối chiếu/tổng hợp của điều phối ban đầu đọc UTF-8 bằng cp1252 của Windows; đã sửa encoding rõ ràng. Label design-metrics-assert chỉ lỗi encoding; phản chứng hợp lệ là [design-metrics-assert-utf8](coord-ba-nhom-lan12-evidence-2026-10-28/runs/design-metrics-assert-utf8.log). Không lấy exit1 của helper lỗi làm bằng chứng sản phẩm sai.

## 3. W-17.1 đã đạt những gì

Guard chỉ xét số admin active khi target vốn active/admin và PATCH khiến kết quả không còn active/admin. B disabled → user, hoặc enable+demote cùng PATCH, không loại admin active nên phải được chấp nhận. Probe HTTP/Argon2/PostgreSQL thật xác nhận200 và SQL role/status/quota đúng; A bootstrap vẫn active/admin, UUID registry đúng A; phiên A dùng được, B không hồi sinh phiên cũ. Audit thay field đúng một lần, replay không ghi trùng, lỗi audit rollback nguyên tử.

Giữ bảo vệ định danh đầu tiên, live Actor, lock đồng bộ với login/reset, thu hồi phiên khi disable, metadata DTO không dữ liệu học riêng và guard quota/tháng Việt Nam. Source/test được soát theo correctness, đơn giản, ranh giới service/store, quyền/bảo mật và truy vấn giới hạn; không có Required mới. [Review lõi](coord-ba-nhom-lan12-evidence-2026-10-28/core-review/review.md), [mutation/SHA](coord-ba-nhom-lan12-evidence-2026-10-28/core-mutations.json). JSON green-enable trong thư mục core-review mô tả trạng thái GREEN cuối; RED có JUnit/log riêng.

**380/380** mục manifest bảo vệ admin đầu tiên và **209/209** mục manifest lượt sửa khớp bytes/SHA blob Git. Hai mục CRLF/LF từng stale đã sửa đúng. Nguồn e7d54a1a→delivery không đổi src/scripts. [Audit](coord-ba-nhom-lan12-evidence-2026-10-28/source-evidence-audit.json).

Migration một head **w17_0009 nối w12_0008**, registry bootstrap_admin singleton/immutable và trigger bảo vệ account đã nhận. API hiện có **GET/PATCH /admin/users và GET /admin/audit**; DTO is_first_admin true/false/null và lỗi protected_admin/bootstrap_required. Spec chức năng/DB/ADR 0030 đã cập nhật. **Chưa chạy migration hoặc CLI gán UUID vào DB dùng chung.** Trước dùng màn admin trên DB hiện hữu phải backup, đối chiếu hồ sơ bootstrap rồi operator áp migration/CLI một lần; không đoán từ thứ tự tạo hay role hiện tại. Fresh test DB bootstrap tự lập định danh.

Toàn W-17 vẫn còn React, danh sách bản dựng/khoá mẫu, chi/validation và các hợp đồng admin retry/cancel. W-20 chưa có delete API; không coi bảo vệ DB là đã làm xong W-20.

## 4. W-23: phần đúng và Required còn lại

Đã kiểm 9 PNG/SHA/bytes,3 crop đúng pixel,3 source rawCRLF/GitLF và decoded PNG 808×62/808×154/366×808. Điều phối trích/băm độc lập 4 khối JSX/CSS: self-check và filter/list/rules không đổi; đây là chứng minh source hẹp hợp lệ. Giữ các đính chính AA/target/no-lag/copy và mốc token/branding/math đã nhận. [Kiểm ảnh](coord-ba-nhom-lan12-evidence-2026-10-28/design-review/evidence-inspection.json), [source hẹp](coord-ba-nhom-lan12-evidence-2026-10-28/independent-leaf-reuse.json). Không cần Cloud.

**D-R12-01 Required:** reactActualMetrics, measuredHeight và cờ leafSourceValid/diff=0 trong script được điền hằng. Probe offline chạy khi không có src/server React vẫn xuất chúng. Không thể gọi đó là đo DOM hiện hành. Khi dùng Be Vietnam Pro thật/CDP trên candidate mới:

| Đại lượng | Receipt thiết kế | DOM đo thực |
|---|---:|---:|
| Chiều cao tab W-10 |44px |45px |
| Chiều rộng hàng tài liệu W-10 |332px |358px |
| Padding ngang hàng W-10 |16px |0px; padding thực16px0 |
| Font-weight h2 tự kiểm tra W-08 |700 |600 |

[Assertion chạy lại](coord-ba-nhom-lan12-evidence-2026-10-28/design-review/design-assertion-proof.json), [log native 1](coord-ba-nhom-lan12-evidence-2026-10-28/runs/design-metrics-assert-utf8.log). Các con số phụ thuộc viewport/content/font; min-height44 chỉ là CSS minimum. Không sửa React cho khớp số ghi nhầm. URL lịch sử khai /courses/c1/modules/m1/... không khớp course UUID/route/module của runtime thực. Lấy URL từ receipt, không gán URL minh hoạ làm URL capture.

Script giữ PNG canonical nếu có nhưng đo trang fresh. Offline HTML W-10 có CSS height 770 trong khi canonical cũ CSS height 807/PNG 808; fallback có thể đổi hình chữ nhật. Phải tách run/font/số đo tương ứng hoặc dùng ảnh mới cùng run. Nhãn ảnh lịch sử và kích thước PNG đã sửa đúng không thay được kiểm DOM thật.

Điều phối cung cấp **ba trạng thái React hiện tại** (thư viện 390 sáng, self-check gập/mở 1280 tối/reduced-motion), mỗi trạng thái có PNG/URL/viewport/CSSrect/decoded size/font. Hai run được tách: [font thương hiệu](coord-ba-nhom-lan12-evidence-2026-10-28/browser-react-fonts/current-react-metrics.json) và [fallback chặn HTTP ngoài](coord-ba-nhom-lan12-evidence-2026-10-28/browser-react-fallback/current-react-metrics.json). Run thương hiệu chỉ cho ứng dụng local và Google font assets; CDP xác nhận Be Vietnam Pro Regular/SemiBold custom. HTTP/auth/PostgreSQL/core thật với model/Mailer/media giả;16 HTTP API/run,0 pageerror,0 USD. Đây không phải kiểm toàn W-23, không phải browser admin UI và không phải lượt Axe mới. [Lệnh/runtime](coord-ba-nhom-lan12-evidence-2026-10-28/browser-command-receipts.json), [review thiết kế](coord-ba-nhom-lan12-evidence-2026-10-28/design-review/review.md).

Nhóm thiết kế dùng trực tiếp ảnh/JSON này, sửa nhãn hằng/URL/script rồi mở rộng W-08/09/10,768/bàn phím/reduced-motion/video. Đề xuất hai/ba tab/cách đặt câu hỏi vẫn mở; giữ React đã nhận trong lúc soát.

## 5. Kế hoạch tiếp theo và điều kiện hoàn tất

| Nhóm | Bắt đầu | Kết quả cần giao |
|---|---|---|
| Web | React W-17.1 đã hết chờ backend | Người dùng/Nhật ký theo3 API đã nhận; xử lý nullable bảo vệ/lỗi/stale callback,259test nền giữ, browser HTTP/PG/SQL/ảnh/video trên source mới |
| Lõi | W-17.2 metadata bản dựng/khoá mẫu | GET /admin/builds và PATCH /admin/courses/{cid}, DTO/filter/pagination/privacy/audit/rollback,0 provider call; chưa nối retry/cancel/chi |
| Thiết kế | D-R12-01 rồi W-23/màn admin | Receipt đo thật, đúng source/run/font/URL; dùng bằng chứng điều phối, mở rộng các cặp và kiểm tương tác còn thiếu |

Sau hai mốc quản trị này mới nghiệm thu các mốc React bản dựng/mẫu, chi/validation, W-18/W-19/W-20 và W-21. Port admin retry/cancel thay chủ vẫn cần phối hợp Claude: không giả Actor requested_by hay nới require_upload, phải chốt lifecycle/idempotency/audit/grant/budget/receipt trước. Không cản metadata/mẫu. [Lời giao chi tiết](lenh-giao-viec-ba-nhom-lan12-2026-10-28.md); chưa gửi phiên bên ngoài.

## 6. Dữ liệu và trạng thái Git

Chỉ ghép đúng source đã kiểm; mã sản phẩm không được điều phối sửa nóng. Chỉ commit local, chưa push theo quyết định chủ dự án 24/10; giữ Vertex, không paid grant/rerun W-15 hoặc bật trần demo. Chi0 USD ở đây chỉ là lượt kiểm mới, không xoá/đổi số tiền và unknown W-15 trước đó.

Fixture phát triển sáu cuốn được chép thường3145 tệp và PDF train 1054520 bytes, đối chiếu SHA; không learner cache live/tập giữ lại/liên kết. Tám tệp tracked dở và 216 untracked trước lượt (gồm 8 W-23) giữ nguyên SHA. Không dọn/xoá worktree/artifact/PDF/ZIP/snapshot/DB W-15; tuyệt đối không đụng tmp/t01a-clean-ff797eb. Hai DB UUID browser của chính lượt này đã được harness kết thúc, kiểm độc lập không còn và port 8032 đóng; không đụng DB của phiên khác/lượt bị ngắt.

[Manifest](coord-ba-nhom-lan12-evidence-2026-10-28/manifest.json) ghi raw SHA và SHA bản archive UTF8/LF; raw vẫn giữ ở worktree/tmp. Các lệnh, native, source, cwd và JUnit ở receipts/helpers. Cửa full PG đã trả; hồ sơ và bản giao việc được commit local sau đợt này.
