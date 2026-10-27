# W-16 React — mức dùng và dải giới hạn — 2026-10-26

Nhánh `work/w16-usage-react`, worktree `tmp/w16-usage-react`, giữ nguyên worktree W-10 và dữ liệu cũ. Bắt đầu từ main 5da43a4 có W-10 aaf68eb đã nhận, backend usage-1 d1bf42b và backend W-04 c1f2fe9. Trước cổng cuối đã nhận main **788b600eedc44a161b6ed4c59e88bd59226aa86f**. Commit sản phẩm **7829b589c4d343ebe4a36cfab0747c905542d55e**, source gồm harness của cổng cuối **012abea28a32272a91aaccfa54823037652af28a**.

## Phần đã triển khai

- Route bảo vệ `/muc-dung`, mở từ menu tài khoản. Vòng tỷ lệ và progress cho trình đọc màn hình dùng đúng learner_today.used_ratio; nhãn Còn nhiều/Gần hết/Đã hết. Mốc 80% chỉ là nhãn trình bày, không thay policy server. Giờ/ngày đặt lại lấy từ API và định dạng bằng Intl theo Asia/Ho_Chi_Minh, không đoán ngày mai theo múi giờ thiết bị.
- builds_this_month.used/max/resets_at: null hiển thị Không giới hạn, không tính thành 0 lượt còn lại; max hữu hạn hiển thị đã dùng/tổng và số còn lại. Không hiển thị USD/cost hoặc tự bịa số lượt học/ngày. Trạng thái đang tải, lỗi và Thử lại có kiểm; không dùng dữ liệu 0 giả khi lỗi.
- Dải giới hạn nằm trong layout chat, cạnh hành động tạo tài liệu của thư viện và trong dialog tạo tài liệu, có giờ Việt Nam. shared_content_today.limited chỉ là thông báo nội dung mới tạm dừng, không suy ra tỷ lệ hay giờ từ trường không có. Trang tiếp tục giải thích cách đọc bài, quiz và thư viện có sẵn.
- Không khoá toàn bộ chat, tài liệu hoặc quiz chỉ vì limited; core quyết định cache/ngân hàng/daily_limit/tran_he_thong. Trang bài giảng giữ nguyên thông điệp/failure/retry W-08. Hạn tiền theo ngày vẫn tách documents_per_hour và 10 lượt trợ lý/phút; React không đặt lại cache, sinh, retry hoặc ngân sách lõi.
- Hook đọc usage gắn identity tài khoản + history entry, xoá snapshot cũ khi route đổi, abort và kiểm callback. Đăng xuất không nhận lại dữ liệu riêng về muộn. Khi lượt chat hiện hành cập nhật usage, phát tín hiệu không mang payload riêng để các dải cùng trang tải lại API; phản hồi lượt cũ vẫn qua guard W-09. Focus cửa sổ cũng tải lại.

Không sửa backend/query/usage-1, core Pha B, migration hoặc transport Vertex. Không làm lại quiz/tài liệu/thư viện, admission chung hay token callback W-10. Không thêm thư viện phụ thuộc. Hướng dẫn mở backend/frontend đúng worktree được bổ sung đầu [src/web/README.md](../src/web/README.md).

## RED → GREEN, guard và soát mã

Ca mới ở Usage.test.tsx dùng App thật/MemoryRouter với HTTP fake để kiểm ba trạng thái, ratio từ API, ngày/giờ Việt Nam từ timestamp Z, null/hữu hạn, retry không ratio giả, route/logout stale, dải và nội dung có sẵn, đồng bộ sau usage change. HTTP giả chỉ dùng kiểm React, không gọi chúng là bằng chứng PG.

usage-red: baseline main chưa có route/màn W-16, các assertion mới đỏ; log/JUnit giữ nguyên. focused-green1/2 còn thiếu setup progress/description của roadmap ở hai ca mở thư viện, đã bổ sung đúng DTO fixture, không giảm assertion/timeout. focused-green3 còn matcher giờ đặt lại gặp hai nội dung đúng trên trang hết trần; sửa kiểm mọi bản hiển thị đều đúng, không bỏ kiểm. focused-green4: 46 đạt; sau đồng bộ usage mới có 47, focused-green7: **48 đạt**, giữ nguyên hồi quy W-09/W-10.

Soát độc lập phát hiện điều kiện disabled cũ trong chat vẫn chặn request có thể dùng cache khi limited. Đã thêm ca `allows core to decide cache reuse under a limited learner quota instead of blocking the question`: chat-limit-red native 1 / assertion textbox disabled; bỏ riêng hai điều kiện quota ở textarea/send, giữ giới hạn request/session đang chạy và dải. GREEN cùng 48 ca. Người soát đọc lại commit 7829b589 xác nhận Required đã sửa, không có lỗi sản phẩm cụ thể khác trong phạm vi; không tự thay phán xét nghiệm thu điều phối.

scripts/w16_mutation_check.py đổi guard max===null thành nhánh số: test Không giới hạn phải đỏ bằng đúng một assertion, 0 setup error; byte nguồn được phục hồi trong finally trước cổng. mutation-null-final chạy trên **012abea**, receipt ghi source/mutated/restored SHA và native 1 của test, native 0 của driver xác nhận phép phá bị bắt. Không chạy mutation khi gate/server hoạt động.

## Browser thật, PostgreSQL và chi phí

scripts/w16_web_runtime.py tạo DB UUID riêng từ cấu hình test, migrations/head thật, compose backend hiện hành, model/Mailer/media giả và fake clock. Chỉ lấy dữ liệu phát triển theo hai manifest W-06, 3.145 bản chép thường được kiểm SHA nguồn/đích trong fixture-copy.json. Không đọc Pha B live/learner CLI, không seed DB phát triển, không liên kết/dọn dữ liệu.

Ledger có cost tổng hợp để projection/guard đi đúng code thật; **không là chi nhà cung cấp**. Fake transport chạy qua admission core (is_replay=False cho các model cần kiểm trần), trong khi provider/ADC/SMTP thật vẫn bị chặn. Không thay cấu hình giá/trần demo của chủ dự án. Browser kiểm max hữu hạn 3 và null bằng settings trong app/DB UUID riêng, không ghi vào env/DB phát triển.

Thử thật ở web: tỷ lệ/giờ/usage JSON, chat hạn ngày trả daily_limit và phát lại cùng intent không gọi model; bài cache ready; bài chưa có phát failure tran_he_thong qua SSE cùng nút Thử lại; quiz có sẵn và ngân hàng vẫn mở được. So sánh model call trước/sau bằng control của harness và SQL độc lập. Không sửa core để làm kiểm xanh. Kiểm browser dùng Playwright với Chrome thật; môi trường không cung cấp Chrome DevTools MCP. Bộ tee SSE và kiểm rejected promises tái dùng từ harness W-10 đã nhận, không quay lại body audit yếu.

### Các lượt phát triển được giữ

- Smoke1: seed bằng GET cache-only nên chưa có bài, assertion seed đỏ; sửa harness seed qua luồng stream giả, không đổi GET/gateway.
- Smoke2: require nhầm tên helper SSE khi đổi tên script; setup MODULE_NOT_FOUND, không là phản chứng chức năng.
- Smoke3: fake replay bỏ check chi nên không tái hiện cap; phát hiện và chuyển fake transport qua admission thật.
- Smoke4: lỗi trần là sự kiện SSE tạm thời, GET cache-only không lưu lỗi đó. Sửa kiểm đúng body SSE của luồng web, không sửa core cache.
- Smoke5: snapshot file:// chưa nhúng CSS nên inspector thấy trang không style. Dùng lại cách nhúng CSS/fonts từ DOM thật đã kiểm của W-10; không giảm luật inspector.
- Smoke6: native 0, 11 ảnh/11 Axe, cache/bank/HTTP daily_limit/replay 0 model mới đạt; đây là lượt phát triển trước source sạch cuối.
- Log ConnectionResetError WinError 10054 của asyncio khi Chrome/inspector đóng kết nối được giữ; không xoá log hoặc gọi đó là lời gọi model thật.

## Thiết kế và taste-skill

Dùng design-taste-frontend phần app screens, frontend-ui-engineering, TDD/ponytail/Git workflow/code-review. Nguồn là spec thiết kế mục Mức dùng, tokens.css và shell/HTML đã nhận trên main (mẫu chat W-09, nội dung W-10). Không có mẫu W-16 riêng trên main; bám yêu cầu vòng tỷ lệ + lượt dựng của spec, không chép nhánh preview chưa duyệt.

Bố cục đọc theo việc cần biết: mức hôm nay trước, lượt dựng tháng bên cạnh; hai khối phẳng với separator, không thêm KPI giả. Giữ Be Vietnam Pro, Artboard 24/28 trong dải logo 9–28, token màu sáng/tối, motion 120/200 ms, reduced-motion. Thanh progress không vẽ lặp dưới vòng tỷ lệ; vẫn có semantics cho trình đọc màn hình. Focus/keyboard/44px và ảnh 390/768/1280 được kiểm trên React thật. Taste inspector chạy app mode trên DOM đã xác thực, nhúng đúng CSS/font để snapshot file:// không đổi thiết kế. Không nhận thay W-23/Cloud Figma.

## Cổng cuối và bàn giao

Cổng đang chạy trên source 012abea, main nền 788b600, các tệp src/scripts đã commit và dirty paths phải rỗng. Log/JUnit/native/source SHA tại report/w16-react-evidence/gate-*-final, browser ở browser-final. Ảnh/video phát triển, fixture metadata và native thất bại tách khỏi ảnh browser bàn giao. Commit báo cáo sau đó chỉ bổ sung hồ sơ.

Chờ điều phối nghiệm thu/ghép W-16 React. **Chưa bắt đầu React W-04**: sau khi W-16 được nhận mới tạo work/w04-account-react, tmp/w04-account-react từ main mới, đọc hợp đồng backend c1f2fe9. Không tự nhận toàn W-04 hoàn tất hoặc sửa use case core.

### Browser cuối source 012abea

**Native 0, 303,08 giây**, source dirty paths rỗng. 12 cấu hình (3 viewport × 2 theme × reduced on/off), **66 ảnh và 66 lượt Axe**, 0 violation; 92 phép đo tương phản thủ công cho incomplete color-contrast, thấp nhất 5,8448:1. 225 phản hồi HTTP, 2 body SSE qua tee đầy đủ (complete=true); không rejected audit job/privacy failure/pageerror. HTTP raw còn hai lượt chat daily_limit + phát lại cùng intent; core không gọi assistant model thêm. Không lấy event terminal classifier của quiz/document làm phán xét lecture.

Đồng hồ và cost ledger là fixture; SQL độc lập có 4 documents, 2 quiz_attempt. Khi cả trần người học và dùng chung đã chạm, bài cache vẫn ready, ngân hàng quiz trả đề, lecture mới có failure tran_he_thong bằng đúng câu Việt W-08 và nút Thử lại. Ledger/model probe trước/sau: 50 row, lectureCalls=1, generatorCalls=1, documentCalls=4, assistantCalls=0, không tăng. DB UUID đã được runtime gỡ, serverThreadStopped=true, externalCostUsd=0.

Console: 2 phản hồi 401 lúc bootstrap, 1 ERR_FAILED chủ ý để kiểm retry, 66 cảnh báo font/CSP và 66 cảnh báo inline style/CSP của Axe. Giữ log WinError10054 khi đóng kết nối; không tắt CSP hoặc che log. Taste 0 FAIL/1 WARN panel-void (48px ở hàng 100%/1280). Soát thiết kế chỉ đọc xác nhận hàng/cột, font, notice và controls đọc được; không Required bố cục. Một ảnh 35%/390/sáng thường lệch vị trí cuộn so với ảnh reduced/tối, ghi đúng giới hạn ảnh này.

Reduced-motion được kiểm bằng emulateMedia thật và computed transitionDuration <=0,001 giây của vòng tỷ lệ ở 18 trạng thái reduced (3 tỷ lệ × 3 cỡ × 2 theme); không khẳng định toàn bộ animation được kiểm từ ảnh. Xem design-review.json và audit/runtime gốc.

Ảnh xem nhanh: [35%, 1280 sáng](w16-react-evidence/browser-final/usage-35-1280-light.png), [85%, 1280 sáng](w16-react-evidence/browser-final/usage-85-1280-light.png), [100%, 1280 sáng](w16-react-evidence/browser-final/usage-100-1280-light.png), [chat 390 tối/reduced](w16-react-evidence/browser-final/chat-limit-390-dark-reduced.png). Video owner/learner và JSON thật ở browser-final. Đây là nội dung giả dùng để kiểm web/PG thật, không phải kết quả chi nhà cung cấp thật.

Cổng React **229 test/native 0**, build native 0 cùng source 012abea; bundle 75 tệp được ghim SHA trước browser. Kết quả Python toàn repo được chốt sau native exit, không dùng kiểm tập trung thay cổng.

### Cổng Python đầu và bổ sung fixture

Lượt gate-python-final native 1: **2.823 đạt, 1 fail, 1 skip, 1 xfail**, 8 warning; fail là FileNotFoundError của test W-15 candidate tại tmp/w15-candidate/input.pdf. Đây không là RED chức năng W-16. Worktree sáu sách theo manifest chưa có tệp train riêng mà test W-15 đã ghép yêu cầu.

Dùng đúng metadata report/w15-evidence/candidate.json đã nhận: nguồn document-data/train/nong-nghiep/rau-thuy-canh.pdf, SHA-256 1f019766e74a747d293c15ad5bc86b2ea90420b49a8437cf27c1f6805656a627. Chép thường một tệp 1.054.520 byte vào tmp/w15-candidate/input.pdf, kiểm nguồn/đích/hash/nlink=1, không ghi đè tệp khác hash, không đọc heldout hoặc chạy operator/model. Receipt w15-candidate-copy.json; PDF không vào Git. Không sửa test, W-15 source hay metadata của làn khác.

candidate-control: đúng test lỗi đã đạt/native 0, 14,73 giây pytest. Sau đó chạy lại toàn PG qua runner với basetemp mới tmp/cong-w16-react-final-2; không chạy hai full gate đồng thời. Source vẫn 012abea, không cần chạy lại React/build/browser vì chỉ bổ sung dữ liệu thử mà bộ browser không dùng. Giữ đầy đủ native/JUnit/lệnh/SHA của cả lượt đỏ lẫn lượt lại.

Kiểm timezone-la-control có TZ=America/Los_Angeles: **9 React đạt**, giờ Việt Nam vẫn đúng; không sửa source để chạy ca này.

### Kết quả chốt

**gate-python-repeat: 2.824 pass, 1 Cloudinary live skip, 1 replay answer-2 xfail có sẵn, 8 warning; native 0**, pytest 936,33 giây, wrapper 948,42 giây. Không thêm skip/xfail hoặc sửa assertion. Cùng source 012abea: React 229 pass/native 0, build native 0, browser native 0; một full PG tại một thời điểm. Main kiểm lại trước đóng gói vẫn **788b600**. Có SHA của 783 tệp src/scripts và 75 tệp bundle, đều khớp; mutation đã phục hồi đúng byte. Không có mã src/scripts sửa sau cổng.

Bàn giao local để điều phối soát/nghiệm thu, chưa ghép/push main. Không có câu hỏi chức năng còn mở; lưu ý thị giác/inspector, log kết nối và lượt thiếu fixture được giữ đúng phạm vi ở trên. Tổng lời gọi nhà cung cấp thật: 0, chi ngoài: 0 USD. W-04 React vẫn chưa mở theo thứ tự giao việc.

Đóng gói: raw-text.zip giữ 245 tệp text nguyên gốc (2.556.736 byte ZIP), 17 log/XML/text bản đọc Git được chuẩn hoá UTF-8/whitespace và có receipt SHA trước/sau; JSON/SSE/ảnh/video không bị sửa byte. Metadata SHA bản chép lịch sử là byte gốc trước chuẩn hoá. files-sha256.json băm bộ hồ sơ hiện hành; PDF/basetemp/tệp ngoài phạm vi không vào commit.
