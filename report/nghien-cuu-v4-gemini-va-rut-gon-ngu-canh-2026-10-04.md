# Nghiên cứu v4: Gemini (giá, giới hạn, cache, Batch/Flex, structured output), rút gọn ngữ cảnh và độ lệch vị trí

Ngày 2026-10-04. Người làm: Claude. Báo cáo trả lời sáu câu hỏi phục vụ nguyên tắc số một của v4: giảm phút/cuốn và USD/cuốn mà
không hạ chất lượng. Báo cáo kiểm lại hai báo cáo trước là [nghiên cứu song song cao (2026-10-02)](nghien-cuu-song-song-cao-2026-10-02.md)
và [nghiên cứu v4 về tiền và thời gian (2026-10-04)](nghien-cuu-v4-chi-phi-thoi-gian-2026-10-04.md). Phần đối chiếu nằm ở mục
"Hệ quả cho v4".

**Cách làm.** Mọi trang của Google được tải và đọc trực tiếp ngày 2026-10-04; ngày "Last updated" của từng trang ghi ở mục Nguồn. Bài báo
được đọc trên arXiv (tóm tắt và toàn văn PDF), số liệu lấy từ chính bài. Hai phép đếm trên sổ chi của dự án dùng một script đọc tệp JSON,
không chạy mã dự án, không gọi API. Không đưa nội dung giáo trình hay dữ liệu dự án vào công cụ tìm kiếm. Chỗ nào tài liệu không nói rõ,
hoặc chỉ thấy ở nguồn thứ cấp, được ghi "chưa xác nhận".

**Tên gọi.** Tài liệu Vertex AI nay mang tên *Gemini Enterprise Agent Platform*. Các URL `docs.cloud.google.com/vertex-ai/...` cũ chuyển
hướng 301 sang URL mới. Báo cáo vẫn gọi là "Vertex" cho liền mạch với các báo cáo trước.

## Tóm tắt

Bảy phát hiện chính, xếp theo mức ảnh hưởng tới v4:

1. **Giá đã khoá trong mã vẫn đúng, nhưng mô hình có hạn dùng.** `gemini-3.1-flash-lite` giá 0,25 USD cho 1 triệu token vào và 1,50 USD
   cho 1 triệu token ra, như nhau trên Developer API và Vertex (endpoint global). Batch và Flex đều bằng một nửa. Google ghi ngày tắt sớm
   nhất của 3.1 Flash-Lite trên Developer API là 2027-05-07 và khuyên chuyển sang `gemini-3.5-flash-lite` (0,30/2,50 USD). Với hồ sơ token
   hiện tại, mô hình thay thế đắt hơn khoảng 31% mỗi lời gọi.
2. **Developer API có hai trần chi, không phải một.** Trần thứ nhất tính theo 10 phút trượt (10/50/200 USD ở bậc 1/2/3, có áp dụng hay không
   tuỳ tài khoản). Trần thứ hai tính theo tháng cho cả tài khoản thanh toán (250/2.000/20.000–100.000+ USD). Ở bậc 1, 250 USD/tháng chỉ đủ
   4 cuốn cỡ doc-4 theo giá v3, khoảng 7 cuốn sau hỏi lười. RPM/TPM/RPD theo mô hình không in trên trang, phải xem trong AI Studio. Credit
   chào mừng 300 USD không trả được Developer API; tài khoản mới phải Prepay.
3. **Cache không áp dụng được cho pass phụ.** Ngưỡng tối thiểu của họ Gemini 3 là 4.096 token, lớn hơn cả lời gọi pass phụ (khoảng 3.280
   token), chứ không riêng phần chung 490 token. Sổ chi v3-r12 xác nhận: 0 lần trúng cache trong 26.992 lời gọi dưới 4.048 token. Đổi thứ tự
   prompt không giải quyết được; chỉ đổi hẳn thiết kế hồ sơ mới có cơ hội.
4. **Batch và Flex cùng rẻ 50% nhưng hợp hai việc khác nhau.** Batch là job bất đồng bộ, mục tiêu 24 giờ, hợp việc nền. Ở bậc 1 Developer
   API, Batch chỉ cho xếp 10 triệu token, ít hơn một pass phụ doc-4. Flex (Preview) là gọi đồng bộ, độ trễ mục tiêu 1–15 phút, có thể bị đẩy
   ra (503) và vẫn tính vào RPM/TPM thường. Flex là ứng viên cho trường hợp người dùng chờ vài chục phút, nhưng chưa có số đo độ trễ thật.
5. **Structured output chỉ bảo đảm cú pháp.** Tài liệu nói rõ JSON sẽ đúng cú pháp nhưng giá trị không chắc đúng nghĩa. Vì vậy 12% cặp bị
   hoãn ở doc-4 nhiều khả năng là lỗi nghĩa hoặc thiếu trường (schema pass phụ chỉ bắt buộc `pair_id`, `decision`, `flags`); cần đọc nhật ký
   để xác nhận. Các phản hồi đó vẫn bị tính tiền. Vertex ghi schema tính vào giới hạn token vào; Developer API không nói. API reference đã
   đánh dấu `responseJsonSchema` là deprecated, thay bằng `responseFormat`.
6. **Rút gọn hồ sơ nên theo câu, không theo token.** Nghiên cứu so sánh độc lập thấy cách chọn câu (extractive) giữ hoặc tăng độ chính xác ở
   mức nén 2–10×. Cách xoá token kiểu LLMLingua kém hơn, lại làm văn bản mất nguyên văn, trái hợp đồng câu trích. Với quan hệ giữa hai thực
   thể, hơn 95% quan hệ cần không quá 3 câu, nhưng 40,7% quan hệ ở DocRED cần nhiều câu, nên phải đo theo từng loại căn cứ.
7. **Hỏi hai thứ tự là cách chuẩn; sau hỏi lười, chi phí của nó còn rất nhỏ.** Độ lệch vị trí có thật, khác nhau theo mô hình và tác vụ, và
   mạnh nhất ở các ca sát nút. Luật "chỉ nhận khi hai thứ tự khớp" trùng với cách bảo thủ của MT-Bench và PRP. Sau hỏi lười, doc-4 còn khoảng
   1,05 lời gọi/cặp, nên không đáng cắt thêm. Nên giữ một mẫu nhỏ luôn hỏi đủ hai thứ tự để còn đo được độ lệch.

## 1. Developer API: giá, bậc giới hạn, khác gì Vertex

### 1.1 Giá

Bảng dưới lấy từ trang [Gemini Developer API pricing](https://ai.google.dev/gemini-api/docs/pricing), đơn vị USD cho 1 triệu token, đầu
vào văn bản (âm thanh đắt hơn):

| mô hình | kiểu chạy | vào | ra (gồm token suy nghĩ) | token vào đã cache | lưu cache (1 triệu token, 1 giờ) |
|---|---|---:|---:|---:|---:|
| `gemini-3.1-flash-lite` | Standard | 0,25 | 1,50 | 0,025 | 1,00 |
| | Batch | 0,125 | 0,75 | 0,0125 | 0,50 |
| | Flex | 0,125 | 0,75 | 0,0125 | 0,50 |
| | Priority | 0,45 | 2,70 | 0,045 | 1,80 |
| `gemini-3.5-flash-lite` | Standard | 0,30 | 2,50 | 0,03 | 1,00 |
| | Batch hoặc Flex | 0,15 | 1,25 | 0,02 | 1,00 |
| | Priority | 0,54 | 4,50 | 0,05 | 1,00 |

Trên Vertex, [bảng giá Agent Platform](https://cloud.google.com/gemini-enterprise-agent-platform/generative-ai/pricing) cho
`gemini-3.1-flash-lite` qua endpoint global có cùng các mức Standard (0,25/1,50, cache 0,025), Priority (0,45/2,70) và Flex/Batch
(0,125/0,75). Endpoint không global đắt hơn 10% (0,275/1,65) từ 2026-07-01; dự án đang dùng `global` (`gemini.py`). Phí lưu cache tường
minh trên Vertex là 0,000001 USD mỗi token-giờ, tức 1 USD cho 1 triệu token-giờ.

Ba điều kiện tính tiền khác có liên quan tới dự án:
- **Token suy nghĩ tính như token ra.** Theo trang [Thinking](https://ai.google.dev/gemini-api/docs/generate-content/thinking), mức suy nghĩ
  mặc định của 3.5 và 3.1 Flash-Lite là `minimal`; trang ghi mức này "không bảo đảm tắt hẳn". Sổ chi v3-r12 (28.650 lời gọi) không có lời
  gọi nào mang `thoughtsTokenCount`, và mã dự án đã cộng trường này vào token ra (`model_calls.py`). Không có đòn bẩy chi phí ở đây.
- **Lời gọi lỗi.** Developer API không tính tiền lời gọi lỗi 400 hoặc 500 nhưng vẫn tính vào hạn mức
  ([Billing](https://ai.google.dev/gemini-api/docs/billing)). Vertex chỉ tính tiền phản hồi mã 200 (bảng giá Agent Platform). Phản hồi 200
  sai nghĩa vẫn bị tính đủ.
- **Vòng đời mô hình.** 3.1 Flash-Lite là bản ổn định phát hành 2026-05-07. Trang
  [Deprecations](https://ai.google.dev/gemini-api/docs/deprecations) ghi ngày tắt sớm nhất trên Developer API là 2027-05-07, thay thế
  khuyên dùng là `gemini-3.5-flash-lite`. Trang [Model versions](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/model-versions)
  của Vertex ghi "May 7, 2027 or later". 3.5 Flash-Lite là Flash-Lite mới nhất, bản ổn định phát hành 2026-07-21
  ([trang mô hình](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite)).

Quy về một lời gọi pass phụ (3.280 token vào, 160 token ra), giá mỗi lời gọi như sau:

| mô hình, kiểu chạy | USD/lời gọi | so với hiện nay |
|---|---:|---:|
| 3.1 Flash-Lite, Standard | 0,00106 | mốc |
| 3.1 Flash-Lite, Flex hoặc Batch | 0,00053 | −50% |
| 3.1 Flash-Lite, Priority | 0,00191 | +80% |
| 3.5 Flash-Lite, Standard | 0,00138 | +31% |

### 1.2 Bậc và giới hạn của Developer API

Trang [Rate limits](https://ai.google.dev/gemini-api/docs/rate-limits) và trang [Billing](https://ai.google.dev/gemini-api/docs/billing)
quy định như sau:
- **Đơn vị là dự án, không phải API key.** Có ba chiều: RPM, TPM (chỉ đếm token vào) và RPD; vượt chiều nào cũng bị 429. RPD đặt lại lúc nửa
  đêm giờ Thái Bình Dương.
- **Số RPM/TPM/RPD theo mô hình không còn in trên trang.** Trang chỉ dẫn "View your active rate limits in AI Studio" và nói con số "không
  được bảo đảm". Một số trang thứ cấp có nêu số cho 3.1 Flash-Lite nhưng không truy được về Google, nên báo cáo không dùng (chưa xác nhận).
- **Trần chi theo 10 phút trượt.** Bậc 1 là 10 USD, bậc 2 là 50 USD, bậc 3 là 200 USD; vượt thì nhận 429 `RESOURCE_EXHAUSTED`. Trang ghi
  rằng trần này có áp dụng cho tài khoản hay không "tuỳ lịch sử thanh toán và tình trạng tài khoản".
- **Trần chi theo tháng cho tài khoản thanh toán.** Mức là 250 / 2.000 / 20.000–100.000+ USD. Tổng được cộng trên mọi dự án gắn với tài
  khoản. Chạm trần thì mọi dự án dừng tới ngày 1 tháng sau. Có thể xin nâng trần.
- **Điều kiện lên bậc.** Bậc 1 cần liên kết một tài khoản thanh toán đang hoạt động; tài khoản mới phải Prepay tối thiểu 5 USD. Bậc 2 cần
  đã trả 100 USD và qua 3 ngày từ lần thanh toán thành công đầu tiên. Bậc 3 cần đã trả 1.000 USD và qua 30 ngày. Điều kiện tính trên tổng chi
  tích luỹ cho các dịch vụ Google Cloud của tài khoản thanh toán, không riêng Gemini API. Việc lên bậc là tự động, thường trong 10 phút, và
  hiếm khi bị từ chối.
- **Prepay (từ 2026-03-23).** Mỗi lần mua tối thiểu 5 USD, số dư tối đa 5.000 USD, credit hết hạn sau 12 tháng và không hoàn. Số dư về 0
  thì mọi key của tài khoản ngừng ngay với lỗi HTTP 402. Hệ thống tính tiền trễ khoảng 10 phút nên có thể chi vượt số dư; job Batch chạy dài
  cũng có thể vượt.
- **Credit chào mừng 300 USD** của Google Cloud không dùng được cho Gemini API với tài khoản mở sau 2026-03-02.
- **Priority** chỉ mở cho dự án bậc 2 và 3 ([blog Google, 2026-04-02](https://blog.google/innovation-and-ai/technology/developers-tools/introducing-flex-and-priority-inference/)).
  Hạn mức mặc định bằng 0,3 lần hạn mức thường; phần vượt được hạ xuống Standard thay vì báo lỗi
  ([Priority inference](https://ai.google.dev/gemini-api/docs/priority-inference)).

Bảng sau gom các bậc lại:

| bậc | điều kiện | trần 10 phút | trần tháng | token Batch được xếp hàng (3.1 Flash-Lite) |
|---|---|---:|---:|---:|
| Free | dự án đang hoạt động | — | — | — |
| 1 | liên kết tài khoản thanh toán, Prepay | 10 USD | 250 USD | 10 triệu |
| 2 | đã trả 100 USD và qua 3 ngày | 50 USD | 2.000 USD | 500 triệu |
| 3 | đã trả 1.000 USD và qua 30 ngày | 200 USD | 20.000–100.000+ USD | 1 tỉ |

### 1.3 Khác gì Vertex Standard PayGo và Provisioned Throughput

Trang [Standard PayGo](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/standard-paygo) cho thấy Vertex vận hành
khác hẳn Developer API:

| | Developer API | Vertex Standard PayGo |
|---|---|---|
| đơn vị giới hạn | dự án | tổ chức |
| bậc dựa vào | tổng đã trả tích luỹ và thời gian từ lần trả đầu | tổng chi 30 ngày trượt cho các dịch vụ Agent Platform (gồm Batch, cache, Provisioned Throughput) |
| thước đo | RPM, TPM vào, RPD theo mô hình, xem trong AI Studio | thông lượng nền TPM, tính riêng cho từng mô hình; không có RPM riêng |
| mức cho Flash và Flash-Lite | (không công bố) | bậc 1 (10–250 USD): 2 triệu TPM; bậc 2 (250–2.000 USD): 4 triệu; bậc 3 (2.000–50.000 USD): 10 triệu; bậc 4 (trên 50.000 USD): 50 triệu |
| khi vượt | 429, phải chờ | được vượt mức nền khi bể chung rảnh; 429 là tắc tạm thời, không phải hết hạn mức cố định |
| trần chi | 10/50/200 USD mỗi 10 phút; 250/2.000/20.000+ USD mỗi tháng | trang không nêu trần chi |
| thanh toán | Prepay; không dùng được credit chào mừng | chu kỳ tính tiền Cloud thông thường |

Ba điểm khác trên trang Standard PayGo có ích cho dự án:
- Mức thông lượng áp dụng độc lập cho từng mô hình; dùng mô hình này không làm giảm mức của mô hình khác.
- Google khuyên dùng endpoint `global` và dàn đều lưu lượng trong từng phút; dồn cục theo giây có thể bị bóp dù trung bình mỗi phút vẫn dưới mức.
- `gemini-3.1-flash-lite` nằm trong danh sách mô hình GA có áp dụng bậc.

Provisioned Throughput là thuê bao cố định theo kỳ, từ 1 tuần tới 1 năm
([tổng quan](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/provisioned-throughput)). Với 3.1 Flash-Lite, 1 GSU cho
4.030 token/giây sau quy đổi, trong đó 1 token vào tính 1 và 1 token ra tính 6
([mô hình hỗ trợ](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/provisioned-throughput/supported-models)). Giá
1 GSU cam kết 1 tuần là 7,14 USD/giờ ở global, khoảng 1.200 USD/tuần (bảng giá Agent Platform). Một lời gọi pass phụ quy đổi thành
3.280 + 6 × 160 = 4.240 token, nên 1 GSU chỉ chạy được khoảng 57 lời gọi/phút; pass phụ doc-4 (43.190 lời gọi) sẽ mất khoảng 12,6 giờ.
Provisioned Throughput không hợp quy mô của dự án. Vertex cũng có Priority PayGo cho 3.1 Flash-Lite với giá 0,45/2,70
([Priority PayGo](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/priority-paygo)), không phải hướng tiết kiệm.

### 1.4 Quy đổi cho một cuốn cỡ doc-4

Áp các giới hạn trên vào pass phụ doc-4 (lượt v3: 43.190 lời gọi, 141,6 triệu token vào, 7,0 triệu token ra), ta được bảng sau:

| cách chạy | USD pass phụ | sàn thời gian do trần 10 phút ở bậc 1 |
|---|---:|---:|
| Standard, như v3 | 45,9 | 40–46 phút |
| Standard và hỏi lười (bớt 38% lời gọi) | khoảng 28,5 | 20–29 phút |
| Flex hoặc Batch, có hỏi lười | khoảng 14,2 | 10–14 phút (suy luận) |
| 3.5 Flash-Lite, Standard, cùng số token | khoảng 60,0 | 50–60 phút |

Bảng cần được đọc với các lưu ý sau:
- **Sàn chỉ tính trần chi.** Cửa sổ 10 phút trượt cho phép tiêu 10 USD ngay từ đầu, nên một việc X USD cần từ khoảng 10·(⌈X/10⌉ − 1) phút
  tới X phút. RPM, TPM và RPD theo mô hình (chưa biết) có thể chặn sớm hơn. Ở mức 1 USD/phút, hồ sơ pass phụ tương đương khoảng 940 lời
  gọi/phút, tức khoảng 3,1 triệu token vào/phút.
- **Dòng Flex là suy luận.** Tài liệu không nói trần chi được tính theo giá Flex, và mỗi lời gọi Flex có thể chậm vài phút.
- **Bậc 2 đổi bài toán.** Trần 10 phút ở bậc 2 là 50 USD, lớn hơn cả pass phụ của một cuốn, nên khi đó TPM, RPM và RPD quyết định tốc độ.
- **Trần tháng chặn số cuốn.** 250 USD/tháng ở bậc 1 đủ cho 4 cuốn cỡ doc-4 theo giá v3 (50,4 USD/cuốn), khoảng 7 cuốn sau hỏi lười (khoảng
  33 USD/cuốn), khoảng 12 cuốn nếu đạt khoảng 20 USD/cuốn.
- **RPD có thể chặn trước.** Một cuốn cỡ doc-4 cần khoảng 44.000 lời gọi pass phụ. Nếu RPD của 3.1 Flash-Lite ở bậc của dự án thấp hơn số
  này, một cuốn không thể xong trong một ngày. Phải xem AI Studio trước khi chọn Developer API cho sản phẩm.
- **So với Vertex bậc 1.** Mức nền 2 triệu TPM tương đương khoảng 71 phút cho 141,6 triệu token vào (74 phút nếu tính cả token ra; trang
  không nói TPM có đếm token ra hay không). Vertex cho vượt mức nền khi bể chung rảnh.

## 2. Cache ngữ cảnh

### 2.1 Quy định trên hai nền tảng

Bảng sau gom quy định về cache implicit và explicit, lấy từ [Context caching (generateContent)](https://ai.google.dev/gemini-api/docs/generate-content/caching),
[Context caching overview (Vertex)](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/context-cache/context-cache-overview),
[Batch API](https://ai.google.dev/gemini-api/docs/batch-api),
[Batch inference with Gemini](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/capabilities/batch-inference) và hai
bảng giá:

| | Developer API | Vertex |
|---|---|---|
| implicit | bật sẵn cho Gemini 2.5 trở lên; "không bảo đảm giảm giá"; token trúng cache tính 0,025 USD/1 triệu với 3.1 Flash-Lite, bằng 10% giá vào | bật sẵn; giảm 90% so với token vào chuẩn; không có phí lưu; hỗ trợ 3.1 Flash-Lite |
| explicit | Beta (v1beta); TTL mặc định 1 giờ, không giới hạn trên hay dưới; phí lưu 1 USD/1 triệu token/giờ (Standard) | giảm 90% với Gemini 2.5 trở lên; TTL mặc định 60 phút, tối thiểu 1 phút, không có tối đa; phí lưu 1 USD/1 triệu token-giờ; token tạo cache tính giá vào chuẩn |
| ngưỡng tối thiểu | bảng chỉ có 3.5–3.8 Flash và 3.1 Pro Preview (4.096), 2.5 Flash và Pro (2.048); không có dòng Flash-Lite | họ Gemini 3: 4.096 cho cả implicit và explicit; 3.0 Flash Preview, 3.1 Pro Preview, 3.7 và 3.8 Flash (implicit): 6.144; họ Gemini 2: 2.048 |
| với hạn mức | không có hạn mức riêng; "token limits include cached tokens", tức TPM vẫn đếm token đã cache | trang tổng quan không nói |
| với Batch | dùng được explicit cache trong batch; trang Batch nói trúng cache thì trả "giá cache chuẩn", còn bảng giá ghi 0,0125 cho Batch, hai trang không khớp | Batch không dùng được explicit cache; implicit giảm 90% và không cộng dồn với mức giảm 50% của Batch |
| cách tăng tỉ lệ trúng | đặt nội dung lớn và dùng chung ở đầu prompt; gửi các request cùng tiền tố gần nhau về thời gian | như Developer API |

### 2.2 Với tiền tố chung khoảng 490 token

Cache không có lợi cho pass phụ, và với thiết kế hiện tại cũng không thể có lợi, vì ba lý do:
- **Dưới ngưỡng.** Ngưỡng 4.096 token lớn hơn cả lời gọi (khoảng 3.280 token), không chỉ lớn hơn phần chung.
- **Cận trên vẫn nhỏ.** Giả sử 490 token chung được cache, khoản lợi tối đa là 490 × 90% × 0,25 USD/1 triệu, khoảng 0,00011 USD/lời gọi,
  tức khoảng 4,8 USD cho 43.190 lời gọi doc-4 (khoảng 10% pass phụ). Cận trên này không đạt được vì lý do thứ nhất.
- **Độn cho đủ ngưỡng thì lỗ.** Độn tiền tố lên 4.096 token rồi dùng explicit cache tốn 0,0001 USD/lời gọi cho phần cache, gần bằng 490 token
  không cache (0,00012 USD). Đổi lại, mô hình phải đọc thêm khoảng 3.600 token, và TPM vẫn đếm đủ token đã cache.

Sổ chi của dự án cho cùng kết luận. Phép đếm 0 USD trên `artifacts/v3-r12-final-evaluation/llm-ledger.jsonl` (28.650 lời gọi có `usage`,
qua Vertex) cho kết quả sau:
- 26.992 lời gọi dưới 4.048 token vào: không lần nào trúng cache.
- 1.658 lời gọi từ 4.048 token trở lên: 12 lần trúng (0,7%), mỗi lần 3.959–6.038 token, tổng 51.809 token, tức tiết kiệm khoảng 0,01 USD.
- Lượng token trúng (3.959, 3.960, 3.977…) không khớp đúng con số 4.096 của tài liệu. Cơ chế chi tiết không được công bố.

### 2.3 Đổi thứ tự prompt

Phần chung đã nằm ở đầu: system prompt đi trong trường `systemInstruction` (`gemini.py`). Schema đi trong `generationConfig`, và tài liệu
không nói schema được đặt ở đâu trong chuỗi token. Vấn đề vì vậy là độ dài, không phải thứ tự. Đổi thứ tự chỉ có tác dụng nếu đổi hẳn thiết
kế, và cái giá phải trả như sau:
- **Thiết kế khả dĩ.** Mọi cặp trong một chương dùng chung một khối đầu dài hơn 4.096 token (ví dụ văn bản chương), phần riêng của cặp đặt ở
  cuối. Cách đặt này cũng khớp lời khuyên "đặt câu hỏi ở cuối" của Google
  ([Long context](https://ai.google.dev/gemini-api/docs/long-context), [Prompting strategies](https://ai.google.dev/gemini-api/docs/prompting-strategies)).
- **Lợi về tiền (minh hoạ, giả định 800 token riêng).** (4.096 × 0,025 + 800 × 0,25) / 1 triệu, khoảng 0,0003 USD/lời gọi, so với khoảng
  0,00082 USD tiền token vào hiện nay.
- **Cái giá.** Implicit không bảo đảm trúng, nên phải dùng explicit và quản lý cache theo chương. TPM tăng vì đếm cả token cache. Mô hình đọc
  cả chương thay vì hồ sơ đã chọn lọc, đi ngược đòn bẩy B và có rủi ro chất lượng (mục 5). Hai thứ tự trình bày phải dùng chung khối đầu.

Hướng này không nên ưu tiên trong v4. Chỉ đáng xét lại sau khi đã đo đòn bẩy B.

## 3. Batch API và Flex

Bảng sau so bốn cách chạy giảm giá, lấy từ [Batch API](https://ai.google.dev/gemini-api/docs/batch-api),
[Rate limits](https://ai.google.dev/gemini-api/docs/rate-limits), [Flex inference](https://ai.google.dev/gemini-api/docs/flex-inference),
[Batch inference with Gemini](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/capabilities/batch-inference) và
[Flex PayGo](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/flex-paygo):

| | Batch, Developer API | Batch, Vertex | Flex, Developer API (Preview) | Flex PayGo, Vertex (Preview) |
|---|---|---|---|---|
| giá | −50% | −50% | −50% | −50% |
| giao diện | job bất đồng bộ | job bất đồng bộ | gọi đồng bộ, trường `serviceTier: flex` | gọi đồng bộ, header `X-Vertex-AI-LLM-Shared-Request-Type: flex` |
| độ trễ theo tài liệu | mục tiêu 24 giờ, "đa số nhanh hơn nhiều"; chờ hoặc chạy quá 48 giờ thì hết hạn, không có kết quả | chờ hàng đợi tối đa 72 giờ; đa số xong trong 24 giờ sau khi bắt đầu chạy; quá 24 giờ thì phần dở bị huỷ, chỉ tính tiền phần đã xong; nằm ngoài SLA | mục tiêu 1–15 phút; best-effort, có thể bị đẩy ra (503); khuyên timeout từ 10 phút; không tự chuyển sang Standard | "độ trễ dài hơn Standard"; timeout tối đa 30 phút; chỉ endpoint global |
| giới hạn riêng | 100 batch đồng thời; tệp vào tối đa 2 GB; lưu trữ tối đa 20 GB; gửi kèm trực tiếp tối đa 20 MB; token xếp hàng cho 3.1 Flash-Lite: 10 triệu / 500 triệu / 1 tỉ ở bậc 1/2/3; tách khỏi hạn mức thường | không có hạn mức định trước (bể chung); tối đa 200.000 request mỗi job; tệp Cloud Storage tối đa 1 GB | tính vào RPM/TPM thường, không có hạn mức mở rộng | 3.000 QPM cho mỗi mô hình gốc trong một dự án |

Về chuyện hợp chạy nền hay hợp người dùng đang chờ, các tài liệu trên dẫn tới những điểm sau:
- **Batch hợp việc nền.** Ví dụ: xử lý lại kho tài liệu hoặc chạy đánh giá. Trong một job không chốt được theo thứ tự, nên pass phụ phải dùng
  chế độ "hỏi tất cả một lần": theo mô phỏng ngày 2026-10-02, chế độ này cần 1–5 lượt và thừa 0,4–12,5% lời gọi. Mỗi lượt có thể mất tới
  24 giờ. Ở bậc 1 Developer API, mức 10 triệu token xếp hàng nhỏ hơn 141,6 triệu token vào của pass phụ doc-4, nên phải chia ít nhất 15
  đợt. Từ bậc 2 (500 triệu) thì xếp được cả cuốn. Trên Vertex, giới hạn 200.000 request mỗi job đủ cho một cuốn.
- **Flex là ứng viên cho người dùng chờ vài chục phút, nhưng phải thử trước.** Flex là gọi đồng bộ nên mã hiện tại chỉ cần thêm một trường.
  Tuy vậy, mỗi lô "hỏi trước, chốt theo thứ tự" phải chờ lời gọi chậm nhất, có thể tới vài phút, nên Flex hợp với chế độ ít lượt. Chưa có số
  đo độ trễ thật của Flex cho 3.1 Flash-Lite, nên cần một lượt thử vài trăm lời gọi (độ trễ p50/p95, tỉ lệ 503 và 429). Tài liệu không nói
  Flex chạy một mô hình khác, nên đầu ra được kỳ vọng như Standard nếu cùng mô hình và cấu hình (suy luận).
- **Priority không phải hướng tiết kiệm.** Với 3.1 Flash-Lite, Priority đắt hơn Standard 80%.

Một chi tiết kỹ thuật cần biết: tài liệu Developer API nay mặc định viết cho Interactions API. Batch API chỉ có ở `generateContent`, đúng
API dự án đang dùng (`v1beta`). Flex có ở cả hai API: trường `serviceTier` nằm trong `GenerateContentRequest` theo
[API reference](https://ai.google.dev/api/generate-content), và [blog Google](https://blog.google/innovation-and-ai/technology/developers-tools/introducing-flex-and-priority-inference/)
xác nhận Flex dùng được với `GenerateContent` cho mọi bậc trả phí.

## 4. Structured output

Tài liệu chính thức nói những điều sau về `responseJsonSchema` và `responseSchema`:
- **Schema có tính vào token vào không.** [Control generated output](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/capabilities/control-generated-output)
  của Vertex ghi: "The size of your response schema counts towards the input token limit." Phía Developer API, trang
  [Structured outputs](https://ai.google.dev/gemini-api/docs/generate-content/structured-output), trang
  [Token counting](https://ai.google.dev/gemini-api/docs/generate-content/tokens) và API reference không có câu tương ứng. Phép đếm của dự án
  (báo cáo v4 mục 3: tổng các phần, gồm 206 token schema, khớp 3.280 token đo thật) phù hợp với việc schema bị tính tiền như token vào.
  Trên Developer API, điểm này chưa xác nhận.
- **Bảo đảm cú pháp, không bảo đảm nghĩa.** Developer API: "structured output guarantees syntactically correct JSON, it does not guarantee the
  values are semantically correct", nên phải kiểm giá trị trong mã. Vertex: muốn JSON hợp lệ 100% thì phải có cả `response_schema` lẫn
  `response_mime_type`; chỉ đặt `application/json` mà không có schema thì chỉ là "gợi ý mạnh", vẫn có thể hỏng.
- **Thứ tự khoá.** Mô hình sinh các khoá theo đúng thứ tự trong schema. `SECONDARY_SCHEMA` của dự án (`prerequisite_prompt.py`) đặt
  `decision` trước `quote` và `reason`, nên mô hình chốt quyết định trước khi viết câu trích.
- **Từ khoá được hỗ trợ có hạn.** API reference chỉ liệt kê `$id`, `$defs`, `$ref`, `$anchor`, `type`, `format`, `title`, `description`,
  `enum`, `items`, `prefixItems`, `minItems`, `maxItems`, `minimum`, `maximum`, `anyOf`, `oneOf`, `properties`, `additionalProperties`,
  `required`. Trang Structured outputs ghi "the model ignores unsupported properties". Vì vậy không thể ép "trích nguyên văn" bằng schema;
  vẫn phải kiểm trong mã như hiện nay.
- **Schema phức tạp có thể bị lỗi 400.** Cách giảm: rút ngắn tên thuộc tính, bớt giá trị enum, bớt trường tuỳ chọn và ràng buộc.
- **`responseJsonSchema` đã bị đánh dấu deprecated.** API reference (cập nhật 2026-09-23) ghi cả `responseSchema` lẫn `responseJsonSchema`
  là "Deprecated. Use responseFormat instead"; trường mới là `responseFormat.text` với `mimeType` và `schema`. Trường cũ vẫn chạy. Khi đổi
  cần kiểm phát lại, vì hash prompt của dự án gồm cả schema.

Liên hệ với 2.710 cặp (12%) bị hoãn vì phản hồi không hợp lệ ở doc-4, có năm điểm:
- Khi đã có schema, lỗi cú pháp JSON gần như không còn, nên phần lớn 12% này nhiều khả năng là lỗi nghĩa (câu trích không nguyên văn, nằm
  ngoài cửa sổ). Báo cáo v4 chưa phân loại lỗi, nên đây vẫn là suy luận cần đọc nhật ký (đòn bẩy C) để xác nhận. Lỗi nghĩa thì schema không
  tự sửa được; chỉ prompt, hồ sơ và bước kiểm trong mã mới giảm được.
- `SECONDARY_SCHEMA` chỉ bắt buộc `pair_id`, `decision` và `flags`, nên một quyết định `create` thiếu `quote` hay `evidence_kind` vẫn hợp lệ
  với schema. Nếu nhật ký cho thấy lỗi "thiếu trường" đáng kể, có thể bắt buộc các trường đó cho nhánh `create` bằng `anyOf` kèm `enum` và
  `required`, đều là từ khoá được hỗ trợ. Đổi schema là đổi đầu vào của mô hình, nên cần phát lại và chấm như mọi thay đổi prompt.
- Cả hai nền tảng đều tính tiền phản hồi 200 sai nghĩa, nên mỗi cặp bị hoãn vẫn tốn đủ tiền.
- [Hướng dẫn Gemini 3](https://ai.google.dev/gemini-api/docs/gemini-3) "strongly recommend" giữ temperature mặc định 1.0, vì đặt thấp hơn
  "may lead to unexpected behavior, such as looping or degraded performance". [Trang mô hình 3.1 Flash-Lite trên Vertex](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/3-1-flash-lite)
  ghi mặc định 1.0; dự án dùng 0. Sổ chi v3-r12 không có dấu hiệu lặp: token ra lớn nhất là 551 trong 28.650 lời gọi, trung vị 82. Đổi
  nhiệt độ là đổi đầu ra và tính tái lập, nên chỉ làm khi có thử đối chứng; đây không phải đòn bẩy chi phí.
- Một nghiên cứu độc lập ([Tam và cộng sự 2024](https://arxiv.org/abs/2408.02442)) thấy ràng buộc định dạng làm giảm năng lực suy luận
  nhưng có thể tăng độ đúng ở tác vụ phân loại, và thứ tự khoá có ảnh hưởng. Pass phụ gần với phân loại có kèm trích dẫn. Đặt `decision`
  trước hay sau `quote` là một biến có thể thử; chưa có bằng chứng trực tiếp cho tác vụ này.

## 5. Rút gọn ngữ cảnh và bằng chứng

### 5.1 Bằng chứng định lượng

Bảng dưới tóm các nghiên cứu gốc đã đọc. Không nghiên cứu nào dùng Gemini 3.1 Flash-Lite hay quan hệ tiên quyết, nên mọi kết luận cho dự án
đều là chuyển giao:

| phương pháp | cách rút gọn | kết quả | bối cảnh |
|---|---|---|---|
| [LLMLingua](https://arxiv.org/abs/2310.05736) (EMNLP 2023) | xoá token theo perplexity của một LM nhỏ | GSM8K: nén 14× và 20× phần ví dụ, EM giảm 1,44 và 1,52 điểm (từ 78,85); BBH nén 5× và 7×: giảm 8,5 và 13,2 điểm | nén phần ví dụ few-shot, tiếng Anh |
| [LongLLMLingua](https://arxiv.org/abs/2310.06839) (ACL 2024) | xoá token có biết câu hỏi, xếp lại tài liệu | NaturalQuestions: tăng tới 21,4% với khoảng 4× ít token (GPT-3.5-Turbo); LooGLE: giảm 94% chi phí; prompt khoảng 10.000 token nén 2–6×: nhanh 1,4–2,6× | nhiều tài liệu dài |
| [LLMLingua-2](https://arxiv.org/abs/2403.12968) (Findings ACL 2024) | phân loại giữ hay bỏ từng token (XLM-RoBERTa) | nén 2–5×, nhanh 1,6–2,9×; LongBench tiếng Trung nén 5×: trung bình 38,1 so với 42,5 của bản gốc (Single-doc 46,7 so với 61,2) | chỉ huấn luyện trên tiếng Anh |
| [Selective Context](https://arxiv.org/abs/2310.06201) (EMNLP 2023) | xoá theo self-information | bớt 50% ngữ cảnh: giảm 36% bộ nhớ, 32% thời gian; BERTScore giảm 0,023, faithfulness giảm 0,038 | tóm tắt, QA, hội thoại |
| [RECOMP](https://arxiv.org/abs/2310.04408) | trích câu hoặc tóm tắt, có huấn luyện | còn 6% độ dài, mất mát nhỏ | mô hình ngôn ngữ, QA mở |
| [FILCO](https://arxiv.org/abs/2311.08377) | lọc theo câu, có huấn luyện | bớt 44–64% độ dài đầu vào, vượt ngữ cảnh đầy đủ ở cả 6 tác vụ (FLAN-T5, LLaMA2); tách theo câu cho kết quả tốt nhất | RAG |
| [Jha và cộng sự](https://arxiv.org/abs/2407.08892) (Es-FoMo, ICML 2024) | so sánh ba họ phương pháp | trích xuất (reranker) thường tốt nhất, nén tới 10× mà suy giảm nhỏ; 2WikiMultihopQA với GPT-3.5-Turbo: nén 7,75× và tăng 7,89 điểm; xoá token thường kém hơn trích xuất | LongBench |

Với quan hệ giữa hai thực thể trong văn bản, các nghiên cứu trích quan hệ cấp tài liệu (DocRE) cho số liệu sau:
- [DocRED](https://arxiv.org/abs/1906.06127) (ACL 2019): mỗi quan hệ có trung bình 1,6 câu bằng chứng; 46,4% quan hệ có hơn một câu bằng
  chứng; 40,7% quan hệ chỉ rút ra được khi đọc nhiều câu.
- [Three Sentences Are All You Need](https://arxiv.org/abs/2106.01793) (ACL 2021): trên DocRED, CDR và GDA, hơn 95% quan hệ cần không quá 3
  câu và 87% cần không quá 2. Ba luật chọn câu đơn giản phủ tới 87,5% bằng chứng do người gán: hai thực thể nằm trong không quá 3 câu liên
  tiếp; hai câu nối qua một thực thể thứ ba; mặc định lấy cặp câu chứa mỗi thực thể.
- [Eider](https://arxiv.org/abs/2106.08657) (Findings ACL 2022, mô hình BERT): kết hợp dự đoán trên bằng chứng trích ra và trên tài liệu
  gốc cho F1 62,48; chỉ dùng bằng chứng trích ra còn 60,44; chỉ dùng tài liệu gốc còn 61,53.
- [LMRC](https://arxiv.org/abs/2408.13889): LLM làm DocRE vẫn kém mô hình truyền thống. Nhóm tác giả xác định nguyên nhân chính là chú ý bị
  phân tán bởi các cặp không có quan hệ, nên họ lọc cặp bằng một bộ phân loại trước khi hỏi LLM. Điều này liên quan tới ý tưởng F của v4.

Về văn bản thừa và vị trí của thông tin, có ba bằng chứng:
- [GSM-IC](https://arxiv.org/abs/2302.00093) (ICML 2023): thêm một ít thông tin không liên quan làm độ đúng giảm mạnh. Trong số bài gốc giải
  được, không quá 18% còn giải đúng nhất quán với mọi loại thông tin thừa.
- [Lost in the Middle](https://arxiv.org/abs/2307.03172) (TACL): độ đúng cao nhất khi thông tin cần nằm ở đầu hoặc cuối ngữ cảnh; GPT-3.5-Turbo
  giảm hơn 20% khi thông tin nằm ở giữa. Thí nghiệm dùng ngữ cảnh khoảng 2.000–6.000 token (10–30 tài liệu), cùng cỡ với hồ sơ pass phụ.
- Google khuyên đặt câu hỏi ở cuối, sau toàn bộ ngữ cảnh ([Long context](https://ai.google.dev/gemini-api/docs/long-context)).

### 5.2 Hệ quả cho hồ sơ gọn (đòn bẩy B)

Các bằng chứng trên dẫn tới bốn điểm cho lượt thử hồ sơ gọn:
- **Không dùng cách xoá token.** LLMLingua và các bản sau làm văn bản không còn nguyên văn, trái hợp đồng câu trích phải nguyên văn và nằm
  trong cửa sổ định nghĩa. Cách này còn cần chạy LM cục bộ, và bằng chứng đa ngôn ngữ yếu (LLMLingua-2 mất 4,4 điểm trung bình trên tiếng
  Trung). Nghiên cứu so sánh cũng xếp nó sau cách trích câu.
- **Chọn theo câu hợp với hợp đồng.** Câu được giữ nguyên nên câu trích vẫn kiểm được, và nhiều nghiên cứu thấy độ đúng giữ nguyên hoặc tăng ở
  mức nén 2–10×. Luật chọn câu có thể dựa hoàn toàn vào cấu trúc (câu nhắc cả hai khái niệm, câu nối qua khái niệm thứ ba, cửa sổ định
  nghĩa), không cần danh sách từ khoá theo ngôn ngữ.
- **Rủi ro nằm ở quan hệ cần nhiều câu.** DocRED có 40,7% quan hệ như vậy; loại căn cứ `mach_trinh_bay` của dự án có thể rơi vào nhóm này.
  Eider cho thấy chỉ dùng bằng chứng kém hơn kết hợp. Lượt thử B nên báo kết quả theo `evidence_kind` và `prerequisite_kind`, không chỉ báo
  tổng.
- **Thứ tự trong hồ sơ có thể quan trọng.** Nên đặt cửa sổ định nghĩa và câu nhắc cả hai khái niệm ở đầu hoặc cuối hồ sơ, câu hỏi ở cuối.

## 6. Độ lệch vị trí khi LLM phán theo cặp

### 6.1 Bằng chứng

Bảng dưới tóm các nghiên cứu gốc về độ lệch vị trí:

| nghiên cứu | thiết lập | số liệu chính |
|---|---|---|
| [Zheng và cộng sự, MT-Bench](https://arxiv.org/abs/2306.05685) (NeurIPS 2023) | so hai câu trả lời, đổi chỗ | tỉ lệ nhất quán khi đổi chỗ: GPT-4 65,0%, GPT-3.5 46,2%, Claude-v1 23,8%; đa số nghiêng về vị trí đầu; ví dụ few-shot nâng GPT-4 lên 77,5% nhưng làm mỗi lời gọi đắt gấp 4; lệch rõ khi hai câu trả lời sát nhau về chất lượng, gần như biến mất khi chênh lớn |
| [Wang và cộng sự](https://arxiv.org/abs/2305.17926) | GPT-4 và ChatGPT làm giám khảo | tỉ lệ mâu thuẫn khi đổi chỗ: GPT-4 46,3% (cặp sát nhau) và 5,0% (cặp chênh xa); ChatGPT 82,5% và 52,5%; mâu thuẫn tăng khi khoảng cách điểm nhỏ; gộp nhiều bằng chứng và nhiều thứ tự (MEC + BPC) nâng độ đúng của GPT-4 từ 52,7% lên 62,5%, chi phí từ 2,00 lên 6,38 USD |
| [Shi và cộng sự](https://arxiv.org/abs/2406.07791) (AACL-IJCNLP 2025) | 15 giám khảo, hơn 150.000 lần phán | độ lệch không do ngẫu nhiên, khác nhau theo giám khảo và tác vụ; position consistency trên MTBench theo cặp: GPT-4 0,82, Gemini-1.5-pro 0,62, Gemini-1.5-flash 0,67; tăng theo khoảng cách chất lượng; phụ thuộc yếu vào độ dài prompt |
| [Qin và cộng sự, PRP](https://arxiv.org/abs/2306.17563) (NAACL 2024) | xếp hạng tài liệu theo cặp | hỏi cả hai thứ tự; khớp thì nhận, không khớp thì coi như hoà |
| [Zheng và cộng sự, PriDe](https://arxiv.org/abs/2309.03882) (ICLR 2024) | câu hỏi trắc nghiệm | ước lượng thiên lệch tiên nghiệm bằng hoán vị trên một phần nhỏ mẫu (ví dụ 5%) rồi khử cho phần còn lại; ước lượng ổn định từ 2% đến 20% mẫu; cần xác suất đầu ra |
| [Pezeshkpour và Hruschka](https://arxiv.org/abs/2308.11483) | câu hỏi trắc nghiệm | đổi thứ tự lựa chọn làm độ đúng chênh khoảng 13–75%; nhạy nhất khi mô hình phân vân giữa 2–3 lựa chọn đầu; hiệu chỉnh tăng tới 8 điểm |
| [Zhao và cộng sự, Calibrate Before Use](https://arxiv.org/abs/2102.09690) (ICML 2021) | few-shot | hiệu chỉnh bằng một đầu vào rỗng tăng độ đúng tới 30,0 điểm tuyệt đối |
| [Li và cộng sự, PORTIA](https://arxiv.org/abs/2310.01432) (EMNLP 2024) | so câu trả lời | cắt rồi ghép các đoạn tương ứng nâng tỉ lệ nhất quán của GPT-4 lên 98%; GPT-3.5 đạt 88% đồng thuận với GPT-4 ở khoảng 10% chi phí |

### 6.2 Cách kiểm tra và giảm

Các nghiên cứu trên đưa ra bốn nhóm cách đo và giảm:
- **Đo.** Tỉ lệ mâu thuẫn khi đổi chỗ (conflict rate, Wang và cộng sự). Ba chỉ số của Shi và cộng sự: position consistency, preference
  fairness (nghiêng về đầu hay cuối) và repetition stability (hỏi lại cùng thứ tự có ra như cũ không).
- **Hỏi hai thứ tự.** Cách bảo thủ chỉ công nhận khi hai thứ tự khớp, mâu thuẫn thì coi như hoà (MT-Bench, PRP). Cách khác là gộp điểm của
  nhiều thứ tự (BPC).
- **Hiệu chỉnh.** Ước lượng thiên lệch trên một mẫu nhỏ rồi trừ đi (PriDe), hoặc hiệu chỉnh bằng đầu vào rỗng (Calibrate Before Use). Cả hai
  cần xác suất đầu ra. Gemini có `responseLogprobs`, nhưng chưa kiểm được trường này dùng chung với structured output trên 3.1 Flash-Lite.
- **Trình bày ngẫu nhiên.** MT-Bench gọi đây là cách "aggressive": gán vị trí ngẫu nhiên và chấp nhận sai số ở quy mô lớn. Cách này đổi đầu
  ra.

### 6.3 Chi phí so với lợi ích cho pass phụ

Áp vào pass phụ của dự án, có năm điểm:
- **Luật gộp hiện tại đã là cách bảo thủ chuẩn.** Hoãn khi hai thứ tự khác nhau chính là cách của MT-Bench và PRP. Độ lệch mạnh nhất ở các ca
  sát nút, đúng loại ca mà luật này hoãn.
- **Sau hỏi lười, chi phí chống lệch còn rất nhỏ.** Ở doc-4, số bản ghi lời gọi giảm từ 38.556 xuống khoảng 24.059 cho 22.972 cặp, tức khoảng
  1,05 lời gọi/cặp. Phần dành cho thứ tự thứ hai chỉ còn khoảng 5%. Các cách khác trong tài liệu tốn hơn nhiều (few-shot gấp 4; MEC + BPC
  khoảng gấp 3,2). Bỏ hẳn thứ tự thứ hai chỉ tiết kiệm tối đa khoảng 5% mà lại đổi đầu ra, nên không đáng.
- **Có thể chọn thứ tự hỏi trước.** Vì thứ tự nào nói "không" cũng làm cặp không ra cạnh, có thể hỏi trước thứ tự có tỉ lệ "không" cao hơn để
  tiết kiệm thêm. Cạnh không đổi; chỉ cờ chẩn đoán có thể khác, như vé v4-01 đã nêu. Chọn được bằng phép đếm 0 USD trên nhật ký v3.
- **Giữ một mẫu kiểm tra.** Sau hỏi lười, dự án mất dữ liệu thứ tự thứ hai của các cặp "không", nên không đo được độ lệch nữa. Một mẫu ngẫu
  nhiên nhỏ (ví dụ 2–5% số cặp) luôn hỏi đủ hai thứ tự sẽ giữ được khả năng đo; cạnh không đổi, thêm khoảng 2–5% lời gọi. Đây là ý của PriDe
  (ước lượng trên mẫu nhỏ) áp vào việc theo dõi.
- **Lấy mốc trước khi triển khai.** Nhật ký v3 còn đủ hai thứ tự, nên tính được 0 USD tỉ lệ mâu thuẫn, tỉ lệ đổi chiều (0,2% ở doc-4) và
  thiên hướng nói "có" theo vị trí. Nên làm việc này trước vé v4-01.

## Hệ quả cho v4

Đối chiếu với hai báo cáo trước, các giả định sau được **xác nhận**:
- Giá đã khoá trong mã (0,25/1,50 USD, `prerequisite_prompt.py`, kiểm 2026-09-18) vẫn đúng ngày 2026-10-04 trên cả Developer API lẫn Vertex
  global.
- "Một việc X USD cần ít nhất khoảng X phút ở bậc 1" đúng với trần 10 USD mỗi 10 phút trượt. Cận dưới chính xác hơn là khoảng
  10·(⌈X/10⌉ − 1) phút, và chỉ đúng khi trần này áp dụng cho tài khoản của dự án.
- Mức nền 2 triệu và 4 triệu TPM của Vertex ở bậc 1 và 2 (báo cáo 2026-10-02 ghi "chưa xác nhận") nay đã đọc trực tiếp và đúng. Trang còn có
  bậc 3 (10 triệu) và bậc 4 (50 triệu), không có RPM riêng, và 429 là tắc tạm thời.
- Điều kiện lên bậc Developer API (đã trả 100 USD, 1.000 USD) đúng; cần thêm điều kiện qua 3 ngày và 30 ngày.
- "Cache ít tác dụng" đúng, và mạnh hơn thế: cache không áp dụng được cho pass phụ, có sổ chi chứng minh.
- Batch và Flex rẻ hơn 50% đúng trên cả hai nền tảng. Hỏi lười giữ nguyên cạnh và khớp cách bảo thủ trong các nghiên cứu.

Các giả định sau cần **đổi hoặc bổ sung**:
- **Thêm trần chi theo tháng.** Ở bậc 1, 250 USD/tháng chỉ đủ khoảng 4–7 cuốn cỡ doc-4. Kế hoạch sản phẩm cần tính bậc 2 (đã trả 100 USD, qua
  3 ngày) hoặc xin nâng trần.
- **Phải xem RPM/TPM/RPD trong AI Studio trước khi chọn Developer API.** RPD có thể chặn trước cả trần chi, vì một cuốn cần khoảng 44.000 lời
  gọi.
- **Credit 300 USD không dùng được cho Developer API; phải Prepay.** Số dư về 0 thì lời gọi lỗi 402, nên bộ chạy cần xử lý mã lỗi này.
- **"Batch chỉ hợp chạy nền" đúng với Batch nhưng chưa đủ.** Flex là gọi đồng bộ, rẻ 50%, độ trễ vài phút mỗi lời gọi, nên là ứng viên cho
  người dùng chờ; cần thử nhỏ. Batch trên Vertex có thể chờ hàng đợi tới 72 giờ chứ không chỉ 24 giờ. Batch bậc 1 Developer API không xếp
  nổi một pass phụ doc-4 trong một đợt.
- **Mô hình có hạn dùng.** 3.1 Flash-Lite có thể bị tắt sớm nhất từ 2027-05-07; mô hình thay thế đắt hơn khoảng 31% mỗi lời gọi pass phụ.
  Mục tiêu USD/cuốn của sản phẩm nên tính cả kịch bản này.
- **Có vé chuyển `responseJsonSchema` sang `responseFormat`**, kèm kiểm phát lại.
- **Hồ sơ gọn (B) nên cắt theo câu**, không theo token, và báo kết quả theo loại căn cứ.
- **Giữ một mẫu kiểm tra hai thứ tự** sau hỏi lười, và cân nhắc chọn thứ tự hỏi trước theo tỉ lệ "không" (0 USD).

Các điểm sau **còn chưa xác nhận**:
- RPM, TPM và RPD của 3.1 Flash-Lite theo từng bậc trên Developer API; chỉ xem được trong AI Studio.
- Trần chi 10 phút có áp dụng cho tài khoản của dự án không, và Flex có được tính theo giá đã giảm trong trần này không.
- Chi trên Vertex trả bằng credit có được tính là "đã trả" khi xét bậc Developer API không. Trang Billing chỉ nói xét theo tổng chi tích luỹ cho
  các dịch vụ Google Cloud của tài khoản thanh toán.
- Ngưỡng cache tối thiểu của Flash-Lite trên Developer API (bảng không có dòng Flash-Lite; Vertex ghi 4.096 cho họ Gemini 3), và vì sao lượng
  token trúng cache quan sát được (từ 3.959) thấp hơn 4.096.
- Schema có bị tính tiền như token vào trên Developer API không.
- 12% phản hồi không hợp lệ ở doc-4 gồm bao nhiêu lỗi nghĩa, bao nhiêu lỗi thiếu trường; chưa ai phân loại.
- Độ trễ thật của Flex và Batch với 3.1 Flash-Lite; tài liệu chỉ công bố mục tiêu.
- Giá cache khi chạy Batch trên Developer API (trang Batch và bảng giá nói khác nhau).
- TPM của Vertex có đếm token ra không.
- `responseLogprobs` có dùng được cùng structured output trên 3.1 Flash-Lite không (cần cho cách hiệu chỉnh kiểu PriDe).
- Không tìm thấy nghiên cứu gốc nào đo việc rút gọn ngữ cảnh cho phán quan hệ tiên quyết bằng LLM; số liệu ở mục 5 là chuyển giao từ DocRE và QA.

## Nguồn

Mọi nguồn dưới đây được đọc trực tiếp ngày 2026-10-04. Ngày trong ngoặc là ngày "Last updated" của trang, nếu trang có ghi.

Tài liệu Gemini Developer API (Google AI for Developers):
- [Gemini Developer API pricing](https://ai.google.dev/gemini-api/docs/pricing) (2026-10-01)
- [Rate limits](https://ai.google.dev/gemini-api/docs/rate-limits) (2026-09-02)
- [Billing](https://ai.google.dev/gemini-api/docs/billing) (2026-09-28)
- [Context caching, bản generateContent](https://ai.google.dev/gemini-api/docs/generate-content/caching) (2026-09-11)
- [Context caching, bản Interactions API](https://ai.google.dev/gemini-api/docs/caching) (2026-09-02)
- [Batch API](https://ai.google.dev/gemini-api/docs/batch-api) (2026-09-17)
- [Flex inference](https://ai.google.dev/gemini-api/docs/flex-inference) (2026-09-23)
- [Priority inference](https://ai.google.dev/gemini-api/docs/priority-inference) (2026-09-23)
- [Structured outputs, bản generateContent](https://ai.google.dev/gemini-api/docs/generate-content/structured-output) (2026-09-02)
- [Structured outputs, bản Interactions API](https://ai.google.dev/gemini-api/docs/structured-output) (2026-09-23)
- [API reference: generateContent](https://ai.google.dev/api/generate-content) (2026-09-23)
- [API reference: countTokens](https://ai.google.dev/api/tokens)
- [Token counting](https://ai.google.dev/gemini-api/docs/generate-content/tokens) (2026-09-04)
- [Thinking](https://ai.google.dev/gemini-api/docs/generate-content/thinking) (2026-09-25)
- [Gemini 3 developer guide](https://ai.google.dev/gemini-api/docs/gemini-3) (2026-09-23)
- [Long context](https://ai.google.dev/gemini-api/docs/long-context) (2026-06-22)
- [Prompting strategies](https://ai.google.dev/gemini-api/docs/prompting-strategies) (2026-09-17)
- [Models](https://ai.google.dev/gemini-api/docs/models) (2026-10-01)
- [Gemini 3.1 Flash-Lite](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite) (2026-07-21)
- [Gemini 3.5 Flash-Lite](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite) (2026-07-30)
- [Deprecations](https://ai.google.dev/gemini-api/docs/deprecations) (2026-10-01)
- [New ways to balance cost and reliability in the Gemini API](https://blog.google/innovation-and-ai/technology/developers-tools/introducing-flex-and-priority-inference/),
  blog Google, đăng 2026-04-02

Tài liệu Vertex (Gemini Enterprise Agent Platform):
- [Standard PayGo](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/standard-paygo) (2026-10-02); URL cũ
  `.../vertex-ai/generative-ai/docs/dynamic-shared-quota` nay chuyển về trang này
- [Flex PayGo](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/flex-paygo) (2026-10-02)
- [Priority PayGo](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/priority-paygo) (2026-10-02)
- [Batch inference with Gemini](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/capabilities/batch-inference) (2026-10-02)
- [Context caching overview](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/context-cache/context-cache-overview) (2026-10-02)
- [Control generated output](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/capabilities/control-generated-output) (2026-10-02)
- [Gemini Enterprise Agent Platform pricing](https://cloud.google.com/gemini-enterprise-agent-platform/generative-ai/pricing) (trang không ghi ngày)
- [Provisioned Throughput overview](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/provisioned-throughput) (2026-10-01)
- [Provisioned Throughput: supported models](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/provisioned-throughput/supported-models) (2026-10-02)
- [Gemini 3.1 Flash-Lite trên Agent Platform](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/3-1-flash-lite) (2026-10-02)
- [Model versions](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/model-versions) (2026-10-02)

Bài báo gốc (đọc tóm tắt và toàn văn trên arXiv; hội nghị lấy theo ghi chú trên trang arXiv, bài không ghi thì để trống):
- Jiang và cộng sự, [LLMLingua: Compressing Prompts for Accelerated Inference of Large Language Models](https://arxiv.org/abs/2310.05736), EMNLP 2023
- Jiang và cộng sự, [LongLLMLingua: Accelerating and Enhancing LLMs in Long Context Scenarios via Prompt Compression](https://arxiv.org/abs/2310.06839), ACL 2024
- Pan và cộng sự, [LLMLingua-2: Data Distillation for Efficient and Faithful Task-Agnostic Prompt Compression](https://arxiv.org/abs/2403.12968), Findings ACL 2024
- Li và cộng sự, [Compressing Context to Enhance Inference Efficiency of Large Language Models (Selective Context)](https://arxiv.org/abs/2310.06201), EMNLP 2023
- Xu và cộng sự, [RECOMP: Improving Retrieval-Augmented LMs with Compression and Selective Augmentation](https://arxiv.org/abs/2310.04408)
- Wang và cộng sự, [Learning to Filter Context for Retrieval-Augmented Generation (FILCO)](https://arxiv.org/abs/2311.08377)
- Jha và cộng sự, [Characterizing Prompt Compression Methods for Long Context Inference](https://arxiv.org/abs/2407.08892), Es-FoMo @ ICML 2024
- Liu và cộng sự, [Lost in the Middle: How Language Models Use Long Contexts](https://arxiv.org/abs/2307.03172), TACL
- Shi và cộng sự, [Large Language Models Can Be Easily Distracted by Irrelevant Context](https://arxiv.org/abs/2302.00093), ICML 2023
- Yao và cộng sự, [DocRED: A Large-Scale Document-Level Relation Extraction Dataset](https://arxiv.org/abs/1906.06127), ACL 2019
- Huang và cộng sự, [Three Sentences Are All You Need: Local Path Enhanced Document Relation Extraction](https://arxiv.org/abs/2106.01793), ACL 2021
- Xie và cộng sự, [Eider: Empowering Document-level Relation Extraction with Efficient Evidence Extraction and Inference-stage Fusion](https://arxiv.org/abs/2106.08657), Findings ACL 2022
- Li và cộng sự, [LLM with Relation Classifier for Document-Level Relation Extraction (LMRC)](https://arxiv.org/abs/2408.13889)
- Tam và cộng sự, [Let Me Speak Freely? A Study on the Impact of Format Restrictions on Performance of Large Language Models](https://arxiv.org/abs/2408.02442)
- Zheng và cộng sự, [Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena](https://arxiv.org/abs/2306.05685), NeurIPS 2023 Datasets and Benchmarks
- Wang và cộng sự, [Large Language Models are not Fair Evaluators](https://arxiv.org/abs/2305.17926)
- Shi và cộng sự, [Judging the Judges: A Systematic Study of Position Bias in LLM-as-a-Judge](https://arxiv.org/abs/2406.07791), AACL-IJCNLP 2025
- Qin và cộng sự, [Large Language Models are Effective Text Rankers with Pairwise Ranking Prompting](https://arxiv.org/abs/2306.17563), NAACL 2024
- Zheng và cộng sự, [Large Language Models Are Not Robust Multiple Choice Selectors (PriDe)](https://arxiv.org/abs/2309.03882), ICLR 2024
- Pezeshkpour và Hruschka, [Large Language Models Sensitivity to The Order of Options in Multiple-Choice Questions](https://arxiv.org/abs/2308.11483)
- Zhao và cộng sự, [Calibrate Before Use: Improving Few-Shot Performance of Language Models](https://arxiv.org/abs/2102.09690), ICML 2021
- Li và cộng sự, [Split and Merge: Aligning Position Biases in LLM-based Evaluators (PORTIA)](https://arxiv.org/abs/2310.01432), EMNLP 2024

Tệp của dự án được đọc (không chạy mã):
- [nghien-cuu-song-song-cao-2026-10-02.md](nghien-cuu-song-song-cao-2026-10-02.md) và
  [nghien-cuu-v4-chi-phi-thoi-gian-2026-10-04.md](nghien-cuu-v4-chi-phi-thoi-gian-2026-10-04.md): giả định được đối chiếu.
- `src/doc2roadmap/infrastructure/llm/gemini.py`: thân request (`systemInstruction`, `responseJsonSchema`, temperature 0, location `global`).
- `src/doc2roadmap/application/prerequisite_prompt.py`: `SECONDARY_SCHEMA` và giá đã khoá.
- `src/doc2roadmap/application/model_calls.py`: token ra được tính bằng `candidatesTokenCount` cộng `thoughtsTokenCount`.
- `artifacts/v3-r12-final-evaluation/llm-ledger.jsonl`: 28.650 lời gọi có `usage`, dùng cho phép đếm cache, token suy nghĩ và độ dài token ra.
