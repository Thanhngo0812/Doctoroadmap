# W-12 — bản vá WEB-R10-01, 2026-10-28

Đây là bàn giao sửa Required, **chờ điều phối soát/nghiệm thu**, không tự đóng W-12 hoặc ghép main. Giữ nguyên bàn giao `af2993a5` và bằng chứng ngày 27/10 làm lịch sử. W-04 đã được nhận, không triển khai lại. W-17.1 React chưa mở: chỉ bắt đầu sau W-12 được nghiệm thu và main nhận backend bảo vệ admin đầu tiên.

## Mã và phạm vi

- Nhánh `work/w12-invitations-react`, worktree `tmp/w12-invitations-react`.
- Nhận main `26d43b83ba0d3f265f28ea7d3220f924ba96a97d` qua merge `067ced637caac7e9ec35ac9498efe1b1e94ff64a`, không rebase/đổi nhánh thư mục chung.
- Bản vá `4019e752ec8256eb1aad680c7ae8f85530763c3c`; sửa tuỳ chọn query trong test ở `a594a4699008665ab8e2aa572cb6f7c90944137a`. Mốc nguồn kiểm cuối là `a594a469` trừ khi phần kết quả cuối bên dưới ghi mốc nhận main mới hơn.
- Product chỉ đổi hai điều kiện trong `EmailInvitations`: nút gửi disabled khi `loading`, và submit từ chối khi `loading`. Cho nhập/giữ draft trong lúc tải; sau tải thành công hoặc thất bại đều hết loading, gửi/thử lại bình thường. Tải lại và mutation vì thế không thể ghi đè lẫn nhau; không thêm thư viện, cache, request hay endpoint.
- Test bổ sung sáu ca: snapshot rỗng/có dữ liệu; POST lỗi → GET tải lại lỗi → gửi lại; GET cũ sau đổi khoá; GET cũ sau unmount; GET cũ sau kết thúc phiên. Giữ 13 ca lời mời cũ, guard fragment và các hồi quy W-04/W-08/W-09/W-10.
- Harness browser bổ sung bốn ca giữ **response GET HTTP thật** bằng `route.fetch`: rỗng/có dữ liệu × chuyển động thường/giảm chuyển động. Không chế DTO cho phản chứng. Kiểm chuột bấm nút disabled không có POST/SQL; giao GET, gửi được, thấy email/nút huỷ đúng POST và SQL; tải lại vẫn giữ dữ liệu.
- Không sửa backend/core/migration. Giữ 50 email đầu vào, gộp trùng, 200 thư/chủ/ngày, TTL 7 ngày, xác minh đúng email và chấp nhận bằng ID công khai. Không gọi SMTP/Gemini/Cloudinary, chi phí 0 USD.

## Bảo toàn Auth và thương hiệu

Merge tự động không xung đột. Phần AuthProvider/epoch/profile/logout-all của main W-04 giữ nguyên; diff Auth với main chỉ là fragment/context/AuthPage W-12. `Account.tsx`/test hồ sơ giữ nguyên main. Có receipt độc lập trong `r10-auth-preservation.json`.

Áp dụng `design-taste-frontend` (quy tắc app screens), `debugging-and-error-recovery`, TDD, Git và tự soát `code-review-and-quality`. Tái dùng hướng/mẫu/token đã duyệt của W-12 thay vì thiết kế lại trong bản vá nhỏ: Be Vietnam Pro, Artboard 24/28, mặt phẳng và phân cấp bằng chữ/đường chia, màu chính cho thao tác, trạng thái tải nói thật. Không chép preview chưa nhận. Giữ vùng bấm 44 px, focus bàn phím, motion/token và reduced-motion thật qua browser. Ảnh mới được xem trực tiếp, không chỉ dựa Axe.

Tham chiếu taste lịch sử: `editorial-greeting`, seed `641862912` trong `taste-direction.json` của bàn giao trước (đã ghi rõ lần draw đó dùng để soát sau triển khai); không tuyên bố draw mới hoặc đổi hướng trong bản vá. Câu hỏi của hộp mời vẫn là “đã mời ai, còn lời mời nào có thể huỷ?”; dấu hiệu WayFinder là logo/font và nhóm dữ liệu chia sẻ theo khoá. Email/trạng thái/hạn đến từ HTTP/PostgreSQL thật với tài khoản tổng hợp/đồng hồ giả, không số liệu sản phẩm bịa để lấp chỗ trống.

## RED → GREEN và mutation

`r10-old-red-final.xml`: đặt lại **nguyên component Invitations.tsx lấy từ git af2993a5** trong worktree đã nhận main (Auth W-04 vẫn hiện hành), chạy test mới với snapshot hợp lệ: **3 assertion fail / 13 control pass, 0 setup error**, native 1. Đây là kiểm hành vi component của af2993a5 trên nền ghép, không tuyên bố checkout toàn repo về af2993a5. `r10-old-red-final-restoration.json` ghi SHA bản cũ/bản sửa và khôi phục byte chính xác. `r10-read-write-green2.xml`: 16 pass; sau bổ sung ba ca cleanup, `r10-read-write-green4.xml`: **19 pass**, native 0.

Phép phá trên `4019e752`: bỏ disabled/loading nút → 3 assertion fail/16 pass; bỏ guard loading trong submit (nút vẫn disabled) → 2 assertion fail/17 pass, 0 setup error, native 1. Khôi phục cùng SHA `beb177d2c591b7b2e8471589b528e07dc55398770e667bd2459215f977a4d9e5` trước kiểm bình thường. Receipt mới theo commit cuối được liệt kê ở phần kết quả cuối; không gán receipt cũ sang HEAD mới. Mutation chạy tuần tự, không cùng server/full gate.

Lặp tuần tự trên nguồn cuối `a594a469` sau browser, phục hồi xong mới khởi động cổng toàn repo:

| Lượt | JUnit | Native | Kết quả độc lập |
|---|---|---|---|
| Component cũ nguyên từ af2993a5 | `r10-old-a594a469-red.xml` | 1 | 3 assertion fail, 16 control pass, 0 setup error |
| Bỏ disabled/loading của nút | `r10-button-a594a469-red.xml` | 1 | 3 assertion fail, 16 control pass, 0 setup error |
| Bỏ guard loading của submit | `r10-handler-a594a469-red.xml` | 1 | 2 assertion fail, 17 control pass, 0 setup error; submit form trực tiếp phát POST dù nút disabled |

Mỗi lượt có `*-restoration.json`, SHA trước/sau khớp và `restored=true`. Test không chỉ đọc cờ nội bộ: kiểm POST count bằng 0 khi GET chờ; khi giao GET thì gửi đúng một POST, email/nút huỷ render đúng và không còn loading/empty giả. Browser đối chiếu thêm hàng pending trên connection SQL độc lập trước/sau mutation và sau reload.

Giữ các lượt chưa đạt đúng tên lịch sử:

- `r10-read-write-red`: 3 assertion đỏ trên component cũ, nhưng fixture parameterized lúc đó bị trải mảng; không dùng làm RED chuẩn.
- `r10-read-write-green`: fixture mảng sai gây 2 fail/1 unhandled error; đã sửa parameterized thành object, không giảm assertion/timeout.
- `r10-read-write-green3`: control đổi khoá chưa mở lại tab email (ShareDialog chủ động về tab link), 1 fail/18 pass; đã thao tác tab đúng như người dùng, không sửa sản phẩm cho test.
- `r10-gate-build-final`: TypeScript từ chối `exact` trong `getByRole`; bỏ đúng option không được hỗ trợ, tên string vốn đã exact. `r10-gate-build-final2` đạt, native 0.
- `r10-gate-react-final` khởi chạy ở `4019e752`; không thay cổng React cuối trên nguồn sau sửa kiểu.
- Helper xác minh fixture lần đầu đọc tệp có BOM bằng `utf8` nên `compile` từ chối U+FEFF; đổi riêng cách đọc sang `utf-8-sig`, rồi kiểm đủ 3.145 tệp và PDF train phụ thuộc gate, không ghi đè dữ liệu khác hash.
- Khi đóng gói phát hiện wrapper chỉ bảo vệ báo cáo lịch sử cho label bắt đầu `gate-python`; label `r10-gate-python-final` không vào nhánh đó. Không dùng cờ `historicalEvidenceRestored=true` tự ghi của wrapper để chứng minh phục hồi. Đã giữ tám JSON mới tại `r10-gate-python-final/legacy-test-output/`, rồi dùng helper `w12-r10-restore-history.py` phục hồi **chỉ tám tệp báo cáo W-06/W-14 do chính lượt test này sửa** từ HEAD. `r10-legacy-report-restoration.json` lưu SHA bản mới/bản phục hồi/blob Git và xác nhận nội dung HEAD sau chuẩn hoá xuống dòng; `git diff` tám tệp rỗng. Không sửa helper capture/mã chạy sau cổng; không xoá thư mục hay làm mất bằng chứng test mới.

## Kết quả cuối

Mốc nguồn `a594a4699008665ab8e2aa572cb6f7c90944137a`, main nền `26d43b83ba0d3f265f28ea7d3220f924ba96a97d`. Cửa PG riêng do chủ dự án xác nhận “Cửa trống; web chạy khi chốt mã”. Dữ liệu kiểm là bản sao thường 3.145 tệp theo hai manifest W-06, xác minh lại SHA nguồn/đích (`r10-fixture-copy.json`); không dùng cache live hay liên kết. Test PG dùng DB UUID riêng, Mailer/model/media giả. Basetemp dưới `tmp/`, không trộn fixture với ảnh browser.

Browser `r10-gate-browser-final/exit.json`: **native 0**, nguồn `a594a469`, `dirtySourcePaths=[]`. **12 cấu hình, 49 PNG, 49 lượt Axe document, 0 violation; 256 HTTP JSON; 15 ảnh chụp SQL qua connection độc lập; 4 ca giữ GET thật; 5 video**. Có CDP chứng minh font Be Vietnam Pro thực sự dùng/custom; mọi ảnh decode được; không tràn ngang hoặc vùng bấm dưới 44 px. Không pageerror hoặc rò token. DB UUID đã gỡ, server thread đã dừng. Ảnh/video/JSON trong `report/w12-react-evidence/browser-r10-final/`.

Quan sát trực tiếp ảnh 390 sáng/tối, 768 sáng và 1280 sáng/tối, cùng trạng thái tải: nội dung/hành động rõ; email/hạn/nút huỷ nằm trong khung; focus tab hiện đúng và không mất controls; khi gửi bị chặn, draft vẫn đọc/sửa được và dòng “Đang tải lời mời…” giải thích trạng thái. Inspector taste có 0 FAIL, 1 WARN về khoảng trống 31% ở trang Khoá học của tôi khi tài khoản chỉ có một khoá và trạng thái chưa có khoá sở hữu; giữ empty state đã nhận, không bịa thêm thẻ cho đầy màn hoặc sửa bố cục ngoài phạm vi Required.

Console giữ lỗi HTTP chủ ý 401/403/409/429 và cảnh báo CSP khi Axe chèn style/kết nối kiểm font; không hạ CSP. Runtime Windows có `WinError 10054` lúc đóng kết nối và “Cancel 0 running task(s), timeout graceful shutdown exceeded”; giữ raw log, không gọi đây là lượt console/runtime tuyệt đối sạch. Đây không phải assertion lỗi của browser; kiểm native 0 và DB/thread cleanup độc lập ở runtime.json.

Ảnh xem nhanh: [hộp mời 1280 sáng](w12-react-evidence/browser-r10-final/email-pending-1280-light.png), [đang tải — khoá gửi](w12-react-evidence/browser-r10-final/serialized-get-race_empty-loading-1280-light.png), [gửi sau tải — email/nút huỷ](w12-react-evidence/browser-r10-final/serialized-get-race_empty-created-1280-light.png), [390 tối](w12-react-evidence/browser-r10-final/email-pending-390-dark.png). Video `owner.webm` gồm thao tác giữ GET/gửi/tải lại và các trạng thái chủ khoá.

Cổng React cuối sau phục hồi mutation `r10-gate-react-final2.xml`: **259 pass / 20 file**, 0 fail/error, native 0, 208,80 giây; nguồn đúng `a594a469`. Build `r10-gate-build-final2/exit.json`: native 0, cùng nguồn. Python/PostgreSQL toàn repo `r10-gate-python-final.xml`: **3.527 pass, 3 skip, 1 xfail, 8 warning**, 0 fail/error, native 0; pytest 927,84 giây, toàn wrapper 943,09 giây. Không hạ assertion/timeout hoặc thêm skip; warning là Swig/Starlette/Docling đã có, skip/xfail giữ chi tiết trong XML. Đã trả cửa PG sau khi lượt đầy đủ kết thúc.

Main vẫn là `26d43b83` khi cổng kết thúc. `r10-manifest.json` ghi SHA-256 raw source/evidence; `r10-source-snapshot.zip` giữ byte source thực dùng (không lẫn SHA checkout CRLF với blob Git LF). `r10-auth-preservation.json`, `r10-mutation-summary.json`, `r10-gate-summary.json`, `r10-http-examples.json` và `r10-sql-copy-receipts.json` là mục vào nhanh. Commit hồ sơ cuối không đổi `src/` hoặc `scripts/` so với nguồn kiểm `a594a469`; SHA commit bàn giao được báo trực tiếp cho chủ dự án.

Các lệnh chạy từ gốc worktree, qua capture để lưu command/native/source SHA (thêm đúng fresh label ở đầu wrapper):

```powershell
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe scripts/w12_react_capture.py r10-gate-python-final C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe scripts/w05_run_tests.py -o addopts= -q --basetemp=tmp/cong-w12-r10-final --junitxml=report/w12-react-evidence/r10-gate-python-final.xml
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe scripts/w12_react_capture.py r10-gate-react-final2 npm.cmd --prefix src/web/frontend test -- --pool=threads --maxWorkers=1 --reporter=default --reporter=junit --outputFile=../../../report/w12-react-evidence/r10-gate-react-final2.xml
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe scripts/w12_react_capture.py r10-gate-build-final2 npm.cmd --prefix src/web/frontend run build
$env:W12_REACT_RUN='browser-r10-final'
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe scripts/w12_react_capture.py r10-gate-browser-final C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe -X utf8 scripts/w12_react_runtime.py
```

Mutation: `C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe report/w12-react-evidence/helpers/w12-r10-mutate.py old` (hoặc `button`, `handler`), từng lượt tuần tự và không chạy khi server/cổng toàn repo đang dùng mã. Helper outer native 0 nghĩa là xác nhận native **1** của Vitest và phục hồi thành công; đọc XML/`exit.json` bên trong để biết assertion fail thực tế. Không chạy lại với cùng label; mọi bằng chứng lịch sử được giữ.
