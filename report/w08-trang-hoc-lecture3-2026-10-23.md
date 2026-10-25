# W-08 — trang học theo lecture-3 — 2026-10-23

## Phạm vi và mốc

- Nhánh `work/w08-lecture`, worktree một cấp `tmp/w08-lecture`, tạo từ main `ecd98c2` có W-11 đã ghép tại `e85427a` theo [nghiệm thu lần 2](dieu-phoi-nghiem-thu-ba-nhom-lan2-2026-10-23.md). Giữ nguyên worktree W-11.
- Lát chuẩn bị `2a55c63` dùng fake đúng shape lecture-3; sau đó nhận main `b5f921e` tại `c9a8099`, gồm **SA-64 ghép `1d91b0b`** và SA-62 ghép `9ac2a85`. [Ghi chú SA-64](pha-b-sa64-2026-10-23.md) xác nhận `parse_version` gắn ngay tại loader và bài `cat_ngan` không lưu vào cache chung.
- Nhận main tài liệu mới nhất `710d013` tại `f34111d`. Mốc cổng sau sửa setup test là **`84fecf1aa92c2c7672ab2d39d6e3ed9bee0643aa`**, manifest 1.003 hash. Khác `f34111d` đúng một tệp `Learning.test.tsx`: nạp renderer thật trước khi bắt đầu đồng hồ stream giả; không đổi sản phẩm, assertion hay timeout. Hai lượt cổng được giữ riêng.
- Mốc `76a129ef1c495984796e6114ed6d5ba4e0f87c45` bổ sung snapshot `src/web/openapi.json`, sinh từ ứng dụng thật: thêm 5 route W-08 và DTO mới, không xoá route. Guard so khớp và guard thêm route vẫn nguyên, [5 test kiến trúc/snapshot đạt](w08-evidence/openapi-green.xml).
- Mốc `d07c31ed0a9020f50d2bcd9e45e1b5cc7af29487` sửa đúng nhãn nút đọc trang khi nguồn DOCX không có trang đánh số, vẫn cho mở tệp gốc. [RED](w08-evidence/docx-label-red.xml) → [GREEN](w08-evidence/docx-label-green.xml), không đổi backend. Các lượt `final3-*` và `final4-*` lưu riêng; sau đó nhận main có SA-65 để chạy `final5-*`, không dùng kết quả trước SA-65 thay cổng tích hợp.
- **Nguồn bàn giao cuối `e6b336e6b31466a89b8a9893312f10f40d75cb8a`**, main nền **`e5fa4924cc7e3d6eda924d6668c8c15b453cea91`**, có SA-65 đã ghép tại `4a4b957`. [Manifest 1.007 tệp](w08-evidence/final5-source-manifest.json) và [đối chiếu blob Git](w08-evidence/source-blob-manifest.json) ghim nguồn thực chạy. Commit hồ sơ sau đó chỉ thêm báo cáo/bằng chứng W-08; nguồn sản phẩm giữ nguyên.
- Chỉ sửa web/gateway/composition/test/harness. Không sửa lõi SA, vé, kế hoạch hoặc handoff; không migration mới, giữ một head `w11_0007`.

## Đã triển khai

- Gateway và HTTP đọc cache `lecture-3`, SSE `skeleton → delta{text} → final{lecture}/failure`. GET bài chỉ đọc cache, không sinh. Route SSE kiểm thành viên/node trước HTTP 200; chặn cross-site gây sinh bài.
- Worker sinh chạy độc lập với kết nối SSE. Người học đóng trang không huỷ công việc; lần đọc sau dùng cache PostgreSQL. Tiến độ gắn theo actor mỗi lần trả, không ghi nhãn cá nhân vào cache chung.
- Phản hồi có projection và DTO rõ trường; validation, sections/bridge, đường nội bộ và public_id không gửi qua JSON/SSE. Log kiểm nội dung không làm lỗi bài. Trước chữ đầu: message tiếng Việt và luôn Thử lại; sau chữ đầu: giữ chữ, ready + cat_ngan.
- Trang module và bài học, danh sách theo thứ tự, dấu đã học riêng và rollback khi SQL lỗi. Tiên quyết gập sẵn, mở bài tiên quyết, Tiếp theo, định nghĩa nguyên văn, ảnh công thức, Trong sách, đáp án tự kiểm tra gập/null.
- Markdown/LaTeX qua react-markdown + remark-math + rehype-katex. Bỏ HTML thô và ảnh do Markdown tự đưa vào; KaTeX trust=false. Chỉ nhãn nguồn đã đăng ký thành nút, nhãn lạ giữ chữ, code không bị đổi thành trích dẫn. Tải riêng bộ dựng công thức khi mở bài. Căn cứ API: [react-markdown](https://github.com/remarkjs/react-markdown), [remark-math](https://github.com/remarkjs/remark-math), [KaTeX options](https://katex.org/docs/options).
- Viewer ảnh trang có trước/sau, Escape, focus trả lại trích dẫn, vùng ảnh nhận bàn phím để cuộn. Giữ page cùng URL ảnh để không gắn số trang mới lên ảnh cũ khi đang tải. DOCX/không có nguồn hiện đúng tình trạng.
- Media/source luôn đi qua guard thành viên. Máy chủ proxy WebP với private max-age=300; mở cả tệp 302 hạn 300 giây. Media chỉ lấy từ allowlist graph đã phát hành; lazy upload dùng khoá giao dịch PostgreSQL và tái sử dụng mapping. Trần cá nhân trên web là 1 USD/ngày theo quyết định mới; W-08 không hiển thị số tiền/token.

## Thiết kế và quan sát

Áp dụng `design-taste-frontend` app screen cùng `frontend-ui-engineering`. Direction `editorial-greeting`, seed `1026014839`, giữ palette/type; bố cục chi tiết theo spec trang học đã duyệt thay bố cục greeting của thư viện vì đây là trang đọc bài. Dùng CourseShell/logo Artboard 24/28, Be Vietnam Pro và token main. Không nhập preview W-24 chưa được nhận nguyên gói. Dấu riêng của WayFinder là định nghĩa đối chiếu tài liệu, nguồn từng trang, tiên quyết và bước tiếp theo.

Các lượt phát triển giữ nguyên lịch sử:

- `contract-red`: thiếu endpoint làm 2 ca đỏ, 2 control node không tồn tại đạt. `contract-green`: 24 ca gateway/quyền hiện có đạt.
- `markdown-red → markdown-green`: LaTeX/nguồn/HTML-URL nguy hiểm từ đỏ sang đạt.
- `browser-dev1`: harness dùng sai context manager PdfPage; sửa bằng close() và khoá render, không sửa sản phẩm để bỏ qua ảnh.
- `browser-dev2`: phát hiện mất focus sau viewer; đã sửa, có test thay nút trích dẫn khi stream.
- `browser-dev3`: Axe yêu cầu soát ký tự phân số KaTeX và biểu tượng mũi tên Unicode. Dùng SVG cho mũi tên; giữ nguyên finding KaTeX, đo màu thực 4,5:1 và thử phá chữ cùng màu nền.
- `browser-dev4`: Axe bắt vùng ảnh chưa focus để cuộn; đã thêm vùng có tên/tabindex. Đồng thời test ảnh trang giữ danh tính khi request mới chậm.
- `browser-smoke1`: Axe incomplete vì lỗi tiến độ có mã dài và sidebar bị che khi cuộn; đã xuống dòng mã, đặt sticky dưới header, giới hạn chiều cao sidebar, kiểm scroll vùng độc lập.
- `browser-smoke2`: Docker không chạy nên kết nối PG timeout trước mở browser; không tính là sản phẩm đỏ. Đã mở lại Docker, chỉ DB kiểm thử.
- `browser-smoke3`: các luồng browser/rollback đã đi qua, nhưng inspector không tạo được profile vì thiếu thư mục cha. Sửa harness tạo thư mục riêng; giữ log lỗi, không tính lượt này đạt.
- `browser-smoke4`: sửa kỳ vọng gỡ thành viên từ 204 sang đúng HTTP 200 của hợp đồng W-11; lượt lỗi làm kiểm shutdown dừng trước dọn DB, đã gỡ riêng đúng UUID theo [biên bản](w08-evidence/smoke4-independent-cleanup.json). Harness mới luôn dọn DB trước khi kiểm thread. `browser-smoke5` đạt 13 ảnh/5 Axe có phạm vi, SQL độc lập và service/DB đã dừng; không thay ma trận cuối.
- Lượt mutation đầu dừng ở vị trí thay thế có CRLF; hai guard trước đó đã đỏ, nguồn phục hồi. Lượt mới chuẩn hoá newline trong bản sai tạm thời nhưng luôn phục hồi nguyên byte gốc, không sửa nguồn chuẩn để phù hợp harness.
- Lượt mutation tiếp theo chỉ bỏ Sec-Fetch-Site nhưng Origin vẫn chặn nên phép phá đó sống; đã sửa bản sai tạm thời bỏ cả hai điều kiện. [Đối chiếu 13/13 guard với nguồn cuối](w08-evidence/mutation-source-match.json): 8 guard backend lấy từ `mutations3`, 5 guard UI được chạy lại trong `mutations4` sau bản vá DOCX. Từng bản sai có native 1, assertion failure và 0 setup error; wrapper native 0, nguồn khôi phục cùng SHA trước cổng/server.
- Audit đầu thấy bản KaTeX cũ trong dependency con theo [advisory upstream](https://github.com/advisories/GHSA-238p-pmpm-9mq7). Dùng override cùng KaTeX 0.19.0 cho toàn cây; [audit sau sửa](w08-evidence/npm-audit-fixed.log) native 0, không advisory; test renderer thật vẫn đạt.
- React ở `f34111d` có 1 ca tìm nút nguồn quá sớm khi module Markdown đang tải (chữ raw đã hiện). Sửa setup test bằng import renderer thật trước nhịp stream; giữ assertion và timeout. Lượt `final2-react` trên `84fecf1` đạt 157/157; không chạy lặp cổng để che ca đỏ cũ.
- Python đầu (`final-python`) có **2.372 đạt, 1 fail snapshot OpenAPI, 1 Cloudinary live bỏ qua**, native 1. Lượt `final2-python` đã khởi động với snapshot cũ được dừng có chủ đích (native 4294967295), không tính là cổng đạt. Sửa snapshot bằng export thật, giữ test gốc; `final3-*` kiểm lại toàn bộ sau sửa. [Danh sách route/schema thêm](w08-evidence/openapi-update.json).

## Kết quả và bằng chứng cuối

- **Python/PostgreSQL toàn repo: 2.385 đạt, 1 Cloudinary live bỏ qua có sẵn, 8 warning thư viện**, native 0 trên nguồn cuối `e6b336e` sau nhận SA-65; [JUnit](w08-evidence/final5-python.xml), [log](w08-evidence/final5-python.log), [lệnh/mốc/native exit](w08-evidence/final5-python-command.json). Không bật kiểm Cloudinary thật trong đợt 0 USD.
- **React 158/158 đạt**, build native 0 trên nguồn cuối `e6b336e`; [JUnit](w08-evidence/final5-react.xml), [build](w08-evidence/final5-build.log). Lệnh/mốc/native exit ở các tệp `final5-*-command.json`; [bảng kết quả](w08-evidence/gate-results.json) và [ánh xạ assertion](w08-evidence/invariant-map.json).
- **Browser native 0 trên đúng `e6b336e`**, không mã dở: [lệnh](w08-evidence/final5-browser-command.json), [audit](w08-evidence/browser-final5/audit.json), [SQL/runtime](w08-evidence/browser-final5/runtime.json). 12 cấu hình 390/768/1280 × sáng/tối × normal/reduced, **101 ảnh, 308 trao đổi HTTP**, hai video [learner](w08-evidence/browser-final5/learner.webm)/[owner](w08-evidence/browser-final5/owner.webm). Từng lượt kiểm text hiện trước khi mô hình kết thúc, reload dùng cache, source label mở đúng trang, trước/sau, Escape/focus và vùng bấm 44×44.
- **17 lượt Axe tại1280**: module/ready/viewer/failure ở hai theme và hai motion setting, cộng rollback. Không violation, không incomplete chưa soát. Giữ nguyên 8 finding glyph KaTeX ngắn và kết quả đo màu thực ≥4,5:1; cố ý đổi chữ thành màu nền bị chính guard bắt, sau đó phục hồi. Không gọi cả101 ảnh đều đã Axe.
- Inspector không FAIL; còn một WARN `font-fallback` cho tên font generic `math` ở MathML. Ở cả ba độ rộng, FontFaceSet chứng minh **Be Vietnam Pro, KaTeX_Main, KaTeX_Math đã tải**; đây không phải thiếu ba font này. Bản snapshot nhúng font để tránh CORS của file://; không thay mạng/HTML của ứng dụng.
- SQL connection độc lập: 1 bài ready trong cache có validation admin, 29 hàng usage giả/2.900 input token giả, tổng tiền fake ledger0; sau gỡ thành viên chỉ còn owner. PostgreSQL giữ progress của người đã rời; không xoá dữ liệu riêng. [Đối soát DB UUID và cổng8018 sau kiểm](w08-evidence/cleanup-check.json) xác nhận không còn DB/service harness.
- Lượt browser có log Windows Proactor `ConnectionResetError` khi đóng kết nối và cảnh báo hết grace shutdown; không có unexpected console/page error/failed request trong browser, native exit0, thread đã dừng và DB đã gỡ. Log gốc giữ nguyên để soát; không bỏ warning khỏi bằng chứng.
- Đã mở xem trực tiếp ảnh cuối: [390 tối/reduced](w08-evidence/browser-final5/ready-390-dark-reduced.png), [390 lỗi/sáng](w08-evidence/browser-final5/failure-390-light.png), [viewer768 sáng](w08-evidence/browser-final5/source-768-light.png), [1280 sáng](w08-evidence/browser-final5/ready-1280-light.png). Cột đọc phân cấp rõ, tên dài xuống dòng, panel không tràn, ảnh PDF đúng trang; công thức artifact gốc giữ nền trắng trong theme tối. [Ghi nhận quan sát](w08-evidence/visual-review.json).
- Ảnh/video/snapshot thiết kế của các lượt phát triển trước giữ nguyên tại đường dẫn local, không đưa các bản trùng vào Git; [danh sách và hash](w08-evidence/local-historical-assets.json). Log/JSON/native exit lịch sử vẫn bàn giao, ảnh/video `browser-final5` được đưa vào Git. Không xoá tệp hay dọn worktree/snapshot.

Các lệnh cổng từ gốc worktree, native exit đều 0:

```powershell
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe scripts/w05_run_tests.py -o addopts= -q --basetemp=tmp/w08-final-20261023-5 --junitxml=report/w08-evidence/final5-python.xml
npm.cmd --prefix src/web/frontend test -- --pool=threads --maxWorkers=1 --reporter=junit --outputFile=../../../report/w08-evidence/final5-react.xml
npm.cmd --prefix src/web/frontend run build
$env:W08_EVIDENCE_RUN = 'browser-final5'
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe -X utf8 scripts/w08_web_runtime.py
```

Báo cáo này là bàn giao của nhóm web, **chờ điều phối soát/nghiệm thu W-08**, không tự đánh dấu vé đạt hoặc ghép main. Các số ở mục lịch sử không thay cổng cuối. Hướng dẫn mở backend/frontend và harness nằm tại [README web](../src/web/README.md).

## Giới hạn phạm vi

- Hỏi trợ lý hiện thông báo chưa sẵn sàng; nối khung chat thuộc W-09. Không dựng trợ lý giả thành tính năng thật. Báo lỗi nội dung thuộc W-19, quiz/tài liệu thuộc W-10/đợt sau, không có nút hứa thành công giả.
- Ảnh trang trong browser lấy từ PDF fixture đã chép đúng manifest và render local bằng MediaStore giả; không gọi Cloudinary. Nội dung bài do mô hình giả, không chứng minh chất lượng bài thật của nhà cung cấp. Mọi chi ngoài 0 USD; PostgreSQL, auth/CSRF, Lecture3UseCase, HTTP/SSE và browser là thật.
- W-09 sau W-08, theo answer-3/ADR 0026, chờ SA-66 ghép; giữ Vertex, không sửa SA-61. Trước W-10 nhận spec/mốc SA-67/68 mới, không tự chốt hợp đồng tương lai.
