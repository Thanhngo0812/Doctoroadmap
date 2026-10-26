# W-10 — sửa hai Required R7, 2026-10-26

Nhánh: `work/w10-quiz-documents`, worktree: `tmp/w10-quiz-documents`. Bản vá chức năng: `ea5728ba8bec144c42ea742c72753f10996d701b`. Sau các sửa harness, nhận main local `163917ca7f0384ef383dd26acab2380f06efef6f` bằng merge `1fc0f553bec808241388b722fa2c10a1c6ead33d`; đây là mốc nguồn của cổng bàn giao mới. Main trước đó `4442666` đã được nhận bằng `7e7476f`. Không tự ghép/push main, sửa vé/kế hoạch/handoff hay mở React W-16 trước nghiệm thu W-10.

## Hai sửa chức năng

**R-W10-1 — hạn tần suất dùng chung.** LearningGateway gắn DocumentRequests theo engine/settings/clock của runtime. Button và công cụ make_document cùng gọi admission PostgreSQL theo actor, xuyên khoá, trước sinh tài liệu. Giữ policy hiện hành: 10 yêu cầu trong cửa sổ một giờ; giao dịch dùng advisory lock theo người và đếm lại sau khi lấy lock. Không thêm bộ đếm khác hoặc chép thuật toán sinh/cache/retry/ngân sách của core. Client turn được phát lại không tạo admission lần hai.

WebAssistantUseCase là adapter web mỏng: dịch WebError rate_limited tại hook _tool hiện hành thành kết quả công cụ có code/message/retry_after; lỗi khác giữ nguyên. Đây là phụ thuộc vào hook core, được kiểm bằng HTTP/PG/core thật. Lượt bị chặn không gọi model tài liệu, không có row tài liệu ready. DTO answer-3 chỉ thêm cảnh báo nghiệp vụ document_rate_limited; UI dùng câu Việt cố định và đọc lại được sau reload. Không đưa raw tools/args, validation hay định danh media riêng ra DTO/SSE, không sửa answer_md. Usage-1 và hạn ngày/chi phí giữ nguyên.

**R-W10-2 — phản hồi thuộc đúng lượt nộp.** QuizPage tạo token mỗi request, gắn cid/aid/location.key. useLayoutEffect vô hiệu hoá token khi chuyển history/attempt/course hoặc unmount. Success/error/finally/focus đều kiểm token; phản hồi cũ không ghi màn khác, không mở khoá request mới. POST phía server vẫn hoàn tất; Back/Forward đọc lại kết quả bền ở đúng quiz, giữ nguyên nộp nguyên tử/idempotent.

Không viết lại ba lát W-10 đã được soát. Mã lõi/transport được nhận nguyên từ main (SA-61); bản vá W-10 không sửa use case Pha B, migration hoặc policy usage.

## RED → GREEN và các assertion

| Bằng chứng | RED đúng hành vi cũ | GREEN / mở rộng |
|---|---|---|
| rate-origin | 1 assertion fail, 0 setup error; model/rows 10→11, bucket vẫn 10 | rate-origin-green1; physical-lock-green: 5 test đạt |
| late-submit | 1 assertion fail, 9 control pass | late-submit-green1: 10 đạt; submit-controls-green2: 33 React đạt |
| notice backend/UI | tool business error đã đúng nhưng thiếu cảnh báo công khai; test thất bại | cảnh báo final/history và UI được kiểm trong cổng |
| bộ kiểm SSE | terminal rỗng hoặc DTO chỉ có contract_version đều bị test RED bắt | kiểm JSON, required/types/nested theo public OpenAPI; payload thật đạt |

Helper điều phối được nhận riêng vào suite, không lấy mã sửa từ nhánh review. Không giảm assertion/timeout, thêm skip hoặc tính lượt thiếu import w07 của helper làm RED.

Các assertion backend nằm trong `src/web/backend/tests/test_content_admission_w10.py`: button→assistant, assistant→button, replay client_turn_id, hai khoá cùng người, người khác tách bucket và forged owner. Hai runtime độc lập tranh lượt cuối: đúng một thành công; quan sát số admission, model call và row ready. Ca giữ advisory lock bằng connection thứ nhất quan sát connection thứ hai chờ Lock qua pg_stat_activity, lấp suất cuối rồi commit; connection chờ phải kiểm lại và từ chối, không gọi model.

React giữ ca coordinator và kiểm thêm success/network/401/not_found về muộn trong lúc attempt mới pending; old finally không mở khoá mới; Back/Forward và đổi course dù aid giống nhau; giữ các ca mất phản hồi/idempotency/lựa chọn khi stream/keyboard.

**Mutation:** 19 phép phá (12 cũ + 7 mới) thực thi tuần tự trên source `9bb90d9c10c125bbdf98e65884fe6a89a26dd57c`, mỗi phép native 1 với assertion fail, không setup error; phục hồi đúng byte trước cổng. Xem mutations-existing-final2, mutations-required-final2 và mutation-handoff-source-proof.json. Không gán lại các lượt này thành chạy trên HEAD mới; tệp sản phẩm đích vẫn được đối chiếu SHA-256. Không chạy mutation cùng gate/server.

## Harness và tính đầy đủ bằng chứng

Browser tee SSE trong fetch; nhánh ghi được chuyển/kiểm ở host trước enqueue sang ứng dụng. Chuyển URL sau final không làm mất body. Mọi original promise trong pending được kiểm kết quả allSettled; catch sớm chỉ ngăn unhandled rejection làm mất hồ sơ. Native 0 chỉ được nhận khi không còn rejected audit job và đủ body.

Terminal phải có data JSON, đủ required field và đúng kiểu theo public OpenAPI; đây không phải trình kiểm toàn bộ JSON Schema, các ràng buộc khác vẫn do Pydantic runtime kiểm. Ngoại lệ có tên duy nhất: stream POST documents bị huỷ chủ ý ở bước disconnect-document, có cancelled và AbortError. Không dùng event final rỗng làm bằng chứng payload an toàn.

Kiểm submit chậm bằng giữ fetch completion sau khi HTTP thật đã chấm/commit PostgreSQL; điều hướng Back/Forward thật, không mock API/result. SQL đọc bằng connection độc lập. Toàn bộ model/Mailer/media giả, PostgreSQL UUID riêng, không gửi thư/upload/gọi Gemini hoặc embedding thật. Chi phí ngoài: 0 USD.

## Giao diện, taste skill và thiết kế

Áp dụng design-taste-frontend phần app screens và frontend-ui-engineering. Giữ khung/nhịp chữ của mẫu đã nhận trên main; Be Vietnam Pro, logo Artboard 9–28, token sáng/tối, motion 120/200 ms và reduced-motion. Notice giới hạn ngắn nằm trong chat, không thêm dialog hoặc CTA cạnh tranh. Tham khảo HTML/CSS/token đã ghép ở design/preview (W-10 quiz), không chép cả nhánh thiết kế chưa duyệt hoặc nhận W-23 thay nhóm thiết kế.

Browser kiểm thật 390/768/1280, sáng/tối, giảm chuyển động theo media preference, keyboard/focus, vùng bấm và nhìn ảnh. Taste inspector chạy app mode trên snapshot DOM đã xác thực ở ba cỡ; warning riêng về family math phải ghi đúng, không gọi là Be Vietnam Pro chưa tải. Axe chỉ được tuyên bố ở các ảnh có entry accessibility trong audit; ảnh khác có kiểm layout/interaction theo harness.

## Lịch sử kiểm, không dùng thay đợt mới

Giữ report/w10-evidence và toàn bộ dữ liệu/worktree/ZIP cũ. Trong R7, các lượt phát triển giữ log/native/audit tại history; ảnh/video phát triển vẫn nguyên trên máy và được ignore, tách khỏi ảnh bàn giao browser-r7-main.

- Smoke1: route.fulfill trễ làm driver lỗi trước khi ghi audit; native 1, DB được đóng.
- Smoke2: rejected route được lưu và guard pendingRejections bắt native 1. Không dùng lượt này làm đạt cuối.
- Smoke3/4: đổi driver giữ fetch completion và siết classifier, native 0. Smoke4: 5 body SSE, 4 terminal hợp lệ và 1 AbortError chủ ý.
- mutations-r7-final: runpy thiếu scripts trong sys.path, setup ModuleNotFoundError; không tính là phép phá. final2 dùng đúng import và hoàn tất 19 phép phá.
- admission-green2: ScriptedModel hết script giữa các phiên. Giữ log; cấp script mới mỗi phiên, không giảm assertion. admission-green3/physical-lock-green xanh.
- React đầu tại 9bb90d9: lỗi setup cũ Courses.test.tsx, resolveList chưa có khi test thấy loading. Không sửa assertion/code/timeout. Kiểm riêng 17 control rồi toàn bộ 219 React trên cùng mã đạt; giữ cả native.
- Browser r7-final: driver bấm theme bị sheet mobile che. r7-delivery: helper chưa nhận vùng learning-chat-panel nên eligible=false. Sửa driver/nhận vùng, giữ phép đo ≥4,5:1 và chống bị che; không đổi CSS ứng dụng để vượt kiểm.
- Mốc 1ea62bb: 2.751 Python đạt, 1 skip/1 xfail có sẵn, 8 warning; 219 React/build đạt. Browser: 12 cấu hình, 96 ảnh, 65 Axe, 250 HTTP, 27 SSE/0 body thiếu/0 rejected; 26 terminal và 1 huỷ chủ ý. Đây là checkpoint trước main mới, không thay cổng source 1fc0f55.

## Cổng sau nhận main — đang chốt native

Log/JUnit/lệnh/native và source SHA trong report/w10-r7-evidence/gate-*-r7-main; browser mới trong browser-r7-main và browser-r7-main-run. Chỉ commit đường dẫn W-10. Tệp SQL tự sinh dưới report/w15-evidence và report/w25-evidence được giữ local, chép riêng vào gói W-10 với SHA nguồn/đích, không stage tệp của vé khác.

Chờ điều phối soát/nghiệm thu/ghép W-10; sau đó mới mở nhánh/worktree React W-16. Không tự xác nhận toàn W-16 đạt từ backend.

### Browser bàn giao source 1fc0f55

Native 0, 395,0 giây; 12 cấu hình (390/768/1280 × sáng/tối × chuyển động thường/giảm), 96 ảnh, 3 video. Có 65 lượt Axe trên các màn được ghi đích danh trong audit, 0 violation; 73 phép đo tương phản thủ công tại các nút/text cần bổ sung, thấp nhất 5,8448:1. Không có overflow/vùng bấm lỗi trong các assertion của harness. Đã mở soát trực tiếp ba ảnh 1280 sáng, 768 sáng và notice 390 tối; xem visual-review.json. Không tuyên bố toàn bộ 96 ảnh đều chạy Axe.

250 phản hồi HTTP, 27 body SSE đầy đủ: 26 terminal có payload hợp lệ, 1 huỷ chủ ý khi disconnect tài liệu. Không missing body, rejected audit job, privacy failure hoặc pageerror. Console ghi 3 phản hồi 401, 1 phản hồi 404 ở ca quyền, 1 ERR_FAILED chủ ý và 65 cảnh báo font/CSP + 65 cảnh báo inline style/CSP do Axe; không gọi console là trống. Taste inspector có 1 WARN generic family math ở ba cỡ, không FAIL; Be Vietnam Pro và KaTeX_Main có trong fontsLoaded. Không tắt CSP hay guard tương phản để làm xanh.

SQL độc lập: 28 documents, 14 quiz_attempt, 6 progress của người học thử; 14 bản kết quả nộp được kiểm. Usage giả có row quiz_gen/quiz_verify/assistant/document/document_validation, USD đều 0. Ca 10 button rồi chat: 0 tài liệu sinh thêm, model-call count giữ nguyên và notice tồn tại sau reload. Ca nộp chậm: phản hồi cũ bị bỏ qua khi lượt mới pending; Forward phục hồi kết quả đã lưu đúng quiz. DB UUID thử đã được runtime gỡ và server đã dừng sau lượt kiểm.

Ảnh xem nhanh: [tài liệu 1280 sáng](w10-r7-evidence/browser-r7-main/document-view-1280-light.png), [notice 390 tối](w10-r7-evidence/browser-r7-main/assistant-hour-limit-390-dark-reduced.png), [dialog 768 sáng](w10-r7-evidence/browser-r7-main/document-create-768-light.png). Video tương tác và nguyên JSON/SQL nằm trong [bộ browser cuối](w10-r7-evidence/browser-r7-main/). Các câu/nội dung sinh trong ảnh là fixture giả, không là kết quả mô hình thật.

### Native cổng toàn repo và mốc main còn chờ

Source **1fc0f553bec808241388b722fa2c10a1c6ead33d**: **2.775 Python đạt, 1 skip, 1 xfail kế thừa, 8 warning**, native 0 (pytest 1.102,31 giây; thời gian wrapper trong exit.json). **219 React đạt, build native 0**, cùng source. Skip là Cloudinary live; xfail là replay answer-2 cũ đã ghi SA-66, không tạo lại bằng lời gọi có tiền. Không thêm skip/xfail. Đối chiếu toàn bộ source SHA trong cổng với tệp hiện hành; bundle 75 tệp khớp main-build-manifest.json. Commit hồ sơ sau mốc này không đổi src/scripts.

Trong lúc cổng chạy, main thêm 1777a5c/8c7aab4, chỉ đổi hai tài liệu đánh giá Pha A, không đổi mã/fixture. Đã gửi lựa chọn cho chủ dự án: chốt nền 163917c cho đợt này hoặc nhận 8c7aab4 và chạy lại. **Chưa nhận câu trả lời, không tự coi đã được miễn mục 3.5 quy trình nhánh.** Hồ sơ ghi đúng cổng đã chạy trên nền 163917c, không tuyên bố đã chạy trên main 8c7aab4. Đây là điểm còn chờ trước đề nghị ghép cuối; hai Required đã có bản vá và bằng chứng hoàn chỉnh.

Không có câu hỏi chức năng mới. Người điều phối quyết định nghiệm thu; chưa mở React W-16. Các log thất bại, nguồn mutation cũ, ảnh/video cũ và SQL ngoài phạm vi vẫn được giữ, không dọn worktree hay dữ liệu.

Ghi chú đóng gói: raw-text ZIP giữ 544 tệp nguyên gốc, 103 log/XML trong bản đọc Git được chuẩn hoá whitespace và có SHA trước/sau. .gitattributes cục bộ giữ byte JSON/ảnh/video. Lượt kiểm whitespace ban đầu coi CR của JSON CRLF là khoảng trắng cuối dòng; shell vẫn tạo commit hồ sơ 7051a6b. Đã sửa khai báo nhận CRLF, giữ các kiểm khoảng trắng chuẩn và kiểm lại toàn diff hồ sơ native 0; không đổi byte payload hoặc src/scripts. Xem packaging-checks.json.
