# R9 — review độc lập React W-16

**Kết luận: Approve phần React W-16 tại `6ee153864522eb1510e3ec88dc5e9c52e1cfe2ca`. Không có Critical, Required hoặc Optional còn mở.** Có thể nhận toàn W-16 khi điều phối hoàn thành cổng tích hợp trên candidate; review này không thay kết quả cổng PG/browser tích hợp của root.

Đã đọc skill code-review-and-quality, vé W-16, spec chức năng mục 8, lời giao R8 và báo cáo tác giả. Review đúng phạm vi trang/dải usage-1 và thay đổi liên quan; không xem các khác biệt lịch sử giữa nhánh cũ và main mới là thay đổi của vé.

## Mã và hành vi đã soát

- `src/web/frontend/src/Usage.tsx:17`: tỷ lệ lấy từ API, đủ 35%/85%/100%, progress có nhãn; lỗi/retry không tạo số 0 giả. `Usage.tsx:39` giữ `max=null` là Không giới hạn, số hữu hạn tính còn lại không âm. `usage-api.ts:9` định dạng ngày và giờ theo Asia/Ho_Chi_Minh, không phụ thuộc timezone thiết bị. UI không có USD/cost.
- `Usage.tsx:8`, `Assistant.tsx:115`, `ContentLibrary.tsx:60`, `ContentLibrary.tsx:104`: dải nằm cạnh hành động, có ngày/giờ reset của learner; shared limit chỉ thông báo từ trường được cấp. Chat textarea/send, tài liệu và quiz không bị khóa chỉ bởi limited, core tiếp tục quyết định cache/bank/admission. Bài giảng W-08 không bị sửa.
- `App.tsx:367`, `Courses.tsx:30`: route bảo vệ và đường vào menu. `useUsage.ts:9`, `useUsage.ts:14`, `useUsage.ts:22` chống snapshot khác route/tài khoản, xử lý refresh/focus và kết quả/401 về muộn sau abort. Đăng xuất không làm xuất hiện lại dữ liệu riêng.
- `useAssistant.ts:107`: chỉ callback hiện hành cập nhật usage và phát sự kiện không payload. Các guard callback/error/finally tại `useAssistant.ts:84`, `useAssistant.ts:109`, `useAssistant.ts:114` tiếp tục bảo vệ lượt mới khi EOF/usage của lượt cũ về muộn. Bộ hồi quy `Assistant.final-usage-race.test.tsx:102`, `Assistant.final-usage-race.test.tsx:140` đã được chạy trong baseline.

## Kiểm chứng ngoại tuyến và phép phá

Tiếp tục nguyên scratch/evidence của reviewer trước, không ghi đè các lượt đã hoàn tất. 57 tệp nguồn chép thường vẫn khớp SHA, dependency dùng installation sẵn có của worker, Vitest chạy config native; toàn bộ HTTP/model trong các test React là fake. 48 ca baseline của tác giả + 2 probe focus độc lập + 1 probe event mới đều pass/native 0, không setup error. Probe event mới tái dùng fixture HTTP/SSE của tác giả, nhưng assertion đếm sự kiện và kiểm payload được reviewer thêm độc lập.

| Phép phá trong scratch | Kết quả có thể tái hiện |
|---|---|
| Đổi guard null thành nhánh số | native 1, 1 assertion fail: mất Không giới hạn |
| Khoá chat khi learner limited | native 1, 1 assertion fail: textarea bị disabled |
| Bỏ timezone Việt Nam, TZ=America/Los_Angeles | native 1, 3 assertion fail: sai ngày/giờ reset |
| Bỏ guard abort của useUsage | native 1, 2 assertion fail: snapshot cũ/401 cũ tác động route mới |
| Đưa notifyUsageChanged ra ngoài guard callback hiện hành | native 1, 1 assertion fail: nhận 2 event thay vì 1 |

Nguồn được phục hồi trong finally và SHA sau phục hồi khớp trước phép phá. Các lượt restored 9/2/1 ca đều native 0. Các ca skipped trong XML mutant là do bộ lọc `-t`, không sửa test thành skip. Chứng cứ: `reviewer-final-audit.json`, `mutation-results.json`, `focus-mutation-proof.json`, `events-mutation-proof.json`, từng log/XML/native receipt và các driver `.cjs` cùng thư mục.

## Nguồn và hồ sơ tác giả

`012abea28a32272a91aaccfa54823037652af28a` là SHA chạy cổng; `git diff` tới SHA bàn giao không có thay đổi src/scripts. Audit lại 299 tệp evidence khớp hash và 4 gate × 783 tệp src/scripts khớp raw receipt. Đối chiếu Git riêng xác nhận nội dung đúng SHA: 764 tệp có checkout CRLF thay vì Git LF, không có khác nội dung. Bản audit thử so raw Git với hash checkout bị đỏ vì CRLF được giữ ở `reviewer-final-audit-raw-git-attempt.json`; audit cuối kiểm cả raw receipt lẫn tương đương checkout/Git, native 0.

Đọc log/native/JUnit gốc: tác giả Python 2.824 pass/1 skip/1 xfail, React 229 pass, build pass; cả bốn gate cùng SHA trên đều native 0. Reviewer không chạy PG hoặc gọi mạng. Browser của tác giả ghi 66 ảnh/Axe, 0 violation, cache/bank dùng được khi limited, replay daily_limit không thêm model call; đã xem trực tiếp ảnh 35/85/100% 1280 sáng và chat limited 390 tối/reduced. Ảnh đọc được, dải không che controls; không dùng ảnh tĩnh làm chứng minh motion/focus. Root giữ trách nhiệm cổng browser/PG tích hợp candidate mới.

Chỉ thêm probe, driver và báo cáo vào scratch. Không sửa worker/main/product, không dùng provider/SMTP/Cloudinary/ADC thật, không đọc live cache/heldout, không push, không tạo link hoặc dọn dữ liệu. Chi ngoài 0 USD.
