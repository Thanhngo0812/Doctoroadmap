# Soát ba nhóm và kế hoạch web tiếp theo — 2026-10-19

**Cập nhật sau bản sửa:** [kiểm lại W-13/W-24](dieu-phoi-kiem-lai-w13-w24-2026-10-19.md) đã nghiệm thu W-13 và đóng các lỗi runtime cũ của W-24.
W-24 chỉ còn phần Figma/đủ trang/prototype và khung auth mới; các kết quả thiếu cache/GIF/guard ở dưới là checkpoint trước bổ sung.

**Phạm vi:** W-13, W-01, W-22/W-24 theo yêu cầu chủ dự án. Đã đọc bàn giao, kiểm mã/test, chạy lại kiểm trọng tâm và trình duyệt.
Không sửa mã sản phẩm, gọi mô hình, gửi thư hoặc chạy lại Cloudinary thật. **Chi phí mô hình: 0 USD.**

**Kết luận:** mở đợt **W-02 cho nhóm web, W-05 cho nhân viên lõi** sau checkpoint ghim W-01. Người thiết kế tiếp tục **W-24**, chưa đóng W-22.
W-13 đạt phần mã lõi được kiểm, còn mở bằng chứng dựng hết cuốn mới. Lượt này soạn việc để chủ dự án giao, chưa gửi lệnh sang phiên nhân viên.

## 1. Trạng thái sau kiểm

| Nhóm / vé | Đã xác minh | Trạng thái điều phối |
|---|---|---|
| Lõi / W-13 | Commit `e9ffce1`; 68 test đạt, gồm integration và kiến trúc; 4/4 phép sửa sai bị bắt | Đã kiểm phần lõi; chưa đóng toàn bộ nghiệm thu vì doc-6 toàn chuỗi chưa hoàn tất |
| Web / W-01 | Nền FastAPI/React/PostgreSQL chạy được, test DB thật đạt; React 23 test và build đạt; trình duyệt đạt 6 tổ hợp sáng/tối × 390/768/1280 | Đạt nền local; đủ căn cứ mở W-02/W-05 sau khi commit đúng phạm vi để ghim đầu vào |
| Thiết kế / W-22/W-24 | Có commit thiết kế và hai bản sửa tiếp; primary tối, khung mobile riêng, preview thích ứng đã cải thiện; 9 test token đạt | Chưa đạt toàn bộ; còn lỗi runtime, guard và bằng chứng Figma |

W-01 hiện có `src/web/` và báo cáo chưa được Git theo dõi trong nhánh đang kiểm. Không coi `HEAD` là snapshot đã chứa W-01.
[Manifest](../artifacts/coord-three-2026-10-19/manifest.json) ghi SHA-256 đầu vào; HEAD lúc ghim là `de7946e`.
Không gom các thay đổi dở của phiên khác vào commit nền.

## 2. Kết quả kiểm độc lập

| Phép kiểm | Kết quả và bằng chứng |
|---|---|
| W-13: use case, pipeline, CLI, log DB, fake, reader, kiến trúc | **68 passed**, 0 fail/error/skip; [XML](../artifacts/coord-three-2026-10-19/w13-tests.xml) |
| W-13: bỏ nhãn, đổi thứ tự nhãn, bỏ kiểm sớm, sai transport | **4/4 bị bắt**; [kết quả](../artifacts/coord-three-2026-10-19/w13-mutations.json) |
| Backend W-01 + token W-24, bắt buộc PostgreSQL test | **71 passed, 1 skipped**; chỉ bỏ qua Cloudinary thật không bật trong lượt soát; [XML](../artifacts/coord-three-2026-10-19/web-and-tokens-tests.xml) |
| React | **23 passed**; TypeScript và Vite build thành công |
| W-01 bỏ guard project Vertex trong tiến trình thử | `test_missing_vertex_project_fails_before_auth_or_model` hỏng đúng assertion, không hỏng collection; [kết quả](../artifacts/coord-three-2026-10-19/w01-vertex-mutation.json) |
| W-01 trình duyệt thật | 6 tổ hợp cỡ/chế độ không tràn; axe không báo lỗi trong phạm vi script; 0 lỗi console ứng dụng; demo, bàn phím, theme, 404 và guard CSS đạt; [audit](../artifacts/coord-three-2026-10-19/w01-browser/browser-audit.json) |
| W-24 preview | Mở 390/768/1280 không tràn ngang; primary tối và các nút trong khung mobile riêng đã sửa; [runtime](../artifacts/coord-three-2026-10-19/design/runtime.json) |

Đã xem ảnh mới, gồm [W-01 desktop](../artifacts/coord-three-2026-10-19/w01-browser/home-1280-light.png),
[W-01 mobile tối](../artifacts/coord-three-2026-10-19/w01-browser/home-390-dark.png) và preview W-24.
Soát theo `code-review-and-quality` và hướng dẫn màn hình ứng dụng của `design-taste-frontend`, ưu tiên spec thương hiệu.

Đợt này không chạy lại toàn bộ 1.956 test hoặc Cloudinary thật mà nhân viên báo ở [bàn giao W-01](w01-nen-web-2026-10-19.md).
Không trộn số tự chạy với số nhân viên báo. Health local trả 200, `db: ok`. Không dừng DB đang chạy của chủ dự án;
nhánh DB lỗi được kiểm bằng backend test và đọc bằng chứng nhân viên.

## 3. Phần còn mở và ảnh hưởng

### W-13: kiểm dừng đúng chưa phải dựng thành công

[Báo cáo W-13](w13-dung-mot-cuon-2026-10-19.md) ghi đúng giới hạn: doc-6 đọc thật rồi thiếu cache `label-roles` tương thích với chunk mới,
dừng `SpendNotAllowed`, không tạo graph. Không dùng cache khác cấu hình hoặc số chi 0 USD này để khẳng định đã dựng xong cuốn mới.
Canonical tái sử dụng cache và đường không đọc vàng có test riêng; chúng không thay cho kiểm hết chuỗi.

**Ảnh hưởng:** không chặn W-05, vì W-05 phụ thuộc nền W-01 và hợp đồng kho Pha B. Chưa mở W-15.
Trước khi đóng hết W-13/W-15, phải có cache đúng cấu hình cho chuỗi hoặc đề nghị chi riêng để chủ dự án duyệt; không tự gọi thêm mô hình.

### W-24: lỗi còn tái hiện

1. **Giảm chuyển động còn hỏng ở desktop sáng/tối.** `screens.html` và `screens_dark.html` khai báo fallback cho `.spinner-gif`,
   nhưng ảnh GIF đang hiển thị không mang lớp đó. Bật thiết lập hệ điều hành trong trình duyệt vẫn thấy nguồn `.gif` và **3 ảnh chụp liên tiếp khác nhau**.
   Trang components và khung mobile riêng chuyển ảnh tĩnh đúng. Nút Workbench đổi ảnh bằng tay chưa thay việc tự theo thiết lập người dùng.
2. **Vùng bấm chưa đạt trên preview mở ở 390.** Trong 24 nút đo trên `screens.html`, 22 nút dưới 44 px ở ít nhất một chiều;
   con số gồm hai nút Workbench, các nút chức năng như Học tiếp cũng chỉ cao 36 px. Khung `mobile_screens.html` riêng có 6 nút được đo đều đạt.
   Không chuyển kết quả hai khung mobile này thành xác nhận cho toàn bộ trang.
3. **Guard bắt primary nhưng chưa bắt mọi token.** Đổi riêng primary CSS sang `#29A9FF` đã làm test đỏ.
   Đổi JSON `space-4` từ 16 thành 18 px, hoặc đổi riêng RGBA `color-brand-tint` tối trong CSS thành đỏ, **9 test vẫn xanh**.
   Script hiện chỉ so màu, còn bỏ qua màu tối không ở dạng hex; chưa có export Variables từ Figma có nguồn gốc.
   [Ba phép thử](../artifacts/coord-three-2026-10-19/token-probes.json) chỉ thay dữ liệu trong tiến trình, không sửa token gốc.
4. **Chat prototype chèn nội dung nhập vào `innerHTML`.** Nhập một thẻ `strong` có ID thử nghiệm tạo được node HTML thật trong câu trả lời mẫu.
   Đây là lỗi preview, không phải kết luận React/API W-01 bị lỗi tương tự. Sửa cách đưa văn bản trước khi dùng làm mẫu tích hợp.

[Runtime và hash ảnh](../artifacts/coord-three-2026-10-19/design/runtime.json) ghi các kết quả trên.
9 test xanh hiện tại không bao phủ những nhánh runtime còn hỏng.

### W-22/W-24: bằng chứng trang và Figma chưa đủ

[Bảng nhân viên](w24-bo-sung-w22-2026-10-19.md) đánh dấu 14 nhóm trang đều có, nhưng nhiều hàng chỉ dẫn tới thành phần hoặc nút mẫu:
ô nhập không thay đủ trang đăng nhập/đăng ký/khôi phục; nút Tạo tài liệu không thay các trạng thái trang tài liệu;
vòng 35% không thay trang mức dùng; quy tắc cuộn ngang không thay bảng quản trị.
Gói HTML vẫn là 5 khung chính và 2 khung mobile, chưa phải ảnh xuất từng trang/trạng thái theo spec mục 11.

Plugin cục bộ tạo ba nhóm frame (nền tảng, thành phần mẫu, một trang lộ trình desktop);
chưa thấy lệnh tạo Variables, component variants hay liên kết prototype trong mã plugin.
Có script sinh hình không chứng minh đã chạy hoặc đã hoàn tất file Figma.

Trình duyệt ẩn danh của lượt soát nhận **403 từ CloudFront** khi mở Figma; không suy ra file rỗng, quyền chủ dự án sai hay không tồn tại.
Người thiết kế cần giao node/ảnh xuất thật, JSON Variables, bốn link prototype và video thao tác.
HTML hiện có xử lý theme, nút giảm chuyển động, accordion, chọn/nộp quiz và chat mẫu;
chưa có luồng đăng ký, chia sẻ/tham gia hoặc tải/xác nhận/dựng đầy đủ.

**Ảnh hưởng:** tiếp tục W-24, chưa mở W-23. React dùng spec và phần thiết kế đã kiểm làm đầu vào tạm, không chờ toàn bộ Figma để làm W-02.

## 4. Việc tiếp theo của từng nhóm

| Nhóm | Việc ngay | Đầu ra để soát |
|---|---|---|
| Web | Ghim commit W-01 đúng phạm vi, rồi [W-02](../task/web/W-02-dang-ky-dang-nhap-phien.md) | Hash nền; báo cáo W-02; migration account/session/rate limit/audit; JSON 4 API; test service/HTTP/PG; ảnh 390/1280, kiểm 768 và video |
| Lõi | [W-05](../task/web/W-05-kho-pha-b-postgresql.md); giữ phần toàn chuỗi W-13 còn mở | Báo cáo W-05; hợp đồng ba store; hai tiến trình sinh đúng một lần; negative cache chung; lọc usage/ẩn danh; EXPLAIN; kiểm giữ chỗ chi và tiến độ |
| Thiết kế | Tiếp tục [W-24](../task/web/W-24-bo-sung-va-sua-ban-giao-w22.md), ưu tiên màn tài khoản cho W-02 | Sửa runtime/guard; bảng đủ/thiếu trung thực; Figma có node, Variables export, ảnh từng trang, prototype và video |

**Lời giao nhóm web:** “Chốt snapshot W-01, không gom thay đổi phiên khác. Làm W-02: đăng ký/đăng nhập/đăng xuất/me,
Argon2id, phiên cookie phía máy chủ, CSRF/Origin và giới hạn thử. Test với PostgreSQL thật và đồng hồ giả, 0 USD mô hình.
Đây là tài khoản thật; không mở rộng trang minh hoạ để giả thay API/DB. Chưa gửi thư thật; xác minh/quên mật khẩu thuộc W-03.”

**Lời giao nhân viên lõi:** “Nhận W-05 sau snapshot W-01. Giữ các bất biến đã vá ở SA-47/SA-48 khi chuyển store sang PostgreSQL,
gồm `atomic()` giữa các tiến trình và ngữ cảnh lồng. Đếm lời gọi bằng đồ giả; không mở tập giữ lại, không nhập `live.json`.
Không dành cả nhóm chờ lượt có tiền W-13; ghi rõ phần thiếu cache đó vẫn mở.”

**Lời giao người thiết kế:** “Tiếp tục W-24, không báo đã đủ từ tên thành phần. Sửa mục 3, ưu tiên đăng nhập/đăng ký và lỗi/giới hạn cho W-02;
bàn giao node/ảnh/tương tác dùng được. Sau đó hoàn thiện checklist W-22, Variables export và bốn prototype thật.
Được dùng taste-skill đã nạp; spec và Artboard 9–28 vẫn là căn cứ.”

## 5. Phối hợp DB và điểm kiểm

Nhóm web giữ cấu trúc/DB nền W-01 và bảng tài khoản W-02; nhân viên lõi làm adapter kho Pha B PostgreSQL W-05.
Schema đã có ở [spec CSDL](../doc/web-co-so-du-lieu-spec.md); thêm bảng theo vé, không thiết kế lại toàn DB.

Domain, service, test và UI làm song song; migration theo một tuyến:

1. Ghim W-01, mốc `w01_0001`.
2. Lõi bàn giao migration W-05 trước, dự kiến `w05_0002` → `w01_0001`.
3. Web chốt migration W-02 sau, dự kiến `w02_0003` → `w05_0002`. HEAD là W-02, vẫn đúng một head.
   Đây là quy ước điều phối đợt này; không sửa migration đã ghép. Nếu phiên khác đã có migration, đối chiếu trước khi tích hợp.
4. Test nền hiện yêu cầu **HEAD chỉ có `alembic_version`**, nên sẽ lỗi khi thêm bảng. Giữ invariant bằng test ở revision `w01_0001` trên DB rỗng;
   thêm kiểm nâng HEAD đủ bảng mới. Không xoá test hoặc nới thành “có ít nhất một bảng” để xanh.
5. Sau ghép: `alembic heads` đúng một head, DB rỗng nâng HEAD thành công, test W-01/W-02/W-05 và regression SA-47/48 đạt;
   lệnh kiểm bắt buộc vẫn hỏng khi thiếu PostgreSQL.

## 6. Các mốc sau đợt này

- **Sau W-02:** W-03 (xác minh/quên mật khẩu), W-04 (hồ sơ/đổi mật khẩu) có thể chia người làm; phối hợp migration.
- **Sau cả W-02 và W-05:** W-06 nối `LearningGateway`, khoá mẫu dev và Khoá học của tôi. Đây là mốc bắt đầu học bằng dữ liệu/use case thật.
- **Sau W-06:** W-07 lộ trình, W-11 chia sẻ; W-14 tải sách/hàng đợi dùng bộ dựng giả khi W-03 cũng đạt.
  Dùng bản vá Pha B 46–50 hiện có; không coi trạng thái trước vá ở SA-34/40/42 là blocker mới chưa xử lý.
- **Sau W-07:** W-08 bài giảng, W-09 trợ lý, W-10 quiz/tài liệu; W-23 đối chiếu cuối khi các vé này và W-22 đạt.
- **W-15 dựng thật:** chờ W-14, bằng chứng còn thiếu của W-13 và phê duyệt chi riêng. Tiếp tục Vertex đến khi chủ dự án yêu cầu đổi lúc chuẩn bị demo.

Đợt W-02/W-05/W-24 không cần duyệt tiền mô hình. Các phần chưa nghiệm thu được giữ mở, không tự hạ tiêu chí để chuyển vé.
