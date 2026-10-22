# Điều phối — kiểm lại W-25, React W-14, W-24 và kế hoạch tiếp — 2026-10-22

## 1. Kết luận và phạm vi

Đợt này ưu tiên gỡ điểm chờ **backend W-14/W-25 trên main** cho web chạy cổng tích hợp cuối. Chưa coi “cả ba nhóm báo xong” là nghiệm thu toàn W-14 hoặc W-24.

| Phần | Mốc bàn giao | Phán xét |
|---|---|---|
| Backend W-14 + W-25 | `c00c0284ffc9df2f05f5b4234fe6b549e19f1a0c` | **Đạt mốc backend/schema** tại `4dbfe8eb64b57ade2a4da27abc841c5c8dd29307`, đã ghép/đẩy `a572459` |
| React/tích hợp W-14 | `6494f51eb6b1033150d041197745b4d88a8a69da` | Đủ điều kiện nhận backend đã duyệt để chạy cổng cuối; chưa nghiệm thu. Cần bỏ32 tệp pytest tạm khỏi Git |
| Thiết kế W-24 | `f1ca86dccdf5f7b8e224d325314324050fe415f1` | Đã sửa nhiều lỗi thực, nhưng **chưa đạt** toàn bộ local/Cloud; còn3 nhóm Required |

**Main nền:** `cd22e9bd3da615197dc478df514b6a1b3972cb0b`. **Ghép backend:** **`a5724597117094600152fb9a705354ebba10bde0`**, đã đẩy GitHub. Web không còn chờ backend được duyệt trên main. **Chi dịch vụ ngoài mới: 0 USD**, không gọi mô hình/mail/Cloudinary thật.

Luật ngày22/10 chia làn: Claude nghiệm thu/ghép nhánh SA, điều phối ghép web. Tệp dở `task/sau-a10/19-dac-ta-bo-cau-hoi-thu.md` của làn khác được giữ nguyên, không stage/commit. Trước ghép kiểm lại main đúng mốc đã nhận; không tự nhập mã SA-52/53 đang nằm ở nhánh riêng.

## 2. Backend W-14/W-25

Reviewer độc lập và điều phối đọc thay đổi production so với `5b24ece`, test trước rồi truy nguyên implementation. Không thấy Critical/Required mới trong phạm vi mốc backend:

- **Confirm/cancel:** UPDATE queue chỉ thành công khi `awaiting_confirmation AND NOT cancel_requested`, có RETURNING để kiểm kết quả. Cancel commit trước thì confirm conflict/rollback, không đổi tên/confirmed_at hoặc tính quota. Confirm commit trước rồi cancel vẫn giữ luật đã dùng một lượt.
- **Terminal/cancel:** `record_usage` kiểm cờ huỷ sau khi khoá hàng và xác minh lease/receipt; chuẩn hoá cả kết quả callback thành cancelled, bỏ graph publication metadata nhưng giữ usage. Worker không gửi thư thành công từ kết quả cũ.
- **Media/cancel:** kiểm trước upload và dưới khoá sau upload; nếu huỷ trong thao tác không dừng được thì xoá đúng public ID vừa tạo chưa đăng ký, không tải tiếp ảnh sau. Không xoá nguồn hay dữ liệu dùng chung.
- **Receipt/lease:** callback lặp không ghi chi hai lần; lease cũ vẫn ghi số thực một lần nhưng không đổi trạng thái lease mới; thiếu số giữ usage_complete=false.

Test mới dùng engine/store/connection PostgreSQL độc lập và SQL kiểm trạng thái cuối, quota, course, upload, ledger, asset, thư. Ca terminal quan sát `pg_blocking_pids` hoặc cancel đã commit trước, rồi kiểm kết quả theo thứ tự thực; không dùng timeout hoặc thiếu khoá làm bằng chứng chính.

### Kiểm độc lập

Tạo worktree mới `tmp/coord-w25-acceptance-20261022` từ main mới, nhận `c00c028` thành **`4dbfe8e`**. Không sửa implementation, không chạy trong worktree nhân viên. Chép **3.144 tệp** theo hai manifest W-06, SHA-256 nguồn/đích khớp; bỏ learner store CLI, không tạo links/đọc live/tập giữ lại hoặc dọn t01a/snapshot/worktree.

| Kiểm | Kết quả |
|---|---|
| Sáu guard W-25 được phá độc lập rồi phục hồi | **6/6 bị assertion bắt**, từng bản sai native exit1, không setup error; wrapper exit0 |
| React nền hiện tại (W-07) | **85 đạt**, exit0; không phải104 React của UI W-14 |
| TypeScript/Vite nền | **Đạt**, exit0 |
| Python toàn repo + PostgreSQL bắt buộc | **2.163 đạt, 0 fail/error, 1 skip Cloudinary live**, native exit0; pytest530,06 giây / wrapper543,74 giây |

Sáu guard gồm CAS confirm, huỷ terminal, huỷ media, receipt chỉ ghi một lần, ngăn thư sau huỷ và khoá terminal. Lượt mutation chỉ đổi đích ghi bằng chứng của harness, không hạ assertion; implementation phục hồi đúng byte trước cổng cuối. Toàn bộ test qua `scripts/w05_run_tests.py`, không pytest trần. Native exit/cwd/argv/commit nằm trong gói bằng chứng.

Migration giữ **`w06_0005 → w14_0006`**, không có migration W-25. Mốc này đủ xét **backend/schema với bộ dựng giả**; không thay nghiệm thu React/browser đầu-cuối hoặc runner thật W-15.

Đã ghép `--no-ff` đúng mốc `4dbfe8e`, main trước ghép vẫn `cd22e9b`; commit ghép `a572459` có hai cha tương ứng. Push thành công `42a3e82..a572459 main -> main` (gồm các commit tài liệu main đã có trước khi kiểm). Đối chiếu `src/`, `tests/`, `scripts/`, `design/` giữa mốc qua cổng và commit ghép không có diff. Không ghép nhánh React hoặc W-24 mới; hồ sơ tiếp theo chỉ đổi tài liệu/bằng chứng.

## 3. Web — đã xong local, chưa phải cổng cuối

Soát chỉ đọc tại `6494f51` không thấy Critical/Required về logic sản phẩm. Hai bổ sung DTO hợp lý và có test quyền: `BuildView.upload_id` tra theo actor/build/course, learner không nhận upload ID của chủ; `UploadView.confirmed_at` riêng mỗi lần tải giúp đặt/xác nhận tên riêng ngay cả khi build dùng chung đã chạy hoặc xong. Giữ chúng khi nhận main backend, không lấy đè bằng DTO gốc.

UI giữ build_id+course_id trong poll/cancel/retry, kiểm ID trả về, abort khi đổi/rời trang; cancel/retry theo capability, không tự xác nhận, không hiện tiền. Hợp đồng backend gốc + hai DTO bổ sung được soát riêng, không thay trạng thái/khóa W-25. Mốc React vẫn cần nhận main backend đã duyệt và chạy lại cổng đúng đỉnh.

**Required trước ghép:** có **32 tệp `synthetic image`** được track dưới hai thư mục:

- `report/w14-react-evidence/basetemp-contract-green/`
- `report/w14-react-evidence/basetemp-contract-green2/`

Đây là dữ liệu tạm của pytest, không phải ảnh QA. Bỏ khỏi Git bằng `git rm --cached`, thêm ignore basetemp và giữ tệp local. Không xoá thư mục hoặc dọn worktree. Đã liệt kê chính xác bằng `git ls-tree -r --name-only 6494f51 report/w14-react-evidence`; gói bằng chứng giữ danh sách.

Số **2.165 Python/104 React**, ba mutation UI, browser **47 ảnh** và SQL trong báo cáo web hiện là **kết quả local của nhân viên**, không ghi thành lượt chạy lại độc lập của điều phối. Nhân viên cũng ghi rõ ảnh/video có trước vá câu chữ `953240b`, chưa chạy lại browser/full Python sau đó. Lượt cuối phải chốt đỉnh mới sau nhận main, sửa vệ sinh bàn giao và kiểm lại.

Giới hạn a11y cần giữ đúng: axe trong harness hiện chỉ chạy trang rejected, không phải mọi47 ảnh. Ở lượt cuối bổ sung upload/confirmation/running/terminal hoặc ghi rõ phạm vi chưa có. Reviewer đã xem confirmation390dark và running1280light, token/logo/bố cục rõ, không có tiền; việc đó không thay kiểm toàn bộ luồng cuối.

**W-11** giữ nguyên `a53f0d3` ở nhánh riêng; chưa nghiệm thu trong đợt này, chưa có migration successor. Sau backend được ghép có thể nối `w11_0007 → w14_0006`; nếu chỉ một phiên web thì hoàn tất W-14 trước rồi quay lại W-11.

## 4. W-24 — cải thiện đã kiểm, ba nhóm Required còn lại

Reviewer chạy Chromium trong bản chép thường `tmp/coord-w24-review-20261022`, chặn HTTP(S) bên ngoài; không sửa source/evidence của nhân viên, không gọi Cloud/model. Điều phối xem ảnh và kiểm lại các con số từ JSON. Đây là bằng chứng local, chưa phải kiểm Figma Cloud.

**Đã xác nhận sửa thực:** 12 cấu hình W-07/W-14 ×390/768/1280×sáng/tối; chữ tối sáng đúng, progress bar có màu, spinner96×96. Tổng/module/bài học cập nhật8→9→8/18 và không cộng trùng khi lặp thao tác; accordion aria/visibility đúng. Prototype baseline4/4; bỏ clipboard write, bỏ scroll hoặc giữ GIF động đều3/4/native1 đúng assertion. Thay bytes PNG tĩnh bằng GIF thật nhưng giữ nguyên filename cũng bị assertion đổi khung bắt, chứng minh guard đo ảnh thực.

**Còn Required:**

1. **Giảm chuyển động theo OS vẫn hỏng ảnh:** CSS `prototype_flows.html:412` còn `content:url('../assets/spinner_frame0_static.png')` không tồn tại. Nút bật tay dùng đường đúng nên guard happy path xanh; OS reduced-motion lại kích hoạt CSS sai. Browser có ERR_FILE_NOT_FOUND, vùng ảnh171×21 thay ảnh thật. DOM naturalWidth2000 không đủ chứng minh ảnh CSS replacement render được. Cần kiểm cả OS setting và nút bật tay.
2. **Token chưa khớp và guard chưa đủ:** so37 biến×2 mode=**74 giá trị, 7 lệch**: bốn tint dark alpha0.15 so CSS0.14, surface-2 light chưa có alias thực, radius-full không có cả hai mode. Thay dark brand tint thành0.99, **toàn bộ28 test vẫn đạt**; guard còn bỏ lọt thay spacing/radius/motion. Cần đọc CSS thật và so mọi mapping/mode. Bản raw trong evidence còn35 biến, bản design37; cập nhật hoặc ghi rõ lịch sử, không gọi đồng bộ100%.
3. **Checklist/đường chứng cứ chưa đủ:** `screens.html` không có landing hero như bảng khai; login/register bị dẫn sang preview verification/reset. Bảng22 dòng chưa phủ các trạng thái gốc: upload finished/cancel/parse-error, lecture pending/stream/fatal/page viewer, chat, quiz generation, lời mời/quản lý khoá/mức dùng và dark coverage từng trang. Bốn nhóm màn thiếu đã được nhân viên nhận rõ nhưng chưa hoàn tất.

**Cloud vẫn mở:** chưa có export Variables/biên nhận được xác minh độc lập, chưa có video bấm bốn prototype và bảng đủ trang/trạng thái. Node/Present URL là khai báo của nhân viên; không có Figma callable trong lượt soát để xác nhận chúng. Không lấy lý do quyền REST hoặc JSON local làm bằng chứng đã xuất từ Cloud.

Không nhập nguyên bản `f1ca86d` vào main khi còn Required. Giữ phần local W-24 đã ghép trước; không giao lại các lỗi chữ tối/clipboard/scroll/khung ảnh vừa chứng minh đã sửa.

## 5. Kế hoạch tiếp theo

| Nhóm | Việc ưu tiên | Xong khi |
|---|---|---|
| Web | Nhận main backend đã duyệt; bỏ32 tệp basetemp khỏi Git; chạy cổng cuối **W-14** | Python/PG, React/build và browser đúng đỉnh, ảnh/video mới, đủ SQL/capability/reuse/cancel, đúng phạm vi axe; điều phối nghiệm thu đầu-cuối |
| Lõi | Bàn giao mốc backend, hỗ trợ tích hợp DTO/usage/race W-14 | Không sửa mốc đã duyệt; lỗi mới có repro/commit riêng. Chuẩn bị tài liệu đầu vào W-15, chưa chạy thật |
| Thiết kế | Tiếp W-24, sửa3 nhóm còn lại và hoàn thiện Cloud/checklist | Guard đủ mọi mode, OS reduced-motion render thật, đủ ảnh/node/video/export, báo phần thiếu trung thực |

Sau W-14 đầu-cuối đạt: web quay W-11 theo tuyến `w06_0005 → w14_0006 → w11_0007`; lõi mới đề xuất dry-run/duyệt tiền W-15. Không coi ngân sách phục hồi hoặc SA-55 là quyền chi cho W-15. Vertex giữ nguyên.

Đã đọc kế hoạch Pha B mới: SA-46/47/51 được Claude nghiệm thu; SA-49 cần SA-53, SA-50 cần SA-52. Vì vậy W-08 còn chờ SA-40/41 qua SA-53, W-10 còn chờ SA-52; các nhánh đó do Claude nghiệm thu/ghép. W-23 vẫn chờ W-22 và các màn học, W-21 sau cùng. Không giao lại W-07 đã đạt hoặc tự mở nhiều màn học khi phụ thuộc chưa đạt.

Đã soạn [lệnh giao việc cho ba nhóm](lenh-giao-viec-sau-w25-2026-10-22.md), chưa gửi sang phiên nhân viên. Không có yêu cầu phê duyệt tiền trong lượt này.

## 6. Bằng chứng và lệnh tái lập

Gói [manifest SHA-256](coord-w25-w14-w24-evidence-2026-10-22/manifest.json), [summary](coord-w25-w14-w24-evidence-2026-10-22/summary.json), SQL cuối, ledger mutation, review/token/browser JSON và ảnh được giữ riêng với hồ sơ nhân viên. Nguồn thô giữ trong scratch, chỉ chuẩn hóa xuống dòng/khoảng trắng log/XML trước lưu; có hash trước/sau, JSON và số testcase không đổi. `.gitattributes` giữ byte khi checkout.

Gói có **79 tệp bằng chứng ngoài manifest**, 1.538.924 byte. Mở trực tiếp: [JUnit cổng backend](coord-w25-w14-w24-evidence-2026-10-22/backend/full-gate.xml), [ledger sáu guard](coord-w25-w14-w24-evidence-2026-10-22/backend/mutations/mutations-confirm-cancel-terminal-cancel-media-cancel-receipt-once-cancel-mail-terminal-row-lock.json), [danh sách32 tệp tạm của web](coord-w25-w14-w24-evidence-2026-10-22/web-handoff-hygiene.json), [review thiết kế](coord-w25-w14-w24-evidence-2026-10-22/w24/review.md), [74 so khớp token/mode](coord-w25-w14-w24-evidence-2026-10-22/w24/token-css-observations.json), [ảnh lỗi OS reduced-motion](coord-w25-w14-w24-evidence-2026-10-22/w24/prototype-os-reduced-motion.png).

Từ `tmp/coord-w25-acceptance-20261022`, các lệnh chốt backend:

```powershell
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe -X utf8 src/web/backend/tests/copy_w06_fixtures.py
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe scripts/w05_run_tests.py -o addopts= -q --basetemp=tmp/coord-w25-full-20261022 --junitxml=C:/Users/ngoco/Desktop/Doctoroadmap/tmp/coord-review-20261022/evidence/backend/full-gate.xml
npm.cmd --prefix src/web/frontend test -- --pool=threads --maxWorkers=1 --reporter=default --reporter=junit --outputFile=C:/Users/ngoco/Desktop/Doctoroadmap/tmp/coord-review-20261022/evidence/backend/react.xml
npm.cmd --prefix src/web/frontend run build
```

Nếu tái lập dùng basetemp mới và tạo thư mục cha tmp trước; không chạy mutation cùng cổng/server trên cùng mã. Lệnh sáu mutation, cwd/commit/native exit và script chỉ chuyển output nằm trong gói. W-24 có script/lệnh và named JSON/log cho từng phản ví dụ. Không suy kết quả web local hoặc Cloud từ cổng backend xanh.
