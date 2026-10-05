# v4 — Nhanh, rẻ, vẫn chuẩn: kế hoạch vé

**Nguyên tắc số một (chủ dự án, 2026-10-03):** đây là ứng dụng phục vụ người dùng, nên phải tối ưu **phút/cuốn** và **USD/cuốn** trước hết.
- Mỗi vé đo hai số trước và sau sửa, trên cùng bộ tài liệu: phút/cuốn và USD/cuốn.
- Chất lượng vẫn đo trên vàng. Cách tiết kiệm nào làm tụt chất lượng thì báo đánh đổi bằng số, chủ dự án quyết.
- Đường gọi sản phẩm là Gemini Developer API, song song cao. Vertex chỉ dùng khi còn credit.

**Nguồn:** [nghiên cứu tiền và thời gian](../../report/nghien-cuu-v4-chi-phi-thoi-gian-2026-10-04.md) ·
[kết quả tập giữ lại v3](../../report/ket-qua-tap-giu-lai-v3-2026-10-04.md) · mục "Hướng v4" của
[kế hoạch v3](../v3-lo-trinh-doc-duoc/00-ke-hoach.md).

**Mốc v3:** doc-4 (giáo trình trọn cuốn) tốn khoảng 50 USD; riêng A8 pass phụ 45,9 USD (91%) và khoảng 4,5–5 giờ trên Vertex.

**Trạng thái:**
- Chủ dự án giao 01/02 ngày 2026-10-04. Phần đo 02 đã xong. 01 đã được Claude kiểm: nhận tiêu chí cờ rộng hơn; còn thiếu mẫu theo dõi 3% và chưa
  commit.
- Từ 2026-10-05, việc chính là **pass phụ không LLM** (vé 11), vòng 1 đã xong.

## Quyết định của chủ dự án ngày 2026-10-05

- **Đồ án chỉ làm tài liệu tiếng Việt.** Luật đa ngôn ngữ không còn ràng buộc luồng chính; được dùng công cụ riêng tiếng Việt, ví dụ tách từ.
- **Pass phụ A8 bỏ LLM**, cho cả đồ án lẫn seminar. Luồng LLM cũ giữ lại, chọn được, để so sánh.
- **Đích dài hạn:** LLM chỉ còn ở A3 (trích ứng viên) và A8 pass chính (agent suy luận cạnh). Các khâu khác nghiên cứu bỏ LLM sau, từng khâu một.
- **A1:** đầu vào sau này sạch như doc-4 hay doc-1 (PDF có lớp chữ), nên chỉ cần nhanh nhất cho ứng dụng.
- Chủ dự án tự làm dữ liệu huấn luyện bằng agentic theo đặc tả của Claude ([D-01](D-01-dac-ta-du-lieu-pass-phu.md)).

## Ràng buộc sản phẩm từ nghiên cứu R-01 (Claude kiểm lại trên trang chính thức 2026-10-04)

Nghiên cứu [R-01](../../report/nghien-cuu-v4-gemini-va-rut-gon-ngu-canh-2026-10-04.md) đổi vài giả định của v4. Các điểm dưới đây Claude đã
tự đọc lại trên trang gốc:
- **Trần chi theo tháng trên cả tài khoản thanh toán** (trang Billing, 2026-09-28): bậc 1 250 USD, bậc 2 2.000 USD (đã trả 100 USD và qua
  3 ngày), bậc 3 20.000–100.000 USD. Chạm trần thì mọi project của tài khoản dừng tới chu kỳ sau. Theo giá v3, bậc 1 chỉ đủ khoảng 5 cuốn
  cỡ doc-4 mỗi tháng. Ngoài ra còn trần 10/50/200 USD mỗi 10 phút trượt.
- **Credit chào mừng của Google Cloud không trả được Gemini API**; Developer API phải nạp trước (Prepay). Đúng với cách đang làm: dùng
  Vertex trong lúc còn credit.
- **`gemini-3.1-flash-lite` tắt sớm nhất ngày 2027-05-07** (trang Deprecations). Mô hình thay thế `gemini-3.5-flash-lite` giá 0,30/2,50 USD,
  đắt hơn khoảng 31% mỗi lời gọi pass phụ. Đổi mô hình là đổi cấu hình, phải đo lại chất lượng.
- **Cache không áp dụng cho pass phụ**: dòng Gemini 3 cần tiền tố ít nhất 4.096 token, lớn hơn cả một lời gọi.
- **Batch** rẻ 50% nhưng mục tiêu 24 giờ, chỉ hợp việc nền. **Flex** rẻ 50%, gọi đồng bộ, độ trễ mục tiêu 1–15 phút: ứng viên cho người dùng
  chờ, cần thử nhỏ.
- RPM/TPM/RPD theo mô hình chỉ xem được trong AI Studio; phải xem trước khi chuyển sang Developer API (một cuốn cần khoảng 44.000 lời gọi).

## Dữ liệu dùng được

- Tập giữ lại v3 (xstk, doc-4) **đã dùng**. Từ v4, hai tài liệu này là tài liệu phát triển, cùng sáu tài liệu cũ.
- Mọi sửa chất lượng của v4 cần **tập giữ lại mới**: tài liệu mới và vàng mới, chọn trước khi sửa. Đổi tiền và thời gian mà đầu ra y hệt
  (như v4-01) thì không cần.

## Phạm vi theo khâu (cả Pha A, A1 → A10)

v4 là đợt tiếp theo của dự án, phủ mọi khâu. Mỗi khâu có thể có việc về thời gian, tiền hoặc chất lượng. Việc đổi đầu ra của một khâu thì
các khâu sau phải chạy lại, và nếu đổi chunk hay khái niệm thì phải ánh xạ lại vàng, nên các việc như vậy gom vào một lượt chạy lại.

| khâu | thời gian / tiền | chất lượng | nguồn bằng chứng |
|---|---|---|---|
| A1 đọc PDF (docling 2.114) | khoảng 7,2 giây/trang, tức khoảng 48 phút cho sách 400 trang. Pipeline song song theo trang **đã là mặc định**. Đòn bẩy chính: **OCR** (docling OCR mọi ảnh phủ ≥ 5% trang, kể cả trang có lớp chữ; engine tự chọn không đọc được dấu tiếng Việt và chữ OCR trong hình không tới adapter) và **số luồng** (mặc định 4, máy có 8 nhân) | công thức thành `[formula]`; cây mục dạng §1, §2; tách âm tiết doc-4 (`enforce_same_font`) | [R-03](../../report/nghien-cuu-v4-a1-docling-2026-10-04.md); script đo dở ở `tmp/thu-a1/` |
| A2 chunk, vai trò vùng | nhỏ | mục "Cách giải" bị gán đề cương (xstk 48/126 đoạn) | kết quả tập giữ lại |
| A3 trích khái niệm | khoảng 0,8 USD/cuốn | thiếu kết quả có tên (vé 13); độ hạt | v3 |
| A4/A5 gộp, mô tả | khoảng 0,6 USD/cuốn | — | — |
| A6 cụm, nhắc tên | nhỏ; số cặp ứng viên quyết định số lời gọi pass phụ | diễn đạt khác không thành cặp | v3 |
| A7, C8 neo, A9'' danh tính | khoảng 0,8 USD/cuốn | C8 không hỏi `kind` với khái niệm chỉ có căn cứ ngoài nội dung; neo sai câu (doc-4 "Kết cấu") | tập giữ lại, vé 21 |
| A8 pass chính, pass phụ | **khoảng 48 USD/cuốn, nhiều giờ**: v4-01, v4-03, bộ lọc cặp (R-02) | cạnh khái niệm khung (doc-4) | nghiên cứu tiền và thời gian |
| A9, A10, tên | gần 0 | R17 làm mềm cạnh ngược sách cả khi đúng (5/11 cạnh ngược doc-4); tên module theo cây mục hỏng | tập giữ lại |

## Vé

| vé | việc | ai | chi phí mô hình | trạng thái |
|---|---|---|---|---|
| [01](01-pass-phu-hoi-luoi.md) | A8 pass phụ hỏi lười thứ tự thứ hai: đầu ra y hệt, bớt 19–38% lời gọi | nhân viên | 0 (phát lại) | mã/test/replay xong; Claude nhận tiêu chí cờ rộng hơn; còn mẫu theo dõi 3% và commit. Từ 2026-10-05 chỉ còn giá trị cho luồng LLM làm mốc so sánh |
| [02](02-thoi-gian-moi-khau.md) | mọi stage ghi thời gian chạy; Claude viết báo cáo phút/USD mỗi cuốn | nhân viên + Claude | 0 | **xong**: phần nhân viên đạt; script `scripts/do-chi-phi/bao_cao.py` (Claude, `1f68209`); nhân viên chưa commit |
| 03 | thử hồ sơ cặp gọn cho pass phụ (bớt toàn văn đoạn) | Claude soạn sau 01 | khoảng 2–4 USD, chờ duyệt | chưa soạn |
| 04 | đọc nhật ký phản hồi lỗi của pass phụ (12% cặp doc-4) | Claude | 0 | chưa làm |
| 05 | sửa chất lượng từ tập giữ lại: A2 "Cách giải", C8 bỏ qua khái niệm ngoài nội dung, R17, cạnh khái niệm khung | Claude soạn | cần tập giữ lại mới | chưa soạn |
| T-01 | chọn 2 tài liệu mới và người gán vàng cho tập giữ lại v4 | **chủ dự án** | 0 | chưa làm |
| R-01 | nghiên cứu nguồn gốc: Gemini Developer API (giá, giới hạn, cache, Batch), rút gọn ngữ cảnh, độ lệch vị trí → [báo cáo](../../report/nghien-cuu-v4-gemini-va-rut-gon-ngu-canh-2026-10-04.md) | Claude (tác tử nền) | 0 | **xong 2026-10-04** |
| 06 | đổi `responseJsonSchema` (đã deprecated) sang `responseFormat` ở bộ chuyển đổi Gemini, kiểm bằng phát lại; xử lý lỗi 402 khi hết tiền nạp trước | nhân viên | 0 | chưa soạn |
| 07 | thử Flex nhỏ: độ trễ thật, tỉ lệ bị từ chối (503), đầu ra có y hệt Standard không | Claude soạn | dưới 1 USD, chờ duyệt | chưa soạn |
| 08 | kế hoạch chuyển sang `gemini-3.5-flash-lite` trước 2027-05: đo chất lượng và USD/cuốn | Claude soạn | cần tập giữ lại mới | chưa soạn |
| R-02 | nghiên cứu ML/DL: lọc cặp trước pass phụ (v4) và học tiên quyết không LLM (seminar) → [báo cáo](../../report/nghien-cuu-ml-dl-loc-cap-va-tien-quyet-2026-10-04.md) | Claude (tác tử nền) | 0 | **xong 2026-10-04** |
| R-03 | nghiên cứu A1: tuỳ chọn tốc độ của docling 2.114 (đọc mã nguồn đã cài), tuỳ chọn nào giữ nguyên đầu ra, nhận dạng công thức chạy tại máy → [báo cáo](../../report/nghien-cuu-v4-a1-docling-2026-10-04.md) | Claude (tác tử nền) | 0 | **xong 2026-10-04** |
| [09](09-khoa-cache-parse.md) | khoá cache parse gồm **mọi** tuỳ chọn pipeline docling và engine OCR ghi đích danh (không để tự chọn), để đổi tuỳ chọn không âm thầm dùng lại parse cũ; chỉ ghi tuỳ chọn khác mặc định nên băm cũ giữ nguyên; làm trước mọi đổi A1 | nhân viên | 0 | **soạn xong 2026-10-05**, chờ giao |
| 10 | đo A1 tại máy (0 USD): cấu hình hiện tại chạy hai lần (có tất định không), số luồng 8, tắt OCR, rồi các tuỳ chọn khác; kiểm đầu ra y hệt ở bốn tầng (JSON docling, từng mục, adapter, tập `chunk_id`); chạy lúc máy rảnh | Claude | 0 | **lượt 1 xong** → [báo cáo](../../report/v4-10-do-a1-tai-may-2026-10-05.md): docling tất định; 8 luồng giữ đầu ra; tắt OCR giữ đầu ra trên PDF có lớp chữ. Số giây bị nhiễu, phải đo lại lúc máy rảnh, sau vé 09 Lượt 2 và bước 2 → [báo cáo](../../report/v4-10-buoc-2-bo-doc-nhe-2026-10-05.md): chia đoạn song song đầu ra y hệt nhưng **không nhanh hơn trên laptop 15 W**; bộ đọc nhẹ pypdfium2 nhanh hơn 35–150 lần, sách chữ (doc-4) gần như thay được, sách toán chưa (công thức, bảng). Đề xuất chọn bộ đọc theo tín hiệu font toán; muốn đưa vào luồng thì cần thí nghiệm có tốn tiền ở các khâu sau (doc-4, khoảng 4–5 USD), chờ duyệt |
| 11 | **pass phụ A8 không LLM** (đồ án và seminar): ứng viên = tên X trong cửa sổ định nghĩa Y theo ranh giới từ tiếng Việt; LightGBM học ý định cạnh cứng của LLM; lắp cạnh tất định qua hợp đồng vé 12 | Claude nghiên cứu; nhân viên triển khai sau vòng 2 | 0 | **vòng 1 xong** → [báo cáo](../../report/nghien-cuu-pass-phu-khong-llm-vong-1-2026-10-05.md): doc-4 hơn LLM cả bốn chỉ số, doc-1 sát, xstk kém độ phủ; 0 USD, khoảng 1–2 phút/cuốn so với 45,9 USD và 4,5–5 giờ. Vòng 2 chờ dữ liệu D-01 |
| [D-01](D-01-dac-ta-du-lieu-pass-phu.md) | dữ liệu huấn luyện đa lĩnh vực cho vé 11: chủ dự án gom ≥ 12 giáo trình tiếng Việt (2 cuốn để riêng làm T-01), gán nhãn bằng agentic theo đặc tả | **chủ dự án** gom và gán; Claude chạy luồng, xuất phiếu, kiểm | chạy A1 → A8 pass chính trên sách mới: chờ dự toán và duyệt | đặc tả xong 2026-10-05 |
