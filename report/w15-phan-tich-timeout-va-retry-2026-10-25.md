# W-15 — tìm nguyên nhân timeout và giữ retry của core — 2026-10-25

Tiếp từ [lượt thật R5](w15-luot-that-2026-10-25.md), commit `c19d461`.
Worktree `tmp/w15-real-build`, nhánh `work/w15-real-build`; root vẫn main `6249dab`.
Không sửa `src/doc2roadmap/`, không đổi .env, không ghép/push main.

## Chỉ thị mới và thay đổi chính sách operator

Chủ dự án yêu cầu:

> hãy tìm nguyên nhân lỗi đi

Sau đó hỏi:

> tôi tưởng bên core phải xử lí retry này kia để ko lỗi, hay do bạn ko dùng core

> cần gì, tôi chỉ muốn backend lắp core vào dự án thôi mà nhỉ, sao backend lại chặn retry của core

> nếu retry thành công thì lấy usage đó thôi chứ có gì đâu

Đã giải thích usage lần retry thành công không bao gồm chi phí có thể phát sinh ở lần timeout.
Theo hướng để core tự retry, bổ sung opt-in **chỉ trong approval operator tin cậy**:
`retry_unknown_within_cap=true`. Core vẫn tự quyết định retry/backoff/số lần qua adapter thật;
backend không viết vòng retry, không đổi thuật toán hoặc adapter lõi.

Mặc định của approval cũ vẫn chặn khi usage unknown. Web thường vẫn allow_spend=False,
không có cờ HTTP/Settings/UI để bật chi hoặc opt-in retry. Cờ approval phải là boolean thật,
validate trước composition; reference vẫn consume một lần, đúng PDF SHA/u-hash/HEAD/config/profile/DB.

Khi opt-in: mỗi lần timeout giữ nguyên reserve thành unknown upper. Mọi lần retry/request mới vẫn cần
`known + unknown upper + held + reserve <= cap`; hết trần/audit hỏng/bound sai vẫn chặn trước provider.
Không coi timeout là 0 USD. Khi core hoàn tất sau retry, wrapper giữ kết quả core và ghi
usage_complete=false nếu còn attempt thiếu usage; không tự đổi kết quả thành failed chỉ vì unknown
đã được owner cho phép tiếp tục trong trần. Nếu core thất bại hoặc guard thực sự dừng, vẫn failed.

## Bằng chứng 0 USD trước gọi thật

- RED policy: 5 ca mới thất bại trên API cũ chưa có opt-in.
- RED operator: 4 ca bắt cờ bị bỏ qua/không validate; ca mặc định còn đạt.
- RED kết quả: core retry trả vector nhưng wrapper đổi succeeded thành failed chỉ vì unknown.
- GREEN: **48 test operator/approval/guard đạt**, PostgreSQL thật, transport fake và guard mạng.
- Lượt GREEN đầu có một lỗi số học trong test: cap 0,72 nhỏ hơn hai reserve generation 0,720896.
  Đã sửa fixture cap thành 0,721: cho phép đúng lần retry thứ hai và vẫn bắt lần thứ ba trước provider.
  Giữ native thất bại, không bỏ test/cận trên hoặc giảm assertion.

## Vị trí lỗi đã biết, giả thuyết đang phân biệt

R5 whole-build cấu hình 100 hoàn tất concepts, canonical 161 node; A6 BuildClusters gửi 100 request
SEMANTIC_SIMILARITY, 19 đủ response, 81 timeout. SHA của cả 100 payload khớp chính xác đầu vào A6.
52 timeout sau HTTP 200 khi read body, 29 trước khi ghi được HTTP status. Không có lỗi generation ở đợt này.
Probe 100 RETRIEVAL_DOCUMENT trước đó đạt, nên không đồng nhất hai workload.

Môi trường kiểm 0 USD: Python 3.12.11 / OpenSSL 3.5.4, urllib không phát hiện proxy;
không có bằng chứng để quy nguyên nhân cho proxy, quota hay model không hỗ trợ task type.
Phép thử tiếp theo cần giữ core/retry nguyên bản, log thời gian nhận header, framing/content-length,
số byte đọc ở socket, traceback và hash request, không ghi Authorization/token hoặc raw nội dung PDF.

Ở mốc code `bd05c1b` chưa chạy thêm lượt có phí; kết quả sau phê duyệt mới ở mục cuối bên dưới. Mọi plan sau đây phải chuẩn bị mới ở đúng commit/config sẽ chạy,
không sửa/tái dùng plan R5. Giữ profile demo embedding_billing_verified=false và trần tổng R5+R6 dưới 4 USD.
Chi R5 theo giả định: known 1,28947575 USD, unknown upper 0,4139008 USD, tổng cận trên 1,70337655 USD.

Nguồn chính thức: [Python 3.12 urllib.request](https://docs.python.org/3.12/library/urllib.request.html)
ghi HTTP/1.1, Connection:close và timeout áp dụng cho thao tác blocking;
[Google Text embeddings API](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/model-reference/text-embeddings-api)
mô tả request/response riêng từng predict và các task type. Các nguồn này không chứng minh nguyên nhân timeout
của máy/lượt chạy này; kết luận phải dựa trên phép thử và log thực tế.

W-15 vẫn mở; kết quả, chi và câu hỏi tiếp theo ghi trực tiếp ở báo cáo này, không gửi message phiên khác.

## Kết quả cuối — lượt mới đã được duyệt

> bạn chạy lại thử luôn đi tôi duyệt tiền

Sau đó chủ dự án chốt hướng tích hợp:

> tôi thấy h biết nguyên nhân là 429 và core đã handle bằng retry, ta đâu cần nghiên cứu, chỉ cần theo họ là đc

Đã theo cơ chế retry/adaptive limiter sẵn có của core, không mở lượt nghiên cứu hoặc phép thử trả phí khác. Các kiểm tra sau dựng chỉ đọc với guard 0 USD.

**Thành công:** native exit 0, toàn lượt **633.92 giây = 10 phút 34 giây**, gồm prepare/ADC/HTTP/worker; không có khoảng nghỉ. Core chạy HEAD `bd05c1b2596d20709efd43c8350bf338af0a614f`; không thay HEAD từ prepare đến execute.
Graph v8, **16 module / 104 khái niệm học**, 14 formula refs; 33 tệp ảnh thật đã giải mã/verify dưới artifact riêng. Quality gate A9 passed=True.

Đếm trực tiếp artifact: **229 thực thể ứng viên, gộp thành 158 canonical node**; cuối cùng 104 khái niệm học,
41 mentioned và 13 non-learnable. Tổng 1.637 request gồm **715 generation + 922 embedding**;
hai lỗi 429 thuộc generation, không phải embedding. [Số đếm độc lập](w15-evidence/r6-20261025/entity-and-request-counts.json).

DB `wayfinder_w15_b5f1aa6534ce`; run `tmp/w15-operator-candidate-b5f1aa6534ce`; reference `w15-owner-core-retry-20261025-dc87f4746a5849c2a5f3b9c17d114a86`.
Pipeline `web-real:bd05c1b2596d20709efd43c8350bf338af0a614f:f0094970d6aedfb24a6c13d19853f72386b5ce4ba5a9dc3c57bb57ce31c7c268`. Plan vẫn approved=false, approval riêng có retry_unknown_within_cap=true; cả hai giữ embedding_billing_verified=false. SHA plan/approval nguồn ở provenance/manifest.

### Retry của core và thời gian từng bước

1.637 dispatch thật: 1.635 HTTP 200, hai HTTP 429 của generateContent ở concepts. Cùng payload bị 429 hai lần rồi có HTTP 200; core tự retry, không có vòng retry backend. 25 lần lặp hash payload trong toàn run còn gồm các thao tác model/repair khác, không gọi tất cả là transport retries.

Peak HTTP theo bước đo từ trace: `{'concepts': 100, 'graph': 49, 'learning_prep': 54}`. Cấu hình max_in_flight=100; sau 429 core tự giảm concurrency, nên graph peak 49, learning_prep peak 54. Không nhận là 100 generation đồng thời hoặc A6 đã vượt qua đúng burst 100 của lượt R5.

| Bước | Generation dispatch | Embedding dispatch | Known USD | Unknown upper USD | Wall giây | Embedding wait giây |
|---|---:|---:|---:|---:|---:|---:|
| doc_reading | 0 | 0 | 0 | 0 | 3.1704 | 0.0000 |
| concepts | 604 | 515 | 0.47390550 | 0 | 501.6158 | 122.0474 |
| graph | 111 | 303 | 0.20404855 | 0 | 99.9914 | 16.3010 |
| learning_prep | 0 | 104 | 0.00138150 | 0 | 6.8321 | 6.0235 |

Parse/chunks dùng bản dry-run cùng nguồn trong DB/artifact mới; label-roles/A3/A3-prime/canonical/graph/concept index là miss và được dựng trong lượt này. Không lấy cache/alias từ run cũ để ép reuse. Cache ngoài các cờ có receipt giữ unknown, không tự suy hit. Embedding wait là hợp khoảng wrapper, có thể gồm limiter/xác thực/retry, không riêng latency mạng.

Không có TimeoutError embedding hoặc unknown upper mới trong lượt R6. Hai 429 có guard actual_usd=0; core meter vẫn giữ usage_complete=false vì hai attempt không có usage response. Giữ nguyên cờ của core, không tự đổi thành true, không gọi các lần 429 là embedding unknown. Điều này khác 81 timeout A6 ở R5; lượt mới không chứng minh rằng 429 là nguyên nhân của những timeout cũ.

### SQL, HTTP và artifact độc lập

Một build attempt, một claim; grant finished/không replay; course `2721b2b6-dd64-4b95-92d4-93b673b25619` ready và pin graph v8. Sổ SQL cost 0.679336 USD khớp meter delta làm tròn 6 số. Trace counted_in=build có cột cost/token bằng 0, không cộng lại. Module/sequence phủ đủ khái niệm đúng một lần; hard requires là DAG và đúng topo; retrieval/chunks fingerprint tương thích.

Đã GET course/roadmap/progress có đăng nhập qua PG thật, HTTP 200, số module/concept/graph khớp; guard provider/ADC/SMTP chặn và ledger không tăng. Mail ConsoleMailer “Bản dựng xong”, không phải SMTP thật. Media local fake; endpoint source-page là payload giả 29 byte, không dùng làm bằng chứng ảnh PDF render thật. Các tệp ảnh/công thức Pha A đã verify trực tiếp, vẫn nằm ở filesystem, không chuyển vào DB/commit.

### Cổng, phạm vi và phần còn mở

Commit code **bd05c1b**: 6 tệp source/test thuộc W-15 + báo cáo, 48 focused pass; 3 mutation đều bị assertion bắt. Full gate ở đúng commit: **2.685 Python pass / 1 skip Cloudinary / 1 xfail SA-55 cũ**, native exit 0. Full test kết thúc trước khi run tới graph/A6; phần concepts có chồng thời gian đầu với full test, không dùng làm benchmark kiểm soát.

Không sửa core/adapter thuật toán, .env, alias/roles hoặc test để ép xanh. Root main vẫn 6249dab; không ghép/push main, không dọn DB/artifact/PDF. Frontend không đổi; cổng React/build đã nhận ở mốc trước, không ghi là đã chạy mới trong R6. Mốc dựng thật/tích hợp backend đã có bằng chứng; W-15 chờ người soát nghiệm thu, chưa triển khai product hay SMTP/Cloudinary thật.

## 10. Chi để bàn giao qua điều phối

Lượt R6: known theo profile demo **0.67933555 USD**, unknown upper **0 USD**, cap **2.25 USD**. Toàn R5+R6: known **1.96881130 USD**, unknown upper giữ lại **0.4139008 USD**, tổng cận trên **2.38271210 USD**, dưới 4 USD. Không đối soát hóa đơn; đơn vị giá embedding online chưa xác minh, vẫn embedding_billing_verified=false.

Báo cáo trực tiếp chủ dự án; điều phối có thể lấy nguyên mục 10 và [final audit](w15-evidence/r6-20261025/final-audit.json). Không gửi message hoặc sửa hồ sơ điều phối. [Manifest](w15-evidence/r6-20261025/manifest.json) và provenance giữ SHA tệp nguồn/bản lưu. Bản evidence chuẩn UTF-8/LF; plan/approval local thật giữ nguyên byte, grant đã consume, không chạy lại từ bản lưu.
