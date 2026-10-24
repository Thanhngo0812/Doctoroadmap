# W-08 — sửa nhãn tiến độ và che tự kiểm tra — 2026-10-24

## Phạm vi và mốc

Tiếp nhánh `work/w08-lecture`, worktree `tmp/w08-lecture`; giữ mốc cũ `89122f6` và toàn bộ bằng chứng ngày 23. Đợt đầu nhận main `a71a90bc19f898e088fdc32ab0b0439d9dd4087c` tại merge `1d34795b76ecb2ad59a2b0a9754bb53edebae5ef`, có SA-66 `ba4350f` và SA-69 `973fa99`. Đợt cuối đã nhận **SA-70 ghép `5188908`**, main nền **`5936a5d91b6c3979f1918b33ce330403414b776f`**. Không sửa core SA, quyền/gateway/Markdown/media, migration, vé/kế hoạch/handoff hoặc main.

Nguồn sửa hai Required: `4862411eb614882130a611e815856747c6a8132d`. **Nguồn cổng cuối `b4136987668c3fb822ea374f399b947064ce7f18`**, sau merge SA-70 `f4ddfce`, preload test `1325ee5`, nhận tài liệu main và sửa cách thu SSE `b413698`. Commit hồ sơ tiếp theo chỉ thêm báo cáo/bằng chứng. Mốc/lệnh/hash ở [đợt cuối sau SA-70](w08-evidence/required3-2026-10-24/); hai thư mục `required-2026-10-24`/`required2-2026-10-24` giữ làm lịch sử.

## Hai lỗi và cách sửa

- **R-W08-1:** `Lesson` nhận `progress.nodes` hiện tại từ trang; Cần biết trước/Tiếp theo đọc cùng nguồn với checkbox và bộ đếm. Khi lưu lỗi, rollback hiện có đổi lại cả nhãn. Tiến độ không nằm trong dependency sinh bài, nên không tải/sinh lại bài chỉ để đổi nhãn.
- **R-W08-2:** biểu thức nhận tiêu đề khi stream khớp `lecture3._HEADING`: đầu dòng có thể thụt space/tab, 2–4 dấu `#`, khoảng trắng tùy chọn, tên không phân biệt hoa/thường, đuôi có space/tab/dấu `:`. Chỉ che khi đang stream; final vẫn dùng nguyên `body_md` và trường `self_check` của core. Không bịa câu hỏi hoặc làm mất phần cuối nếu core trả `self_check: null`.

Mã sản phẩm chỉ đổi `Learning.tsx`. Các tệp còn lại là ca hồi quy và harness kiểm hai lỗi.

## RED → GREEN và phép phá

Ban đầu nhận nguyên byte helper của điều phối thành `src/web/frontend/src/Learning.review-repro.test.tsx`; [nguồn/hash](w08-evidence/required-2026-10-24/repro-input.json). Sau khi gặp lại timeout do nạp module, đổi riêng setup sang import tĩnh renderer thật; [đối chiếu toàn bộ thân test giữ nguyên](w08-evidence/required3-2026-10-24/review-test-preservation.json). Không giảm assertion/timeout, không mock renderer.

- `repro-red` đầu tiên bị timeout hook nạp module thật trước khi test chạy: 17 case bị skip và 1 hook failure; **không tính đây là chứng minh hai lỗi**. Giữ log/JUnit gốc.
- `repro-red2` chạy đúng `Learning.tsx` của commit cũ, rồi phục hồi nguyên byte bản sửa: **6 assertion fail, 11 control pass, 0 error/skip**. [JUnit RED](w08-evidence/required-2026-10-24/repro-red2.xml).
- `repro-green`: toàn bộ 17 case đạt. [JUnit GREEN](w08-evidence/required-2026-10-24/repro-green.xml).
- Bổ sung hai ca deferred save success/rollback: quan sát đồng thời checkbox, bộ đếm, nhãn tiên quyết/tiếp theo và số HTTP lecture không tăng. Bốn ca final-null dùng tiêu đề hợp lệ nhưng thiếu khuôn hỏi/đáp: che trong stream, khôi phục đầy đủ ở final. [Kiểm tập trung](w08-evidence/required-2026-10-24/focused-green.xml).
- Chạy tuần tự **7 phép phá UI**: 5 guard trước đây và 2 guard Required mới; từng bản sai native 1, có assertion fail, 0 setup error, phục hồi cùng SHA. Đã chạy lại sau thay setup test và nhận SA-70: [kết quả cuối](w08-evidence/mutations-required2-20261024/results.json); lượt trước giữ ở `mutations-required-20261024`. 8 guard backend được giữ từ lượt đã đạt, đối chiếu byte nguồn không đổi; không chạy lại phần đã được soát chỉ để đổi số. [Đối chiếu 15 guard với nguồn cuối](w08-evidence/required3-2026-10-24/mutation-source-match.json).
- Đợt đầu trước SA-70: **2.454 Python đạt, 4 lỗi so khớp lời nhắc/spec, 1 skip và 1 xfail có sẵn**, native 1. Các lỗi thuộc test so lời nhắc của SA-64/66/69 với spec đã đi trước code; không sửa core/test lõi để xanh. React 181 đạt, build/browser native 0 (109 ảnh/17 Axe/345 trao đổi HTTP). Sau khi Claude ghép SA-70, nhận main và chạy lại riêng toàn bộ cổng; không lấy browser trước SA-70 thay kết quả cuối.
- Lượt focused đầu sau SA-70 bị timeout hook import renderer ở `Learning.test.tsx`; 17 ca của helper điều phối đạt, 16 ca tệp kia chưa chạy. Thay preload async trong hook bằng import tĩnh renderer thật ở hai suite; mọi thân test/assertion/timeout giữ nguyên. [33 ca sau sửa setup đạt](w08-evidence/required2-2026-10-24/sa70-focused-green.xml).
- Đợt `required2` sau SA-70: **2.511 Python đạt, 1 skip và 1 xfail có sẵn**, native 0; 181 React/build đạt. Browser dừng ở phép thu raw SSE mới vì DevTools không giữ body cho `response.text()` (103 ảnh đã thu/17 Axe); đây là lỗi collector, không tính lượt này là browser cuối đạt. Sửa bằng `Response.clone().text()` trên phản hồi fetch thật, trả nguyên phản hồi cho ứng dụng, không thay request/response hoặc dựng dữ liệu giả. [Smoke collector đạt](w08-evidence/required3-2026-10-24/browser-smoke-command.json): 21 ảnh/5 Axe ở một cấu hình, không thay ma trận đầy đủ.
- Guard đọc delta mới được lấy đúng đoạn mã của harness để thử với một SSE fixture cố ý chứa phần tự kiểm tra: native 1 và `ERR_ASSERTION`. [Phản ví dụ](w08-evidence/required3-2026-10-24/http-wire-counterexample.json) được ghi rõ là dữ liệu tổng hợp, không gọi là capture HTTP thật. Việc replay audit cũ không có body trước đó chỉ gặp TypeError, không được tính là guard đã bắt lỗi.

## Thiết kế đã tham khảo

Tiếp tục áp dụng `design-taste-frontend` cho app screen, hướng `editorial-greeting` đã chọn ở W-08, cùng `frontend-ui-engineering` và TDD. Tham khảo `tmp/w24-figma-evidence/design/preview/w08_lecture_screens.html` trên nhánh thiết kế riêng và `design/preview/` của main. Chọn các phần đúng spec: bố cục bài đọc, đáp án gập, tiên quyết/tiếp theo, token font/màu, vùng bấm 44 px và giảm chuyển động. Không nhập nhánh W-24 hoặc chép cây React; không lấy emoji/nút ngoài phạm vi trong preview làm tính năng mới. Giữ CourseShell/logo Artboard 24/28, Be Vietnam Pro và token đã duyệt. [Nguồn thiết kế và quyết định áp dụng](w08-evidence/required-2026-10-24/design-reference.json).

## Cổng và bằng chứng cuối

**Cổng cuối trên `b413698` đã xanh toàn bộ, native exit 0:**

- Python/PostgreSQL toàn repo: **2.511 đạt, 1 skip Cloudinary live, 1 xfail replay answer-2 có sẵn trên main**, 8 warning thư viện. Không thêm skip/xfail hoặc hạ assertion trong vé web. [JUnit](w08-evidence/required3-2026-10-24/python.xml), [lệnh/native](w08-evidence/required3-2026-10-24/python-command.json).
- React: **181/181 đạt**; build native 0. [JUnit](w08-evidence/required3-2026-10-24/react.xml), [build](w08-evidence/required3-2026-10-24/build.log).
- Browser thật: **12 cấu hình, 109 ảnh, 17 lượt Axe có phạm vi, 348 trao đổi HTTP và 5 stream SSE thu byte thật**, native 0. [Audit](w08-evidence/browser-required3-20261024/audit.json), [runtime/SQL](w08-evidence/browser-required3-20261024/runtime.json), video [learner](w08-evidence/browser-required3-20261024/learner.webm)/[owner](w08-evidence/browser-required3-20261024/owner.webm). Không có lỗi console/page/network ngoài dự kiến.
- Axe: 0 violation, 0 incomplete chưa soát; 8 glyph KaTeX ngắn được đo tương phản độc lập và thử cùng màu nền để chứng minh guard bắt lỗi. **Không gọi cả 109 ảnh đều đã Axe**: 17 lượt ở 1280 gồm module/ready/source/failure ở hai theme/hai motion, cộng rollback của bài đang mở. Inspector còn WARN generic font `math` của MathML, không FAIL; các font Be Vietnam Pro/KaTeX thực đã tải.
- SQL qua engine độc lập xác nhận B `learned` sau lưu, vẫn `learned` khi bỏ dấu thất bại/rollback, rồi `not_learned` sau bỏ dấu thành công; số request lecture và fake model không tăng. Usage giả có **35 hàng/3.500 input token giả, fake ledger 0 USD**; provider calls 0. Sau gỡ thành viên, request kế tiếp bị chặn và dữ liệu học riêng còn nguyên.
- [Kết quả ghim nguồn](w08-evidence/required3-2026-10-24/gate-results.json), [ánh xạ assertion](w08-evidence/required3-2026-10-24/invariant-map.json), [đối chiếu blob Git](w08-evidence/required3-2026-10-24/source-blob-manifest.json), [kiểm DB UUID/cổng sau chạy](w08-evidence/required3-2026-10-24/cleanup-check.json).

Cổng từ gốc worktree, PostgreSQL thật, provider giả, basetemp mới:

```powershell
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe scripts/w05_run_tests.py -o addopts= -q --basetemp=tmp/w08-required-20261024-3 --junitxml=report/w08-evidence/required3-2026-10-24/python.xml
npm.cmd --prefix src/web/frontend test -- --pool=threads --maxWorkers=1 --reporter=junit --outputFile=../../../report/w08-evidence/required3-2026-10-24/react.xml
npm.cmd --prefix src/web/frontend run build
$env:W08_EVIDENCE_RUN = 'browser-required3-20261024'
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe -X utf8 scripts/w08_web_runtime.py
```

Harness mở DB UUID riêng, actual Lecture3UseCase/HTTP/SSE/auth/CSRF/PG; model/Mailer/MediaStore giả, render trang PDF fixture local. Đã bổ sung đọc tiến độ qua engine SQL độc lập cho thao tác đánh dấu B, bỏ dấu lỗi/rollback và bỏ dấu thành công khi vẫn đọc A; số request lecture và lượt fake model không tăng. Năm dạng tiêu đề mới qua HTTP/core/React giữ đáp án ẩn trước final, gập sau final và mở được theo yêu cầu; final không tách được vẫn giữ nguyên phần cuối. Sau SA-70, harness còn phân tích raw HTTP/SSE: nối các delta đúng bằng phần chính, không chứa tiêu đề/câu hỏi/đáp án; không dùng việc React che chữ làm bằng chứng rằng HTTP cũng an toàn. Các test React vẫn tự đưa delta đầy đủ để bộ che phía web luôn được kiểm, dù core mới đã chặn từ trước.

Đã mở xem ảnh thật [B lưu thành công](w08-evidence/browser-required3-20261024/related-saved-1280-dark-reduced.png), [B rollback](w08-evidence/browser-required3-20261024/related-rollback-1280-dark-reduced.png), [mobile tối](w08-evidence/browser-required3-20261024/ready-390-dark-reduced.png), [viewer 768](w08-evidence/browser-required3-20261024/source-768-light.png) và [final không tách được](w08-evidence/browser-required3-20261024/unsplit-final-1280-dark-reduced.png). Nhãn/bộ đếm/checkbox nhất quán, lỗi sidebar xuống dòng, cột đọc không tràn. Ảnh năm tiêu đề là trạng thái **sau khi chủ động mở đáp án**; việc ẩn trước final/gập sau final được kiểm trong audit/video, không suy từ ảnh đó. [Quan sát thị giác](w08-evidence/required3-2026-10-24/visual-review.json).

Collector dùng bản sao phản hồi fetch thật để vượt giới hạn lấy SSE body của DevTools; không mock response. Nhánh đọc thứ hai là instrumentation kiểm thử, nên bằng chứng SSE disconnect hoàn tất cache dựa vào ca direct HTTP/PostgreSQL riêng, không suy từ browser đã gắn collector. Log Windows Proactor `ConnectionResetError` khi đóng kết nối và warning grace shutdown vẫn được giữ; native browser 0, thread dừng và DB UUID được gỡ. Ảnh/video đợt phát triển giữ nguyên local theo [hash](w08-evidence/required3-2026-10-24/historical-browser-assets.json), không đưa các bản trùng vào Git.

## Giới hạn và bước tiếp

Chi ngoài 0 USD, không Gemini/embedding/SMTP/Cloudinary thật. Nội dung giả không chứng minh chất lượng model thật. Các cảnh báo/thất bại phát triển được giữ đúng phạm vi; ảnh/video và dữ liệu học của các lượt cũ không bị dọn.

Chờ điều phối soát/ghép W-08 rồi mở worktree W-09 mới từ main đã ghép. W-09 theo ADR 0026/answer-3 và mục 8 spec trợ lý, nhận SA-66/69/70; không vá scope ở web, artifact từ sự kiện có cấu trúc, focus lecture cache-only, giới hạn tỷ lệ/ngày và 10 lượt/phút. Nhóm web không sửa lõi. W-10 chờ mốc document-3/quiz-3 được Claude nghiệm thu. Không tự ghép main hoặc đóng vé.
