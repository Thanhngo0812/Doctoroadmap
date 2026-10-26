# R4 — rà soát thiết kế web W-24 tại eb29f29

Phạm vi: các sửa mới so với mốc thiết kế web đã chấp nhận `f292f18`; nhánh `work/w24-figma-evidence`, commit `eb29f291709245a9ccf3d121415f6202fdeaae7f`. Thực hiện static review và focused unit/VM trên 26 bản sao ordinary file có SHA-256. Đây **không phải cổng PostgreSQL của repo**, không chạy provider/ADC, không sửa main hoặc worktree của nhóm thiết kế. Runtime browser do điều phối viên thực hiện riêng.

Quyết định người dùng ngày 2026-10-24 được giữ nguyên: bỏ Cloud Figma khỏi điều kiện nghiệm thu, giữ mốc thiết kế web đã pass; triển khai HTML/CSS/token → React → cùng soát. Không yêu cầu Variables receipt, bindings, Present hoặc mở lại các hạng mục đã pass.

## Required — các lỗi web mới

1. **W-09 có class KaTeX nhưng thiếu toàn bộ CSS bố trí toán.** `design/preview/w09_chat_screens.html:254` thêm nhiều lớp `katex`, `mathnormal`, `msub`, `vlist-*`; trang chỉ liên kết `tokens.css` và không có bất kỳ quy tắc `.katex`/`.msub`/`.vlist-*` nào trong style nội tuyến hoặc file được liên kết. Vì vậy các chỉ số `coronary`, `diastolic`, `LVEDP` không nhận kiểu chỉ số dưới. Bằng chứng: `test_w09_formula_has_subscript_layout_styles` đỏ; browser root ở 1280 sáng đo base và sub cùng y=998.5625, font 14px, `verticalAlign=baseline`, screenshot hiện `Pcoronary = Pdiastolic - PLVEDP` trên cùng dòng chữ. Sửa bằng công thức được render đúng cùng CSS đi kèm, hoặc markup toán native tương đương; không chỉ thêm class để qua kiểm thử chuỗi.

2. **Công thức mới biến mất khỏi nội dung đọc được của công cụ hỗ trợ.** `w08_lecture_screens.html:272`, `:275` và `w09_chat_screens.html:254`: toàn bộ chữ toán nằm trong `aria-hidden="true"`; không có nhánh MathML, nhãn thay thế hay văn bản truy cập tương đương. Hai assertion `test_w08_formulas_have_accessible_content` và `test_w09_formulas_have_accessible_content` đỏ. Browser root xác nhận snapshot công thức khối W-08 và công thức W-09 rỗng; snapshot `.katex` đầu W-08 **không rỗng**, nhưng chỉ còn câu “Lưu lượng dòng máu…” và không có nội dung toán. Bổ sung MathML hoặc nội dung/nhãn truy cập tương đương khi sửa công thức.

3. **Công thức inline W-08 thiếu đóng span ngoài, nuốt công thức khối và đoạn giải thích phía sau.** Tại `design/preview/w08_lecture_screens.html:272`, cây phân tích HTML đặt `.katex` thứ hai và câu “Lưu lượng dòng máu đạt đỉnh…” bên trong `.katex` đầu. Đây là markup mới, làm phạm vi font/line-height/inline-block của công thức lan sang nội dung thường. Assertion `test_w08_formula_nodes_are_not_accidentally_nested` đỏ. Browser root xác nhận `nested=1`, outer `.katex` tại 390 sáng cao 132.34375px, chứa cả hai công thức và câu giải thích; screenshot cho thấy câu này chuyển sang font serif của công thức. Đóng đúng cấu trúc để đoạn giải thích giữ font văn bản thường.

Tôi đã đọc JSON đo runtime và xem hai screenshot do root tạo; tôi không trực tiếp chạy browser. Bằng chứng root: `../coord-r4-tools-20261024/design-browser/observations.json`, `w09-active-1280.png`, `w08-ready-390.png`. JSON có 24 hàng = 12 cấu hình × 2 trang (390/768/1280, sáng/tối, thường/giảm chuyển động), browser `156.0.8078.4`, không overflow. Tham chiếu và SHA nằm trong `browser-evidence-reused.json`; đây là diagnostic browser, không phải repo gate.

## Đã kiểm chứng đạt

- Focused file `tests/unit/presentation/test_tokens_and_wcag.py`: **52 passed in 0.96s**, native exit 0, Python 3.12 từ môi trường repo nhưng cwd/config/conftest cô lập trong scratch.
- VM baseline: 37 variable records, 74 mode values được ghi; đếm độc lập `valuesByMode` khớp `report.created=74`, lỗi 0.
- VM ép `createVariable` lỗi cho `color/primary`: 36 records, 72 mode values, `failed=2`, một lỗi tạo biến, có thông báo lỗi. Không cần Cloud để xác minh hành vi local này.
- Mutant bỏ `variableReport.created += 1`: vẫn có 74 mode writes thực tế nhưng reported created bằng 0; test đầu ra baseline hiện có **đỏ native exit 1**, sau đó khôi phục bản sao. Vì vậy guard mới thực sự bắt việc mất accounting, không chỉ dò chuỗi mã.
- GIF và PNG tồn tại, nằm trong cây file dự kiến và giải mã hết: GIF **61 frames**, PNG **1 frame**. HTML đặt kích thước 96×96 và `<picture><source media="(prefers-reduced-motion: reduce)">` chọn PNG. Natural size asset 2000×2000; đây là cỡ hiển thị 96 px, không phải file nguồn 96 px. Root kiểm lựa chọn `currentSrc` và đứng khung thực tế.
- W-08: cả hai trạng thái lỗi trước khi có chữ chứa nút retry trong đúng section; lỗi đuôi còn `cat_ngan` và không còn hứa “Tải lại bản đủ”. Đây là kiểm cấu trúc màn hình thiết kế, không tuyên bố backend retry đã nối.
- Hai định danh báo cáo mới `#btn-delete-course-permanent` và `#text-tool-action` đều tồn tại trong đúng preview.
- SHA source và bản sao đều khớp manifest sau mutation/khôi phục; worker HEAD vẫn `eb29f29`, cây làm việc worker sạch.

## Optional — cập nhật tài liệu và câu chữ

`report/w24-kiem-lai-2026-10-22.md:14` và phần 3 vẫn ghi W-22/W-24/W-23 MỞ vì thiếu Cloud, rồi yêu cầu chủ dự án thực thi plugin và quay Present. Đó là trạng thái lịch sử đã bị quyết định người dùng 2026-10-24 thay thế. Nên thêm mốc cập nhật ở đầu báo cáo để người đọc không hiểu Cloud là điều kiện đang chặn. Đây **không phải lý do mở lại mốc thiết kế web đã pass**, và không yêu cầu làm thêm Cloud.

`design/preview/w08_lecture_screens.html:327` và mục 1.1 của báo cáo còn nói phần nhận trước lỗi đuôi được “lưu giữ an toàn”. Hành vi hiện tại `src/doc2roadmap/application/phase_b/lecture3.py:229`–231 cố ý không đưa kết quả `cat_ngan` vào cache chung. Nên dùng “Nội dung đã nhận vẫn được giữ trên màn hình” để tránh người học hiểu là được lưu bền hoặc sẽ phục vụ lại từ cache. Đây là Optional wording; việc bỏ nút tải bản đủ ngoài hợp đồng vẫn được đóng đạt.

## Bằng chứng và giới hạn

`copy-manifest.json`, `post-run-hash-verification.json`, `native-records.json`, `pytest-focused-baseline.xml`, các file `vm-*.json`, `vm-independent-observations.json`, `artwork-decode.json`, `structural-observations.json`, stdout/stderr log và hai script tái chạy nằm trong thư mục này. Reviewer-added structural assertions: 4 PASS / 4 FAIL, native exit 1; bốn FAIL quy về ba vấn đề Required ở trên.

Preflight đầu dùng `pytest -c NUL` đã lỗi collection trên Windows do rootdir trỏ về thiết bị NUL và gặp `C:\Documents and Settings`. Đã giữ riêng `preflight-failed-native-records.json` cùng log, rồi chuyển sang file ini scratch thật và rootdir tường minh. Không dùng thất bại preflight đó để kết luận lỗi sản phẩm, không coi baseline isolated là repo gate.

Kết luận vòng static/focused: **cần sửa các công thức mới**, còn các sửa retry, ảnh, định danh và guard VM đạt kiểm tra được giao. Giữ nguyên mốc pass thiết kế web trước đó và quyết định bỏ Cloud Figma.
