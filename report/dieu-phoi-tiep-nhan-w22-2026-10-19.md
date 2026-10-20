# Tiếp nhận W-22 — 2026-10-19

**Trạng thái:** đã kiểm bộ bàn giao tại máy; **chưa đủ nghiệm thu W-22**. Đã soạn vé sửa
[W-24](../task/web/W-24-bo-sung-va-sua-ban-giao-w22.md) để chủ dự án giao người làm W-22. Chưa gửi sang phiên khác.

**Căn cứ:** [vé W-22](../task/web/W-22-ban-figma.md), [spec thiết kế](../doc/web-thiet-ke-giao-dien-spec.md),
[báo cáo nhân viên](w22-ban-figma-2026-10-19.md). Không đổi yêu cầu hay quyết định của chủ dự án.

**Phạm vi:** đọc token, ba bản HTML, script/test và báo cáo; chạy lại test, kiểm bằng Chrome ở 1280/768/390 px, thử chế độ tối và giảm chuyển động.
Không sửa mã sản phẩm hoặc tài sản thiết kế. Chi phí mô hình: **0 USD**. Bộ đầu vào chưa commit riêng cho W-22 tại lúc soát;
[manifest](../artifacts/coord-w22-2026-10-19/manifest.json) ghi HEAD và SHA-256 từng tệp để phân biệt với thay đổi của phiên khác.

## 1. Phần đã xác minh

| Hạng mục | Kết quả | Giới hạn |
|---|---|---|
| Unit test của nhân viên | **20/20 đạt**, không bỏ qua; [XML](../artifacts/coord-w22-2026-10-19/baseline-tests.xml) | Chưa phải kiểm thử toàn bộ giao diện hay Figma |
| Script tương phản | **17/17 cặp đạt**; xanh thương hiệu trên trắng đạt khoảng **2,56:1**, đúng là không dùng cho chữ thường trên trắng | Các cặp trong `PAIRS` là mã màu viết sẵn, không đọc giá trị token đang bàn giao |
| JSON so với CSS | **56 giá trị được đối chiếu khớp**: màu sáng/tối, khoảng cách, bo góc, bóng và chuyển động có trong ánh xạ đã kiểm | Chưa chứng minh toàn bộ thang chữ, định dạng chuẩn hoặc đồng bộ với Figma Variables; [kết quả](../artifacts/coord-w22-2026-10-19/token-audit.json) |
| Bản sáng | Đã có hướng thị giác WayFinder: Be Vietnam Pro, thẻ, điểm ảnh xanh, khối bài giảng và các màn chính | Chưa đủ trang, trạng thái và tương tác để xác nhận hoàn thiện theo mục 3a |

Đã dùng skill `design-taste-frontend` ở chế độ màn hình ứng dụng để kiểm và xem ảnh. Script kiểm trả mã 1 vì có các cảnh báo/lỗi.
Đã đọc kết quả trong bối cảnh đây là trang tập hợp mockup: không lấy cảnh báo nhiều tiêu đề, khung điện thoại, khoảng trống canvas,
dấu tích/biểu tượng hoặc bóng được spec cho phép làm lý do bắt thiết kế lại. Phán xét dưới đây dựa trên yêu cầu cụ thể của dự án.

## 2. Các mục cần sửa hoặc bổ sung

### A. Chữ nút trong chế độ tối sai tương phản

`tokens.css` đổi `color-primary` thành `#29A9FF` khi tối, nhưng `.btn-primary` trong các preview vẫn đặt chữ trắng.
Chrome xác nhận nút thường cỡ chữ 14/16 px có chữ `rgb(255,255,255)` trên nền `rgb(41,169,255)`: **2,56:1 < 4,5:1**.
Trong khi báo cáo và cặp kiểm `dark_btn_text_on_primary` lại dùng chữ tối `#0E1217`.

[Ảnh thực trên Chrome](../artifacts/coord-w22-2026-10-19/components-dark.png) được tạo từ bản sao thử nghiệm trong `tmp/`, chỉ thêm thuộc tính
`data-theme="dark"` và đường dẫn cơ sở để dùng nguyên CSS/HTML bàn giao. Không sửa tệp thiết kế gốc.
Sửa màu chữ nút đúng theo spec ở từng chế độ; soát cả trạng thái hover/focus và các nút trạng thái khác.

### B. Vùng bấm điện thoại dưới mức 44×44 px

Đo trong khung điện thoại của `mobile_screens.html` trên Chrome:

| Nút | Chiều cao thực | Yêu cầu spec mục 9 |
|---|---:|---:|
| Học tiếp | 32 px | ≥ 44 px |
| Đọc trang | 28 px | ≥ 44 px |
| Hỏi trợ lý | 39 px | ≥ 44 px |
| Đánh dấu đã học | 44 px | ≥ 44 px |

Chưa có vùng bấm bao ngoài bù chiều cao cho ba nút nhỏ. [Số đo runtime](../artifacts/coord-w22-2026-10-19/browser-runtime.json).

### C. Giảm chuyển động chưa thay GIF bằng ảnh tĩnh

Khi Chrome xác nhận `prefers-reduced-motion: reduce` đang bật, nguồn ảnh vẫn là `Untitled_Artwork.gif`.
Bốn ảnh chụp riêng vùng GIF, cách nhau khoảng 400 ms, cho **bốn khung hình khác nhau**. Vòng chờ vẫn chuyển động.
CSS rút ngắn `animation-duration`/`transition-duration` không dừng được GIF trong thẻ `img`.

Bằng chứng: [khung 0](../artifacts/coord-w22-2026-10-19/reduced-motion-gif-0.png),
[khung 1](../artifacts/coord-w22-2026-10-19/reduced-motion-gif-1.png),
[khung 2](../artifacts/coord-w22-2026-10-19/reduced-motion-gif-2.png),
[khung 3](../artifacts/coord-w22-2026-10-19/reduced-motion-gif-3.png),
cùng hash trong kết quả runtime. Cần tài sản ảnh tĩnh và cách chọn đúng khi giảm chuyển động, như spec đã yêu cầu.

### D. Bộ test chưa bắt được token sai hoặc JSON/CSS lệch

Thử thay **riêng giá trị CSS đọc vào test**, từ `--color-primary: #0A6AB3` sang `#29A9FF`, giữ JSON ở `#0A6AB3`.
Như vậy CSS vừa lệch JSON vừa tạo cặp chữ trắng/nền xanh chỉ 2,56:1. Kết quả: **20/20 test vẫn đạt**.
Phép thử chỉ thay dữ liệu đọc trong tiến trình; không ghi thay đổi vào CSS gốc.

[Kết quả phép thử](../artifacts/coord-w22-2026-10-19/unsafe-css-result.json),
[XML](../artifacts/coord-w22-2026-10-19/unsafe-css-tests.xml),
[log](../artifacts/coord-w22-2026-10-19/unsafe-css-tests.log).
Test phủ định hiện có chứng minh phép tính của một cặp hằng số; chưa chứng minh guard bảo vệ tệp token được dùng thật.
Đây cũng là phép sửa sai được yêu cầu sẵn ở phần "Quyết định kiểm thử" của spec thiết kế.

### E. Chưa đủ bằng chứng về toàn bộ Figma, trang/trạng thái và bốn luồng bấm

Gói tại máy có **5 khung desktop**, **2 khung điện thoại** và một trang thành phần. Spec mục 11 còn yêu cầu các nhóm trang xác thực,
tham gia, tài liệu, thành viên/tiến độ lớp, quản lý khoá, hồ sơ/mức dùng, quản trị, 404; các trạng thái tải/rỗng/lỗi/không có quyền,
kết quả quiz, cùng các màn tối. Chưa có bảng ánh xạ từng mục kiểm sang node Figma/ảnh xuất tương ứng.

Ba HTML không có script, bộ xử lý sự kiện, liên kết điều hướng hay khối `details`; chúng không thực hiện được bốn luồng trong báo cáo.
Mục 5 báo cáo mới mô tả các bước, chưa có link chạy prototype, node bắt đầu hoặc video thao tác.
Điều này **không kết luận file Figma không tồn tại hay không có prototype**: công cụ web của lượt soát không truy cập được nội dung file.
Link được nhân viên cung cấp là [Figma doctoroadmap](https://www.figma.com/design/UVhhlZnqdpV0JDcAHwJczo/doctoroadmap).
Chưa xác minh trực tiếp quyền xem, cấu trúc trang, Variables, thành phần hay liên kết tương tác trong file.

`screens.html` dùng canvas cố định rộng 1280 px. Khi mở ở 768 px, trang tràn ngang **532 px**;
ở 390 px, nội dung desktop bị cắt dù phép đo tràn ngang trả 0. Đây là giới hạn của preview được bàn giao,
không đủ làm bằng chứng rằng bố cục sản phẩm đã đạt 390/768/1280.
[Ảnh 768](../artifacts/coord-w22-2026-10-19/screens-768.jpg),
[ảnh desktop mở ở 390](../artifacts/coord-w22-2026-10-19/screens-390.jpg),
[khung mobile riêng](../artifacts/coord-w22-2026-10-19/mobile-preview-390.jpg).

Người làm cần cung cấp node/ảnh còn thiếu nếu đã có trong Figma; phần chưa có thì hoàn thiện trong phạm vi W-22.
Không yêu cầu biến trang trưng bày mockup thành ứng dụng React. Cần bằng chứng bố cục ở 768, prototype bấm được,
video hiệu ứng và bản xuất Variables kèm tên công cụ để đối chiếu được. Chưa có căn cứ xác nhận tuyên bố "W3C/Figma/CSS đồng bộ 100%".

## 3. Phân công tiếp theo

- **Người làm W-22 / người thiết kế:** nhận [W-24](../task/web/W-24-bo-sung-va-sua-ban-giao-w22.md), sửa A–D và bổ sung E.
  Báo cáo lại những mục đã có, đã sửa và còn thiếu; commit đúng tài sản/tệp của vé, không gom thay đổi của phiên khác.
- **Nhóm React W-01:** tiếp tục nền FastAPI/React/PostgreSQL, router, khung chung, token theo spec.
  Có thể dùng bộ token và preview hiện có làm đầu vào tạm; kiểm từng thành phần khi tích hợp, đặc biệt ba lỗi A–C.
  Chưa coi W-22 là bản Figma đã được nghiệm thu. Test hợp đồng React phải đọc bản xuất Variables có nguồn gốc và CSS thực.
- **Người soát:** kiểm lại W-24 với dữ liệu đầu vào đã ghim; phép sửa sai phải bị bắt. Chỉ đóng W-22 khi đủ tiêu chí ban đầu.
- **W-23:** tiếp tục chờ W-22 nghiệm thu và W-08/W-09/W-10 theo phụ thuộc đã có. Bộ ảnh hiện tại chưa thay thế đầu vào này.

**Nguồn chân lý vẫn là spec thiết kế và các quyết định của chủ dự án.** Figma thể hiện spec để React đối chiếu; link bàn giao không tự thay thế spec.

## 4. Lệnh kiểm đã chạy

```powershell
.venv/Scripts/python.exe -X utf8 -m pytest tests/unit/presentation/test_tokens_and_wcag.py -p no:cacheprovider --basetemp=tmp/coord-w22-20261019 --junitxml=tmp/coord-w22-20261019.xml --tb=short -ra
.venv/Scripts/python.exe -X utf8 scripts/verify_wcag_contrast.py
node .agents/skills/design-taste-frontend/scripts/inspect.mjs design/preview/components.html --app --widths 1280,768,390 --out tmp/coord-w22-inspect/components --json
node .agents/skills/design-taste-frontend/scripts/inspect.mjs design/preview/screens.html --app --widths 1280,768,390 --out tmp/coord-w22-inspect/screens --json
node .agents/skills/design-taste-frontend/scripts/inspect.mjs design/preview/mobile_screens.html --app --widths 1280,768,390 --out tmp/coord-w22-inspect/mobile --json
```

Phép thử CSS sai và kiểm runtime dùng script thử trong `tmp/coord-w22-mutate-css.py`, `tmp/coord-w22-runtime.mjs`.
Kết quả và ảnh đã lưu riêng trong `artifacts/coord-w22-2026-10-19/`; không phụ thuộc vào ảnh tự báo của nhân viên.
