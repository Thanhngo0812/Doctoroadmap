# R5 — nghiệm thu sửa công thức thiết kế web, 2026-10-25

**Đề nghị nhận phần sửa tại `aa387f3`: cả ba Required R4 đã đóng; không có Required mới trong phạm vi được giao.** Toàn nhánh có thể được ghép sau các cổng tích hợp của điều phối viên; không cần lọc prefix chỉ để cách ly phạm vi source. Mốc W-22/W-24 thiết kế web đã pass có ghi chú được giữ nguyên, Cloud Figma không phải điều kiện nghiệm thu.

Review dùng `code-review-and-quality`: chỉ xét thay đổi mới từ `eb29f29`, kiểm rủi ro phạm vi toàn nhánh so với `main` tại `46d829a`, đọc báo cáo cập nhật và đối chiếu auth hiện có. Không mở lại token/plugin hoặc phạm vi đã được người dùng chấp nhận. Tôi không sửa worker/main, không chạy PostgreSQL/full suite, provider, ADC, live cache hoặc push.

## Ba Required đã đóng

| Mã | Kết luận | Bằng chứng cụ thể |
|---|---|---|
| D-R4-01 | **Đóng — W-09 có chỉ số dưới thực** | CSS `.msub`/`.vlist-*` đã có. Browser 1280 sáng đo chữ chính 15.4px tại y=998.5625 và chỉ số dưới 11.55px tại y=1006.4375; cả 12 cấu hình đạt assertion cỡ chữ nhỏ hơn và vị trí thấp hơn. Ảnh `w09-active-1280.png` cho thấy công thức có chỉ số dưới. |
| D-R4-02 | **Đóng — công thức có nội dung truy cập** | Cả ba công thức có `role="math"`, nhãn khớp biểu thức, một MathML đúng namespace không nằm trong nhánh `aria-hidden`. Hai công thức áp lực có ba `msub`, công thức Q có phân số `mfrac`; cùng dấu bằng/trừ đúng. Browser ghi nhận cả 36 snapshot công thức trên 24 trang đều chứa math và tên tương ứng. |
| D-R4-03 | **Đóng — span inline không còn nuốt nội dung sau** | Source và DOM thực có `nested=0` cho mọi công thức. Công thức khối và câu “Lưu lượng dòng máu…” nằm ngoài công thức inline. Ảnh `w08-ready-390.png` cho thấy đoạn giải thích dùng lại font văn bản thường. |

Tôi đã đọc JSON runtime, kịch bản assertions và xem hai PNG do root tạo. Browser thực chạy trên worktree tích hợp `tmp/coord-r5-acceptance-20261025` tại `31d14b573a8d9852bfd0aa5d5185753a99a05ecc`; Git blob của cả hai HTML toán **giống hệt** worker `aa387f33542250b08487c2dd1ce105abc68fd9ed`. Record launcher ghi cwd repo ở `d8d5659…`; đó là commit của nơi gọi lệnh, **không phải commit mà browser mở**. Kịch bản trỏ worktree tích hợp tường minh.

Browser Chromium `156.0.8078.4`, native exit 0, `diagnosticOnly=false`: 390/768/1280 × sáng/tối × thường/giảm chuyển động, hai trang = 24 trang. Không overflow. Khối chờ W-08 vẫn 96×96, chọn GIF thường và PNG khi giảm chuyển động. Chi tiết, SHA của evidence root, provenance launcher và hai Git blob nằm trong `browser-evidence-reused.json`.

## Kiểm thử isolated có đối chứng

- Sao chép **26 ordinary files**, ghi SHA-256 trước/sau. Worker HEAD giữ `aa387f3`, cây làm việc sạch; bản sao được khôi phục nguyên byte sau mỗi mutation.
- File focused `test_tokens_and_wcag.py`: **58 passed in 1.30s**, native exit 0. Dùng Python 3.12 của repo nhưng cwd, pytest ini/rootdir và conftest cô lập trong scratch; đây **không phải repo PostgreSQL gate**. Những test token/plugin cũ chỉ chạy như hồi quy trong file này, không bị mở lại tiêu chí nghiệm thu.
- Giữ bốn guard mới, thay riêng hai HTML trên bản sao bằng nội dung `eb29f29`: **4 failed in 1.53s**, native exit 1. Tên: `test_w08_formulas_have_accessible_content`, `test_w09_formulas_have_accessible_content`, `test_w08_formula_nodes_are_not_accidentally_nested`, `test_w09_formula_has_subscript_layout_styles`.
- Khôi phục HTML hiện tại rồi chạy đúng bốn guard: **4 passed in 0.78s**, native exit 0.
- Assertion bổ sung về ba mẫu toán: nhãn đúng biểu thức, MathML không bị ẩn, đúng số chỉ số dưới/phân số, không lồng `.katex`, không chứa văn xuôi: PASS, native exit 0. Đối chiếu bằng cấu trúc thực trong `math-structure.json`, không chỉ kiểm có tên class.

## Optional — guard CSS còn chấp nhận trường hợp thiếu bố trí chỉ số dưới

`tests/unit/presentation/test_tokens_and_wcag.py:979`, `test_w09_formula_has_subscript_layout_styles`, dùng regex OR chỉ cần thấy **một** rule `.msub`, `.vlist-t` **hoặc `.katex`**. Trên bản sao, tôi xoá riêng `.msub/.vlist-*` nhưng giữ typography `.katex`; guard vẫn PASS native exit 0. Guard này chứng minh phát hiện việc hoàn toàn thiếu CSS ở HTML cũ, chưa tự chứng minh chỉ số dưới được bố trí đúng.

Không có lỗi bố trí đó trong bản hiện tại: browser root đã đo và assert hành vi độc lập. Đề xuất giữ phép đo cỡ chữ/vị trí trong hồi quy trình duyệt; không yêu cầu sửa thêm để nhận bản HTML đang đúng. Log: `mutation-removed-subscript-rules-css-guard.stdout.log` và `native-records.json`.

## Phạm vi source toàn nhánh so với main

`46d829a` là tổ tiên của `aa387f3`. Diff có **85 paths**, trong đó 71 báo cáo/evidence và **14 paths ngoài report**: 10 tệp thiết kế, ba script kiểm/chụp thiết kế, một file unit test. Không có thay đổi nào dưới `src/`, không đổi dependency hoặc active application/auth runtime.

Đã đọc auth hiện tại và so Git blob: `src/web/frontend/src/Auth.tsx`, `W11AuthReturn.repro.test.tsx`, `design/preview/auth_screens.html`, `w03_auth_screens.html` đều giống hệt main `46d829a`. Merge toàn nhánh không đưa auth cũ đè auth hiện tại. Các tệp token/plugin và màn hình ngoài hai trang toán thuộc phạm vi thiết kế đã được chấp nhận; review này không phủ nhận hoặc nhận lại các mốc ấy. `branch-scope.json` ghi đầy đủ đường dẫn và blob identity.

**Đề xuất:** nhận toàn nhánh thiết kế trong phạm vi hiện tại nếu các cổng tích hợp của root đạt. Không thấy lý do về scope để phải lọc prefix; lựa chọn merge hoặc mang source có thể tuân theo workflow điều phối. Tôi không tuyên bố đã chạy hoặc thay root xác nhận cổng PostgreSQL/full suite.

## Báo cáo và giới hạn bàn giao

Hai ghi chú tài liệu R4 cũng đã được sửa: đầu báo cáo ghi W-22/W-24 đạt có ghi chú, bỏ Cloud gate; phần Cloud cũ có disclaimer chỉ giữ để tham khảo. Lỗi đuôi nay nói “phần đã nhận vẫn hiện trên màn hình”, không hứa lưu cache/bền.

Phạm vi toán được chấp nhận là **ba công thức mẫu tĩnh** và nhánh MathML tương ứng. HTML hiện không nạp bộ parser LaTeX hoặc toàn bộ engine/CSS KaTeX; không có bằng chứng về renderer tổng quát. Câu “đầy đủ bộ CSS” trong báo cáo được hiểu trong ngữ cảnh các mẫu/fallback đã nêu, không dùng làm lý do thay renderer toán thực của React. Không có Required thêm từ giới hạn này.

Artefact: `summary.json`, `native-records.json`, manifest/SHA verification, XML/log của các lần chạy, `math-structure.json`, `branch-scope.json`, `browser-evidence-reused.json` và ba script tái kiểm trong thư mục này. Browser root được tham chiếu tại `../coord-r5-tools-20261025/design-browser/`; tôi trực tiếp chạy isolated unit/structural checks và trực tiếp đọc/xem evidence browser, không trực tiếp chạy browser.
