# W-11 — bản vá giữ link mời khi đổi form — 2026-10-23

## Mốc và phạm vi

- Tiếp nhánh `work/w11-share-links`, worktree `tmp/w11-share-links`, giữ mốc soát `85397092ed10bffe2db3bda96d2db6a6d2759c48` và [bằng chứng ngày 22](w11-chia-se-link-thanh-vien-2026-10-22.md).
- Nhận main `3f22c524d709e42208e688c426ee6738ad9f5d65` tại `9361191`; commit bản vá **`0a72f31`**, rồi nhận main **`865974ae14e03bdc5e37283aa496972f8c3c622d`** tại **`2c5166bfcf30ee8cd1a784f8da6891278b260522`**. Chủ dự án đã chốt `865974a` làm main nền cho đợt vá này.
- Trước khi câu trả lời chốt nền đến, đã nhận thêm main `1d193735a9ba1bde3c7316d5372fcd0be0e0f12a` tại **`33f9c2521ba0379d89c3fe942ea754f9f06b49a6`** và khởi động lượt kiểm bổ sung. Chênh lệch chỉ là `task/sau-a10/00-ke-hoach.md` nhận từ main; **639 hash mã/test/script không đổi** so với `2c5166b`. Không nhận thêm main sau quyết định chốt. [Ghi nhận nền và đối chiếu](w11-evidence/auth-return-2026-10-23/baseline-approval.json).
- Chỉ lấy riêng tệp test từ `3f3e923`, không merge nhánh review. [Nguồn nhập và thay đổi tương thích kiểu](w11-evidence/auth-return-2026-10-23/repro-import.json). Không sửa vé/kế hoạch/handoff hoặc tự ghép main.

## Required đã sửa

`AuthPage` đã sanitize `next` nhưng `switchTarget` chỉ chứa `/dang-nhap` hoặc `/dang-ky`. Vì cả header, footer và `navigate` trong view transition dùng biến này, đổi form làm mất đích rồi xác thực về `/khoa-hoc`.

Bản vá tạo `switchPath`, rồi gắn query từ **`next` đã sanitize**, không lấy nguyên `requestedNext`. Cả hai link và nhánh transition tiếp tục dùng chung `switchTarget`. Khi không có `next`, giữ hành vi mặc định. Không đổi bộ lọc chặn URL ngoài, dấu gạch chéo kép, backslash hoặc khoảng trắng.

Màn auth dùng lại SVG đổi theme từ `CourseShell` trên main. Axe trước đó trả incomplete `color-contrast/nonBmp` cho ký tự biểu tượng, kể cả khi đặt trong span aria-hidden; đây là yêu cầu xem thủ công, không phải kết luận màu sai. SVG giữ tên nút và dùng màu hiện hành, không thay CSS/palette/font/motion. Các sửa sản phẩm nằm trong `Auth.tsx`; backend W-11 đã soát không được viết lại.

## RED → GREEN và guard

| Phép kiểm | Bằng chứng |
|---|---|
| Test điều phối, trước sửa | [RED JUnit](w11-evidence/auth-return-2026-10-23/auth-return-red.xml), [log](w11-evidence/auth-return-2026-10-23/auth-return-red.log): 8 ca đổi form đỏ, 2 control trực tiếp xanh, native 1. |
| Sau sửa | [GREEN JUnit](w11-evidence/auth-return-2026-10-23/auth-return-green.xml): 22 đạt, native 0; gồm 8 ca hai chiều × header/footer × transition, 2 control và 12 ca `next` nguy hiểm. |
| Chặn open redirect | [Mutation trên mã cuối](w11-evidence/auth-return-2026-10-23/unsafe-next-final-mutation.json): bỏ bộ lọc `next` làm cả 12 ca nguy hiểm đỏ, native 1, không setup error; phục hồi nguồn đúng byte/SHA. Mười ca còn lại không được chọn trong lượt mutation, không thêm skip vào test. |
| Guard backend giữ nguyên | [8/8 mutation bị bắt](w11-evidence/auth-return-2026-10-23/mutations/results.json): token, revoke, expiry, giới hạn/lượt, transaction, mất quyền ngay và giữ dữ liệu riêng. Từng bản sai native 1, không setup error; wrapper native 0. Nguồn phục hồi trước khi chạy server/cổng. |
| Browser/Axe auth | Lượt `browser-dev` và `browser-dev2` ghi nhận incomplete của ký tự đổi theme; `browser-dev3` đạt sau khi dùng SVG. Không tắt rule, bỏ assertion hoặc hạ ngưỡng. |

Tệp test được nhập có bốn option `getByRole(..., exact: true)` không thuộc kiểu Testing Library đang dùng; TypeScript đã bắt ở [build đỏ](w11-evidence/auth-return-2026-10-23/build-dev.log). Đã bỏ riêng option không hỗ trợ; tên truy vấn dạng chuỗi vẫn khớp chính xác, các assertion gốc giữ nguyên. Các truy vấn label giữ `exact` đúng API.

## Cổng cuối

| Cổng | Trên `2c5166b`, main nền `865974a` | Lượt bổ sung trên `33f9c25`, cùng 639 hash nguồn | Native exit |
|---|---|---|---|
| Python/PostgreSQL toàn repo | [JUnit](w11-evidence/auth-return-2026-10-23/final-python.xml): 2.292 đạt, 1 bỏ qua | [JUnit](w11-evidence/auth-return-2026-10-23/latest-python.xml): 2.292 đạt, 1 bỏ qua | 0 cả hai lượt |
| React | [JUnit](w11-evidence/auth-return-2026-10-23/final-react.xml): 143 đạt | [JUnit](w11-evidence/auth-return-2026-10-23/latest-react.xml): 143 đạt | 0 cả hai lượt |
| Build | [Log](w11-evidence/auth-return-2026-10-23/final-build.log): đạt | [Log](w11-evidence/auth-return-2026-10-23/latest-build.log): đạt | 0 cả hai lượt |
| Browser HTTP/PostgreSQL | Lượt dự kiến dừng trước khi mở server vì main đổi; không tính là bằng chứng browser | [Lượt cuối](w11-evidence/auth-return-2026-10-23/final-browser-command.json): 8 ca auth-return và các luồng W-11 đạt | 0 |

[Kết quả, lệnh, mốc và native exit đầy đủ](w11-evidence/auth-return-2026-10-23/gate-results.json). Một test Python bỏ qua là Cloudinary live chưa bật, đúng yêu cầu 0 USD; không thêm skip. Có 8 cảnh báo thư viện trong mỗi lượt, không có failure/error. `final-*` là lượt ở nền được chốt; `latest-*` là lượt bổ sung đã khởi động trước câu trả lời chốt nền. Lệnh dưới đây là lượt bổ sung; cả hai bộ command JSON được lưu riêng.

Lệnh từ gốc worktree, không chạy pytest trần:

```powershell
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe scripts/w05_run_tests.py -o addopts= -q --basetemp=tmp/w11-auth-return-final-20261023-2 --junitxml=report/w11-evidence/auth-return-2026-10-23/latest-python.xml
npm.cmd --prefix src/web/frontend test -- --pool=threads --maxWorkers=1 --reporter=junit --outputFile=../../../report/w11-evidence/auth-return-2026-10-23/latest-react.xml
npm.cmd --prefix src/web/frontend run build
$env:W11_EVIDENCE_RUN='browser-final'
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe -X utf8 scripts/w11_web_runtime.py
```

Migration vẫn một head **`w11_0007 → w14_0006`**. Các kiểm PostgreSQL giữ: link một lượt đua hai người; rollback membership/lượt nếu audit lỗi; hai link tranh chỗ cuối tại trần 200; revoke không xoá thành viên; remove/leave mất quyền ở request kế tiếp; tham gia lại giữ chính xác progress/session riêng. Guard tự liệt kê route và hai DTO W-14 `upload_id`/`confirmed_at` được giữ. [Ánh xạ bất biến tới assertion có tên trong JUnit cuối](w11-evidence/auth-return-2026-10-23/invariant-map.json).

## Browser thật và thiết kế

- PostgreSQL UUID riêng, Auth/CSRF/SharingService/LearningGateway/PostgresPhaseBStore thật; FakeMailer, media không dùng; chặn model/ADC/SMTP/Cloudinary. Không mock HTTP để giả thành công. Kiểm lại SHA-256 của 3.144 tệp fixture theo hai manifest; không nối link thư mục, không dùng kho CLI learner/live/heldout.
- Tám lượt browser: từ login/register, qua header/footer, với media setting `reduce`/`no-preference`. Mỗi lượt vào link mời, đổi form, xác thực, trở về **đúng cùng token**, bấm tham gia và GET khoá thành công. Mỗi lượt dùng tài khoản test riêng rồi rời khoá.
- Nhánh thường gọi `document.startViewTransition` native đúng một lần khi đổi form; nhánh giảm chuyển động không gọi. Wrapper chỉ đếm rồi chuyển tiếp API native, không thay bằng transition giả. Browser media setting và số lần gọi được ghi trong `audit.authReturns`.
- Kết nối SQL độc lập kiểm link của tám lượt có `use_count = 8`, tám ID người học riêng; cuối cùng còn một owner, link kiểm chính chỉ dùng một lượt, dữ liệu Pha B còn nguyên và đủ audit. Giữ cả luồng one-time URL, list tail, revoke/remove/leave của đợt trước.
- Ma trận 8 màn × 390/768/1280 × sáng/tối: **48 ảnh**. Axe từng màn sáng/tối tại 1280: **16 lượt**, không gọi cả 48 ảnh là đã Axe. Có video owner/learner/auth-return, kiểm vùng bấm 44×44, không tràn ngang, focus/keyboard và giảm chuyển động.
- Tiếp tục áp dụng `design-taste-frontend` app-screen cùng direction W-11, logo Artboard/font/token đã nhận trên main; không dùng preview W-24 mới làm chuẩn. Bản vá giữ bố cục auth hiện hành, SVG lấy từ khung khoá học để thống nhất giao diện.

- [Audit browser cuối](w11-evidence/auth-return-2026-10-23/browser-final/audit.json): 113 trao đổi HTTP đã che token, 8 ca auth-return đạt, 48 ảnh và 16 lượt Axe không violation/incomplete; không lỗi console ngoài dự kiến, page error hoặc failed request.
- [Runtime/SQL độc lập](w11-evidence/auth-return-2026-10-23/browser-final/runtime.json), [lệnh và commit browser](w11-evidence/auth-return-2026-10-23/final-browser-command.json), [xác nhận DB đã gỡ và cổng service đã dừng](w11-evidence/auth-return-2026-10-23/cleanup-check.json).
- Ảnh auth: [390 tối](w11-evidence/auth-return-2026-10-23/browser-final/auth-register-390-dark.png), [390 sáng](w11-evidence/auth-return-2026-10-23/browser-final/auth-register-390-light.png), [768 tối](w11-evidence/auth-return-2026-10-23/browser-final/auth-login-768-dark.png), [768 sáng](w11-evidence/auth-return-2026-10-23/browser-final/auth-login-768-light.png), [1280 sáng](w11-evidence/auth-return-2026-10-23/browser-final/auth-login-1280-light.png), [1280 tối](w11-evidence/auth-return-2026-10-23/browser-final/auth-login-1280-dark.png). Các màn mời/chia sẻ/thành viên có đủ ma trận trong cùng thư mục.
- Video [đổi form → xác thực → đúng link mời → tham gia](w11-evidence/auth-return-2026-10-23/browser-final/auth-return.webm), [owner](w11-evidence/auth-return-2026-10-23/browser-final/owner.webm), [learner](w11-evidence/auth-return-2026-10-23/browser-final/learner.webm). Đã xem trực tiếp ảnh auth 390 tối và 1280 sáng của lượt cuối.

Token mời và auth/cookie/CSRF không xuất trong bằng chứng. Token test bị mutation cố ý làm lộ được che trong chẩn đoán, giữ trạng thái JUnit/native exit. Basetemp ở `tmp/`; ảnh browser tách khỏi export SQL/JSON hồi quy. UUID DB và service harness được dừng sau kiểm. Chi phí nhà cung cấp **0 USD**.

## Bàn giao

[README mở PostgreSQL/backend/frontend](../src/web/README.md) đã cập nhật mốc bản vá. Commit bằng chứng sau mốc mã chỉ thêm báo cáo/evidence, không thay runtime/test/harness; manifest SHA-256 đối chiếu nguồn và blob bàn giao. Các worktree/snapshot/ZIP được giữ nguyên; không đụng `tmp/t01a-clean-ff797eb`.

**Chờ điều phối soát/ghép W-11 rồi mới làm W-08** trong worktree mới từ main đã ghép. Ghi nhận W-08 đủ SA-53, stream sau cổng, không hiện bản lùi, fatal có lối ra và media/source kiểm quyền. Khi được giao W-09 sẽ dùng hợp đồng SA-56/57/58, chuyển `cache_only` xuống `LectureUseCase.make`, enum search lõi và fixture mới 0 USD. Giữ Vertex; không sửa SA-61 trong bản vá này.
