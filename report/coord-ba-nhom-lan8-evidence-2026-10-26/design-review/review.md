# Soát độc lập thiết kế vòng 8 — 2026-10-26

Pin `feb5f5e1ac847b8b8bfa0db726b4d26142859f6d`, main đối chiếu `153c5778b04474307395fb7d86c4d7605bf83855`. Delta 3 tệp, không đổi nguồn preview đã nhận ở vòng 7. Không Cloud Figma theo quyết định chủ dự án.

**Kết luận:** nhận mốc D-R7-02 thực thi JavaScript thật. W-23 vẫn mở. Có thể nhận nhánh với đính chính báo cáo có ngày của điều phối; không công nhận bảng đối chiếu mới là nghiệm thu W-23. Chi mới 0 USD.

## Kiểm độc lập

- Chép thường 54 tệp design/scripts/test vào scratch, có danh sách SHA-256. Không sửa worker hoặc mã main.
- Chạy đúng runner `scripts/w05_run_tests.py` trong scratch; conftest riêng chỉ nhận cờ runner, không có test DB. Đây là bằng chứng design/offline, không thay cổng PostgreSQL của root.
- Baseline3: **64 pass/native0**; final-green2: **64 pass/native0**. XML và log tại scratch.
- Mutation trên HTML thực: `cardGroup === group` → `!==`: **1 assertion fail/0 error/native1**.
- Mutation thay so sánh group bằng origin button/assistant (hành vi lọc cũ): **1 assertion fail/0 error/native1**.
- Mutation `checked > 5` → `checked >= 5`: **1 assertion fail/0 error/native1** tại quan sát nút/cảnh báo ở 5 module.
- Cả ba chạy test `test_w10_library_filters_by_group_independent_of_origin` bình thường, không gọi biến thể kiểm lỗi có sẵn của tác giả. Phản chứng vì danh sách tiêu đề hoặc nút sai, không phải lỗi import/setup.
- SHA nguồn gốc, phục hồi scratch và worker cùng `a6d42207d1c4f3915734b9efff6c757442ca6fefead5bec61706b9eddf7c0ecf`.
- VM đọc script HTML thật, không chép lại thuật toán group trong Python. Bốn record chéo lấy từ chính markup; expected title độc lập. Cách làm đủ cho mốc guard chức năng.

Các lỗi thiết lập của reviewer được giữ: baseline2 thiếu tệp `scripts/verify_figma_plugin_vm.cjs` khi tự chép dẫn đến3fail, đã bổ sung đúng nguồn rồi chạy64pass; không phải lỗi tác giả. NodeREPL bị giới hạn20giây khi đang chạy biến thể thứ hai; lượt XML thiếu native không được tính, đã phục hồi và chạy lại độc lập.

## D-R8-01 — Required: đính chính bảng W-23, không cản mốc guard sau đính chính

Tệp `report/w24-w10-w23-phoihop-2026-10-25.md`, dòng52–56. Đã mở xem thực tế cả10PNG trong5cặp. Cả10PNG và2WEBM đều tồn tại, SHA root/worker khớp; vấn đề là diễn giải ảnh, không phải mất artifact.

| Dòng | Câu hiện tại sai hoặc quá mức bằng chứng | Câu cần thay/đính chính |
|---|---|---|
|52|React là bài tim mạch, HTML self-check mở, không lệch token/khoảng cách.|React là Đại số tuyến tính → Phần tử, tự kiểm tra đã mở. HTML là catalog6trạng thái, self-check đang gập. 1280×2572 so1280×3493; chưa có cặp cùngstate/crop để kết luận token/spacing.|
|53|SourceViewer chiếm nửa phải tablet, preview section lecture-ready.|React source là modal ở giữa gần toàn chiều ngang768px; HTML là viewer inline ở section-page-image-viewer trong catalog. Chưa cùnglayout/state.|
|54|Section section-lecture-generating và cùng reduced-motion.|Anchor đó không tồn tại; đúng section-lecture-waiting-first-chunk. Reactwaiting390lightreduced là trạng thái chờ; HTML390×5384 là catalog, producer không đặt reduced-motion. Chỉ xác nhận ý tưởng nhân vật chờ tương ứng.|
|55|Section section-chat-answered và khớp định dạng/cặp bố cục.|Anchor không tồn tại, đúng section-chat-active. React là roadmap+chat bên phải, HTMLcatalog có khung chat rộng và nội dung khác. Có kiểm riêng math/nguồn/ratio trong báo cáo web cũ, chưa chứng minh pair conformance.|
|56|Section section-chat-options, các nút Tạo tài liệu/Đặt câu hỏi/Xóa hội thoại xếp dọc.|Anchor không tồn tại. React390×900 mở menu Đổi tên/Xóa cuộc trò chuyện; HTML390×2725 không có menu đó. Không thể ghi khớp tương tác từ cặp này.|

Runtime nguồn W08 ghi `b4136987668c3fb822ea374f399b947064ce7f18`, W09 ghi `0ba4ac8f5bc63256e33d736a08c0d6411a5b0b48`. Frontend diff đến các mốc báo cáo `c4d281b` và `378131e` là rỗng, nên không coi là source bị giả; cần ghi đúng origin và không gọi đó là cặp ảnh mới của toàn main hiện tại. Chưa có per-pair URL, full commit/SHA, crop/state/theme/motion manifest theo yêu cầu vòng7.

Các video có thật và SHA/size ghi trong referenced-evidence.json; reviewer không giải mã từng frame, không khẳng định nội dung/timestamp từng thao tác. Không có video HTML/React cùngstate mới trong delta.

Nguồn producer HTML `scripts/capture_w24_screenshots.cjs` chụp fullPage file:// catalog ở viewport390×844,768×1024,1280×900, không set reducedMotion hoặc mở self-check/menu. Vì thế tên section trong văn bản không làm PNG thành sectioncrop/cùngtrạngthái.

## D-R8-02 — Optional: giữ thêm guard liên kết tab

`scripts/test_w10_library_filter_vm.cjs:93` gọi `sandbox.filterLibrary('here', tabs['here'])` trực tiếp. Python bỏ các assertion cũ bảo vệ onclick tab. Chỉ sửa inline `here→button` và `elsewhere→assistant`, giữ hàm group đúng: **64pass/native0**. Người dùng bấm tab sẽ không nhận cùng tham số mà VM đang kiểm.

Đây là gap wiring còn lại, tách khỏi D-R7-02 đã đạt cho actual function. Thêm test click/dispatch thật hoặc khôi phục assertion wiring cũ; không thay thuật toán expected bằng codecopy. Guard trình duyệt độc lập R7 vẫn đã kiểm tab đúng của nguồn preview được nhận, không có bug wiring hiện tại.

## Ghi chú khác

- File-links mới tại dòng32,60,61 dùng file:// tuyệt đối, nên đổi relative; Nit, không cản guard.
- Ghi chú font fallback/CDP là đúng hướng, không còn dùng document.fonts.check=true như bằng chứng font thật. Không chạy font/browser mới ở vòng8 vì delta không đổi UI/CSS.
- Không tạo hoặc xóa worktree/DB/artifact, không đọc cache sống/heldout, không gọi provider, không push. Chỉ scratch review.
